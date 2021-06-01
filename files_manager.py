from pandas.core.frame import DataFrame
from db_transactions import PsqlPy
from zipfile import ZipFile
import pandas as pd

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
    df_id_aux = []

    # Iterate through files to verify integrity
    for obj in zip_file.infolist():
        if obj.filename.endswith('.csv'):
            continue
        elif '/' in obj.filename:
            file_name = obj.filename.split('/')
            if file_name[0] in df_id:
                if not file_name[1].split('.')[1] in ['jpg','jpeg','png']:
                    if obj.file_size < 1:
                        raise Exception(f"Image file is empty: {obj.filename}")
                    else:
                        raise Exception(f"There's no image file inside folder: {file_name[0]}")
                else:
                    if file_name[0] not in df_id_aux:
                        df_id_aux.append(file_name[0])
            else:
                raise Exception(f"There's no ID related to folder: {file_name[0]}")
        else:
            raise Exception("There's no csv or image folders!")

    # If there's more IDs on csv than image folders
    df_id.sort()
    df_id_aux.sort()
    if df_id != df_id_aux:
        raise Exception("There's not enough image folders")
    return df



def insert_full_zip() -> None:
    """
    Inserts full zip into DB
    """
    with ZipFile('./dataset.zip', 'r') as zip_file:
        print(zip_file.filename)
        df = validator_zip(zip_file)
        for obj in zip_file.infolist():
            if '/' in obj.filename:
                zip_file.extract(obj, path='shr-data')

    db = PsqlPy()
    db.connect()
    for _, row in df.iterrows():
        db.insert_reg(
            id=row['identificacao'],
            nome=row['nome'],
            email=row['email'],
            telefone=row['telefone']
        )
    db.disconnect()
