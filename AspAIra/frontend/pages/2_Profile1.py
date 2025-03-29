import streamlit as st
import requests

# Initialize session states
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'profile1_complete' not in st.session_state:
    st.session_state.profile1_complete = False

# Page configuration
st.set_page_config(
    page_title="AspAIra - Profile Part 1",
    page_icon="🌱",
    layout="centered",
    initial_sidebar_state="collapsed"
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

def update_profile(data):
    try:
        headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
        response = requests.post(
            "http://localhost:8001/user/profile1",
            headers=headers,
            json=data
        )
        if response.status_code == 200:
            st.session_state.profile1_complete = True
            return True
        return False
    except requests.RequestException:
        return False

# Title with icon
st.markdown("""
<div class="title-container" style="text-align: center; width: 100%; margin-bottom: 2rem;">
    <h1 style="margin: 0; padding: 0;">🌱 AspAIra</h1>
</div>
""", unsafe_allow_html=True)

# Progress bar and text
st.progress(0.5)
st.markdown('<p class="progress-text">Step 1 of 2: Profile Intake</p>', unsafe_allow_html=True)

# Form container
st.markdown('<div class="form-container">', unsafe_allow_html=True)

# Form fields
with st.form("profile1_form"):
    country_of_origin = st.selectbox("Country of Origin", ["", "Filipino", "Kenyan", "Sri Lankan"])
    time_in_uae = st.selectbox("How long have you been in UAE", ["", "Less than a year", "1-3 years", "3-5 years", "5-10 years", "10+ years"])
    job_title = st.selectbox("Job Title", ["", "Live In maid", "Live out maid", "Cook", "Nanny"])
    housing = st.selectbox("Housing", ["", "Live In", "Live Out", "Temporary Housing"])
    education_level = st.selectbox("Education Level", ["", "None", "Primary school", "High school", "College"])
    number_of_kids = st.selectbox("Number of Kids", ["", "None", "1", "2", "3", "More than 3"])

    # Update button to match Profile2 style
    submitted = st.form_submit_button(
        "Continue",
        type="primary",
        use_container_width=True,
        help="Continue to next step"
    )
    
    if submitted:
        # Check if any field is empty
        if "" in [country_of_origin, time_in_uae, job_title, housing, education_level, number_of_kids]:
            st.error("Please fill all fields")
        else:
            data = {
                "country_of_origin": country_of_origin,
                "time_in_uae": time_in_uae,
                "job_title": job_title,
                "housing": housing,
                "education_level": education_level,
                "number_of_kids": number_of_kids
            }
            
            if update_profile(data):
                st.session_state.profile1_complete = True
                st.success("Profile updated successfully!")
                st.switch_page("pages/2_Profile2.py")
            else:
                st.error("Failed to update profile. Please try again.")

st.markdown('</div>', unsafe_allow_html=True) 