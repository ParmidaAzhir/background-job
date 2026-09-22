from fastapi import FastAPI

app = FastAPI()

@app.get("/health")  # When someone sends a GET request to /health, run health() and return the status.
def health():
    return {"status": "ok"}