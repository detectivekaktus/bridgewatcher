FROM python:3.13.7-slim

WORKDIR /app

COPY . /app
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir poetry
RUN poetry install --without dev

CMD [ "poetry", "run", "python3", "main.py" ]