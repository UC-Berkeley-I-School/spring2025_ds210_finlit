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
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""
if 'conversation_id' not in st.session_state:
    st.session_state.conversation_id = None
if 'is_loading' not in st.session_state:
    st.session_state.is_loading = False
if 'waiting_for_navigation' not in st.session_state:
    st.session_state.waiting_for_navigation = False
if 'last_username' not in st.session_state:
    st.session_state.last_username = None

# Get username from token if not set
if st.session_state.access_token and not st.session_state.username:
    try:
        response = requests.get(
            "http://localhost:8001/token/verify",
            headers={"Authorization": f"Bearer {st.session_state.access_token}"}
        )
        if response.status_code == 200:
            user_data = response.json()
            st.session_state.username = user_data.get("username")
            print(f"Frontend: User authenticated - {st.session_state.username}")
    except Exception as e:
        print(f"Frontend: Error initializing user session - {str(e)}")
        st.error("Error initializing user session")

# Check if username has changed (new user logged in)
if st.session_state.username and st.session_state.username != st.session_state.last_username:
    print(f"Frontend: New user logged in - {st.session_state.username}")
    # Clear chat-related states for new user
    st.session_state.chat_history = []
    st.session_state.conversation_id = None
    st.session_state.waiting_for_navigation = False
    st.session_state.last_username = st.session_state.username

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
    header[data-testid="stHeader"] {display: none !important;}
    
    /* Fixed header section */
    .header-section {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background: white;
        padding: 1.5rem;
        z-index: 1000;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        max-width: 100%;
        height: auto;
    }
    
    /* Add padding to main content to prevent overlap with fixed header */
    .main .block-container {
        padding-top: 180px !important;
    }
    
    /* Chat container specific padding and positioning */
    .stChat {
        margin-top: 20px !important;
        padding-top: 20px !important;
        position: relative !important;
        z-index: 1 !important;
    }

    /* Ensure chat messages container is properly positioned */
    .stChatMessageContainer {
        margin-top: 20px !important;
        position: relative !important;
        z-index: 1 !important;
    }
    
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

    /* Clear floats after messages */
    .message-container {
        clear: both;
    }

    /* Help text container */
    .help-text-container {
        color: #666;
        font-size: 0.9em;
        margin: 0;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

def get_initial_message():
    """Get the initial welcome message from the Dify agent"""
    try:
        print(f"Frontend: Starting initial message request for user {st.session_state.username}")
        st.session_state.is_loading = True
        
        # Send request with streaming
        with requests.post(
            "http://localhost:8001/api/chat",
            headers={"Authorization": f"Bearer {st.session_state.access_token}"},
            json={
                "message": "Please start a new conversation and provide the opening statement so we can get started",
                "username": st.session_state.username
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
                                response_data = json.loads(data)
                                
                                # Update conversation ID first
                                if response_data.get('conversation_id'):
                                    st.session_state.conversation_id = response_data['conversation_id']
                                
                                # Then add message to chat history
                                if response_data.get('response'):
                                    st.session_state.chat_history.append({
                                        "role": "assistant",
                                        "content": response_data['response']
                                    })
                            except json.JSONDecodeError:
                                continue
            else:
                error_data = response.json()
                st.error(f"Error: {error_data.get('detail', 'Unknown error occurred')}")
            
    except Exception as e:
        print(f"Frontend: Error getting initial message - {str(e)}")
        st.error(f"Error getting initial message: {str(e)}")
    finally:
        st.session_state.is_loading = False
        st.rerun()

# Show loading state while initializing
if not st.session_state.chat_history and not st.session_state.is_loading:
    with st.spinner("Loading Financial Coach Content..."):
        st.empty()  # Placeholder for the spinner
        get_initial_message()

# Main page content
st.markdown("""
<div class="header-section">
    <div style="margin-bottom: 0; text-align: center;">
        <h1 style="margin: 0; padding: 0; font-size: 2.2em; line-height: 1.2;">🌱 AspAIra</h1>
        <div class="help-text-container" style="margin-top: 0.25rem;">
            In order to end a learning session or start a new one just input "STOP" and a final quiz will be provided
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

def start_fresh_conversation():
    """Start a completely fresh conversation by clearing state and getting initial message"""
    print("Frontend: Starting fresh conversation")
    # Clear all session state except authentication-related states
    auth_token = st.session_state.get('access_token')
    username = st.session_state.get('username')
    last_username = st.session_state.get('last_username')
    
    # Clear all session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    # Restore authentication states
    if auth_token:
        st.session_state.access_token = auth_token
    if username:
        st.session_state.username = username
    if last_username:
        st.session_state.last_username = last_username
    
    # Initialize required session states
    st.session_state.chat_history = []
    st.session_state.conversation_id = None
    st.session_state.waiting_for_navigation = False
    st.session_state.is_loading = False
    st.session_state.user_input = ""
    
    # Get initial message
    get_initial_message()

def send_message():
    """Send message to backend and update chat history"""
    if not st.session_state.user_input:
        return
        
    # Get user input and clear the input field
    message = st.session_state.user_input
    st.session_state.user_input = ""
    
    # Check if we're waiting for navigation input
    if st.session_state.waiting_for_navigation:
        # Convert input to lowercase for case-insensitive matching
        message_lower = message.lower()
        
        # Handle navigation options
        if message_lower in ["1", "start new topic"]:
            # Start fresh conversation
            start_fresh_conversation()
        elif message_lower in ["2", "end the session", "end session"]:
            # Clear all session state before redirecting
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.switch_page("Home.py")
        return
    
    print(f"Frontend: Sending message - {message}")
    
    # Add user message to chat history immediately
    st.session_state.chat_history.append({
        "role": "user",
        "content": message
    })
    
    try:
        st.session_state.is_loading = True
        
        # Show thinking indicator
        with st.spinner("Thinking..."):
            # Send request with streaming
            with requests.post(
                "http://localhost:8001/api/chat",
                headers={"Authorization": f"Bearer {st.session_state.access_token}"},
                json={
                    "message": message,
                    "username": st.session_state.username,
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
                                    response_data = json.loads(data)
                                    
                                    # Update conversation ID
                                    if response_data.get('conversation_id'):
                                        st.session_state.conversation_id = response_data['conversation_id']
                                    
                                    # Add assistant message to chat history
                                    if response_data.get('response'):
                                        st.session_state.chat_history.append({
                                            "role": "assistant",
                                            "content": response_data['response']
                                        })
                                        
                                        # Check for navigation prompt
                                        if "Would you like to: 1️⃣ Start a new Topic 2️⃣ End The Session" in response_data['response']:
                                            st.session_state.waiting_for_navigation = True
                                        
                                        st.rerun()
                                except json.JSONDecodeError:
                                    continue
                else:
                    error_data = response.json()
                    st.error(f"Error: {error_data.get('detail', 'Unknown error occurred')}")
                
    except Exception as e:
        print(f"Frontend: Error sending message - {str(e)}")
        st.error(f"Error sending message: {str(e)}")
    finally:
        st.session_state.is_loading = False

def render_chat_interface():
    """Render the chat interface"""
    # Create a container for chat messages
    chat_container = st.container()
    
    # Display chat history with improved formatting
    with chat_container:
        # If chat history is empty and not loading, get initial message from agent
        if not st.session_state.chat_history and not st.session_state.is_loading:
            get_initial_message()
        
        # Only display messages if we have them
        if st.session_state.chat_history:
            # Display all messages in chronological order using Streamlit's native chat components
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.write(message["content"])
    
    # Chat input for free-form conversation
    if prompt := st.chat_input("Ask your question here..."):
        st.session_state.user_input = prompt
        send_message()

# Render chat interface
render_chat_interface() 