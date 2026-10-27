from fastapi import FastAPI
from mangum import Mangum

from atomize_api.routers import health

app = FastAPI(title="Atomize API", version="0.1.0")

app.include_router(health.router)

# Lambda entrypoint (API Gateway -> Lambda, per docs/TECH_STACK.md).
handler = Mangum(app)
