FROM python:3.9
ADD requirements.txt /app/
RUN pip install -U -r /app/requirements.txt
