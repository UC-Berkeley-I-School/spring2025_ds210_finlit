from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from . import models, database
from typing import Optional, List, Literal, Dict, Tuple
import uvicorn
from .services.dify_service import DifyService
from .config import API_CONFIG, ACTIVE_AGENT_VERSION, AGENT_CONFIGS
import json
import asyncio
import requests
#from sseclient import SSEClient
from datetime import datetime
from .database import UserExistsError
import logging
import uuid
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def detect_quiz_interaction(response: str) -> Tuple[str, Optional[Dict]]:
    """
    Detect quiz interactions and return interaction type and quiz data.
    Returns (interaction_type, quiz_data)
    """
    logger.info(f"Detecting quiz interaction for response: {response[:200]}...")
    
    if "LEARNING CHECK 📝" in response:
        logger.info("Detected quiz prompt pattern")
        questions = []
        lines = response.split('\n')
        current_question = None
        
        for line in lines:
            if line.startswith(('1.', '2.', '3.')):
                if current_question:
                    questions.append(current_question)
                current_question = {
                    "number": int(line[0]),
                    "question": line[2:].strip(),
                    "options": {}
                }
            elif line.strip().startswith(('a)', 'b)', 'c)')):
                option_letter = line[0]
                option_text = line[2:].strip()
                current_question["options"][option_letter] = option_text
                
        if current_question:
            questions.append(current_question)
            
        if len(questions) == 3:
            logger.info("Detected quiz prompt")
            return "quiz_prompt", {
                "quiz_id": "",  # Empty for now
                "questions": questions
            }
            
    logger.info("Checking for quiz result pattern...")
    lines = [line.strip() for line in response.split('\n') if line.strip()]
    score_line = None
    for line in lines:
        if "You answered" in line and "/3 questions correctly!" in line:
            score_line = line
            break
    
    if score_line:
        logger.info(f"Found score line: {score_line}")
        try:
            score_text = score_line.split("You answered")[1].split("/3")[0].strip()
            score = int(score_text)
            logger.info(f"Extracted score: {score}")
            
            user_answers = []
            correct_answers = []
            
            for line in lines:
                if any(line.startswith(f"{i}.") for i in range(1, 4)) and ("Correct -" in line or "Incorrect -" in line):
                    is_correct = "Correct -" in line
                    logger.info(f"Found {'correct' if is_correct else 'incorrect'} answer line: {line}")
                    
                    if "You answered" in line and "and the answer was" in line:
                        user_answer = line.split("You answered")[1].split("and the answer was")[0].strip()
                        correct_answer = line.split("and the answer was")[1].split("-")[0].strip()
                        
                        logger.info(f"Extracted user answer: {user_answer}")
                        logger.info(f"Extracted correct answer: {correct_answer}")
                        
                        user_answers.append(user_answer)
                        correct_answers.append(correct_answer)
            
            logger.info(f"Found {len(user_answers)} answers, {len(correct_answers)} correct")
            
            if len(user_answers) == 3:
                logger.info("Detected complete quiz result")
                return "quiz_result", {
                    "quiz_id": "",  # Empty for now
                    "user_answers": user_answers,
                    "correct_answers": correct_answers,
                    "score": score
                }
            else:
                logger.warning(f"Expected 3 answers but found {len(user_answers)}")
                
        except Exception as e:
            logger.error(f"Error processing quiz result: {str(e)}")
            return "content", None
            
    elif "There was an issue processing your answers" in response:
        logger.info("Detected invalid quiz answer format")
        return "content", None
        
    logger.info("No quiz pattern detected, returning content type")
    return "content", None

# Create FastAPI app with configuration
app = FastAPI(**API_CONFIG)

# Initialize services
dify_service = DifyService()

# CORS configuration
# For production, update the ALLOWED_ORIGINS environment variable to your production frontend URL(s)
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8501").split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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
    logger.info(f"Received signup request for username: {user.username}")
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
        logger.info(f"User created successfully: {user.username}")
        return {"message": "User created successfully"}
    except UserExistsError as e:
        logger.info(f"User already exists: {str(e)}")
        return JSONResponse(
            status_code=409,
            content={"message": str(e)}
        )
    except Exception as e:
        logger.error(f"Error in create_user: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Error creating account: {str(e)}"}
        )

