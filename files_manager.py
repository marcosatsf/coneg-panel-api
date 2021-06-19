from pandas.core.frame import DataFrame
from db_transactions import PsqlPy
from zipfile import ZipFile
import pandas as pd
import shutil
import glob
import os


def insert_full_zip() -> None:
    """
    Inserts full zip into DB
    """
    try:
        with ZipFile('./dataset.zip', 'r') as zip_file:
            print(f'Uploading full register named: {zip_file.filename}')
            df = validator_zip(zip_file)

            for obj in zip_file.infolist():
                if len(obj.filename.split('/')) == 2:
                    zip_file.extract(obj.filename, path='tmp/')
            # Remove old faces in case if there's old ones
            if os.path.exists('shr-data/faces/'):
                shutil.rmtree('shr-data/faces/')
            # Creates faces dir
            os.mkdir('shr-data/faces/')
            for files in glob.glob('tmp/*/*'):
                shutil.move(files, f"shr-data/faces/{files.split('/')[-1]}")
            shutil.rmtree('tmp/')

        db = PsqlPy()
        db.trunc_table()
        for _, row in df.iterrows():
            db.insert_reg(
                id=row['identificacao'],
                nome=row['nome'],
                email=row['email'],
                telefone=row['telefone']
            )
        db.disconnect()
    except Exception as e:
        raise e


def validator_zip(zip_file: ZipFile) -> pd.DataFrame:
    """
    Validates if zip is valid, it means, contains one and only one csv.
    Also validates if there's folders related to ID and if there's image
    files inside them.

    Args:
        zip_file (ZipFile): ZipFile cursor

    Raises:
        Exception: Any error not following pattern

    Returns:
        pd (DataFrame): DataFrame containing all user data
    """
    # Check if there's only one and only one csv
    csvs = [e for e in zip_file.infolist() if e.filename.endswith('.csv')]
    if len(csvs) != 1:
        raise Exception("There's no CSV file or have more than one!")

    # Load csv and gets a list of IDs
    with zip_file.open(csvs[0]) as f:
        df = pd.read_csv(f)
    df_id = [str(e) for e in df['identificacao']]

    # Iterate through files to verify integrity
    for obj in zip_file.infolist():
        if obj.filename.endswith('.csv'):
            continue
        elif len(obj.filename.split('/')) == 2:
            file_info = obj.filename.split('/')[1].split('.')
            if not file_info[1] in ['jpg','jpeg']:
                if obj.file_size < 1:
                    raise Exception(f"File is empty: {obj.filename}")
                else:
                    raise Exception(f"There's not only JPG/JPEG files inside folder, example: {obj.filename}")
            else:
                if file_info[0] in df_id:
                    df_id.remove(file_info[0])
                else:
                    raise Exception(f"There's a image not related to an ID or there's a duplicated file of ID: {file_info[0]}")
        else:
            raise Exception("There's no csv or image folder!")

    if len(df_id):
        raise Exception("There's not enough image on folder!")
    return df


def insert_one(ident: int, nome: str, email: str, tel: str) -> None:
    """
    Inserts one record into DB

    Args:
        ident (int): ID of record
        nome (str): name of record
        email (str): email of record
        tel (str): phone of record
    """
    print(f'Uploading single register')
    try:
        if os.path.exists(f"shr-data/faces/{ident}.jpg"):
            is_update = True
        else:
            is_update = False
            if not os.path.exists('shr-data/faces/'):
                os.mkdir('shr-data/faces/')

        shutil.move(f'./{ident}.jpg', f"shr-data/faces/{ident}.jpg")

        db = PsqlPy()
        if is_update:
            db.update_row(
                id=ident,
                nome=nome,
                email=email,
                telefone=tel
            )
        else:
            db.insert_reg(
                id=ident,
                nome=nome,
                email=email,
                telefone=tel
            )
        db.disconnect()
    except Exception as e:
        raise e