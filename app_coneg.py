from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.param_functions import Depends
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from fastapi_login import LoginManager
from fastapi_login.exceptions import InvalidCredentialsException
from fastapi.middleware.cors import CORSMiddleware
import files_manager as fm
import shutil
import uvicorn
import os
import io

SECRET = os.urandom(24).hex()

app = FastAPI()

# manager = LoginManager(SECRET, token_url='/auth/token')
# fake_db = {'marquin@gmail.com':{'password':'pass_test'}}

origins = [
    "http://localhost",
    "http://localhost:8080",
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
    return {"message": "Hello World!"}

@app.post("/upload")
def upload_file(
    file_rec: UploadFile = File(...)
):
    with open('./dataset.zip', 'wb') as buffer:
        shutil.copyfileobj(file_rec.file, buffer)
    try:
        fm.insert_full_zip()
        return {"success_zipname": file_rec.filename}
    except Exception as error:
        raise HTTPException(status_code=406, detail=error)
    finally:
        os.remove('./dataset.zip')


# -------------------Login login---------------------
# @manager.user_loader
# def load_user(email: str):
#     user = fake_db.get(email)
#     return user

# @app.post('/auth/token')
# def login(data: OAuth2PasswordRequestForm = Depends()):
#     email = data.username
#     password = data.password

#     user = load_user(email)
#     if not user or password != user['password']:
#         raise InvalidCredentialsException

#     access_token = manager.create_access_token(data=dict(sub=email))
#     return {'access_token': access_token, 'token_type':'bearer'}

if __name__ == "__main__":
    uvicorn.run(app, port=5000, host='0.0.0.0')
