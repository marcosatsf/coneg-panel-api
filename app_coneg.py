from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from db_transactions import PsqlPy
import pandas as pd
import shutil
import uvicorn
import zipfile
import os

app = FastAPI()

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
    

if __name__ == "__main__":
    uvicorn.run(app, port=5000, host='0.0.0.0')
