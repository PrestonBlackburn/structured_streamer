## Manually run tests

```bash
fastapi dev tests/02_app/server.py
uvicorn tests.02_app.server:app --host 0.0.0.0 --port 8000
```

## Automatically run tests

Run from root dir with:
```bash
pytest
```

## Docker hosting 

Run from root dir with:
```bash
docker build -f tests/02_app/Dockerfile -t struct_strm_server:latest .
```
