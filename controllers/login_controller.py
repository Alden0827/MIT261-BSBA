import streamlit as st

# Inject Bootstrap CSS
st.markdown(
    """
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    """,
    unsafe_allow_html=True,
)

# Centered login card
st.markdown(
    """
    <div class="container d-flex justify-content-center align-items-center" 
         style="min-height: 100vh;">
        <div class="card shadow-lg p-4 rounded-4" style="max-width: 420px; width: 100%;">
            
            <!-- Logo + University Name -->
            <div class="text-center mb-4">
                <img src="https://upload.wikimedia.org/wikipedia/en/thumb/5/50/University_of_the_Philippines_seal.svg/120px-University_of_the_Philippines_seal.svg.png" 
                     width="80" class="mb-3"/>
                <h4 class="fw-bold">Your University Name</h4>
                <p class="text-muted">Login Portal</p>
            </div>
            
            <!-- Username + Password fields (labels only, Streamlit will render inputs) -->
            <div class="mb-3">
                <label class="form-label">Username</label>
            </div>
            <div class="mb-3">
                <label class="form-label">Password</label>
            </div>
            
            <!-- Placeholder for Streamlit inputs -->
        </div>
    </div>
    
    <!-- Author -->
    <div class="text-center mt-3 text-muted">
        <small>Developed by <b>Alden A. Quiñones</b></small>
    </div>
    """,
    unsafe_allow_html=True,
)

# Streamlit inputs (aligned with Bootstrap labels above)
username = st.text_input("Username", key="username_input")
password = st.text_input("Password", type="password", key="password_input")

# Login button
if st.button("Login", use_container_width=True):
    if username == "admin" and password == "1234":
        st.success("✅ Login successful!")
    else:
        st.error("❌ Invalid username or password")