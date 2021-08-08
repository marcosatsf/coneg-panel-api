from timeseries import TimeSeriesLSTM
from typing import List, Dict
from db_transactions import PsqlPy
from threading import Lock, Thread


def build_info(where_which: str) -> Dict:
    """
    Build information requested by ConEg Panel

    Args:
        where_which (str): String which informs which type of data
        that panel requests and from which camera

    Returns:
        data (dict): Data for each requested type given a camera
        location
    """
    tmp = where_which.split('.')
    where = tmp[0]
    which = tmp[1:]
    data = {}
    db = PsqlPy()
    for element in which:
        if element == 'weeklydata':
            # Receive data
            data_ret = db.select_query(query_path='weekly_data_query.sql', local=where)
            # Transform it
            data_temp = {}
            for e in data_ret:
                if data_temp.get(e[0]):
                    data_temp[e[0]].append([e[1],e[2]])
                else:
                    data_temp[e[0]] = [[e[1],e[2]]]
            # Link to element
            data[element] = data_temp
        elif element == 'dailydata':
             # Receive data
            data_ret = db.select_query(query_path='daily_data_query.sql', local=where)
            # Transform it
            data_temp = {}
            for e in data_ret:
                if data_temp.get(e[0]):
                    data_temp[e[0]].append([e[1],e[2]])
                else:
                    data_temp[e[0]] = [[e[1],e[2]]]
            # Link to element
            data[element] = data_temp
        elif element == 'usagedata':
            data[element] = db.select_query(query_path='usage_data_query.sql', local=where, unique=True)
        elif element == 'infodata':
            # max and min not using mask. Given a day
            data[element] = db.select_query(query_path='info_data_query.sql', local=where)
        elif element == 'timeseries':
            # exe = Thread(target=self.send2api, args=(frame_in_bytes, count_no_mask, count_mask,))
            # exe.start()
            data[element] = TimeSeriesLSTM().get_prediction()
    db.disconnect()
    return data


def build_info_all() -> Dict:
    db = PsqlPy()
    res_tmp = db.select_query(query_path='abstract_query.sql')
    res = {}
    for elem in res_tmp:
        if res.get(elem[0]):
            res[elem[0]].append(elem[1])
        else:
            res[elem[0]] = [elem[1]]
    db.disconnect()
    return res