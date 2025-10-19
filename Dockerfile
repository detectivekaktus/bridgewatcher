FROM python:3.12.4-alpine3.19

WORKDIR /app

COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

RUN python3 bot.py database --populate

VOLUME [ "/app/logs" ]

CMD [ "python3", "bot.py", "run" ]