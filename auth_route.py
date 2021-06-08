from typing import Optional
from fastapi.routing import APIRouter
from passlib.hash import bcrypt
from fastapi_login.exceptions import InvalidCredentialsException
from user_model import User, User_Pydantic, UserIn_Pydantic
from fastapi.security.oauth2 import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import HTTPException, status, Depends
from datetime import datetime, timedelta
import jwt
import os

JWT_SECRET = os.urandom(24).hex()
ACCESS_TOKEN_EXPIRE_MINUTES = 10

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

authentication_router = APIRouter(
    tags=["auth"]
)

async def authenticate_user(username: str, password: str):
    user = await User.get(username=username)
    if not user or not user.verify_password(password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid username or password'
        )
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm='HS256')
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms='HS256')
        print(payload)
        user = await User.get(id=payload['sub'].get('id'))
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid username or password'
        )
    return await User_Pydantic.from_tortoise_orm(user)

@authentication_router.post('/token')
async def generate_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid username or password'
        )
    user_obj = await User_Pydantic.from_tortoise_orm(user)
    print(user_obj.dict())
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_obj.dict()}, expires_delta=access_token_expires
    )
    #token = jwt.encode(user_obj.dict(),JWT_SECRET)
    return {'access_token': access_token, 'token_type':'bearer'}

@authentication_router.post('/users', response_model=User_Pydantic)
async def create_user(user: UserIn_Pydantic):
    user_obj = User(username=user.username, password_hash=bcrypt.hash(user.password_hash))
    await user_obj.save()
    return await User_Pydantic.from_tortoise_orm(user_obj)

@authentication_router.get('/users/me', response_model=User_Pydantic)
async def get_user(data: int, user: User_Pydantic = Depends(get_current_user)):
    print(data)
    return user