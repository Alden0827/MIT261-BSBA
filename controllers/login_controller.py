import streamlit as st
from helpers.data_helper import get_user, verify_password
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError
from config.settings import APP_TITLE
def login_view():
    """
    Displays the login form and handles user authentication with error handling.
    """

    # --- HEADER with University Logo and Title ---
    st.markdown(
        f"""
        <div style="text-align:center; margin-bottom:20px;">
            <img src="https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEjvoWxGatGPpCoUDlDd_tHUcWr92COSNaEE4-1rtDQ0aplkWFjqhUBjraQHKx-3AmVB224hNeZWZzt-fTZ8ZQvSA8Wlu-zCh3xZ5FCJTwhyaBkWAm4nYRn4GaPVYT5Kxsp785Cma5prdWRW/s1600/ndmu-seal1.png" 
                 alt="NDMU Logo" width="100">
            <h2 style="margin:5px 0;">Notre Dame of Marbel University</h2>
            <h4 style="color:gray; margin:0;">{APP_TITLE}</h4>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- Login Form ---
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if not username or not password:
            st.error("Please enter both username and password.")
            return

        try:
            user = get_user(username)  # DB query
            print(user)
            if user and verify_password(password, user["passwordHash"]):
                st.session_state["logged_in"] = True
                st.session_state["user_role"] = user["role"]
                st.session_state["username"] = user["username"]
                st.session_state["fullname"] = user["fullName"]
                st.session_state["uid"] = user["UID"]

                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid username or password.")

        except ServerSelectionTimeoutError:
            st.error("Cannot connect to the database. Please try again later.")
        except PyMongoError as e:
            st.error("A database error occurred. Please contact support.")
            st.exception(e)
        except Exception as e:
            st.error("An unexpected error occurred.")
            st.exception(e)

    # --- FOOTER with Author ---
    st.markdown(
        """
        <hr>
        <div style="text-align:center; font-size:14px; color:gray;">
            Developed by <b>Alden A. Quiñones</b> <br>
            © 2025 Notre Dame of Marbel University
        </div>
        """,
        unsafe_allow_html=True
    )
