FROM python:3.10-slim-buster

WORKDIR /usr/src/app

COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install --no-cache-dir dash[diskcache] gunicorn pyarrow joblib

COPY OpenAlex_concepts_in_use_(17_August_2022)_-_concepts.csv OpenAlex_concepts_in_use_(17_August_2022)_-_concepts.csv
COPY list_all_institutions_full.parquet list_all_institutions_full.parquet
COPY redis.conf redis.conf
COPY start_celery_worker.sh /start_celery_worker.sh
COPY *.py ./
COPY pages/*.py pages/

CMD [ "gunicorn", "--workers=3", "--threads=4", "-b 0.0.0.0:8050", "main_app:server"]
