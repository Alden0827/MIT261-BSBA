import streamlit as st
from helpers.data_helper import get_user, verify_password
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError

def login_view():
    """
    Displays the login form and handles user authentication with error handling.
    """
    st.title("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if not username or not password:
            st.error("Please enter both username and password.")
            return

        try:
            user = get_user(username)  # This may raise a PyMongoError if DB is down

            if user and verify_password(password, user["passwordHash"]):
                st.session_state["logged_in"] = True
                st.session_state["user_role"] = user["role"]
                st.session_state["username"] = user["username"]
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid username or password.")

        except ServerSelectionTimeoutError as e:
            st.error("Cannot connect to the database. Please try again later.")
            # st.exception(e)
        except PyMongoError as e:
            st.error("A database error occurred. Please contact support.")
            st.exception(e)
        except Exception as e:
            st.error("An unexpected error occurred.")
            st.exception(e)
