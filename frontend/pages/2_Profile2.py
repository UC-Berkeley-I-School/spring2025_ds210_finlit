import streamlit as st
import requests

# Page configuration
st.set_page_config(
    page_title="AspAIra - Financial Profile",
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
        width: 100%;
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
st.markdown("### Please help us understand your financial situation...")

# Profile form
with st.form("profile_part2"):
    bank_account = st.selectbox(
        "Bank Account Information",
        ["FAB", "Emirates NBD", "ADCB", "ADIB", "No Bank Account"]
    )
    
    debt_info = st.selectbox(
        "Debt Information",
        ["Debt in Home Country", "Debt in UAE", "No Debt"]
    )
    
    remittance = st.selectbox(
        "Remittance Information",
        ["Send Money through Bank", "Send Money through Exchange House", 
         "Send Money through Informal Network", "Don't know how to Send Money"]
    )
    
    submit = st.form_submit_button("Continue")
    
    if submit:
        try:
            response = requests.post(
                "http://localhost:8000/profile/part2",
                headers={"Authorization": f"Bearer {st.session_state.access_token}"},
                json={
                    "bank_account": bank_account,
                    "debt_information": debt_info,
                    "remittance_information": remittance
                }
            )
            if response.status_code == 200:
                st.success("Financial information saved!")
                st.switch_page("pages/3_Coach_Landing.py")
            else:
                st.error("Failed to save financial information. Please try again.")
        except requests.RequestException:
            st.error("Connection error. Please try again.")

st.markdown('</div>', unsafe_allow_html=True) 