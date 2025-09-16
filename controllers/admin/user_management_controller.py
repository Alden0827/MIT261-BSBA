import streamlit as st
import helpers.user_helper as uh
import pandas as pd
def user_management_view(db):
    r = uh.data_helper({"db": db})
    st.header("User Management")

    # --- User List ---
    st.subheader("Existing Users")

    def refresh_users():
        st.session_state.users_df = r.get_all_users()

    if 'users_df' not in st.session_state:
        refresh_users()

    users_df = st.session_state.users_df

    if not users_df.empty:
        # Header
        col1, col2, col3, col4 = st.columns([2, 2, 3, 2])
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
            col1, col2, col3, col4 = st.columns([2, 2, 3, 2])
            with col1:
                st.write(row['username'])
            with col2:
                st.write(row['role'])
            with col3:
                st.write(row['fullName'])
            with col4:
                # Use sub-columns to place buttons side-by-side
                edit_col, delete_col = st.columns(2)
                with edit_col:
                    if st.button("Edit", key=f"edit_{row['username']}"):
                        st.session_state.edit_user = row
                with delete_col:
                    if st.button("Delete", key=f"delete_{row['username']}"):
                        success, message = r.delete_user(row['username'])
                        if success:
                            st.success(message)
                            refresh_users()
                            st.rerun()
                        else:
                            st.error(message)
    else:
        st.info("No users found.")

    # --- Edit User Dialog ---
    if 'edit_user' in st.session_state and st.session_state.edit_user is not None:
        user_to_edit = st.session_state.edit_user

        @st.dialog("Edit User")
        def edit_user_dialog():
            st.subheader(f"Editing: {user_to_edit['username']}")

            with st.form("edit_form"):
                fullname = st.text_input("Full Name", value=user_to_edit['fullName'])

                roles = ["admin", "faculty", "student", "registrar"]
                current_role_index = roles.index(user_to_edit['role']) if user_to_edit['role'] in roles else 0
                role = st.selectbox("Role", roles, index=current_role_index)

                st.subheader("Change Password (optional)")
                new_password = st.text_input("New Password", type="password")

                submitted = st.form_submit_button("Save Changes")
                if submitted:
                    update_success, update_message = r.update_user(user_to_edit['username'], fullname, role)
                    if update_success:
                        st.success(update_message)
                    else:
                        st.error(update_message)

                    if new_password:
                        pw_success, pw_message = change_password(user_to_edit['username'], new_password)
                        if pw_success:
                            st.success(pw_message)
                        else:
                            st.error(pw_message)

                    refresh_users()
                    st.session_state.edit_user = None
                    st.rerun()

        edit_user_dialog()

    # --- Add New User Dialog ---
    if st.button("Add New User"):
        @st.dialog("Add New User")
        def add_user_dialog():
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
                        success, message = r.add_user(new_username, new_password, new_role, new_fullname)
                        if success:
                            st.success(message)
                            refresh_users()
                        else:
                            st.error(message)

        add_user_dialog()