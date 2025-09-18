import re
import bcrypt
from pymongo import MongoClient

# MongoDB connection

try:
    client = MongoClient("mongodb+srv://aldenroxy:N53wxkFIvbAJjZjc@cluster0.l7fdbmf.mongodb.net")
    db = client['mit261']
    subjects = db["subjects"]
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


def create_username(full_name: str) -> str:
    """
    Converts a teacher's full name into a username.
    Example: "Prof. Tony Lim" -> "prof_tlim"
    """
    # lower case
    name = full_name.strip().lower()

    # remove unwanted characters except dot and space
    name = re.sub(r"[^a-z.\s]", "", name)

    parts = name.split()
    if len(parts) == 1:
        return parts[0]  # just in case only one word

    # first part could be title (prof., dr., etc.)
    if parts[0].endswith("."):
        title = parts[0]
        first_name = parts[1]
        last_name = parts[-1]
    else:
        title = "prof"
        first_name = parts[0]
        last_name = parts[-1]

    username = f"{title}_{first_name[0]}{last_name}"
    username = username.replace(".", "")  # remove dot from prof.
    return username


def main():
    # Get unique teacher names
    teacher_names = subjects.distinct("Teacher")

    for idx, teacher in enumerate(teacher_names, start=1):
        username = create_username(teacher)
        password_hash = generate_password_hash("password")

        user_doc = {
            "username": username,
            "role": "teacher",
            "linkedId": idx,  # assuming auto incremental link ID (adjust if needed)
            "passwordHash": password_hash,
            "fullName": teacher,
            "UID": None,
        }

        # Check if already exists to avoid duplicates
        if not userAccounts.find_one({"username": username}):
            userAccounts.insert_one(user_doc)
            print(f"Inserted: {username}")
        else:
            print(f"Skipped (already exists): {username}")


if __name__ == "__main__":
    main()
