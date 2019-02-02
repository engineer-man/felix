FROM python:3.6.8-jessie

RUN pip install -U git+https://github.com/Rapptz/discord.py@rewrite#egg=discord.py && \
    pip install requests
