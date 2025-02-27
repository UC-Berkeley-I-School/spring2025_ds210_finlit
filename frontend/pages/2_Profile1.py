import streamlit as st
import requests

# Page configuration
st.set_page_config(
    page_title="AspAIra - Profile Setup",
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
    .progress-container {
        width: 100%;
        max-width: 400px;
        background-color: #f0f0f0;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .progress-bar {
        width: 50%;
        height: 10px;
        background-color: #4CAF50;
        border-radius: 10px;
    }
    .form-container {
        width: 100%;
        max-width: 400px;
    }
</style>
""", unsafe_allow_html=True)

# Check authentication
if 'access_token' not in st.session_state or not st.session_state.access_token:
    st.switch_page("pages/1_Login.py")

# Main container
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Progress bar
st.markdown('<div class="progress-container"><div class="progress-bar"></div></div>', unsafe_allow_html=True)

# Title
st.markdown("### Please help us understand a little bit about you...")

# Profile form
with st.form("profile_part1"):
    country = st.selectbox(
        "Country of Origin",
        ["Philippines", "Kenya", "Ethiopia", "India", "Sri Lanka"]
    )
    
    time_in_uae = st.selectbox(
        "How Long Have you been in the UAE",
        ["Less than a year", "1-3 Years", "3-5 Years", "5-10 Years", "10+ Years"]
    )
    
    job_title = st.selectbox(
        "Job Title",
        ["Live-In Maid", "Live-Out Maid", "Cook", "Nanny", "Seeking Employment"]
    )
    
    housing = st.selectbox(
        "Housing",
        ["Live-In", "Live-Out", "Temporary Housing"]
    )
    
    education = st.selectbox(
        "Education Level",
        ["None", "Primary School", "High School", "College"]
    )
    
    dependents = st.selectbox(
        "Number of Dependents",
        ["None", "1", "2", "3", "More than 3"]
    )
    
    submit = st.form_submit_button("Continue")
    
    if submit:
        try:
            response = requests.post(
                "http://localhost:8000/profile/part1",
                headers={"Authorization": f"Bearer {st.session_state.access_token}"},
                json={
                    "country_of_origin": country,
                    "time_in_uae": time_in_uae,
                    "job_title": job_title,
                    "housing": housing,
                    "education_level": education,
                    "number_of_dependents": dependents
                }
            )
            if response.status_code == 200:
                st.success("Profile information saved!")
                st.switch_page("pages/2_Profile2.py")
            else:
                st.error("Failed to save profile information. Please try again.")
        except requests.RequestException:
            st.error("Connection error. Please try again.")

st.markdown('</div>', unsafe_allow_html=True) 