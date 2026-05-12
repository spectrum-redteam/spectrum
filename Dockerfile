FROM python:3.11-slim

RUN pip install spectrum-security

ENTRYPOINT ["spectrum"]
