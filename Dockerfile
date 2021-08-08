FROM python:3.8
WORKDIR /coneg_root
RUN apt-get update -y && \
    apt-get install cron -y
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN rm requirements.txt
COPY /sql ./sql/
COPY /model ./model/
COPY app_coneg.py db_transactions.py files_manager.py dash_process.py routes.py reset_notif.py timeseries.py cron_scheduler.sh ./
RUN bash cron_scheduler.sh
CMD ["python", "app_coneg.py"]