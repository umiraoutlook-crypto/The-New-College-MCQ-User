"""
One-time / repeatable seed script: imports CIA student data and semester subjects
from CSV, then creates 5 private question categories (Semester 5 subjects) with
sample MCQs. Run: python seed_database.py
"""

import csv
import os

os.environ["MONGO_URI"] = "mongodb+srv://umiraoutlook_db_user:umira123@cluster0.x4b4h0j.mongodb.net/mcq_system?retryWrites=true&w=majority&appName=Cluster0"
os.environ["SECRET_KEY"] = "super_secret_mcq_key_123"

from db import get_db, init_indexes
from mongo_data import parse_dob_to_iso

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CIA_DATA_PATH = os.path.join(BASE_DIR, "Cia Data.csv")
SEMESTER_PATH = os.path.join(BASE_DIR, "Semester.csv")

SAMPLE_QUESTIONS = {
    "24BQM509": [
        {
            "question": "Who is known as the 'Father of the Nation' in India?",
            "options": {"a": "Mahatma Gandhi", "b": "Jawaharlal Nehru", "c": "Subhas Chandra Bose", "d": "B.R. Ambedkar"},
            "answer": "a",
        },
        {
            "question": "In which year did the Jallianwala Bagh massacre take place?",
            "options": {"a": "1917", "b": "1919", "c": "1921", "d": "1930"},
            "answer": "b",
        },
        {
            "question": "The Non-Cooperation Movement was launched in which year?",
            "options": {"a": "1919", "b": "1920", "c": "1921", "d": "1922"},
            "answer": "b",
        },
        {
            "question": "Who founded the Indian National Congress in 1885?",
            "options": {"a": "A.O. Hume", "b": "Dadabhai Naoroji", "c": "W.C. Bonnerjee", "d": "Bal Gangadhar Tilak"},
            "answer": "a",
        },
        {
            "question": "The Quit India Movement was launched in:",
            "options": {"a": "1930", "b": "1935", "c": "1942", "d": "1947"},
            "answer": "c",
        },
        {
            "question": "Who was the Viceroy of India during the partition of Bengal (1905)?",
            "options": {"a": "Lord Curzon", "b": "Lord Ripon", "c": "Lord Minto", "d": "Lord Hardinge"},
            "answer": "a",
        },
        {
            "question": "The Simon Commission arrived in India in:",
            "options": {"a": "1927", "b": "1928", "c": "1929", "d": "1930"},
            "answer": "b",
        },
        {
            "question": "Who wrote the book 'India Wins Freedom'?",
            "options": {"a": "Jawaharlal Nehru", "b": "Maulana Abul Kalam Azad", "c": "Sardar Patel", "d": "Rajendra Prasad"},
            "answer": "b",
        },
        {
            "question": "The Dandi March was associated with protest against:",
            "options": {"a": "Rowlatt Act", "b": "Salt Tax", "c": "Partition of Bengal", "d": "Simon Commission"},
            "answer": "b",
        },
        {
            "question": "Who was known as 'Lokmanya'?",
            "options": {"a": "Gopal Krishna Gokhale", "b": "Bal Gangadhar Tilak", "c": "Lala Lajpat Rai", "d": "Bipin Chandra Pal"},
            "answer": "b",
        },
    ],
    "24BQM510": [
        {
            "question": "World War I began in which year?",
            "options": {"a": "1912", "b": "1914", "c": "1916", "d": "1918"},
            "answer": "b",
        },
        {
            "question": "The Balfour Declaration of 1917 concerned:",
            "options": {"a": "Sykes-Picot Agreement", "b": "A Jewish homeland in Palestine", "c": "Oil rights in Persia", "d": "Independence of Egypt"},
            "answer": "b",
        },
        {
            "question": "Which country was formerly known as Persia?",
            "options": {"a": "Iraq", "b": "Iran", "c": "Turkey", "d": "Syria"},
            "answer": "b",
        },
        {
            "question": "The Suez Canal connects the Mediterranean Sea with:",
            "options": {"a": "Persian Gulf", "b": "Red Sea", "c": "Arabian Sea", "d": "Black Sea"},
            "answer": "b",
        },
        {
            "question": "The Arab Spring protests began prominently in:",
            "options": {"a": "2009", "b": "2010", "c": "2011", "d": "2012"},
            "answer": "c",
        },
        {
            "question": "OPEC was founded primarily to coordinate policies on:",
            "options": {"a": "Natural gas", "b": "Petroleum", "c": "Coal", "d": "Nuclear energy"},
            "answer": "b",
        },
        {
            "question": "The Sykes-Picot Agreement divided spheres of influence in:",
            "options": {"a": "Africa", "b": "Middle East", "c": "South Asia", "d": "Central Asia"},
            "answer": "b",
        },
        {
            "question": "Which city is considered holy in Islam, Christianity, and Judaism?",
            "options": {"a": "Mecca", "b": "Jerusalem", "c": "Cairo", "d": "Baghdad"},
            "answer": "b",
        },
        {
            "question": "The Iran-Iraq War lasted approximately:",
            "options": {"a": "1975-1979", "b": "1980-1988", "c": "1990-1991", "d": "2003-2011"},
            "answer": "b",
        },
        {
            "question": "Gamal Abdel Nasser was a prominent leader of:",
            "options": {"a": "Saudi Arabia", "b": "Egypt", "c": "Jordan", "d": "Lebanon"},
            "answer": "b",
        },
    ],
    "24BQM511": [
        {
            "question": "The French Revolution began in:",
            "options": {"a": "1776", "b": "1789", "c": "1799", "d": "1815"},
            "answer": "b",
        },
        {
            "question": "Napoleon Bonaparte was finally defeated at:",
            "options": {"a": "Austerlitz", "b": "Waterloo", "c": "Leipzig", "d": "Trafalgar"},
            "answer": "b",
        },
        {
            "question": "The Congress of Vienna (1815) aimed to:",
            "options": {"a": "Spread revolution", "b": "Restore stability after Napoleon", "c": "Divide Africa", "d": "Form the League of Nations"},
            "answer": "b",
        },
        {
            "question": "Karl Marx co-authored which influential work?",
            "options": {"a": "Wealth of Nations", "b": "Communist Manifesto", "c": "Social Contract", "d": "Leviathan"},
            "answer": "b",
        },
        {
            "question": "The unification of Germany was largely completed under:",
            "options": {"a": "Kaiser Wilhelm I and Bismarck", "b": "Frederick the Great", "c": "Hitler", "d": "Metternich"},
            "answer": "a",
        },
        {
            "question": "The Industrial Revolution is most closely associated with which country first?",
            "options": {"a": "France", "b": "Britain", "c": "Germany", "d": "Russia"},
            "answer": "b",
        },
        {
            "question": "World War I ended with the signing of the Treaty of:",
            "options": {"a": "Paris", "b": "Versailles", "c": "Vienna", "d": "Brest-Litovsk"},
            "answer": "b",
        },
        {
            "question": "The Russian Revolution of 1917 overthrew:",
            "options": {"a": "The Romanov dynasty", "b": "The Habsburg dynasty", "c": "The Bourbon dynasty", "d": "The Hohenzollern dynasty"},
            "answer": "a",
        },
        {
            "question": "Benito Mussolini led which European country?",
            "options": {"a": "Spain", "b": "Italy", "c": "Portugal", "d": "Greece"},
            "answer": "b",
        },
        {
            "question": "The Enlightenment emphasized:",
            "options": {"a": "Divine right of kings", "b": "Reason and individual rights", "c": "Feudal obligations", "d": "Isolationism"},
            "answer": "b",
        },
    ],
    "24BQM512": [
        {
            "question": "The American Declaration of Independence was adopted in:",
            "options": {"a": "1774", "b": "1776", "c": "1783", "d": "1789"},
            "answer": "b",
        },
        {
            "question": "Who was the first President of the United States?",
            "options": {"a": "Thomas Jefferson", "b": "George Washington", "c": "John Adams", "d": "Benjamin Franklin"},
            "answer": "b",
        },
        {
            "question": "The American Civil War was fought between:",
            "options": {"a": "1775-1783", "b": "1812-1815", "c": "1861-1865", "d": "1898-1901"},
            "answer": "c",
        },
        {
            "question": "The Emancipation Proclamation was issued by:",
            "options": {"a": "George Washington", "b": "Abraham Lincoln", "c": "Ulysses S. Grant", "d": "Andrew Johnson"},
            "answer": "b",
        },
        {
            "question": "The Louisiana Purchase was made during the presidency of:",
            "options": {"a": "Madison", "b": "Jefferson", "c": "Monroe", "d": "Jackson"},
            "answer": "b",
        },
        {
            "question": "The New Deal was introduced by President:",
            "options": {"a": "Hoover", "b": "Franklin D. Roosevelt", "c": "Truman", "d": "Eisenhower"},
            "answer": "b",
        },
        {
            "question": "The USA entered World War I in:",
            "options": {"a": "1914", "b": "1915", "c": "1917", "d": "1918"},
            "answer": "c",
        },
        {
            "question": "The 19th Amendment to the US Constitution granted:",
            "options": {"a": "Abolition of slavery", "b": "Women's suffrage", "c": "Prohibition", "d": "Direct election of senators"},
            "answer": "b",
        },
        {
            "question": "The Marshall Plan aimed to:",
            "options": {"a": "Rebuild Europe after WWII", "b": "Invade Vietnam", "c": "Annex Cuba", "d": "Establish NATO only"},
            "answer": "a",
        },
        {
            "question": "The Watergate scandal led to the resignation of:",
            "options": {"a": "Lyndon Johnson", "b": "Richard Nixon", "c": "Gerald Ford", "d": "Jimmy Carter"},
            "answer": "b",
        },
    ],
    "24BQM513": [
        {
            "question": "Mahatma Gandhi was born in which year?",
            "options": {"a": "1869", "b": "1875", "c": "1885", "d": "1890"},
            "answer": "a",
        },
        {
            "question": "Gandhi's philosophy of non-violence is called:",
            "options": {"a": "Satyagraha", "b": "Swaraj", "c": "Khilafat", "d": "Swadeshi"},
            "answer": "a",
        },
        {
            "question": "Gandhi led the Champaran Satyagraha in:",
            "options": {"a": "1915", "b": "1917", "c": "1919", "d": "1920"},
            "answer": "b",
        },
        {
            "question": "The concept of 'Swadeshi' emphasizes:",
            "options": {"a": "Foreign imports", "b": "Use of indigenous goods", "c": "Military action", "d": "Urban industrialization"},
            "answer": "b",
        },
        {
            "question": "Gandhi's autobiography is titled:",
            "options": {"a": "Discovery of India", "b": "My Experiments with Truth", "c": "Hind Swaraj", "d": "India Wins Freedom"},
            "answer": "b",
        },
        {
            "question": "Gandhi's first major civil disobedience in South Africa is associated with:",
            "options": {"a": "Pass laws", "b": "Salt tax", "c": "Partition", "d": "Quit India"},
            "answer": "a",
        },
        {
            "question": "The Sabarmati Ashram was established in:",
            "options": {"a": "Delhi", "b": "Ahmedabad", "c": "Wardha", "d": "Sevagram"},
            "answer": "b",
        },
        {
            "question": "Gandhi advocated village self-rule through:",
            "options": {"a": "Panchayat Raj only", "b": "Swaraj", "c": "Dyarchy", "d": "Federalism"},
            "answer": "b",
        },
        {
            "question": "The Khadi movement promoted:",
            "options": {"a": "Hand-spun cloth", "b": "British textiles", "c": "Silk exports", "d": "Mechanized mills"},
            "answer": "a",
        },
        {
            "question": "Gandhi's fast unto death in 1932 was related to:",
            "options": {"a": "Communal Award / separate electorates", "b": "Salt tax", "c": "Partition", "d": "World War II"},
            "answer": "a",
        },
    ],
}