@app.post("/user/profile1")
async def update_profile_part1(
    profile: models.ProfilePart1,
    current_user: dict = Depends(get_current_user)
):
    logger.info(f"Received profile update request for user: {current_user['username']}")
    logger.info(f"Profile data received: {profile.dict()}")
    try:
        result = database.update_profile_part1(current_user["username"], profile.dict())
        if not result:
            logger.error("Failed to update profile in database")
            raise HTTPException(
                status_code=500, 
                detail="Failed to update profile. Please check server logs for details."
            )
        logger.info("Profile updated successfully")
        return {"message": "Profile updated successfully"}
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
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
        logger.info("=== Starting Chat Request ===")
        logger.info(f"Current user: {current_user}")
        logger.info(f"Chat request: {chat_request}")
        logger.info(f"Conversation ID from request: {chat_request.conversation_id}")
        
        profile_data = {
            "profile1": current_user.get("profile1", {}),
            "profile2": current_user.get("profile2", {})
        }
        logger.info(f"Profile data: {json.dumps(profile_data, indent=2)}")

        async def event_generator():
            try:
                logger.info("=== Starting Event Generator ===")
                chat_data = {
                    'message_id': None,
                    'conversation_id': None,
                    'response': None,
                    'dify_metadata': {},
                    'usage_metrics': None,
                    'is_complete': False,
                    'has_saved': False,
                    'interaction_type': 'content',
                    'quiz_data': None
                }
                
                logger.info(f"Initial chat_data: {json.dumps(chat_data, indent=2)}")
                
                try:
                    logger.info("Calling Dify service process_message...")
                    for event in dify_service.process_message(
                        username=current_user["username"],
                        message=chat_request.message,
                        profile_data=profile_data,
                        conversation_id=chat_request.conversation_id
                    ):
                        try:
                            logger.info(f"New Event Received: {json.dumps(event, indent=2)}")
                            logger.info(f"Event type: {event.get('event')}")
                            
                            if event.get('event') == 'agent_message':
                                logger.info("Processing agent_message event...")
                                if event.get('data', {}).get('message_id'):
                                    chat_data['message_id'] = event.get('data', {}).get('message_id')
                                if event.get('data', {}).get('conversation_id'):
                                    chat_data['conversation_id'] = event.get('data', {}).get('conversation_id')
                                logger.info(f"Updated chat_data after agent_message: {json.dumps(chat_data, indent=2)}")
                            
                            elif event.get('event') == 'agent_thought':
                                logger.info("Processing agent_thought event...")
                                response_text = event.get('data', {}).get('thought', '')
                                chat_data['response'] = response_text
                                
                                interaction_type, quiz_data = detect_quiz_interaction(response_text)
                                chat_data['interaction_type'] = interaction_type
                                if quiz_data:
                                    chat_data['quiz_data'] = quiz_data
                                
                                chat_data['dify_metadata'] = {
                                    "message_files": event.get('data', {}).get('message_files', []),
                                    "feedback": event.get('data', {}).get('feedback', None),
                                    "retriever_resources": event.get('data', {}).get('retriever_resources', []),
                                    "agent_thoughts": event.get('data', {}).get('agent_thoughts', []),
                                    "quiz_data": quiz_data
                                }
                                logger.info(f"Updated chat_data after agent_thought: {json.dumps(chat_data, indent=2)}")
                            
                            elif event.get('event') == 'message_end' and not chat_data['has_saved']:
                                logger.info("Processing first message_end event...")
                                chat_data['usage_metrics'] = event.get('data', {}).get('metadata', {}).get('usage', {})
                                chat_data['is_complete'] = True
                                
                                logger.info("Chat Data State Before Save:")
                                logger.info(f"message_id: {chat_data['message_id']}")
                                logger.info(f"conversation_id: {chat_data['conversation_id']}")
                                logger.info(f"response length: {len(chat_data['response']) if chat_data['response'] else 0}")
                                logger.info(f"dify_metadata: {json.dumps(chat_data['dify_metadata'], indent=2)}")
                                logger.info(f"usage_metrics: {json.dumps(chat_data['usage_metrics'], indent=2)}")
                                
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
                                            interaction_type=chat_data['interaction_type'],
                                            quiz_data=chat_data.get('quiz_data'),
                                            dify_metadata=chat_data['dify_metadata'],
                                            usage_metrics=chat_data['usage_metrics']
                                        )
                                        if success:
                                            chat_data['has_saved'] = True
                                            logger.info("Successfully saved chat message")
                                            response_data = {
                                                'conversation_id': chat_data['conversation_id'], 
                                                'response': chat_data['response'],
                                                'interaction_type': chat_data['interaction_type'],
                                                'quiz_data': chat_data.get('quiz_data')
                                            }
                                            yield f"data: {json.dumps(response_data)}\n\n"
                                            yield "data: [DONE]\n\n"
                                        else:
                                            logger.error("Failed to save chat message")
                                    except Exception as e:
                                        logger.error(f"Error saving chat message: {str(e)}")
                                else:
                                    logger.error("Save conditions not met, skipping save")
                                    logger.error(f"Missing required fields: message_id present: {bool(chat_data['message_id'])}, conversation_id present: {bool(chat_data['conversation_id'])}, response present: {bool(chat_data['response'])}")
                            
                            elif event.get('event') == 'message_end' and chat_data['has_saved']:
                                logger.info("Skipping second message_end event (already saved)")
                                continue
                            
                            elif event.get('event') == 'error':
                                logger.error(f"Error event received: {event.get('error')}")
                                return
                                
                        except Exception as e:
                            logger.error(f"Error processing event: {str(e)}")
                            continue
                            
                except Exception as e:
                    logger.error(f"Error in Dify service process_message: {str(e)}")
                    return
                
            except Exception as e:
                logger.error(f"Error in event_generator: {str(e)}")
                return

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/api/chat/history")
async def get_chat_history(
    conversation_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get chat history for the current user.
       If conversation_id is not provided, group messages by conversation.
    """
    try:
        messages = database.get_chat_history(
            username=current_user["username"],
            conversation_id=conversation_id
        )
        # If a specific conversation_id is requested, return messages as is.
        if conversation_id:
            return {"messages": messages}

        # Otherwise, group messages by conversation_id.
        conversations = {}
        for msg in messages:
            conv_id = msg.get("conversation_id")
            if conv_id not in conversations:
                conversations[conv_id] = {
                    "conversation_id": conv_id,
                    # Initialize last_timestamp with the message timestamp
                    "last_timestamp": msg.get("timestamp"),
                    "messages": []
                }
            # Update last_timestamp if the current message is newer.
            if msg.get("timestamp") > conversations[conv_id]["last_timestamp"]:
                conversations[conv_id]["last_timestamp"] = msg.get("timestamp")
            conversations[conv_id]["messages"].append(msg)
        
        # Convert the grouped conversations to a sorted list,
        # sorted by last_timestamp in descending order.
        sorted_conversations = sorted(
            conversations.values(), 
            key=lambda x: x["last_timestamp"], 
            reverse=True
        )
        return {"conversations": sorted_conversations}
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
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
        profile_data = {
            "profile1": user.get("profile1", {}),
            "profile2": user.get("profile2", {})
        }
        logger.info(f"User data from database: {user}")
        logger.info(f"Returning profile data: {profile_data}")
        return profile_data
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/token/verify")
async def verify_token(request: Request):
    """Verify JWT token and return user data"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={"detail": "No authorization header"}
            )
        token = auth_header.split(' ', 1)[1] if ' ' in auth_header else auth_header
        current_user = await get_current_user(token)
        return {"username": current_user["username"]}
    except Exception as e:
        logger.error(f"Backend: Error verifying token - {str(e)}")
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid token"}
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)