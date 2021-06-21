from fastapi.routing import APIRouter
from passlib.hash import bcrypt
from model.notificacao_model import UpdateNotifi
from model.user_model import User, User_Pydantic, UserIn_Pydantic
from fastapi.security.oauth2 import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import HTTPException, status, Depends, UploadFile, File, Form
from datetime import datetime, timedelta
import files_manager as fm
import shutil
import yaml
import jwt
import os


JWT_SECRET = os.urandom(24).hex()
ACCESS_TOKEN_EXPIRE_MINUTES = 20


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

# ------------------------------------------------------AUTH
authentication_router = APIRouter(
    tags=["auth"]
)

async def check_user_existence(username: str) -> bool:
    user = await User.get(username=username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail='Username already taken'
        )
    return False

async def authenticate_user(username: str, password: str) -> User_Pydantic:
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
    """
    Route to generate token given a valid user.

    Args:
        form_data (OAuth2PasswordRequestForm, optional): Form including username and password.

    Raises:
        HTTPException: User not exists.

    Returns:
        dict: Containing access information and token.
    """
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
    """
    Route to create a new user

    Args:
        user (UserIn_Pydantic): Username and password to be registered.

    Returns:
        User_Pydantic: User saved. 
    """
    user_obj = User(username=user.username, password_hash=bcrypt.hash(user.password_hash))
    await user_obj.save()
    return await User_Pydantic.from_tortoise_orm(user_obj)

@authentication_router.get('/users/me', response_model=User_Pydantic)
async def get_user(user: User_Pydantic = Depends(get_current_user)):
    """
    Route to get user information.

    Args:
        user (User_Pydantic, optional): Username and password to be registered.

    Returns:
        User_Pydantic: User queried. 
    """
    return user

# ------------------------------------------------------NOTIFICATION
notification_router = APIRouter(
    tags=["notification"]
)


@notification_router.get("/current_notif")
def get_notif(user: User_Pydantic = Depends(get_current_user)):
    """
    Send the current notification message and method adopted by the
    ConEg system.

    Returns:
        (dict): Current method and message stored.
    """
    try:
        with open(f'./shr-data/config_notificacao.yaml', 'r') as f:
            data = yaml.load(f)
    except FileNotFoundError as e:
        with open(f'./shr-data/config_notificacao.yaml', 'w') as f:
            data = {
                "method": "Ainda não definido.",
                "message": "Ainda não definido."
            }
            yaml.dump(data, f)

    return {
        "method": data['method'],
        "message": data['message']
      }


@notification_router.post("/update_notif")
def register_notif(
    item: UpdateNotifi,
    user: User_Pydantic = Depends(get_current_user)
    ):
    """
    Receive new notification configuration.

    Args:
        item (UpdateNotifi): Model of request containing method and message
        to be used on notification.

    Returns:
        (dict): Current method and message stored.
    """
    item_dict = item.dict()
    with open(f'./shr-data/config_notificacao.yaml', 'w', encoding='utf-8') as f:
        data = {
            "method": item_dict['method'],
            "message": item_dict['message']
        }
        yaml.dump(data, f)

    return {
        "method": data['method'],
        "message": data['message']
    }


# ------------------------------------------------------REGISTRATION
register_router = APIRouter(
    tags=["registration"]
)

@register_router.post("/upload")
def upload_file(
    user: User_Pydantic = Depends(get_current_user),
    file_rec: UploadFile = File(...)
):
    """
    Route to manage full zip file.

    Args:
        file_rec (UploadFile): Zip file to register on DB.

    Raises:
        HTTPException: Any mismatch on zip pattern or failure to
        insert on Postgres.
    Returns:
        (dict): Response with name of the zip file.
    """
    with open('./dataset.zip', 'wb') as buffer:
        shutil.copyfileobj(file_rec.file, buffer)
    try:
        fm.insert_full_zip()
        return {"success_zipname": file_rec.filename}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=error)
    finally:
        os.remove('./dataset.zip')


@register_router.post("/upload_single")
def upload_single(
    user: User_Pydantic = Depends(get_current_user),
    nome: str = Form(...),
    email: str = Form(...),
    telefone: str = Form(...),
    file_rec: UploadFile = File(...)
):
    """
    Route to manage a single record.

    Args:
        nome (str): name of record.
        email (str): email of record.
        tel (str): phone of record.
        file_rec (UploadFile): image file of the given ID.

    Raises:
        HTTPException: Any mismatch on file pattern or failure to
        insert on Postgres.

    Returns:
        (dict): Response with ID of register.
    """
    name_from_id = file_rec.filename.split('.')[0]
    with open(f'./{name_from_id}.jpg', 'wb') as buffer:
        shutil.copyfileobj(file_rec.file, buffer)
    try:
        fm.insert_one(
            ident=name_from_id,
            nome=nome,
            email=email,
            tel=telefone
        )
        return {"success_insert_id": str(name_from_id)}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=error)