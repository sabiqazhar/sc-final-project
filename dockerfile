# create your dockerfile here, for more information, read readme.md
FROM python:3.9-slim-buster

# working directory
WORKDIR /app

# setting env
ENV POSTGRES_DB=fashion-campus-db
ENV POSTGRES_USER=users
ENV POSTGRES_PASSWORD=password
ENV POSTGRES_HOST=34.142.244.100
ENV POSTGRES_PORT=5432

# copy requirement file
COPY requirements.txt requirements.txt
COPY app .

# install requirements
RUN pip install -r requirements.txt

# run flask app
CMD [ "flask", "--app", "app", "run", "--host=0.0.0.0"]