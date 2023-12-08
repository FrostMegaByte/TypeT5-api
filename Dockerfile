FROM python:3.10-slim

WORKDIR /app

COPY Pipfile Pipfile.lock ./
COPY .env README.md requirements.txt setup.py ./
COPY src/typet5 ./src/typet5

RUN pip install pipenv
RUN pipenv --python /usr/local/bin/python3
RUN pipenv sync

COPY src ./src

EXPOSE 5000

CMD ["pipenv",  "run", "python3", "src/api/app.py"]