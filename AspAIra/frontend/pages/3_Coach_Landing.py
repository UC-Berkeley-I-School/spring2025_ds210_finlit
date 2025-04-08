import os
import streamlit as st
import requests
from datetime import datetime
import json
import time
from contextlib import contextmanager

# Retrieve the backend URL from environment variables (default to localhost)
backend_url = os.getenv("BACKEND_URL", "http://localhost:8001")

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
if 'initialization_attempted' not in st.session_state:
    st.session_state.initialization_attempted = False
if 'api_overloaded' not in st.session_state:
    st.session_state.api_overloaded = False
if 'retry_after' not in st.session_state:
    st.session_state.retry_after = 0

# Custom CSS for fixed header
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
</style>
""", unsafe_allow_html=True)

@contextmanager
def loading_state():
    """Context manager for loading state"""
    st.session_state.is_loading = True
    try:
        yield
    finally:
        st.session_state.is_loading = False

def update_chat_state(message, role):
    """Central function for updating chat state"""
    if not message or not message.strip():
        return False
    st.session_state.chat_history.append({
        "role": role,
        "content": message.strip()
    })
    return True

def clear_session_state():
    """Centralized session state management"""
    auth_states = {
        'access_token': st.session_state.get('access_token'),
        'username': st.session_state.get('username'),
        'last_username': st.session_state.get('last_username')
    }
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    for key, value in auth_states.items():
        if value:
            st.session_state[key] = value

def reset_for_new_topic():
    """Reset only chat-related states while preserving auth"""
    chat_states = ['chat_history', 'conversation_id', 'waiting_for_navigation', 'is_loading', 'user_input', 'api_overloaded', 'retry_after']
    for state in chat_states:
        if state in st.session_state:
            del st.session_state[state]
    # Reinitialize required states
    st.session_state.chat_history = []
    st.session_state.conversation_id = None
    st.session_state.waiting_for_navigation = False
    st.session_state.is_loading = False
    st.session_state.user_input = ""
    st.session_state.api_overloaded = False
    st.session_state.retry_after = 0

def handle_session_end():
    """Complete session end handling"""
    clear_session_state()
    st.switch_page("Home.py")

def handle_navigation(message):
    """Handle navigation options with proper state management"""
    message_lower = message.lower().strip()
    
    # Check for variations of "start new topic"
    if message_lower in ["1", "start new topic", "start a new topic", "new topic", "start topic"]:
        print("Frontend: User selected to start a new topic")
        # Reset all chat-related states
        reset_for_new_topic()
        # Reset initialization flag to allow new initial message
        st.session_state.initialization_attempted = False
        # Force a complete page rerun
        st.rerun()
    # Check for variations of "end session"
    elif message_lower in ["2", "end the session", "end session", "end", "stop"]:
        print("Frontend: User selected to end session")
        handle_session_end()
    else:
        print(f"Frontend: Invalid navigation option: {message_lower}")
        st.error("Please select a valid option: 1️⃣ Start a new Topic or 2️⃣ End The Session")
        st.session_state.waiting_for_navigation = True

def process_response(response_data):
    """Handle all response processing in one place"""
    if response_data.get('conversation_id'):
        st.session_state.conversation_id = response_data['conversation_id']
    
    if response_data.get('response'):
        # First add message to chat
        if update_chat_state(response_data['response'], 'assistant'):
            # Then check for navigation
            if "Would you like to: 1️⃣ Start a new Topic 2️⃣ End The Session" in response_data['response']:
                st.session_state.waiting_for_navigation = True
    return False

def handle_api_error(error_msg):
    """Handle API errors, especially overloaded errors"""
    if 'overloaded' in error_msg.lower():
        st.session_state.api_overloaded = True
        st.session_state.retry_after = int(time.time()) + 30  # Retry after 30 seconds
        return True
    return False

def get_initial_message():
    """Get the initial welcome message from the Dify agent"""
    if st.session_state.initialization_attempted:
        return
        
    st.session_state.initialization_attempted = True
    
    try:
        print(f"Frontend: Starting initial message request for user {st.session_state.username}")
        
        with loading_state():
            with requests.post(
                f"{backend_url}/api/chat",
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
                                data = line[6:]
                                if data == '[DONE]':
                                    break
                                try:
                                    response_data = json.loads(data)
                                    if 'error' in response_data:
                                        error_msg = response_data['error']
                                        if handle_api_error(error_msg):
                                            return
                                    process_response(response_data)
                                except json.JSONDecodeError:
                                    continue
                else:
                    error_data = response.json()
                    st.error(f"Error: {error_data.get('detail', 'Unknown error occurred')}")
            
    except Exception as e:
        print(f"Frontend: Error getting initial message - {str(e)}")
        st.error(f"Error getting initial message: {str(e)}")
    finally:
        st.rerun()

def start_fresh_conversation():
    """Start a completely fresh conversation"""
    print("Frontend: Starting fresh conversation")
    reset_for_new_topic()
    st.session_state.initialization_attempted = False
    st.rerun()  # Ensure clean state

def process_message(message):
    """Process a message after the spinner is shown"""
    if st.session_state.waiting_for_navigation:
        handle_navigation(message)
        return
    
    if not update_chat_state(message, 'user'):
        return
    
    print(f"Frontend: Sending message - {message}")
    
    try:
        with requests.post(
            f"{backend_url}/api/chat",
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
                            data = line[6:]
                            if data == '[DONE]':
                                break
                            try:
                                response_data = json.loads(data)
                                if 'error' in response_data:
                                    error_msg = response_data['error']
                                    if handle_api_error(error_msg):
                                        return
                                process_response(response_data)
                            except json.JSONDecodeError:
                                continue
            else:
                error_data = response.json()
                st.error(f"Error: {error_data.get('detail', 'Unknown error occurred')}")
            
    except requests.exceptions.RequestException as e:
        st.error("Network error. Please check your connection and try again.")
    except Exception as e:
        print(f"Frontend: Error sending message - {str(e)}")
        st.error(f"An error occurred: {str(e)}")

def send_message():
    """Initiate message sending and show spinner"""
    if not st.session_state.user_input or not st.session_state.user_input.strip():
        return
        
    # Store message and show spinner
    st.session_state.pending_message = st.session_state.user_input.strip()
    st.session_state.user_input = ""
    st.session_state.is_loading = True
    st.rerun()

def render_chat_interface():
    """Render the chat interface"""
    chat_container = st.container()
    
    with chat_container:
        # Display chat history with support for multiple message formats
        if st.session_state.chat_history:
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.write(message["content"])
    
        # Show loading spinner when processing
        if st.session_state.is_loading:
            with st.spinner("Thinking..."):
                st.empty()
                # Process message if we have one pending
                if st.session_state.pending_message:
                    process_message(st.session_state.pending_message)
                    st.session_state.pending_message = None
                    st.session_state.is_loading = False
                    st.rerun()
        
        if st.session_state.api_overloaded:
            current_time = int(time.time())
            if current_time < st.session_state.retry_after:
                wait_time = st.session_state.retry_after - current_time
                st.warning(f"The service is currently experiencing high load. Please try again in {wait_time} seconds.")
                if st.button("Retry Now"):
                    st.session_state.api_overloaded = False
                    st.session_state.initialization_attempted = False
                    st.rerun()
            else:
                st.session_state.api_overloaded = False
                st.session_state.initialization_attempted = False
                st.rerun()
        
        if not st.session_state.chat_history and not st.session_state.is_loading and not st.session_state.api_overloaded:
            get_initial_message()
    
    if prompt := st.chat_input("Ask your question here...", disabled=st.session_state.is_loading or st.session_state.api_overloaded):
        st.session_state.user_input = prompt
        send_message()

# Main page content - Fixed header
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

# Show loading state while initializing
if not st.session_state.chat_history and not st.session_state.is_loading and not st.session_state.api_overloaded:
    with st.spinner("Loading Financial Coach Content..."):
        st.empty()
        get_initial_message()

# Render chat interface
render_chat_interface() 