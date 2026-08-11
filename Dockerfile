FROM python:3.9-slim
WORKDIR /app
RUN pip install Flask docker
RUN apt-get update && apt-get install -y docker.io
COPY orchestrator.py .
CMD ["python", "orchestrator.py"]
