FROM python:3.11-slim

WORKDIR /app
COPY . .

CMD ["python3", "super_flips_bot.py"]