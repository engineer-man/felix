# pull official base image
FROM python:3.10.6
ADD requirements.txt /app/
RUN pip install -U -r /app/requirements.txt
