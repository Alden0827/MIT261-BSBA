import streamlit as st
from helpers.data_helper import get_subjects
import pandas as pd

def subjects_manager_page(db):
    st.subheader("📚 Subjects Manager")

    # --- Dialog for adding/editing a subject ---
    @st.dialog("Add/Edit Subject")
    def subject_dialog(subject=None):
        dialog_title = "Edit Subject" if subject else "Add New Subject"
        st.subheader(dialog_title)

        subject_code = st.text_input("Subject Code", value=subject.get("_id", "") if subject else "", disabled=subject is not None)
        description = st.text_input("Description", value=subject.get("Description", "") if subject else "")
        units = st.number_input("Units", min_value=1, max_value=5, value=subject.get("Units", 3) if subject else 3)

        if st.button("Save"):
            subject_data = {
                "Description": description.strip(),
                "Units": units,
                "Teacher": ""
            }

            if subject:
                db.subjects.update_one({"_id": subject["_id"]}, {"$set": subject_data})
                st.success("✅ Subject updated successfully.")
            else:
                subject_data["_id"] = subject_code.strip()
                if db.subjects.find_one({"_id": subject_data["_id"]}):
                    st.error("❌ Subject code already exists.")
                    return
                db.subjects.insert_one(subject_data)
                st.success("✅ Subject added successfully.")

            # Clear cache
            if pd.io.common.file_exists('./cache/subjects_cache.pkl'):
                pd.io.common.get_handle('./cache/subjects_cache.pkl', 'w').close()

            st.rerun()

    if st.button("➕ Add New Subject"):
        subject_dialog()

    # --- Search bar ---
    search_query = st.text_input("🔍 Search subjects", placeholder="Enter keywords (e.g. 'IT101 Introduction')")

    # --- Fetch all subjects ---
    with st.spinner(f"Loading subject list...", show_time=True):
        subjects = get_subjects().to_dict("records")
    
    if not subjects:
        st.info("No subjects found. Add a new subject to get started.")
        return

    # --- Apply multi-keyword search filter ---
    if search_query.strip():
        keywords = search_query.lower().split()
        filtered = []
        for s in subjects:
            # Use 'Subject Code' for searching, which is the renamed '_id'
            record_text = f"{s.get('Subject Code', '')} {s.get('Description', '')} {s.get('Units', '')}".lower()
            if all(kw in record_text for kw in keywords):
                filtered.append(s)
        subjects = filtered

    # --- Pagination ---
    page_size = 10
    total_subjects = len(subjects)
    total_pages = (total_subjects - 1) // page_size + 1 if total_subjects > 0 else 1
    if "subject_page" not in st.session_state:
        st.session_state.subject_page = 1
    # Reset to page 1 if search changes
    if search_query and st.session_state.subject_page != 1:
        st.session_state.subject_page = 1

    col_prev, col_page, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("⬅️ Prev", disabled=st.session_state.subject_page <= 1):
            st.session_state.subject_page -= 1
            st.rerun()
    with col_page:
        st.markdown(f"**Page {st.session_state.subject_page} of {total_pages}**")
    with col_next:
        if st.button("Next ➡️", disabled=st.session_state.subject_page >= total_pages):
            st.session_state.subject_page += 1
            st.rerun()

    # --- Slice subjects for current page ---
    start_idx = (st.session_state.subject_page - 1) * page_size
    end_idx = start_idx + page_size
    subjects_page = subjects[start_idx:end_idx]

    # --- Table Header ---
    header_cols = st.columns([2, 5, 2, 2])
    header_cols[0].markdown("**Subject Code**")
    header_cols[1].markdown("**Description**")
    header_cols[2].markdown("**Units**")
    header_cols[3].markdown("**Actions**")
    st.markdown("---")

    # --- Table Rows ---
    if not subjects_page:
        st.warning("No subjects match your search.")
    else:
        for subject in subjects_page:
            # The _id from MongoDB is the subject code, which get_subjects renames to 'Subject Code'
            subject_id = subject['Subject Code']
            row = st.columns([2, 5, 2, 2])
            row[0].write(subject_id)
            row[1].write(subject.get("Description", "N/A"))
            row[2].write(subject.get("Units", "N/A"))

            edit_col, delete_col = row[3].columns(2)
            # Use the original '_id' for database operations, which is in 'Subject Code'
            if edit_col.button("✏️", key=f"edit_{subject_id}"):
                # We need to pass the original subject dict to the dialog,
                # but with '_id' field for consistency in the dialog function.
                dialog_subject = subject.copy()
                dialog_subject['_id'] = subject_id
                subject_dialog(dialog_subject)
            if delete_col.button("🗑️", key=f"delete_{subject_id}"):
                db.subjects.delete_one({"_id": subject_id})
                if pd.io.common.file_exists('./cache/subjects_cache.pkl'):
                    pd.io.common.get_handle('./cache/subjects_cache.pkl', 'w').close()
                st.warning(f"Deleted subject {subject.get('Description', 'Unknown')}")
                st.rerun()
