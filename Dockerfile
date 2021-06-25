FROM python:3.8
WORKDIR /coneg_root
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN rm requirements.txt
COPY /sql ./sql/
COPY /model ./model/
COPY app_coneg.py db_transactions.py files_manager.py dash_process.py routes.py ./
CMD ["python", "app_coneg.py"]