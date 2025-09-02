import streamlit as st
from helpers.data_helper import get_user, verify_password

def login_view():
    """
    Displays the login form and handles user authentication.
    """
    st.title("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if not username or not password:
            st.error("Please enter both username and password.")
            return

        user = get_user(username)

        if user and verify_password(password, user["passwordHash"]):
            st.session_state["logged_in"] = True
            st.session_state["user_role"] = user["role"]
            st.session_state["username"] = user["username"]
            st.success("Logged in successfully!")
            st.experimental_rerun()
        else:
            st.error("Invalid username or password.")
