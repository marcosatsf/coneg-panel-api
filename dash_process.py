from typing import List
from db_transactions import PsqlPy


def build_info(where: str, which: List[str]):
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
        elif element == 'usagedata':
            data[element] = db.select_query(query_path='usage_data_query.sql', local=where)
            pass
        elif element == 'infodata':
            pass
    db.disconnect()
    return data


def weeklydata_f():
    pass

def usagedata_f():
    pass

def infodata_f():
    pass