from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from . import models, database
from fastapi.responses import JSONResponse
from typing import Optional, List, Literal
import uvicorn
from .services.dify_service import DifyService
from .config import API_CONFIG, ACTIVE_AGENT_VERSION, AGENT_CONFIGS
import json
import asyncio
import streamlit as st
import requests
from sseclient import SSEClient
from datetime import datetime

app = FastAPI(**API_CONFIG)

# Initialize services
dify_service = DifyService()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Streamlit frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = database.get_user_from_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = database.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = database.create_access_token({"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/signup")
async def create_user(user: models.UserCreate):
    print(f"Received signup request for username: {user.username}")  # Debug log
    try:
        if not user.username or not user.password:
            return JSONResponse(
                status_code=400,
                content={"message": "Username and password are required"}
            )
            
        if len(user.password) < 6:
            return JSONResponse(
                status_code=400,
                content={"message": "Password must be at least 6 characters long"}
            )
            
        database.create_user(user.username, user.password)
        print(f"User created successfully: {user.username}")  # Debug log
        return {"message": "User created successfully"}
    except Exception as e:
        print(f"Error in create_user: {str(e)}")  # Debug log
        return JSONResponse(
            status_code=500,
            content={"message": f"Error creating account: {str(e)}"}
        )

@app.post("/user/profile1")
async def update_profile_part1(
    profile: models.ProfilePart1,
    current_user: dict = Depends(get_current_user)
):
    print(f"Received profile update request for user: {current_user['username']}")  # Debug log
    print(f"Profile data received: {profile.dict()}")  # Debug log
    try:
        result = database.update_profile_part1(current_user["username"], profile.dict())
        if not result:
            print("Failed to update profile in database")  # Debug log
            raise HTTPException(
                status_code=500, 
                detail="Failed to update profile. Please check server logs for details."
            )
        print("Profile updated successfully")  # Debug log
        return {"message": "Profile updated successfully"}
    except Exception as e:
        print(f"Error updating profile: {str(e)}")  # Debug log
        raise HTTPException(
            status_code=400,
            detail=f"Error updating profile: {str(e)}"
        )

@app.post("/user/profile2")
async def update_profile_part2(
    profile: models.ProfilePart2,
    current_user: dict = Depends(get_current_user)
):
    result = database.update_profile_part2(current_user["username"], profile.dict())
    if not result:
        raise HTTPException(status_code=500, detail="Failed to update profile")
    return {"message": "Profile updated successfully"}

@app.get("/user/profile-status")
async def get_profile_status(current_user: dict = Depends(get_current_user)):
    status = database.get_profile_status(current_user["username"])
    return status

@app.get("/debug/users")
async def get_all_users():
    users = database.scan_all_users()
    return {"users": users}

@app.post("/api/chat")
async def chat(
    chat_request: models.ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """Process a chat message and return the response"""
    try:
        print("\n=== Starting Chat Request ===")
        print(f"Current user: {current_user}")
        print(f"Chat request: {chat_request}")
        
        # Use profile data directly from current_user
        profile_data = {
            "profile1": current_user.get("profile1", {}),
            "profile2": current_user.get("profile2", {})
        }
        print(f"Profile data: {json.dumps(profile_data, indent=2)}")

        async def event_generator():
            try:
                print("\n=== Starting Event Generator ===")
                # Initialize chat data structure
                chat_data = {
                    'message_id': None,
                    'conversation_id': None,
                    'response': None,
                    'dify_metadata': {},
                    'usage_metrics': None,
                    'is_complete': False,
                    'has_saved': False  # Track if we've saved the data
                }
                
                print("\n=== Starting Event Collection ===")
                print(f"Initial chat_data: {json.dumps(chat_data, indent=2)}")
                
                try:
                    print("\nCalling Dify service process_message...")
                    # Process message through Dify
                    for event in dify_service.process_message(
                        username=current_user["username"],
                        message=chat_request.message,
                        profile_data=profile_data
                    ):
                        try:
                            print("\n=== New Event Received ===")
                            print(f"Raw event: {json.dumps(event, indent=2)}")
                            print(f"Event type: {event.get('event')}")
                            
                            if event.get('event') == 'agent_message':
                                print("\nProcessing agent_message event...")
                                # Store message_id and conversation_id
                                if event.get('data', {}).get('message_id'):
                                    chat_data['message_id'] = event.get('data', {}).get('message_id')
                                if event.get('data', {}).get('conversation_id'):
                                    chat_data['conversation_id'] = event.get('data', {}).get('conversation_id')
                                print(f"Updated chat_data after agent_message: {json.dumps(chat_data, indent=2)}")
                            
                            elif event.get('event') == 'agent_thought':
                                print("\nProcessing agent_thought event...")
                                # This is the main response content
                                chat_data['response'] = event.get('data', {}).get('thought', '')
                                # Update metadata
                                chat_data['dify_metadata'] = {
                                    "message_files": event.get('data', {}).get('message_files', []),
                                    "feedback": event.get('data', {}).get('feedback', None),
                                    "retriever_resources": event.get('data', {}).get('retriever_resources', []),
                                    "agent_thoughts": event.get('data', {}).get('agent_thoughts', [])
                                }
                                print(f"Updated chat_data after agent_thought: {json.dumps(chat_data, indent=2)}")
                            
                            elif event.get('event') == 'message_end' and not chat_data['has_saved']:
                                print("\nProcessing first message_end event...")
                                # Get usage metrics
                                chat_data['usage_metrics'] = event.get('data', {}).get('metadata', {}).get('usage', {})
                                chat_data['is_complete'] = True
                                
                                # Log current state before save attempt
                                print("\nChat Data State Before Save:")
                                print(f"message_id: {chat_data['message_id']}")
                                print(f"conversation_id: {chat_data['conversation_id']}")
                                print(f"response length: {len(chat_data['response']) if chat_data['response'] else 0}")
                                print(f"dify_metadata: {json.dumps(chat_data['dify_metadata'], indent=2)}")
                                print(f"usage_metrics: {json.dumps(chat_data['usage_metrics'], indent=2)}")
                                
                                # Save if we have the minimum required data
                                if chat_data['message_id'] and chat_data['conversation_id'] and chat_data['response']:
                                    try:
                                        success = database.save_chat_message(
                                            message_id=chat_data['message_id'],
                                            conversation_id=chat_data['conversation_id'],
                                            username=current_user["username"],
                                            agent_id=ACTIVE_AGENT_VERSION,
                                            timestamp=datetime.now(),
                                            message=chat_request.message,
                                            response=chat_data['response'],
                                            interaction_type="chat",
                                            dify_metadata=chat_data['dify_metadata'],
                                            usage_metrics=chat_data['usage_metrics']
                                        )
                                        if success:
                                            chat_data['has_saved'] = True
                                            print("Successfully saved chat message")
                                        else:
                                            print("Failed to save chat message")
                                    except Exception as e:
                                        print(f"Error saving chat message: {str(e)}")
                                        print(f"Error type: {type(e)}")
                                        import traceback
                                        print(f"Traceback: {traceback.format_exc()}")
                                else:
                                    print("Save conditions not met, skipping save")
                                    print(f"Missing required fields:")
                                    print(f"message_id present: {bool(chat_data['message_id'])}")
                                    print(f"conversation_id present: {bool(chat_data['conversation_id'])}")
                                    print(f"response present: {bool(chat_data['response'])}")
                            
                            elif event.get('event') == 'message_end' and chat_data['has_saved']:
                                print("\nSkipping second message_end event (already saved)")
                                continue
                            
                            elif event.get('event') == 'error':
                                print(f"\nError event received: {event.get('error')}")
                                return
                            
                            # Stream the event to frontend
                            yield f"data: {json.dumps({'event': event.get('event'), 'data': event.get('data', {})})}\n\n"
                                
                        except Exception as e:
                            print(f"\nError processing event: {str(e)}")
                            print(f"Error type: {type(e)}")
                            import traceback
                            print(f"Traceback: {traceback.format_exc()}")
                            continue
                            
                except Exception as e:
                    print(f"\nError in Dify service process_message: {str(e)}")
                    print(f"Error type: {type(e)}")
                    import traceback
                    print(f"Traceback: {traceback.format_exc()}")
                    return
                
            except Exception as e:
                print(f"\nError in event_generator: {str(e)}")
                print(f"Error type: {type(e)}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                return

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        print(f"\nError in chat endpoint: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/api/chat/history")
async def get_chat_history(
    conversation_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get chat history for the current user"""
    try:
        # Get chat history from database
        history = database.get_chat_history(
            username=current_user["username"],
            conversation_id=conversation_id
        )
        
        return {"messages": history}
        
    except Exception as e:
        print(f"Error getting chat history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/api/chat/conversations")
async def get_conversations(
    current_user: dict = Depends(get_current_user)
):
    """Get all conversations for the current user"""
    try:
        # Get conversations from database
        conversations = database.get_conversations(
            username=current_user["username"]
        )
        
        return {"conversations": conversations}
        
    except Exception as e:
        print(f"Error getting conversations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/user/profile")
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """Get complete user profile data"""
    try:
        user = database.get_user(current_user["username"])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        # Extract profile data with proper structure
        profile_data = {
            "profile1": user.get("profile1", {}),
            "profile2": user.get("profile2", {})
        }
        
        print(f"User data from database: {user}")
        print(f"Returning profile data: {profile_data}")
        
        return profile_data
    except Exception as e:
        print(f"Error getting user profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/token/verify")
async def verify_token(current_user: dict = Depends(get_current_user)):
    """Verify token and return user data"""
    return {"username": current_user["username"]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 