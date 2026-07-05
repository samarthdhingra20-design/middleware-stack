from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import time

EMAIL = "24f1002646@ds.study.iitm.ac.in"

ALLOWED_ORIGIN = "https://app-y0dxcr.example.com"
EXAM_ORIGIN = "https://exam.sanand.workers.dev"

RATE_LIMIT = 14
WINDOW = 10

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        ALLOWED_ORIGIN,
        EXAM_ORIGIN,
    ],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

client_requests = {}


@app.middleware("http")
async def middleware(request: Request, call_next):

    request_id = request.headers.get("x-request-id")
    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    client_id = request.headers.get("x-client-id", "anonymous")

    now = time.time()

    timestamps = client_requests.get(client_id, [])
    timestamps = [t for t in timestamps if now - t < WINDOW]

    if len(timestamps) >= RATE_LIMIT:
        response = JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
        )
        response.headers["Retry-After"] = str(WINDOW)
        response.headers["X-Request-ID"] = request_id
        return response

    timestamps.append(now)
    client_requests[client_id] = timestamps

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/")
def home():
    return {
        "status": "running"
    }


@app.get("/ping")
def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }