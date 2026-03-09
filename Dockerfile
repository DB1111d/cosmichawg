FROM selenium/standalone-chrome:latest

USER root

WORKDIR /app

COPY requirements-dockermain.txt .
RUN pip install --no-cache-dir -r requirements-dockermain.txt

COPY . .

CMD ["python3", "schedule_test.py"]
