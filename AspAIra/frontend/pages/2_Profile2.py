import streamlit as st
import requests

# Initialize session states if not exists
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'profile2'

# Page configuration
st.set_page_config(
    page_title="AspAIra - Profile Part 2",
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
        width: 200px !important;
        padding: 0.75rem 1.5rem !important;
        font-size: 1.1rem !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
        background-color: #2E8B57 !important;
        color: white !important;
        border: none !important;
        cursor: pointer !important;
        transition: background-color 0.2s ease !important;
        margin: 0 auto !important;
        display: block !important;
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
            forced-colors-adjust: none !important;
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
            forced-colors-adjust: none !important;
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
</style>
""", unsafe_allow_html=True)

def update_profile_part2(profile_data: dict):
    try:
        headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
        response = requests.post(
            "http://localhost:8001/user/profile2",
            json=profile_data,
            headers=headers
        )
        if response.status_code == 200:
            return True
        return False
    except requests.RequestException:
        return False

# Main container
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Title with centered styling
st.markdown("""
<div class="title-container" style="text-align: center; width: 100%; margin-bottom: 2rem;">
    <h1 style="margin: 0; padding: 0;">🌱 AspAIra</h1>
</div>
""", unsafe_allow_html=True)

# Progress bar and text
st.progress(1.0)
st.markdown('<p class="progress-text">Step 2 of 2: Financial Information Intake</p>', unsafe_allow_html=True)

# Form container with grey background
st.markdown('<div class="form-container">', unsafe_allow_html=True)

# Create form with select boxes
with st.form("profile2_form"):
    bank_account = st.selectbox(
        "Which Bank Do You Use?",
        ["", "FAB", "Emirates NBD", "ADCB", "Mashreq Bank", "RAKBANK", "Dubai Islamic Bank", "Sharjah Islamic Bank", "Emirates Islamic Bank", "CBD", "No Bank Account"],
        key="bank_account"
    )
    
    debt_information = st.selectbox(
        "Do You Have Any Debt?",
        ["", "Debt in Home Country", "Debt in UAE", "No Debt"],
        key="debt_information"
    )
    
    remittance_information = st.selectbox(
        "How Do You Send Money Home?",
        ["", "Send money with Bank Transfer", "Send money with Exchange House", 
         "Send money offline", "Don't Send any money"],
        key="remittance_information"
    )
    
    remittance_amount = st.selectbox(
        "How Much Do You Send Home Monthly?",
        ["", "Less than 100 AED", "100-500 AED", "500-1000 AED", "1000-2000 AED", "More than 2000 AED"],
        key="remittance_amount"
    )

    financial_dependents = st.selectbox(
        "Who Do You Financially Support Back Home?",
        ["", "No One", "Just Kids", "Just Parents", "Kids and Parents", "Entire Extended Family"],
        key="financial_dependents"
    )
    
    # Submit button with proper title and no ARIA attributes
    submit_button = st.form_submit_button(
        "Continue",
        type="primary",
        use_container_width=True,
        help="Continue to next step"
    )

# Handle form submission
if submit_button:
    # Check if any field is empty
    if "" in [bank_account, debt_information, remittance_information, remittance_amount, financial_dependents]:
        st.error("Please fill all fields")
    else:
        profile_data = {
            "bank_account": bank_account,
            "debt_information": debt_information,
            "remittance_information": remittance_information,
            "remittance_amount": remittance_amount,
            "financial_dependents": financial_dependents
        }
        
        if update_profile_part2(profile_data):
            st.success("Profile updated successfully!")
            st.switch_page("pages/3_Coach_Landing.py")
        else:
            st.error("Failed to update profile. Please try again.")

st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)