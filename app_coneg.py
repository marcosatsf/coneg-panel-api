from fastapi import FastAPI, UploadFile, File
from fastapi.param_functions import Depends
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from fastapi_login import LoginManager
from fastapi_login.exceptions import InvalidCredentialsException
from fastapi.middleware.cors import CORSMiddleware
from db_transactions import PsqlPy
import pandas as pd
import shutil
import uvicorn
import zipfile
import os

SECRET = os.urandom(24).hex()

app = FastAPI()

manager = LoginManager(SECRET, token_url='/auth/token')
fake_db = {'marquin@gmail.com':{'password':'pass_test'}}

origins = [
    "http://localhost",
    "http://localhost:8083",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    db = PsqlPy()
    db.connect()
    dfCad = pd.read_csv('files/cadastros.csv')
    for _, row in dfCad.iterrows():
        db.insert_reg(
            id=row['identificacao'],
            nome=row['nome'],
            email=row['email'],
            telefone=row['telefone']
        )
    db.disconnect()
    return {"message": "Hello World!"}

@app.post("/upload")
def upload_file(
    file_rec: UploadFile = File(...)
):
    with open('files/data.zip', 'wb') as buffer:
        shutil.copyfileobj(file_rec.file, buffer)
    return {
        "filename": file_rec.filename
    }

# -------------------Login login---------------------
@manager.user_loader
def load_user(email: str):
    user = fake_db.get(email)
    return user

@app.post('/auth/token')
def login(data: OAuth2PasswordRequestForm = Depends()):
    email = data.username
    password = data.password

    user = load_user(email)
    if not user or password != user['password']:
        raise InvalidCredentialsException
    
    access_token = manager.create_access_token(data=dict(sub=email))
    return {'access_token': access_token, 'token_type':'bearer'}

if __name__ == "__main__":
    uvicorn.run(app, port=5000, host='0.0.0.0')
