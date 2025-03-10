import streamlit as st
import requests
from datetime import datetime
import json

# Initialize session states
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = None
if 'current_topic' not in st.session_state:
    st.session_state.current_topic = None
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""
if 'quiz_state' not in st.session_state:
    st.session_state.quiz_state = {
        'active': False,
        'current_question': 0,
        'answers': [],
        'questions': []
    }

# Page configuration
st.set_page_config(
    page_title="AspAIra - Financial Coach",
    page_icon="🌱",
    layout="wide",
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
    
    /* Message bubbles */
    .user-message {
        background-color: #2E8B57;
        color: white;
        padding: 1rem;
        border-radius: 15px 15px 0 15px;
        margin: 0.5rem 0;
        max-width: 80%;
        margin-left: auto;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .assistant-message {
        background-color: #f0f0f0;
        color: #333;
        padding: 1rem;
        border-radius: 15px 15px 15px 0;
        margin: 0.5rem 0;
        max-width: 80%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .message-content {
        margin-bottom: 0.5rem;
    }
    
    .message-timestamp {
        font-size: 0.8rem;
        color: #666;
        text-align: right;
    }

    /* Option buttons */
    .option-button {
        background-color: #2E8B57;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        margin: 0.25rem 0;
        width: 100%;
        cursor: pointer;
        transition: background-color 0.3s;
    }

    .option-button:hover {
        background-color: #236B47;
    }

    /* Quiz interface */
    .quiz-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }

    .quiz-question {
        font-weight: bold;
        margin-bottom: 1rem;
    }

    .quiz-option {
        margin: 0.5rem 0;
        padding: 0.5rem;
        border: 1px solid #ddd;
        border-radius: 4px;
        cursor: pointer;
    }

    .quiz-option:hover {
        background-color: #f0f0f0;
    }

    /* Clear chat button */
    .clear-chat-button {
        background-color: #dc3545;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        margin: 1rem 0;
        cursor: pointer;
        transition: background-color 0.3s;
    }
    
    .clear-chat-button:hover {
        background-color: #c82333;
    }
</style>
""", unsafe_allow_html=True)

def get_user_profile():
    """Fetch user profile data from backend"""
    try:
        headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
        # First get profile status
        status_response = requests.get("http://localhost:8001/user/profile-status", headers=headers)
        if status_response.status_code != 200:
            st.error("Failed to get profile status")
            return None
            
        # Then get the full user data
        user_response = requests.get("http://localhost:8001/user/profile", headers=headers)
        if user_response.status_code == 200:
            user_data = user_response.json()
            # Extract and validate required profile data
            profile_data = {
                "dependents_count": user_data.get("profile1", {}).get("number_of_dependents", ""),
                "bank_account": user_data.get("profile2", {}).get("bank_account", ""),
                "debt_status": user_data.get("profile2", {}).get("debt_information", ""),
                "remittance_status": user_data.get("profile2", {}).get("remittance_information", ""),
                "remittance_amount": user_data.get("profile2", {}).get("remittance_amount", ""),
                "country_of_origin": user_data.get("profile1", {}).get("country_of_origin", ""),
                "time_in_uae": user_data.get("profile1", {}).get("time_in_uae", ""),
                "job_title": user_data.get("profile1", {}).get("job_title", ""),
                "housing": user_data.get("profile1", {}).get("housing", ""),
                "education_level": user_data.get("profile1", {}).get("education_level", "")
            }
            
            # Check if any required fields are missing
            missing_fields = [k for k, v in profile_data.items() if not v]
            if missing_fields:
                st.warning("Some profile information is missing. The AI coach may not be able to provide fully personalized responses.")
                st.warning(f"Missing fields: {', '.join(missing_fields)}")
            
            return profile_data
        else:
            st.error(f"Failed to get user profile. Status code: {user_response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error fetching profile: {str(e)}")
        return None

def send_message():
    """Send message to backend and update chat history"""
    if not st.session_state.user_input:
        return
        
    # Get user input and clear the input field
    message = st.session_state.user_input
    st.session_state.user_input = ""
    
    # Get user profile data
    profile_data = get_user_profile()
    
    # Send message to backend
    try:
        print(f"Sending message to backend: {message}")
        response = requests.post(
            "http://localhost:8001/api/chat",
            headers={"Authorization": f"Bearer {st.session_state.access_token}"},
            json={"message": message, "profile_data": profile_data},
            timeout=60  # Add explicit timeout
        )
        
        print(f"Received response status: {response.status_code}")
        
        # Enhanced error handling
        if response.status_code == 401:
            st.error("Your session has expired. Please log in again.")
            st.switch_page("pages/1_Login.py")
            return
        elif response.status_code == 404:
            st.error("The chat service is currently unavailable. Please try again later.")
            return
        elif response.status_code == 500:
            st.error("An internal server error occurred. Please try again later.")
            return
        elif response.status_code != 200:
            error_message = response.json().get("message", "Unknown error occurred")
            st.error(f"Failed to get response from AI coach: {error_message}")
            return
        
        data = response.json()
        print(f"Received response data: {data}")
        
        if not data.get("message"):
            st.error("Received empty response from AI coach")
            return
            
        # Clear previous chat history
        st.session_state.chat_history = []
        
        # Add the full response to chat history
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": data["message"],
            "timestamp": data.get("timestamp"),
            "message_id": data.get("message_id"),
            "conversation_id": data.get("conversation_id")
        })
        
        print(f"Updated chat history: {st.session_state.chat_history}")
        
        # Handle quiz if present
        if data.get("quiz"):
            st.session_state.current_quiz = data["quiz"]
            st.session_state.quiz_answers = []
            st.session_state.showing_quiz = True
            
        # Rerun the app to refresh the page with new chat history
        st.rerun()
            
    except requests.Timeout:
        st.error("The request is taking longer than expected. Please try again.")
        return
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the server. Please check your internet connection and try again.")
    except Exception as e:
        print(f"Error in send_message: {str(e)}")
        st.error(f"An unexpected error occurred: {str(e)}")
        st.error("Please try again or contact support if the problem persists.")

def render_quiz_interface(quiz_data: dict):
    """Render the quiz interface"""
    st.markdown("### Quiz Time! 📝")
    
    for i, question in enumerate(quiz_data['questions']):
        st.markdown(f"**Question {i+1}:** {question['question']}")
        
        # Show options as buttons
        for j, option in enumerate(question['options']):
            if st.button(f"{j+1}. {option}", key=f"quiz_q{i}_opt{j}"):
                # Handle answer submission
                response = send_message()
                if response and response.get('interaction_type') == 'feedback':
                    st.markdown(f"**Feedback:** {response['message']}")
                    st.rerun()

def render_chat_interface():
    """Render the chat interface"""
    # Create a container for chat messages
    chat_container = st.container()
    
    # Display chat history with improved formatting
    with chat_container:
        # If chat history is empty, show initial welcome message
        if not st.session_state.chat_history:
            welcome_message = {
                "role": "assistant",
                "content": """Hello! I am your financial education bot. Let's talk about how to create a budget and save money.

Budgeting is important because it helps you manage your money better. You can see where your money goes and how much you can save. Would you like to learn about:

1. Creating a budget
2. Saving strategies
3. Tips for sending money home

Please choose a number to continue.""",
                "timestamp": datetime.now().strftime("%H:%M")
            }
            st.session_state.chat_history.append(welcome_message)
        
        # Display all messages including welcome message
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)
            else:
                # Add timestamp to assistant messages
                timestamp = message.get("timestamp", datetime.now().strftime("%H:%M"))
                st.markdown(f'<div class="assistant-message"><div class="message-content">{message["content"]}</div><div class="message-timestamp">{timestamp}</div></div>', unsafe_allow_html=True)
    
    # Chat input for free-form conversation
    if prompt := st.chat_input("Ask your question here..."):
        st.session_state.user_input = prompt
        # Show loading state
        with st.spinner("Thinking..."):
            send_message()
            st.rerun()

# Main page content
st.title("🌱 AspAIra Financial Coach")

# Check if profile exists
if not st.session_state.user_profile:
    st.session_state.user_profile = get_user_profile()

# Render chat interface
render_chat_interface() 