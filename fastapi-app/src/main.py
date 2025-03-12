import httpx
import uvicorn

from src import init_app

app = init_app()


@app.get("/healthcheck")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
