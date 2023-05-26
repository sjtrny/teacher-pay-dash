FROM python:3.9-bullseye

WORKDIR /usr/src

COPY src ./

RUN pip install --no-cache-dir -r requirements.txt

CMD ["gunicorn"  , "-b", "0.0.0.0:80", "app:server"]
