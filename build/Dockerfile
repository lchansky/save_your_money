FROM python:3.8

RUN apt-get update -y && apt-get upgrade -y

COPY ./src /src
COPY ./requirements.txt /tmp/requirements.txt

WORKDIR /src

RUN pip3 install -r /tmp/requirements.txt
RUN python3 manage.py makemigrations && python3 manage.py migrate

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
