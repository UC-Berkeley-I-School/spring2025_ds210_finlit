import streamlit as st
import requests

# Page configuration
st.set_page_config(
    page_title="AspAIra - Financial Coach",
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
        margin-bottom: 60px;  /* Space for bottom nav */
    }
    .chatbot-container {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 2rem;
        width: 100%;
        max-width: 400px;
    }
    .chatbot-icon {
        font-size: 2rem;
    }
    .chatbot-text {
        text-align: left;
        flex-grow: 1;
    }
    .module-button {
        width: 100%;
        max-width: 400px;
        margin: 0.5rem 0;
        padding: 1rem;
        background-color: #f0f0f0;
        border: none;
        border-radius: 10px;
        cursor: pointer;
        text-align: left;
    }
    .module-button:hover {
        background-color: #e0e0e0;
    }
    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        padding: 1rem;
        display: flex;
        justify-content: space-around;
        align-items: center;
        box-shadow: 0 -2px 5px rgba(0,0,0,0.1);
    }
    .nav-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        font-size: 0.8rem;
    }
    .nav-item.active {
        font-weight: bold;
        color: #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

# Check authentication
if 'access_token' not in st.session_state or not st.session_state.access_token:
    st.switch_page("pages/1_Login.py")

# Main container
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Chatbot section
st.markdown("""
<div class="chatbot-container">
    <div class="chatbot-icon">🤖</div>
    <div class="chatbot-text">
        <p>Hello! Here are some recommended Learning Modules for you!</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Learning modules
modules = [
    "Banking Options",
    "Debt Repayment",
    "Sending Money Home",
    "Creating a Budget",
    "Learn Financial Basics"
]

for module in modules:
    if st.button(module, key=module, use_container_width=True):
        # Store the interaction in DynamoDB (to be implemented)
        st.info(f"Module {module} selected - This feature will be implemented in the next phase")

# Bottom navigation
st.markdown("""
<div class="bottom-nav">
    <div class="nav-item active">
        <div>📚</div>
        Coach
    </div>
    <div class="nav-item">
        <div>👤</div>
        Profile
    </div>
    <div class="nav-item">
        <div>💬</div>
        Chat Support
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True) 