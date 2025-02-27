from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from . import models, database

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
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
    access_token = database.create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=models.User)
async def create_user(user: models.UserCreate):
    if database.create_user(user.username, user.password):
        return {"id": user.username, "username": user.username, "is_active": True}
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Username already registered"
    )

@app.post("/profile/part1")
async def update_profile_part1(
    profile: models.ProfilePart1,
    current_user: dict = Depends(get_current_user)
):
    result = database.update_profile_part1(current_user["username"], profile.dict())
    if result:
        return {"status": "success", "message": "Profile part 1 updated"}
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Failed to update profile"
    )

@app.post("/profile/part2")
async def update_profile_part2(
    profile: models.ProfilePart2,
    current_user: dict = Depends(get_current_user)
):
    result = database.update_profile_part2(current_user["username"], profile.dict())
    if result:
        return {"status": "success", "message": "Profile part 2 updated"}
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Failed to update profile"
    )

@app.get("/profile/status")
async def get_profile_status(current_user: dict = Depends(get_current_user)):
    status = database.get_profile_status(current_user["username"])
    if status:
        return status
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Profile not found"
    ) 