import psycopg2

class PsqlPy:
    def connect(self):
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
            print('Connected DB!')
        except Exception as e:
            print('Cannot connect to DB!')

    def insert_reg(self, **row):
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
        if not self.delete_row:
            with open('sql/delete_row.sql','r') as f:
                self.delete_row = f.read()

        try:
            data = (id, )
            self.cur.execute(self.delete_row, data)
        except Exception:
            print(f"Cannot delete id={id}!")
            raise Exception

    def disconnect(self):
        if self.cur is not None:
            self.cur.close()
        if self.conn is not None:
            self.conn.close()
            print('Disconnected DB!')