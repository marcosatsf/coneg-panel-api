
from db_transactions import PsqlPy

db = PsqlPy()
db.reset_notif()
db.disconnect()