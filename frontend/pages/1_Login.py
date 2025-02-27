import streamlit as st
import requests
from streamlit.runtime.scriptrunner import get_script_run_ctx

# Page configuration
st.set_page_config(
    page_title="AspAIra - Login",
    page_icon="🌱",
    layout="centered"
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        max-width: 100%;
        padding: 1rem;
    }
    .main-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        padding: 1rem;
    }
    .logo {
        font-size: 2rem;
        margin-bottom: 2rem;
    }
    .form-container {
        width: 100%;
        max-width: 400px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'access_token' not in st.session_state:
    st.session_state.access_token = None

def login(username: str, password: str):
    try:
        response = requests.post(
            "http://localhost:8000/token",
            data={"username": username, "password": password}
        )
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException:
        return None

def create_account(username: str, password: str):
    try:
        response = requests.post(
            "http://localhost:8000/users/",
            json={"username": username, "password": password}
        )
        if response.status_code == 200:
            return True
        return False
    except requests.RequestException:
        return False

# Main container
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Logo
st.markdown('<div class="logo">🌱 AspAIra</div>', unsafe_allow_html=True)

# Login form
with st.form("login_form"):
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    col1, col2 = st.columns(2)
    with col1:
        login_button = st.form_submit_button("Sign In")
    with col2:
        signup_button = st.form_submit_button("Sign Up")

    if login_button and username and password:
        result = login(username, password)
        if result:
            st.session_state.access_token = result["access_token"]
            st.success("Login successful!")
            st.switch_page("pages/2_Profile1.py")
        else:
            st.error("Invalid username or password")

    if signup_button and username and password:
        if create_account(username, password):
            st.success("Account created successfully! Please sign in.")
        else:
            st.error("Username already exists or error creating account")

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True) 