def seed_students():
    db = get_db()
    db.students.delete_many({})

    students = []
    with open(CIA_DATA_PATH, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            reg_no = (row.get("Reg. No.") or "").strip()
            if not reg_no:
                continue
            dob_iso = parse_dob_to_iso(row.get("D.O.B", ""))
            students.append(
                {
                    "register_number": reg_no,
                    "name": (row.get("Name") or "").strip(),
                    "dob": dob_iso,
                    "dob_display": (row.get("D.O.B") or "").strip(),
                    "programme": (row.get("Programme") or "").strip(),
                    "admission_year": (row.get("Adm. year") or "").strip(),
                    "serial_no": (row.get("Sl") or "").strip(),
                }
            )

    if students:
        db.students.insert_many(students)
    return len(students)


def seed_subjects():
    db = get_db()
    db.subjects.delete_many({})

    subjects = []

    with open(SEMESTER_PATH, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            semester_raw = (row.get("Semester") or "").strip()
            subject_code = (row.get("Subject Code") or "").strip()
            subject_title = (row.get("Subject Title") or "").strip()
            if not semester_raw or not subject_code:
                continue

            semester = int(semester_raw)
            subjects.append(
                {
                    "semester": semester,
                    "subject_code": subject_code,
                    "subject_title": subject_title,
                }
            )

    if subjects:
        db.subjects.insert_many(subjects)

    return len(subjects)


def main():
    init_indexes()
    student_count = seed_students()
    subject_count = seed_subjects()

    print("MongoDB seed completed successfully.")
    print(f"  Students imported:          {student_count}")
    print(f"  Subjects imported:            {subject_count}")


if __name__ == "__main__":
    main()
