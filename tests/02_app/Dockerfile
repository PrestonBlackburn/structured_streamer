
FROM python:3.11-slim


RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the source code and project definition
COPY ./ /app

# Install the project and its dependencies
RUN pip install --no-cache-dir .[dev] 
# Copy the test application
COPY ./tests/02_app /app/tests/app

EXPOSE 8000

CMD ["uvicorn", "tests.app.server:app", "--host", "0.0.0.0", "--port", "8000"]
