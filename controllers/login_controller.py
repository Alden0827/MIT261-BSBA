import streamlit as st
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError
from config.settings import APP_TITLE, UNIVERSITY_NAME
import helpers.user_helper as uh

def login_view(db):
    r1 = uh.user_helper({"db": db})
    # r2 = dh.data_helper({"db": db})
    """
    Displays the login form in the sidebar with a tiled background image and handles
    user authentication, while showing the school info and logo on the main page.
    """

    # --- Sidebar Styling ---
    st.markdown(
        """
            <style>
            [data-testid="stSidebar"] {
                background-image: url('https://sms.ndmu.edu.ph/storage/carousel/1749470855_ndmu.jpg');
                background-repeat: no-repeat;       /* prevent tiling */
                background-size: auto 100%;         /* stretch vertically, width auto */
                background-position: center top;    /* align top-center */
            }
            </style>
        """,
        unsafe_allow_html=True
    )

    # --- Sidebar Login Form ---
    with st.sidebar:
        # Login Box
        st.markdown(
            """
            <div style="
                border: 1px solid #d3d3d3;
                border-radius: 10px;
                padding: 0px;
                background-color: rgba(255, 255, 255, 0.9);
                margin-top: 0px;
                position: relative;
                z-index: 1;
            ">
            <h1 style="text-align:center; margin-bottom:5px;">Please login to continue</h1>
            </div>

            
            <style>
            /* Style the login button */
            div.stButton > button:first-child {
                background-color: #4CAF50;   /* Green background */
                color: white;                 /* White text */
                font-size: 16px;              /* Bigger text */
                padding: 10px 24px;           /* Vertical and horizontal padding */
                border-radius: 8px;           /* Rounded corners */
                border: none;                 /* Remove default border */
                transition: 0.3s;             /* Smooth hover transition */
                width: 100%;
            }

            /* Hover effect */
            div.stButton > button:first-child:hover {
                background-color: #45a049;   /* Slightly darker green on hover */
                cursor: pointer;
            }

            /* Make input labels bigger and colored */
            div[data-testid="stTextInput"] label {
                font-size: 24px;       /* Bigger text */
                color: #4CAF50;        /* Green color */
                font-weight: bold;      /* Optional: make bold */
            }

            /* Optional: make the input box text bigger too */
            div[data-testid="stTextInput"] input {
                font-size: 16px;
                padding: 6px;
            }
            </style>

            """,
            unsafe_allow_html=True
        )

        # --- Inputs and Button ---
        username = st.text_input("Username", key="sidebar_username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", key="sidebar_password", placeholder="Enter your password")
        if st.button("Login", key="sidebar_login_btn"):
            if not username or not password:
                st.error("Please enter both username and password.")
            else:
                try:
                    user = r1.get_user(username)  # DB query
                    if user and r1.verify_password(password, user["passwordHash"]):
                        st.session_state["logged_in"] = True
                        st.session_state["user_role"] = user["role"]
                        st.session_state["username"] = user["username"]
                        st.session_state["fullname"] = user["fullName"]
                        st.session_state["uid"] = user["UID"]
                        st.success(f"Welcome {user['fullName']}!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
                except ServerSelectionTimeoutError:
                    st.markdown(
                        "<span style='color:red; font-weight:bold'>Cannot connect to the database. Please try again later.</span>",
                        unsafe_allow_html=True
                    )
                except PyMongoError as e:
                    st.error("A database error occurred. Please contact support.")
                    st.exception(e)
                except Exception as e:
                    st.error("An unexpected error occurred.")
                    st.exception(e)

    # --- Main Page Content ---
    st.markdown(
        f"""
        <div style="text-align:center; margin-bottom:30px;">
            <img src="https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEjvoWxGatGPpCoUDlDd_tHUcWr92COSNaEE4-1rtDQ0aplkWFjqhUBjraQHKx-3AmVB224hNeZWZzt-fTZ8ZQvSA8Wlu-zCh3xZ5FCJTwhyaBkWAm4nYRn4GaPVYT5Kxsp785Cma5prdWRW/s1600/ndmu-seal1.png" 
                 alt="NDMU Logo" width="150">
            <h1 style="margin:5px 0;">{UNIVERSITY_NAME}</h1>
            <h3 style="color:gray; margin:0;">{APP_TITLE}</h3>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("Welcome to the university portal. Please login from the sidebar to access your account.")

    # --- Footer ---
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
