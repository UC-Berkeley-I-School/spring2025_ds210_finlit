import streamlit as st
import requests

# Initialize session states if not exists
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'login'

# Page configuration
st.set_page_config(
    page_title="AspAIra - Login",
    page_icon="🌱",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Custom CSS
st.markdown("""
<style>
    /* Hide Streamlit elements */
    [data-testid="collapsedControl"] {display: none !important;}
    section[data-testid="stSidebar"] {display: none !important;}
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    
    /* Block analytics */
    iframe[src*="analytics"], iframe[src*="segment"],
    script[src*="analytics"], script[src*="segment"],
    div[data-testid="stGoogleAnalytics"] {
        display: none !important;
    }
    
    /* Main styles */
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
        max-width: 800px;
        margin: 0 auto;
    }
    
    .logo {
        font-size: 2rem;
        margin-bottom: 2rem;
        color: #000000;
    }
    
    .form-container {
        width: 100%;
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background-color: #f8f9fa;
        border-radius: 8px;
    }
    
    /* Button styles */
    .stButton > button {
        width: 100% !important;
        padding: 0.75rem 1.5rem !important;
        font-size: 1.1rem !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
        background-color: #2E8B57 !important;
        color: white !important;
        border: none !important;
        cursor: pointer !important;
        transition: background-color 0.2s ease !important;
        margin-bottom: 0.5rem !important;
    }
    
    .stButton > button:hover {
        background-color: #3CB371 !important;
    }
    
    .stButton > button:focus {
        box-shadow: 0 0 0 2px #3CB371 !important;
    }
    
    /* Hide problematic elements */
    [data-baseweb="select"] > div[aria-hidden="true"] {
        display: none !important;
    }
    
    /* Form field styles */
    .stTextInput > div > div > input {
        font-size: 1rem !important;
    }
    
    .form-row {
        margin-bottom: 1rem;
    }
    
    @media (forced-colors: active) {
        .stButton > button {
            border: 2px solid ButtonText !important;
            background-color: ButtonFace !important;
            color: ButtonText !important;
        }
        
        .stButton > button:hover,
        .stButton > button:focus {
            border-color: Highlight !important;
            background-color: ButtonFace !important;
            color: Highlight !important;
        }
        
        .form-container {
            border: 1px solid ButtonText !important;
            background-color: Canvas !important;
            color: CanvasText !important;
        }
        
        .stTextInput > div > div > input {
            border-color: ButtonText !important;
            background-color: Field !important;
            color: FieldText !important;
        }
        
        .logo {
            color: CanvasText !important;
        }
    }
    
    /* Center title */
    .title-container {
        text-align: center;
        padding: 2rem 0;
    }
    
    /* Form container */
    .form-container {
        width: 100%;
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background-color: #f8f9fa;
        border-radius: 8px;
    }
    
    /* Button container */
    .button-container {
        display: flex;
        gap: 1rem;
        margin-top: 1rem;
    }
    
    .button-container > div {
        flex: 1;
    }
</style>
""", unsafe_allow_html=True)

def login(username: str, password: str):
    try:
        print(f"Attempting login for username: {username}")  # Debug log
        response = requests.post(
            "http://localhost:8001/token",
            data={"username": username, "password": password}
        )
        print(f"Login response status: {response.status_code}")  # Debug log
        print(f"Login response body: {response.text}")  # Debug log
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Login failed with status {response.status_code}: {response.text}")  # Debug log
            return None
    except requests.RequestException as e:
        print(f"Login request error: {str(e)}")  # Debug log
        return None

def create_account(username: str, password: str):
    try:
        print(f"Attempting to create account for username: {username}")  # Debug log
        response = requests.post(
            "http://localhost:8001/signup",
            json={"username": username, "password": password}
        )
        print(f"Create account response status: {response.status_code}")  # Debug log
        print(f"Create account response body: {response.text}")  # Debug log
        if response.status_code == 200:
            return True
        else:
            error_message = response.json().get("message", "Unknown error")
            print(f"Account creation failed: {error_message}")  # Debug log
            return False
    except requests.RequestException as e:
        print(f"Create account request error: {str(e)}")  # Debug log
        return False

def check_profile_status(token: str):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get("http://localhost:8001/user/profile-status", headers=headers)
        if response.status_code == 200:
            return response.json()
        return {"profile1_complete": False, "profile2_complete": False}
    except requests.RequestException:
        return {"profile1_complete": False, "profile2_complete": False}

# Main container
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Title
st.markdown('<div class="title-container"><h1>🌱 AspAIra</h1></div>', unsafe_allow_html=True)

# Form container with grey background
st.markdown('<div class="form-container">', unsafe_allow_html=True)

username = st.text_input("Username")
password = st.text_input("Password", type="password")

# Button container for side-by-side buttons
col1, col2 = st.columns(2)

with col1:
    if st.button("Sign In"):
        if not username or not password:
            st.error("Please enter both username and password")
        else:
            success = login(username, password)
            if success:
                st.session_state.access_token = success["access_token"]
                # Check profile status after successful login
                profile_status = check_profile_status(success["access_token"])
                print(f"Profile status: {profile_status}")  # Debug log
                if profile_status["profile1_complete"] and profile_status["profile2_complete"]:
                    st.success("Login successful!")
                    st.switch_page("pages/3_Coach_Landing.py")
                else:
                    st.success("Login successful! Please complete your profile.")
                    st.switch_page("pages/2_Profile1.py")
            else:
                st.error("Login failed. Please check your credentials and try again.")

with col2:
    if st.button("Create Account"):
        if not username or not password:
            st.error("Please enter both username and password")
        else:
            if create_account(username, password):
                st.success("Account created successfully!")
                # Log in the user automatically
                success = login(username, password)
                if success:
                    st.session_state.access_token = success["access_token"]
                    st.switch_page("pages/2_Profile1.py")
                else:
                    st.error("Account created but login failed. Please try logging in manually.")
            else:
                response = requests.post(
                    "http://localhost:8001/signup",
                    json={"username": username, "password": password}
                )
                error_message = response.json().get("message", "Unknown error")
                st.error(f"Failed to create account: {error_message}")

st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True) 