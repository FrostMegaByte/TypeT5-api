FROM python:3.10

WORKDIR /app

RUN pip install pipenv
COPY .env Pipfile Pipfile.lock README.md requirements.txt setup.py ./
COPY /src ./src

RUN pipenv --python /usr/local/bin/python3
RUN pipenv sync

EXPOSE 5000

CMD ["pipenv",  "run", "python3", "src/api/app.py"]