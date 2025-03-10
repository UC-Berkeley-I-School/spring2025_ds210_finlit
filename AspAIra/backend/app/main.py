from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from . import models, database
from fastapi.responses import JSONResponse
from typing import Optional, List, Literal
import uvicorn
from .services.dify_service import DifyService
from .config import API_CONFIG

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
    request: models.ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """Process chat message and return response"""
    try:
        # Get user profile
        user = database.get_user(current_user["username"])
        profile_data = {
            "dependents_count": user.get("profile1", {}).get("number_of_dependents", ""),
            "bank_account": user.get("profile2", {}).get("bank_account", ""),
            "debt_status": user.get("profile2", {}).get("debt_information", ""),
            "remittance_status": user.get("profile2", {}).get("remittance_information", ""),
            "remittance_amount": user.get("profile2", {}).get("remittance_amount", "")
        }

        # Process message
        response = await dify_service.process_message(
            username=current_user["username"],
            message=request.message,
            profile_data=profile_data
        )

        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}"
        )

@app.get("/api/chat/history")
async def get_chat_history(
    current_user: dict = Depends(get_current_user)
):
    """Get user's chat history"""
    try:
        history = database.get_chat_history(current_user["username"])
        return {"history": history}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving chat history: {str(e)}"
        )

@app.get("/user/profile")
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """Get complete user profile data"""
    try:
        user = database.get_user(current_user["username"])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        # Return only the necessary profile data
        return {
            "profile1": user.get("profile1", {}),
            "profile2": user.get("profile2", {})
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving profile: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 