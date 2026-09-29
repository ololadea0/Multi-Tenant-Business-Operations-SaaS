from fastapi import FastAPI

app = FastAPI(
    title="Multi-Tenant Business Operations SaaS",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "Multi-Tenant Business Operations API is running"
    }