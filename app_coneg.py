from fastapi import FastAPI, Depends
from tortoise.contrib.fastapi import register_tortoise
from db_transactions import PsqlPy
from model.user_model import User_Pydantic
from fastapi.middleware.cors import CORSMiddleware
from routes import get_current_user, authentication_router, register_router, notification_router, dashboard_router, config_router, user_router
import uvicorn


# Consts
ORIGINS = [
    "http://localhost",
    "http://localhost:8080",
]


# Instantiate app and routes
app = FastAPI()
app.include_router(authentication_router)
app.include_router(dashboard_router)
app.include_router(register_router)
app.include_router(notification_router)
app.include_router(config_router)
app.include_router(user_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register DB
register_tortoise(
    app,
    db_url='postgres://coneg_user:conegpass@db:5432/coneg_user?schema=coneg',
    #db_url='postgres://coneg_user:conegpass@localhost:5435/coneg_user?schema=coneg',
    modules={'models': ['model.user_model']},
    add_exception_handlers=True
)


@app.get("/inpector_list")
def cams_list(user: User_Pydantic = Depends(get_current_user)):
    """
    List all cameras/inspectors activelly sending logs.

    Returns:
        (dict): Names of each inspector.
    """
    db = PsqlPy()
    res = db.select_query_distinct(select='local', table='fato_faces')
    db.disconnect()
    return {'cams': res}


if __name__ == "__main__":
    uvicorn.run(app, port=5000, host='0.0.0.0')