from flask import Flask, render_template, request, redirect, session
import os
import datetime
import threading
import smtplib
from email.message import EmailMessage

import os
os.environ["MONGO_URI"] = "mongodb+srv://umiraoutlook_db_user:umira123@cluster0.x4b4h0j.mongodb.net/mcq_system?retryWrites=true&w=majority&appName=Cluster0"
os.environ["SECRET_KEY"] = "super_secret_mcq_key_123"

from db import get_db, init_indexes
from mongo_data import (
    authenticate_student,
    get_random_exam_questions,
    get_subjects_for_semester,
    load_subjects_by_semester,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super_secret_mcq_key_123")

db = get_db()
exam_results = db["exam_results"]

init_indexes()


def require_login():
    return "user" in session


def require_exam_selection():
    return require_login() and session.get("exam_selection")


def build_result_query(user, selection):
    return {
        "register_number": user["register_number"],
        "subject_code": selection["subject_code"],
        "cia": selection["cia"],
    }


def load_existing_result(user, selection):
    return exam_results.find_one(build_result_query(user, selection))


def populate_result_session(result):
    session["score"] = result["score"]
    session["total"] = result["total"]
    session["correct"] = result.get("correct", result["score"])
    session["wrong"] = result.get("wrong", result["total"] - result["score"])
    session["unanswered"] = result.get("unanswered", 0)
    session["exam_date"] = result.get("exam_date", "N/A")
    session["violation"] = result.get("terminated_due_to_violation", False)


def send_result_email_async(user, selection, score, total, correct, wrong, unanswered, violation, exam_date):
    email = user.get("email")
    if not email:
        return

    def send_email():
        try:
            sender_email = os.environ.get("SMTP_EMAIL", "thenewcollegemcq@gmail.com")
            sender_password = os.environ.get("SMTP_PASSWORD", "slsk jyio adui qzej")

            msg = EmailMessage()
            msg["Subject"] = "CIA Assessment Result - The New College"
            msg["From"] = sender_email
            msg["To"] = email

            percentage = (score / total) * 100 if total > 0 else 0
            status_text = "Exam Terminated (Violation)" if violation else ("Passed" if percentage >= 50 else "Failed")

            msg.set_content(
                f"Hello {user.get('name', '')},\n\n"
                f"Register Number: {user.get('register_number', '')}\n"
                f"Subject: {selection.get('subject_title', '')}\n"
                f"CIA: {selection.get('cia', '')}\n"
                f"Score: {score}/{total} ({percentage:.2f}%)\n"
                f"Status: {status_text}\n"
                f"Date: {exam_date}\n"
            )

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, sender_password)
                server.send_message(msg)
        except Exception as e:
            print(f"Failed to send email: {e}")

    threading.Thread(target=send_email, daemon=True).start()


@app.route("/api/questions")
def api_questions():
    if not require_exam_selection():
        return {"error": "Unauthorized"}, 401

    selection = session["exam_selection"]
    subject_code = selection.get("subject_code")
    selected = get_random_exam_questions(subject_code, count=10)

    if not selected:
        return {"error": "No questions available for this subject. Contact your administrator."}, 503

    session["exam_answers"] = {q["id"]: q["answer"] for q in selected}

    frontend_questions = [
        {"id": q["id"], "question": q["question"], "options": q["options"]}
        for q in selected
    ]
    return {"questions": frontend_questions}


@app.route("/api/subjects/<int:semester>")
def api_subjects(semester):
    if not require_login():
        return {"error": "Unauthorized"}, 401
    if semester < 1 or semester > 6:
        return {"error": "Invalid semester"}, 400
    return {"subjects": get_subjects_for_semester(semester)}


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        register_number = request.form.get("register_number", "").strip()
        dob = request.form.get("dob", "").strip()

        student = authenticate_student(register_number, dob)
        if not student:
            return render_template(
                "login.html",
                error="Invalid Register Number or Date of Birth. Please check your college records.",
            )

        session.clear()
        session["user"] = student
        return redirect("/select-exam")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/select-exam", methods=["GET", "POST"])
