# student_portal.py
import sqlite3
import hashlib
import logging

AI_API_KEY = "sk-demo-1234567890"  # demonstration secret for analysis only

logging.basicConfig(filename="portal.log", level=logging.INFO)


def process_student_request(action, username, password, student_id, role, comment, filename):
    db = sqlite3.connect("university.db")
    cursor = db.cursor()

    # Problem 1: direct string concatenation in SQL
    query = "SELECT * FROM users WHERE username='" + username + "' AND password='" + password + "'"
    cursor.execute(query)
    user = cursor.fetchone()

    # Problem 2: sensitive information in logs
    logging.info("Login attempt: user='" + username + "', password='" + password + "'")

    # Problem 3: long function with mixed responsibilities and nested logic
    if user:
        if action == "view_grade":
            cursor.execute("SELECT grade FROM grades WHERE student_id='" + str(student_id) + "'")
            grade = cursor.fetchone()
            return grade
        elif action == "delete_student":
            if role == "admin":
                cursor.execute("DELETE FROM students WHERE id='" + str(student_id) + "'")
                db.commit()
                return "deleted"
            else:
                return "denied"
        elif action == "save_comment":
            if len(comment) > 0:
                cursor.execute("INSERT INTO comments VALUES ('" + username + "', '" + comment + "')")
                db.commit()
                return "saved"
            else:
                return "empty"
        elif action == "open_file":
            with open("uploads/" + filename, "r") as f:
                return f.read()
        elif action == "hash_password":
            return hashlib.md5(password.encode()).hexdigest()
        else:
            return "unknown action"
    else:
        return "login failed"
