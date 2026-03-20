FROM python:3-slim

WORKDIR /app
RUN pip install --proxy=http://proxy.cmb.mc:8080 beautifulsoup4 influxdb

COPY main.py main.py
COPY avqmaillib.py avqmaillib.py

CMD ["python", "-u", "main.py"]
