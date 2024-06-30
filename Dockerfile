FROM python:3.12.4-alpine3.20
WORKDIR /bridgewatcher
COPY . .
RUN pip3 install -r requirements.txt
CMD ["sh", "-c", "python3 bot.py database --populate && python3 bot.py run"]
