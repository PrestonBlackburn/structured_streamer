
FROM python:3.11-slim


RUN apt-get update && apt-get install -y curl git build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the source code and project definition
COPY ./ /app

# Install the project and its dependencies
RUN pip install --upgrade pip wheel setuptools hatch
RUN hatch build
RUN pip install --no-cache-dir dist/struct_strm-*.whl
RUN pip install --no-cache-dir .[dev] 
# Copy the test application
COPY ./tests/02_app /app/tests/02_app

EXPOSE 8000

CMD ["uvicorn", "tests.02_app.server:app", "--host", "0.0.0.0", "--port", "8000"]
