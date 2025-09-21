def get_subjects_by_teacher(db,teacher_name, batch_size=1000):
    """
    Returns a DataFrame of subjects handled by a specific teacher.
    Ensures consistent columns: [Subject Code, Description, Units, Teacher].
    """
    cursor = db.subjects.find(
        {"Teacher": teacher_name},   # filter by teacher
        {"_id": 1, "Description": 1, "Units": 1, "Teacher": 1}  # projection
    )

    docs, chunks = [], []
    for i, doc in enumerate(cursor, 1):
        docs.append(doc)
        if i % batch_size == 0:
            chunks.append(pd.DataFrame(docs))
            docs = []

    if docs:
        chunks.append(pd.DataFrame(docs))

    df = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()

    if not df.empty:
        if "_id" in df.columns:
            df.rename(columns={"_id": "Subject Code"}, inplace=True)
            df["Subject Code"] = df["Subject Code"].astype(str)

        # Guarantee schema
        for col in ["Description", "Units", "Teacher"]:
            if col not in df.columns:
                df[col] = ""

    return df


if __name__ == "__main__":
    import pandas as pd
    import re
    import bcrypt
    from pymongo import MongoClient
    import sys, os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

    # MongoDB connection

    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['mit261']
        subjects = db["subjects"]
        userAccounts = db["userAccounts"]
        print("✅ Successfully connected to MongoDB!")
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")
        sys.exit()


    subjects_df = get_subjects_by_teacher(db,'Leonor Rivera')
    

    if "Subject Code" in subjects_df.columns:
        subject_list = [""] + subjects_df["Subject Code"].tolist()
    elif "Code" in subjects_df.columns:  # fallback
        subject_list = [""] + subjects_df["Code"].tolist()
    else:
        subject_list = []
        st.warning("⚠️ No subject code column found in subjects_df.")

    print(subject_list)