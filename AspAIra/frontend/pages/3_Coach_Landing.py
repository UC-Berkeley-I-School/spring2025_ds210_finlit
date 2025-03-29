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

    /* Clear floats after messages */
    .message-container {
        clear: both;
    }
</style>
""", unsafe_allow_html=True)

def get_initial_message():
    """Get the initial welcome message from the Dify agent"""
    try:
        print(f"Frontend: Starting initial message request for user {st.session_state.username}")
        st.session_state.is_loading = True
        
        # Show thinking indicator
        with st.spinner("Thinking..."):
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
                    print("Frontend: Received successful response from backend")
                    for line in response.iter_lines():
                        if line:
                            line = line.decode('utf-8')
                            if line.startswith('data: '):
                                data = line[6:]  # Remove 'data: ' prefix
                                if data == '[DONE]':
                                    print("Frontend: Received completion signal")
                                    break
                                try:
                                    response_data = json.loads(data)
                                    print(f"Frontend: Received response data - {json.dumps(response_data, indent=2)}")
                                    
                                    # Update conversation ID
                                    if response_data.get('conversation_id'):
                                        st.session_state.conversation_id = response_data['conversation_id']
                                        print(f"Frontend: Updated conversation_id - {response_data['conversation_id']}")
                                    
                                    # Add assistant message to chat history
                                    if response_data.get('response'):
                                        st.session_state.chat_history.append({
                                            "role": "assistant",
                                            "content": response_data['response']
                                        })
                                        print(f"Frontend: Added initial message to chat history")
                                except json.JSONDecodeError:
                                    print(f"Frontend: Error decoding JSON - {data}")
                                    continue
                else:
                    error_data = response.json()
                    print(f"Frontend: Received error response - {error_data}")
                    st.error(f"Error: {error_data.get('detail', 'Unknown error occurred')}")
                
    except Exception as e:
        print(f"Frontend: Error getting initial message - {str(e)}")
        st.error(f"Error getting initial message: {str(e)}")
    finally:
        st.session_state.is_loading = False

def send_message():
    """Send message to backend and update chat history"""
    if not st.session_state.user_input:
        return
        
    # Get user input and clear the input field
    message = st.session_state.user_input
    st.session_state.user_input = ""
    
    print("\n=== Starting Message Send ===")
    print(f"Frontend: Sending user message - {message}")
    print(f"Frontend: Current conversation_id - {st.session_state.conversation_id}")
    print(f"Frontend: Current chat history before update: {json.dumps(st.session_state.chat_history, indent=2)}")
    print(f"Frontend: Current loading state - {st.session_state.is_loading}")
    
    # Add user message to chat history immediately
    st.session_state.chat_history.append({
        "role": "user",
        "content": message
    })
    print(f"Frontend: Added user message to chat history. New length: {len(st.session_state.chat_history)}")
    print(f"Frontend: Updated chat history after user message: {json.dumps(st.session_state.chat_history, indent=2)}")
    
    try:
        st.session_state.is_loading = True
        print("Frontend: Set loading state to True")
        
        # Show thinking indicator
        with st.spinner("Thinking..."):
            # Send request with streaming
            print("Frontend: Sending request to backend...")
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
                print(f"Frontend: Response status code - {response.status_code}")
                if response.status_code == 200:
                    print("Frontend: Received successful response from backend")
                    for line in response.iter_lines():
                        if line:
                            line = line.decode('utf-8')
                            print(f"Frontend: Raw line received - {line}")
                            if line.startswith('data: '):
                                data = line[6:]  # Remove 'data: ' prefix
                                print(f"Frontend: Processing data - {data}")
                                if data == '[DONE]':
                                    print("Frontend: Received completion signal")
                                    break
                                try:
                                    response_data = json.loads(data)
                                    print(f"Frontend: Parsed response data - {json.dumps(response_data, indent=2)}")
                                    
                                    # Update conversation ID
                                    if response_data.get('conversation_id'):
                                        st.session_state.conversation_id = response_data['conversation_id']
                                        print(f"Frontend: Updated conversation_id - {response_data['conversation_id']}")
                                    
                                    # Add assistant message to chat history
                                    if response_data.get('response'):
                                        print(f"Frontend: Adding assistant message to chat history")
                                        print(f"Frontend: Current chat history before assistant message: {json.dumps(st.session_state.chat_history, indent=2)}")
                                        st.session_state.chat_history.append({
                                            "role": "assistant",
                                            "content": response_data['response']
                                        })
                                        print(f"Frontend: Chat history length after update - {len(st.session_state.chat_history)}")
                                        print(f"Frontend: Updated chat history: {json.dumps(st.session_state.chat_history, indent=2)}")
                                        print("Frontend: Triggering Streamlit rerun")
                                        st.rerun()
                                    else:
                                        print("Frontend: No response field in data")
                                except json.JSONDecodeError as e:
                                    print(f"Frontend: Error decoding JSON - {str(e)}")
                                    print(f"Frontend: Problematic data - {data}")
                                    continue
                else:
                    error_data = response.json()
                    print(f"Frontend: Received error response - {error_data}")
                    st.error(f"Error: {error_data.get('detail', 'Unknown error occurred')}")
                
    except Exception as e:
        print(f"Frontend: Error sending message - {str(e)}")
        print(f"Frontend: Error type - {type(e)}")
        import traceback
        print(f"Frontend: Traceback - {traceback.format_exc()}")
        st.error(f"Error sending message: {str(e)}")
    finally:
        st.session_state.is_loading = False
        print(f"Frontend: Set loading state to False")
        print(f"Frontend: Final chat history length - {len(st.session_state.chat_history)}")
        print(f"Frontend: Final chat history content - {json.dumps(st.session_state.chat_history, indent=2)}")
        print("=== Message Send Complete ===\n")

def render_chat_interface():
    """Render the chat interface"""
    print("\n=== Starting Chat Interface Render ===")
    print(f"Frontend: Current chat history length: {len(st.session_state.chat_history)}")
    print(f"Frontend: Current chat history content: {json.dumps(st.session_state.chat_history, indent=2)}")
    print(f"Frontend: Is loading state: {st.session_state.is_loading}")
    print(f"Frontend: Current conversation_id: {st.session_state.conversation_id}")
    
    # Create a container for chat messages
    chat_container = st.container()
    
    # Display chat history with improved formatting
    with chat_container:
        # If chat history is empty and not loading, get initial message from agent
        if not st.session_state.chat_history and not st.session_state.is_loading:
            print("Frontend: No chat history, getting initial message")
            get_initial_message()
        
        # Only display messages if we have them
        if st.session_state.chat_history:
            print(f"Frontend: Displaying {len(st.session_state.chat_history)} messages")
            # Display all messages in chronological order using Streamlit's native chat components
            for idx, message in enumerate(st.session_state.chat_history):
                print(f"Frontend: Rendering message {idx + 1}: {message['role']}")
                with st.chat_message(message["role"]):
                    st.write(message["content"])
    
    # Chat input for free-form conversation
    if prompt := st.chat_input("Ask your question here..."):
        print("\n=== User Input Received ===")
        print(f"Frontend: User entered prompt: {prompt}")
        st.session_state.user_input = prompt
        send_message()
    
    print("=== Chat Interface Render Complete ===\n")

# Main page content
st.title("🌱 AspAIra Financial Coach")

# Render chat interface
render_chat_interface() 