def select_exam():
    if not require_login():
        return redirect("/login")

    user = session["user"]
    error = None

    if request.method == "POST":
        semester = request.form.get("semester", "").strip()
        subject_code = request.form.get("subject_code", "").strip()
        cia = request.form.get("cia", "").strip()

        if semester not in {"1", "2", "3", "4", "5", "6"}:
            error = "Please select a valid semester (1 to 6)."
        elif cia not in {"1", "2"}:
            error = "Please select CIA 1 or CIA 2."
        else:
            subjects = get_subjects_for_semester(semester)
            subject = next((s for s in subjects if s["subject_code"] == subject_code), None)
            if not subject:
                error = "Please select a valid subject for the chosen semester."
            else:
                selection = {
                    "semester": int(semester),
                    "subject_code": subject["subject_code"],
                    "subject_title": subject["subject_title"],
                    "cia": int(cia),
                }
                session["exam_selection"] = selection

                existing = load_existing_result(user, selection)
                if existing:
                    populate_result_session(existing)
                    return redirect("/result")

                return redirect("/exam")

    return render_template(
        "select_exam.html",
        user=user,
        error=error,
        semesters=list(range(1, 7)),
        subjects_by_semester=load_subjects_by_semester(),
    )


@app.route("/exam", methods=["GET", "POST"])
def exam():
    if not require_exam_selection():
        return redirect("/select-exam")

    user = session["user"]
    selection = session["exam_selection"]

    if request.method == "GET":
        existing = load_existing_result(user, selection)
        if existing:
            populate_result_session(existing)
            return redirect("/result")

    if request.method == "POST":
        score = 0
        unanswered = 0
        wrong = 0
        exam_answers = session.get("exam_answers", {})

        for q_id, correct_ans in exam_answers.items():
            user_ans = request.form.get(q_id)
            if not user_ans:
                unanswered += 1
            elif user_ans == correct_ans:
                score += 1
            else:
                wrong += 1

        violation_submit = request.form.get("violation_submit") == "true"
        exam_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        result_doc = {
            "register_number": user["register_number"],
            "name": user["name"],
            "dob": user["dob"],
            "programme": user["programme"],
            "admission_year": user["admission_year"],
            "semester": selection["semester"],
            "subject_code": selection["subject_code"],
            "subject_title": selection["subject_title"],
            "cia": selection["cia"],
            "score": score,
            "total": len(exam_answers),
            "correct": score,
            "wrong": wrong,
            "unanswered": unanswered,
            "terminated_due_to_violation": violation_submit,
            "exam_date": exam_date,
        }

        exam_results.update_one(
            build_result_query(user, selection),
            {"$set": result_doc},
            upsert=True,
        )

        populate_result_session(result_doc)
        send_result_email_async(
            user=user,
            selection=selection,
            score=score,
            total=len(exam_answers),
            correct=score,
            wrong=wrong,
            unanswered=unanswered,
            violation=violation_submit,
            exam_date=exam_date,
        )
        return redirect("/result")

    exam_user = {
        **user,
        "subject": selection["subject_title"],
        "subject_code": selection["subject_code"],
        "semester": selection["semester"],
        "cia": selection["cia"],
    }
    return render_template("exam.html", user=exam_user)


@app.route("/result")
def result():
    if "score" not in session or not require_login():
        return redirect("/login")

    user = session.get("user", {})
    selection = session.get("exam_selection", {})

    display_user = {
        **user,
        "subject": selection.get("subject_title", user.get("subject", "N/A")),
        "subject_code": selection.get("subject_code", ""),
        "semester": selection.get("semester", ""),
        "cia": selection.get("cia", ""),
    }

    return render_template(
        "result.html",
        score=session["score"],
        total=session["total"],
        correct=session.get("correct", session["score"]),
        wrong=session.get("wrong", session["total"] - session["score"]),
        unanswered=session.get("unanswered", 0),
        exam_date=session.get("exam_date", "N/A"),
        user=display_user,
        violation=session.get("violation", False),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
