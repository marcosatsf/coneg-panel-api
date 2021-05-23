FROM python:3.8
WORKDIR /coneg_root
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN rm requirements.txt
COPY /sql ./sql/
COPY /files ./files/
COPY app_coneg.py db_transactions.py ./
CMD ["python", "app_coneg.py"]