# Minimal React + FastAPI NDJSON Streaming Example

This example demonstrates incremental JSON streaming using FastAPI and React for the `structured_streamer` project.

## Backend (FastAPI)

Run the backend server:

```bash
cd tests/react/backend
pip install fastapi uvicorn
uvicorn main:app --reload
```

This exposes `/stream`, which streams newline-delimited JSON objects incrementally.

## Frontend (React)

Run a static server (e.g., with Python):

```bash
cd tests/react/frontend
python -m http.server 8000
```

Open [http://localhost:8000](http://localhost:8000) in your browser. Click "Start" to begin streaming. The React app will fetch `/stream` and render each JSON object as it arrives.

## Notes
- Make sure the backend is running and accessible from the frontend (CORS may need to be enabled for real deployments).
- The example is minimal and isolated for demonstration purposes.
