from datetime import datetime

from db import get_db


def parse_dob_to_iso(dob_str):
    """Normalize DOB from CSV (M/D/YYYY) or HTML date input (YYYY-MM-DD)."""
    dob_str = (dob_str or "").strip()
    if not dob_str:
        return None

    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(dob_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    parts = dob_str.replace("-", "/").split("/")
    if len(parts) == 3:
        try:
            if len(parts[0]) == 4:
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            else:
                m, d, y = int(parts[0]), int(parts[1]), int(parts[2])
            return datetime(y, m, d).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            return None
    return None


def authenticate_student(register_number, dob_input):
    register_number = (register_number or "").strip()
    dob_iso = parse_dob_to_iso(dob_input)
    if not register_number or not dob_iso:
        return None

    student = get_db().students.find_one(
        {"register_number": register_number, "dob": dob_iso},
        {"_id": 0},
    )
    return student


def load_subjects_by_semester():
    by_semester = {str(i): [] for i in range(1, 7)}
    cursor = get_db().subjects.find({}, {"_id": 0, "semester": 1, "subject_code": 1, "subject_title": 1}).sort(
        [("semester", 1), ("subject_code", 1)]
    )
    for doc in cursor:
        semester = str(doc.get("semester", ""))
        if semester in by_semester:
            by_semester[semester].append(
                {
                    "subject_code": doc["subject_code"],
                    "subject_title": doc["subject_title"],
                }
            )
    return by_semester


def get_subjects_for_semester(semester):
    return load_subjects_by_semester().get(str(semester), [])


def get_random_exam_questions(subject_code, count=10):
    """
    Pull random questions for an active exam.
    Question categories and the full bank are never exposed via public routes.
    """
    subject_code = (subject_code or "").strip()
    if not subject_code:
        return []

    pipeline = [
        {"$match": {"subject_code": subject_code, "status": "live"}},
        {"$sample": {"size": count}},
        {
            "$project": {
                "id": {"$toString": "$_id"},
                "question": "$question_text",
                "options": 1,
                "answer": "$correct_answer",
                "_id": 0,
            }
        },
    ]
    return list(get_db()["Live questions"].aggregate(pipeline))
