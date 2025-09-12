import streamlit as st
import pandas as pd
from helpers.data_helper import get_all_users, add_user, delete_user

def user_management_view(st, db):
    st.header("User Management")

    # --- User List ---
    st.subheader("Existing Users")

    def refresh_users():
        st.session_state.users_df = get_all_users()

    if 'users_df' not in st.session_state:
        refresh_users()

    users_df = st.session_state.users_df

    if not users_df.empty:
        # Header
        col1, col2, col3, col4 = st.columns([2, 2, 3, 1])
        with col1:
            st.markdown("**Username**")
        with col2:
            st.markdown("**Role**")
        with col3:
            st.markdown("**Full Name**")
        with col4:
            st.markdown("**Actions**")

        # User rows
        for index, row in users_df.iterrows():
            col1, col2, col3, col4 = st.columns([2, 2, 3, 1])
            with col1:
                st.write(row['username'])
            with col2:
                st.write(row['role'])
            with col3:
                st.write(row['fullName'])
            with col4:
                if st.button("Delete", key=f"delete_{row['username']}"):
                    success, message = delete_user(row['username'])
                    if success:
                        st.success(message)
                        refresh_users()
                        st.rerun()
                    else:
                        st.error(message)
    else:
        st.info("No users found.")

    st.subheader("Add a New User")
    with st.form("new_user_form", clear_on_submit=True):
        new_username = st.text_input("Username")
        new_password = st.text_input("Password", type="password")
        new_fullname = st.text_input("Full Name")
        new_role = st.selectbox("Role", ["admin", "faculty", "student", "registrar"])

        submitted = st.form_submit_button("Add User")
        if submitted:
            if not all([new_username, new_password, new_fullname, new_role]):
                st.warning("Please fill out all fields.")
            else:
                success, message = add_user(new_username, new_password, new_role, new_fullname)
                if success:
                    st.success(message)
                    refresh_users()
                else:
                    st.error(message)

    st.subheader("Edit a User")
    st.info("Functionality to edit users will be implemented in a future update.")
