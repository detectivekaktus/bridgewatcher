FROM python:3.12.4-alpine3.19

WORKDIR /app

COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

# Not sure if seeding here is the best choice...
CMD [ "sh", "-c", "python3 seed.py && python3 bot.py" ]