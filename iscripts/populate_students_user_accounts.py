import re
import bcrypt
from pymongo import MongoClient

# MongoDB connection

try:
    client = MongoClient("mongodb+srv://aldenroxy:N53wxkFIvbAJjZjc@cluster0.l7fdbmf.mongodb.net")
    db = client['mit261']
    students = db["students"]
    userAccounts = db["userAccounts"]
    print("✅ Successfully connected to MongoDB!")
except Exception as e:
    print(f"❌ Error connecting to MongoDB: {e}")
    sys.exit()


def generate_password_hash(password: str) -> bytes:
    """
    Generates a bcrypt hash for a given plain-text password.
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed


def create_student_username(full_name: str) -> str:
    """
    Converts student name into a username.
    Example: "Jones, Gracy I." -> "jonesg"
    Rule: lastname + first initial (all lowercase)
    """
    name = full_name.strip()
    # split "Lastname, Firstname Middlename"
    if "," in name:
        last, rest = [p.strip() for p in name.split(",", 1)]
    else:
        parts = name.split()
        last, rest = parts[-1], " ".join(parts[:-1])

    first_name = rest.split()[0] if rest else ""
    username = f"{last}{first_name[0] if first_name else ''}".lower()
    username = re.sub(r"[^a-z0-9]", "", username)  # clean unwanted chars
    return username


def main():
    # Get all students
    student_list = students.find()

    for student in student_list:
        full_name = student.get("Name", "").strip()
        sid = student.get("_id")

        username = create_student_username(full_name)
        password_hash = generate_password_hash("password")

        user_doc = {
            "username": username,
            "role": "student",
            "linkedId": sid,  # link to student._id
            "passwordHash": password_hash,
            "fullName": full_name,
            "UID": sid,
        }

        # Avoid duplicates
        if not userAccounts.find_one({"username": username}):
            userAccounts.insert_one(user_doc)
            print(f"Inserted: {username}")
        else:
            print(f"Skipped (already exists): {username}")


if __name__ == "__main__":
    main()
