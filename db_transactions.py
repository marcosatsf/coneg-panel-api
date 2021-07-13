import psycopg2
from psycopg2 import sql

class PsqlPy:
    def __init__(self) -> None:
        """
        Initialize DB connection, retrieving the current cursor
        to it and set auto-commit ON.
        """
        try:
            self.conn = psycopg2.connect(
                host="db",
                port="5432",
                database="coneg_user",
                user="coneg_user",
                password="conegpass"
            )
            self.conn.set_session(autocommit=True)
            self.insert_row = ''
            self.delete_row = ''
            self.cur = self.conn.cursor()
            self.cur.execute("SET TIMEZONE='America/Sao_Paulo'")
            print('Connected DB!')
        except Exception as e:
            print('Cannot connect to DB!')


    def select_query_distinct(self, select: str, table: str):
        """
        Selects distinct value from a given table

        Args:
            select (str): value to be placed on distinct
            table (str): table from which query

        Raises:
            Exception: Cannot select distinct.

        Returns:
            List[str]: list of strings
        """
        with open('sql/select_distinct.sql','r') as f:
            query = f.read()
        try:
            self.cur.execute(sql.SQL(query).format(
                select=sql.Identifier(select),
                table=sql.Identifier(table)
                ))
            res = [row[0] for row in self.cur.fetchall()]
            return res
        except Exception:
            print("Cannot select distinct!")
            raise Exception


    def select_query(self, query_path: str, local: str = None, unique: bool = False):
        with open(f'sql/{query_path}', 'r') as f:
            query = f.read()

        try:
            if local:
                data = (local, )
                self.cur.execute(query, data)
            else:
                self.cur.execute(query)

            if unique:
                res = [row[0] for row in self.cur.fetchall()]
            else:
                res = [list(row) for row in self.cur.fetchall()]
            return res
        except Exception:
            print("Cannot select!")
            raise Exception


    def insert_reg(self, **row):
        """
        Insert row to registration table.

        Raises:
            Exception: Cannot insert register.
        """
        if not self.insert_row:
            with open('sql/insert_cad.sql','r') as f:
                self.insert_row = f.read()

        try:
            data = (row['id'], row['nome'], row['email'], row['telefone'], )
            self.cur.execute(self.insert_row, data)
        except Exception:
            print("Cannot insert!")
            raise Exception


    def delete_reg(self, id):
        """
        Delete a register on registration table, given an ID.

        Args:
            id (int): Identification (unique number).

        Raises:
            Exception: Cannot delete register.
        """
        if not self.delete_row:
            with open('sql/delete_row.sql','r') as f:
                self.delete_row = f.read()

        try:
            data = (id, )
            self.cur.execute(self.delete_row, data)
        except Exception:
            print(f"Cannot delete id={id}!")
            raise Exception


    def trunc_table(self):
        """
        Truncate registration table.

        Raises:
            Exception: Cannot truncate table.
        """
        with open('sql/trunc.sql','r') as f:
            query = f.read()

        try:
            self.cur.execute(query)
        except Exception:
            print(f"Cannot Truncate table!")
            raise Exception


    def update_row(self, **row):
        """
        Update row of registration table.

        Raises:
            Exception: Cannot update row.
        """
        with open('sql/update_row.sql','r') as f:
            query = f.read()

        try:
            data = (row['nome'], row['email'], row['telefone'], row['id'], )
            self.cur.execute(query, data)
        except Exception:
            print(f"Cannot update table on id [{row['id']}]!")
            raise Exception


    def disconnect(self):
        """
        Invalidate DB connection.
        """
        if self.cur is not None:
            self.cur.close()
        if self.conn is not None:
            self.conn.close()
            print('Disconnected DB!')