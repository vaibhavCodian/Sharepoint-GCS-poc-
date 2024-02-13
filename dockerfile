FROM python:3.9-slim

ENV PYTHONUNBUFFERED True

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install Flask gunicorn

EXPOSE 8080
ENV PORT 8080

CMD ["python", "main.py"]