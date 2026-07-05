from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import time

EMAIL = "24f1002646@ds.study.iitm.ac.in"

RATE_LIMIT = 14
WINDOW = 10

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app-y0dxcr.example.com",
        "https://exam.sanand.workers.dev",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

client_requests = {}


@app.middleware("http")
async def middleware(request: Request, call_next):
    # ---------- Request ID ----------
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    # ---------- Rate limiting ----------
    client_id = request.headers.get("X-Client-Id", "anonymous")
    now = time.time()

    timestamps = client_requests.get(client_id, [])
    timestamps = [t for t in timestamps if now - t < WINDOW]

    if len(timestamps) >= RATE_LIMIT:
        response = JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
        )
        response.headers["X-Request-ID"] = request_id
        return response

    timestamps.append(now)
    client_requests[client_id] = timestamps

    response = await call_next(request)

    # Echo request ID in every response
    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/")
def home():
    return {"status": "running"}


@app.get("/ping")
def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }