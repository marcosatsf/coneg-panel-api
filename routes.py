from typing import Dict
from timeseries import TimeSeriesLSTM
from threading import Thread, Lock
from fastapi.routing import APIRouter
from passlib.hash import bcrypt
from model.notificacao_model import UpdateNotifi
from model.location_model import UpdateLocation
from model.user_model import User, User_Pydantic, UserIn_Pydantic
from fastapi.security.oauth2 import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import HTTPException, status, Depends, UploadFile, File, Form
from datetime import datetime, timedelta
import files_manager as fm
import dash_process as dp
from db_transactions import PsqlPy
import base64
from glob import glob
import shutil
import yaml
import jwt
import os


JWT_SECRET = os.urandom(24).hex()
ACCESS_TOKEN_EXPIRE_MINUTES = 60


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

lock_server = Lock()


# ------------------------------------------------------AUTH
authentication_router = APIRouter(
    tags=["auth"]
)


# async def check_user_existence(username: str) -> bool:
#     user = await User.get(username=username)
#     if user.verify_password():
#         raise HTTPException(
#             status_code=status.HTTP_406_NOT_ACCEPTABLE,
#             detail='Username already taken'
#         )
#     return False


async def authenticate_user(username: str, password: str) -> User_Pydantic:
    user = await User.get(username=username)
    if not user or not user.verify_password(password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid username or password'
        )
    return user


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
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
    #access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # access_token = create_access_token(
    #     data={"sub": user_obj.dict()}#, expires_delta=access_token_expires
    # )
    #token = jwt.encode(user_obj.dict(),JWT_SECRET)
    return {'access_token': create_access_token(
        data={"sub": user_obj.dict()}), 'token_type':'bearer'}


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


@notification_router.get("/get_ranking")
def get_ranking(user: User_Pydantic = Depends(get_current_user)):
    """
    Get ranking of people by the 5 most notified ones.

    Returns:
        (dict): Current method and message stored.
    """
    return dp.build_ranking()


