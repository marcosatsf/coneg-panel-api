FROM python:3.8
WORKDIR /coneg_root
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN rm requirements.txt
COPY /sql ./sql/
COPY app_coneg.py auth_route.py db_transactions.py files_manager.py user_model.py ./
CMD ["python", "app_coneg.py"]