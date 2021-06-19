from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends, status
from tortoise.contrib.fastapi import register_tortoise
from db_transactions import PsqlPy
from pydantic import BaseModel
from user_model import User, User_Pydantic, UserIn_Pydantic
from fastapi.middleware.cors import CORSMiddleware
import files_manager as fm
import yaml
from auth_route import get_current_user, authentication_router
import shutil
import sys
import uvicorn
import os


# Consts
JWT_SECRET = os.urandom(24).hex()
ACCESS_TOKEN_EXPIRE_MINUTES = 10
# ORIGINS = [
#     "http://localhost",
#     "http://localhost:8080",
# ]


# Instantiate app and routes
app = FastAPI()
app.include_router(authentication_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register DB
register_tortoise(
    app,
    db_url='postgres://coneg_user:conegpass@db:5432/coneg_user?schema=coneg',
    #db_url='postgres://coneg_user:conegpass@localhost:5435/coneg_user?schema=coneg',
    modules={'models': ['user_model']},
    add_exception_handlers=True
)

class UpdateNotifi(BaseModel):
    """
    Model to exchange info about the method and the message.
    It is used to receive the packet to update the current
    configuration.
    """
    method: str
    message: str


@app.post("/upload")
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


@app.post("/upload_single")
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


@app.get("/inpector_list")
def cams_list(user: User_Pydantic = Depends(get_current_user)):
    """
    List all cameras/inspectors activelly sending logs.

    Returns:
        (dict): Names of each inspector.
    """
    db = PsqlPy()
    res = db.select_query(select='local', distinct=True, table='fato_faces')
    db.disconnect()
    return {'cams': res}


@app.get("/current_notif")
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


@app.post("/update_notif")
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


if __name__ == "__main__":
    uvicorn.run(app, port=5000, host='0.0.0.0')