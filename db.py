import os

from pymongo import ASCENDING, MongoClient

MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://umiraoutlook_db_user:umira123@cluster0.x4b4h0j.mongodb.net/mcq_system?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = os.environ.get("MONGO_DB_NAME", "mcq_system")

_client = None
_db = None


def get_client():
    global _client
    if _client is None:
        if not MONGO_URI:
            raise RuntimeError(
                "MONGO_URI environment variable is required. "
                "Set it to your MongoDB Atlas connection string."
            )
        _client = MongoClient(MONGO_URI)
    return _client


def get_db():
    global _db
    if _db is None:
        _db = get_client()[DB_NAME]
    return _db


def init_indexes():
    """Ensure indexes exist without dropping or modifying data."""
    db = get_db()

    db.students.create_index([("register_number", ASCENDING)], unique=True, name="register_number_unique")
    db.subjects.create_index([("semester", ASCENDING), ("subject_code", ASCENDING)], unique=True, name="semester_subject_unique")
    db["Live questions"].create_index([("subject_code", ASCENDING), ("status", ASCENDING)], name="live_questions_by_subject")
    db.exam_results.create_index(
        [("register_number", ASCENDING), ("subject_code", ASCENDING), ("cia", ASCENDING)],
        unique=True,
        name="unique_attempt_per_subject_cia",
    )
    db.exam_results.create_index([("exam_date", ASCENDING)], name="exam_date_idx")
