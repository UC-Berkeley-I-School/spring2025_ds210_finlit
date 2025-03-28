import streamlit as st
import requests
from datetime import datetime
import json

# Initialize session states
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_topic' not in st.session_state:
    st.session_state.current_topic = None
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""
if 'conversation_id' not in st.session_state:
    st.session_state.conversation_id = None
if 'quiz_state' not in st.session_state:
    st.session_state.quiz_state = {
        'active': False,
        'current_question': 0,
        'answers': [],
        'questions': []
    }
if 'conversations' not in st.session_state:
    st.session_state.conversations = []

# Get username from token if not set
if st.session_state.access_token and not st.session_state.username:
    try:
        # Get username from token
        response = requests.get(
            "http://localhost:8001/token/verify",
            headers={"Authorization": f"Bearer {st.session_state.access_token}"}
        )
        if response.status_code == 200:
            user_data = response.json()
            st.session_state.username = user_data.get("username")
            print(f"Got username from token: {st.session_state.username}")
    except Exception as e:
        print(f"Error getting username from token: {str(e)}")
        st.error("Error initializing user session")

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
        padding: 0.75rem 1rem;
        border-radius: 15px 15px 0 15px;
        margin: 0.5rem 0;
        max-width: 60%;
        margin-left: auto;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        display: inline-block;
        float: right;
        clear: both;
    }
    
    .assistant-message {
        background-color: #f0f0f0;
        color: #333;
        padding: 1rem;
        border-radius: 15px 15px 15px 0;
        margin: 0.5rem 0;
        max-width: 80%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        display: inline-block;
        float: left;
        clear: both;
    }

    .message-content {
        margin-bottom: 0.5rem;
    }
    
    .message-timestamp {
        font-size: 0.8rem;
        color: #666;
        text-align: right;
    }

    /* Clear floats after messages */
    .message-container {
        clear: both;
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
                "number_of_dependents": user_data.get("profile1", {}).get("number_of_dependents", ""),
                "bank_account": user_data.get("profile2", {}).get("bank_account", ""),
                "debt_information": user_data.get("profile2", {}).get("debt_information", ""),
                "remittance_information": user_data.get("profile2", {}).get("remittance_information", ""),
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

def get_initial_message():
    """Get the initial welcome message from the Dify agent"""
    try:
        # Get user profile data
        profile_data = get_user_profile()
        if not profile_data:
            st.error("Failed to get user profile. Please complete your profile first.")
            return
        
        # Show thinking indicator
        with st.spinner("Thinking..."):
            # Send request with streaming
            with requests.post(
                "http://localhost:8001/api/chat",
                headers={"Authorization": f"Bearer {st.session_state.access_token}"},
                json={
                    "message": "Please start a new conversation and provide the opening statement so we can get started",
                    "username": st.session_state.username,
                    "profile_data": profile_data
                },
                stream=True
            ) as response:
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            line = line.decode('utf-8')
                            if line.startswith('data: '):
                                data = line[6:]  # Remove 'data: ' prefix
                                if data == '[DONE]':
                                    break
                                try:
                                    chunk = json.loads(data)
                                    print(f"Frontend received chunk: {chunk}")  # Debug log
                                    
                                    # Handle different event types
                                    if 'event' in chunk:
                                        if chunk['event'] == 'agent_thought':
                                            # This contains the complete response
                                            assistant_message = chunk.get('data', {}).get('thought', '')
                                            print(f"Received complete message: {assistant_message}")
                                            # Add the complete assistant message to chat history
                                            st.session_state.chat_history.append({
                                                "role": "assistant",
                                                "content": assistant_message,
                                                "timestamp": datetime.now().strftime("%H:%M")
                                            })
                                        elif chunk['event'] == 'message_end':
                                            print("Received message_end event")
                                            if 'conversation_id' in chunk:
                                                st.session_state.conversation_id = chunk['conversation_id']
                                                print(f"Received conversation ID: {chunk['conversation_id']}")
                                    
                                    # Handle errors
                                    if 'error' in chunk:
                                        st.error(f"Error: {chunk['error']}")
                                        break
                                except json.JSONDecodeError:
                                    print(f"Error decoding JSON: {data}")
                                    continue
                else:
                    error_data = response.json()
                    st.error(f"Error: {error_data.get('detail', 'Unknown error occurred')}")
                    
    except Exception as e:
        st.error(f"Error getting initial message: {str(e)}")
        print(f"Error details: {str(e)}")

def send_message():
    """Send message to backend and update chat history"""
    if not st.session_state.user_input:
        return
        
    # Get user input and clear the input field
    message = st.session_state.user_input
    st.session_state.user_input = ""
    
    # Add user message to chat history immediately
    st.session_state.chat_history.append({
        "role": "user",
        "content": message,
        "timestamp": datetime.now().strftime("%H:%M")
    })
    
    try:
        print(f"Sending message to backend: {message}")
        
        # Get user profile data
        profile_data = get_user_profile()
        if not profile_data:
            st.error("Failed to get user profile. Please complete your profile first.")
            return
        
        # Show thinking indicator
        with st.spinner("Thinking..."):
            # Send request with streaming
            with requests.post(
                "http://localhost:8001/api/chat",
                headers={"Authorization": f"Bearer {st.session_state.access_token}"},
                json={
                    "message": message,
                    "username": st.session_state.username,
                    "profile_data": profile_data,
                    "conversation_id": st.session_state.conversation_id
                },
                stream=True
            ) as response:
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            line = line.decode('utf-8')
                            if line.startswith('data: '):
                                data = line[6:]  # Remove 'data: ' prefix
                                if data == '[DONE]':
                                    break
                                try:
                                    chunk = json.loads(data)
                                    print(f"Frontend received chunk: {chunk}")  # Debug log
                                    
                                    # Handle different event types
                                    if 'event' in chunk:
                                        if chunk['event'] == 'agent_thought':
                                            # This contains the complete response
                                            assistant_message = chunk.get('data', {}).get('thought', '')
                                            print(f"Received complete message: {assistant_message}")
                                            # Add the complete assistant message to chat history
                                            st.session_state.chat_history.append({
                                                "role": "assistant",
                                                "content": assistant_message,
                                                "timestamp": datetime.now().strftime("%H:%M")
                                            })
                                        elif chunk['event'] == 'message_end':
                                            print("Received message_end event")
                                            if 'conversation_id' in chunk:
                                                st.session_state.conversation_id = chunk['conversation_id']
                                                print(f"Received conversation ID: {chunk['conversation_id']}")
                                    
                                    # Handle errors
                                    if 'error' in chunk:
                                        st.error(f"Error: {chunk['error']}")
                                        break
                                except json.JSONDecodeError:
                                    print(f"Error decoding JSON: {data}")
                                    continue
                else:
                    error_data = response.json()
                    st.error(f"Error: {error_data.get('detail', 'Unknown error occurred')}")
                    
    except Exception as e:
        st.error(f"Error sending message: {str(e)}")
        print(f"Error details: {str(e)}")

def load_conversations():
    """Load user's conversations from the backend"""
    try:
        response = requests.get(
            "http://localhost:8001/api/chat/conversations",
            headers={"Authorization": f"Bearer {st.session_state.access_token}"}
        )
        if response.status_code == 200:
            st.session_state.conversations = response.json().get("conversations", [])
        else:
            st.error("Failed to load conversations")
    except Exception as e:
        st.error(f"Error loading conversations: {str(e)}")

def load_chat_history(conversation_id: str):
    """Load chat history for a specific conversation"""
    try:
        response = requests.get(
            f"http://localhost:8001/api/chat/history?conversation_id={conversation_id}",
            headers={"Authorization": f"Bearer {st.session_state.access_token}"}
        )
        if response.status_code == 200:
            messages = response.json().get("messages", [])
            st.session_state.chat_history = [
                {
                    "role": "assistant" if msg.get("role") == "assistant" else "user",
                    "content": msg.get("message", ""),
                    "timestamp": datetime.fromisoformat(msg.get("timestamp")).strftime("%H:%M")
                }
                for msg in messages
            ]
            st.session_state.conversation_id = conversation_id
        else:
            st.error("Failed to load chat history")
    except Exception as e:
        st.error(f"Error loading chat history: {str(e)}")

def render_chat_interface():
    """Render the chat interface"""
    # Load conversations if not already loaded
    if not st.session_state.conversations:
        load_conversations()
    
    # Create a container for chat messages
    chat_container = st.container()
    
    # Display chat history with improved formatting
    with chat_container:
        # If chat history is empty, get initial message from agent
        if not st.session_state.chat_history:
            get_initial_message()  # This will handle adding to chat history internally
        
        # Display all messages in chronological order
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f'<div class="message-container"><div class="user-message">{message["content"]}</div></div>', unsafe_allow_html=True)
            else:
                # Add timestamp to assistant messages
                timestamp = message.get("timestamp", datetime.now().strftime("%H:%M"))
                st.markdown(f'<div class="message-container"><div class="assistant-message"><div class="message-content">{message["content"]}</div><div class="message-timestamp">{timestamp}</div></div></div>', unsafe_allow_html=True)
    
    # Chat input for free-form conversation
    if prompt := st.chat_input("Ask your question here..."):
        st.session_state.user_input = prompt
        # Show loading state
        with st.spinner("Thinking..."):
            send_message()

# Main page content
st.title("🌱 AspAIra Financial Coach")

# Render chat interface
render_chat_interface() 