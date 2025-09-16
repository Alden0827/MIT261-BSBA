import streamlit as st
from controllers.admin.user_management_controller import user_management_view

def admin_view(db):
    st.title("Admin Section")

    menu = st.sidebar.selectbox(
        "Admin Menu",
        ["User Management", "System Settings"]
    )

    if menu == "User Management":
        user_management_view(db)
    elif menu == "System Settings":
        st.write("System Settings Page (to be implemented)")
