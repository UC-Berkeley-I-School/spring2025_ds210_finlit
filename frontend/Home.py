import streamlit as st

# Page configuration
st.set_page_config(
    page_title="AspAIra",
    page_icon="🌱",
    layout="centered"
)

# Custom CSS for mobile-first design
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
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    .main-image {
        max-width: 100%;
        margin: 1rem 0;
        border-radius: 10px;
    }
    .mission-text {
        font-size: 1.1rem;
        line-height: 1.6;
        margin: 1rem 0;
    }
    .language-selector {
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for language
if 'language' not in st.session_state:
    st.session_state.language = 'English'

# Main container
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Logo and Title
st.markdown('<div class="logo">🌱 AspAIra</div>', unsafe_allow_html=True)

# Main image
st.image("https://images.unsplash.com/photo-1512075135822-67cdd9dd7314", 
         caption="Empowering Domestic Workers in Dubai",
         use_column_width=True)

# Mission Statement
st.markdown(
    '<div class="mission-text">'
    'Here to Empower you! Our mission is to empower you with AI-driven financial '
    'literacy education to help you navigate the financial ecosystem in the UAE, '
    'break out of debt cycle, increase savings, and build a stable financial '
    'future as you adjust to life in the UAE.'
    '</div>',
    unsafe_allow_html=True
)

# Sign In Button
if st.button("Sign In", use_container_width=True):
    st.switch_page("pages/1_Login.py")

# Language Selection
st.markdown('<div class="language-selector">', unsafe_allow_html=True)
language = st.selectbox(
    "Select Language",
    ["English", "Tagalog"],
    key="language_selector"
)
st.session_state.language = language
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True) 