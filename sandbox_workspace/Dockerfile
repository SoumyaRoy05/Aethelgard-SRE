# target_service/Dockerfile

FROM python:3.10-slim

WORKDIR /app

# Pre-install core runtime libraries required within the sandboxed verification cluster
RUN pip install --no-cache-dir fastapi uvicorn requests numpy pydantic

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]