@notification_router.get("/get_hist_notif")
async def get_hist_notif(
    pesid: int = 0,
    offset: int = 0,
    user: User_Pydantic = Depends(get_current_user)
    ):
    """
    Get historical cases for that given ID.

    Args:
        pesid (int): ID of person.
        offset (int): Offset to search in DB.

    Returns:
        (dict): Current method and message stored.
    """
    db = PsqlPy()
    query_res = db.select_query(
        query_path='hist_notif_query.sql',
        tuple_params=(pesid, offset, )
        )
    res = []

    for row in query_res:
        tmp = {}
        tmp['pesid'] = row[0]
        tmp['name'] = row[1]
        tmp['ts'] = row[2]
        tmp['local'] = row[3]

        timestamp_fmt = int(datetime.fromisoformat(str(row[2])).timestamp())-10800
        #print(timestamp_fmt)
        path_frame = f'.{os.sep}shr-data{os.sep}registry{os.sep}*.jpg'

        file_path_list = [e.split('/')[-1] for e in glob(path_frame)]

        tmp['notified'] = 0
        tmp['image'] = ''

        for file_path in file_path_list:
            #print(file_path, f'{timestamp_fmt}.jpg', str(row[0]))
            if (f'{timestamp_fmt}.jpg' in file_path) and (str(row[0]) in file_path):
                name_splitted = file_path.split('_')
                # 1 to notified, 0 to not notified
                tmp['notified'] = int(name_splitted[0])
                file_rec = File(...)
                with open(f'.{os.sep}shr-data{os.sep}registry{os.sep}{file_path}', 'rb') as buffer:
                    tmp['image'] = base64.b64encode(buffer.read())
                    # shutil.copyfileobj(buffer, file_rec.file)
                # tmp['image'] = file_rec

        res.append(tmp)

    db.disconnect()
    return res


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
    identificacao: int = Form(...),
    nome: str = Form(...),
    email: str = Form(...),
    telefone: str = Form(...),
    file_rec: UploadFile = File(...)
):
    """
    Route to manage a single record.

    Args:
        identificacao (int): Id of record.
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
    with open(f'./{identificacao}.jpg', 'wb') as buffer:
        shutil.copyfileobj(file_rec.file, buffer)
    try:
        fm.insert_one(
            ident=identificacao,
            nome=nome,
            email=email,
            tel=telefone
        )
        return {"success_insert_id": str(identificacao)}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=error)


@register_router.get("/get_lista_user")
async def get_registry_from_coneg(
    pesid: int = None,
    offset: int = 0,
    user: User_Pydantic = Depends(get_current_user)
    ):
    """
    Get List of registered user.

    Args:
        pesid (int): ID of person.
        offset (int): Offset to search in DB.

    Returns:
        (dict): Current method and message stored.
    """
    db = PsqlPy()
    if pesid:
        try:
            resp = db.select_query(
                query_path='verify_user.sql',
                tuple_params=(pesid, ),
                unique=True
                )[0]
            data = {'alreadyHasId': True}
        except IndexError as e:
            data = {'alreadyHasId': False}
    else:
        data = {'users': [{'pesid':row[0], 'name':row[1], 'email':row[2], 'tel':row[3]} for row in db.select_query(query_path='list_user_query.sql',tuple_params=(offset, ))]}
    db.disconnect()
    return data

# ------------------------------------------------------DASHBOARD
dashboard_router = APIRouter(
    tags=["dashboard"]
)


@dashboard_router.get("/route_info")
def packet_info(
    where_which: str,
    user: User_Pydantic = Depends(get_current_user),
):
    """
    Execute a complete query with all requested charts from an
    especific location.

    Args:
        where_which (str): String containing the cam location (1st),
        followed by each needed chart request, separated by '.'

    Returns:
        (dict): Each key is a requested chart and their respective
        values are the response from each of them.
    """
    return dp.build_info(where_which, lock_server)


@dashboard_router.get("/route_all_info")
def abstract_info(
    user: User_Pydantic = Depends(get_current_user),
):
    """
    Used by the main page of dashboard, which holds a resumed
    information about every cam location.

    Returns:
        (dict): Each key is a cam location and have as they value
        a list with today's statistics about 3 status.
    """
    return dp.build_info_all()

# ------------------------------------------------------ACCOUNT CONFIG
config_router = APIRouter(
    tags=["configuration"]
)


@config_router.get("/current_location")
def get_system_location(user: User_Pydantic = Depends(get_current_user)):
    """
    Send the current location used by ConEg system.

    Returns:
        (dict): Current city and state/province stored.
    """
    try:
        with open(f'./shr-data/config_location.yaml', 'r') as f:
            data = yaml.load(f)

    except FileNotFoundError as e:
        with open(f'./shr-data/config_location.yaml', 'w') as f:
            data = {
                "city": "Ainda não definida",
                "state": "NA"
            }
            yaml.dump(data, f)

    return {
        "city": data['city'],
        "state": data['state']
      }


def create_timeseriesLSTM():
    # context manager to acquire and release lock
    print('routes_out_locker')
    with lock_server:
        print('routes_in_locker')
        TimeSeriesLSTM(f_model_creation=True)


@config_router.post("/update_location")
def register_system_location(
    item: UpdateLocation,
    user: User_Pydantic = Depends(get_current_user)
    ):
    """
    Update the current location used by ConEg system.

    Args:
        item (UpdateLocation): Request model containing city and state
        to be used on system prediction.

    Returns:
        (dict): Current city and state stored.
    """
    item_dict = item.dict()
    with open(f'./shr-data/config_location.yaml', 'w', encoding='utf-8') as f:
        data = {
            "city": item_dict['city'],
            "state": item_dict['state']
        }
        yaml.dump(data, f)

    exe = Thread(target=create_timeseriesLSTM)
    exe.start()

    return {
        "city": data['city'],
        "state": data['state']
    }


@config_router.post("/change_pw")
async def register_new_pw(
    current_pw: str = Form(...),
    new_pw: str = Form(...),
    user: User_Pydantic = Depends(get_current_user)
    ):
    """
    Update password.

    Args:
        current_pw (str): current password for current user.
        new_pw (str): new password for current user.

    Returns:
        (dict): Current and new one password to be stored.
    """
    #user = authenticate_user(user.dict()['username'], current_pw)
    user_obj = await User.get(username=user.username)
    if not user_obj.verify_password(current_pw):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Invalid current password'
        )
    user_obj.password_hash = bcrypt.hash(new_pw)
    await user_obj.save(update_fields=['password_hash'])
    user_pydantic = await User_Pydantic.from_tortoise_orm(user_obj)
    return {
        'access_token': create_access_token(data={"sub": user_pydantic.dict()}), 
        'token_type':'bearer'
    }


def create_module(module: str, name: str, size:int=1) -> Dict:
    item = {}
    item['module'] = module
    item['size'] = size
    item['name'] = name
    return item


@config_router.get("/available_infos")
def get_available_infos(user: User_Pydantic = Depends(get_current_user)):
    """
    List all available infos (charts and metrics) from this ConEg system.

    Returns:
        (dict): Current available infos.
    """
    # Retrieve all available locals
    db = PsqlPy()
    res = db.select_query_distinct(select='local', table='fato_faces')
    db.disconnect()

    # Building response packet
    data = {'features':[]}
    available_options = [
        'weeklydata',
        'dailydata',
        'usagedata',
        'infodata',
    ]
    available_options_human_readable = [
        'Dados semanais',
        'Dados diários',
        'Dados gerais',
        'Métricas',
    ]
    # Convolute locals with options
    for local in res:
        for idx, option in enumerate(available_options):
            data['features'].append(create_module(
                module=f'{local}.{option}',
                name=f'{available_options_human_readable[idx]} de {local}'
            ))

    # Prediction feature
    date_now = datetime.now().strftime("%d/%m/%Y")
    data['features'].append(create_module(
                module=f'{date_now}.timeseries',
                name=f'Predição de casos para a semana',
                size=2
            ))

    # All feature
    data['features'].append(create_module(
                module=f'{date_now}.allinfodata',
                name=f'Dados de hoje',
                size=2
            ))

    return data


@config_router.get("/current_user_setup")
def get_current_user_setup(user: User_Pydantic = Depends(get_current_user)):
    """
    Get the current user setup used by ConEg system.

    Returns:
        (dict): Current user setup stored.
    """
    try:
        with open(f'./shr-data/config_user_setup.yaml', 'r') as f:
            data = yaml.load(f)

    except FileNotFoundError as e:
        with open(f'./shr-data/config_user_setup.yaml', 'w') as f:
            data = {
                '0,0': {'module': '-', 'name': 'Vazio', 'size': 1},
                '0,1': {'module': '-', 'name': 'Vazio', 'size': 1},
                '1,0': {'module': '-', 'name': 'Vazio', 'size': 1},
                '1,1': {'module': '-', 'name': 'Vazio', 'size': 1},
            }
            yaml.dump(data, f)

    return data


@config_router.post("/update_user_setup")
def get_current_user_setup(
    set_user_setup: Dict[str, Dict],
    user: User_Pydantic = Depends(get_current_user)
    ):
    """
    Send the configuration user setup made by admin.

    Args:
        set_user_setup (dict): Configuration made by user.

    Returns:
        (dict): Current user setup stored.
    """
    with open(f'./shr-data/config_user_setup.yaml', 'w') as f:
        yaml.dump(set_user_setup, f)

    return set_user_setup

# ------------------------------------------------------USER CONFIG
user_router = APIRouter(
    tags=["user_panel"]
)
@user_router.get("/setup_user")
def get_current_user_setup():
    """
    Get the current user setup used by ConEg system. (No Authentication)

    Returns:
        (dict): Current user setup stored.
    """
    try:
        with open(f'./shr-data/config_user_setup.yaml', 'r') as f:
            data = yaml.load(f)

    except FileNotFoundError as e:
        with open(f'./shr-data/config_user_setup.yaml', 'w') as f:
            data = {
                '0,0': {'module': '-', 'name': 'Vazio', 'size': 1},
                '0,1': {'module': '-', 'name': 'Vazio', 'size': 1},
                '1,0': {'module': '-', 'name': 'Vazio', 'size': 1},
                '1,1': {'module': '-', 'name': 'Vazio', 'size': 1},
            }
            yaml.dump(data, f)
    return data


@user_router.get("/data_to_user")
def get_data_to_user(
    batch: str,
):
    """
    Execute a complete query with all requested charts.

    Args:
        where_which (dict): Request from a batch of modules.

    Returns:
        (dict): Each key is a requested chart and their respective
        values are the response from each of them.
    """
    modules_listed = batch.split(':')

    coords_list = [
        '0,0',
        '0,1',
        '1,0',
        '1,1'
    ]

    data_res = {}
    for idx, module in enumerate(modules_listed):
        if module != 'Vazio':
            data_res[coords_list[idx]] = dp.build_info(module, lock_server)
    print(data_res)

    return data_res