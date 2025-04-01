import streamlit as st

# Initialize session states
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'language' not in st.session_state:
    st.session_state.language = 'English'
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'

# Page configuration
st.set_page_config(
    page_title="AspAIra - Home",
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
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    [data-testid="collapsedControl"] {display: none !important;}
    section[data-testid="stSidebar"] {display: none !important;}
    header[data-testid="stHeader"] {display: none !important;}
    div[data-testid="stToolbar"] {display: none !important;}
    div[data-testid="stDecoration"] {display: none !important;}
    
    /* Center title */
    .title-container {
        text-align: center;
        padding: 0.5rem 0;
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background: white;
        z-index: 1000;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Main content container */
    .main-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 1rem;
        text-align: center;
        padding-top: 60px;
    }
    
    /* Image styling */
    .hero-image {
        max-width: 85%;
        height: 300px;
        object-fit: cover;
        margin: 1rem auto;
        border-radius: 10px;
        display: block;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #2E8B57 !important;
        color: white !important;
        border: none !important;
        padding: 0.75rem 1.5rem !important;
        font-size: 1.1rem !important;
        cursor: pointer !important;
        border-radius: 8px !important;
        transition: background-color 0.2s ease !important;
        width: 200px !important;
        margin: 2rem auto !important;
        display: block !important;
    }
    
    .stButton > button:hover {
        background-color: #3CB371 !important;
    }
    
    .stButton > button:focus {
        box-shadow: 0 0 0 2px #3CB371 !important;
    }
    
    /* Description text */
    .description {
        font-size: 1rem;
        line-height: 1.5;
        color: #333;
        margin: 1rem auto;
        max-width: 600px;
        text-align: center;
        padding: 0 1rem;
    }

    /* Responsive design */
    @media screen and (max-width: 768px) {
        .main-container {
            padding: 0.5rem;
            padding-top: 50px;
        }
        
        .title-container {
            padding: 0.5rem 0;
        }
        
        .hero-image {
            max-width: 95%;
            height: 250px;
            margin: 0.5rem auto;
        }
        
        .description {
            font-size: 0.9rem;
            padding: 0 0.5rem;
            margin: 0.5rem auto;
        }
        
        h1 {
            font-size: 1.8rem !important;
            margin: 0.5rem 0 !important;
        }
        
        h2 {
            font-size: 1.5rem !important;
            margin: 0.5rem 0 !important;
        }

        .stButton > button {
            margin: 1.5rem auto !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# Main container
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Title
st.markdown('<div class="title-container"><h1>🌱 AspAIra</h1></div>', unsafe_allow_html=True)

# Hero image - using a different plant image
st.markdown("""
<img src="https://images.unsplash.com/photo-1520412099551-62b6bafeb5bb" 
     alt="Beautiful Green Plant Symbolizing Growth" 
     class="hero-image">
""", unsafe_allow_html=True)

# Empowerment message
st.markdown('<h2 style="text-align: center;">Here to Empower You!</h2>', unsafe_allow_html=True)

# Description
st.markdown("""
<div class="description">
    Our AI-powered financial literacy platform is designed specifically for you. 
    We provide personalized guidance to help you manage your finances, set savings goals, and make informed financial decisions. 
    Join us on your journey to financial independence!
</div>
""", unsafe_allow_html=True)

# Get Started button
if st.button("Get Started"):
    st.switch_page("pages/1_Login.py")

st.markdown('</div>', unsafe_allow_html=True) 