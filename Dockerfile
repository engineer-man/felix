FROM python:3.7.3-stretch
ADD requirements.txt /app/
RUN pip install -U -r /app/requirements.txt 
