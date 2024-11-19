# app/main.py

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.db.database import engine
from app.db import models
from app.api.endpoints import subdomain, dns, http, automation
from app.core.logging_config import setup_logging

logger = setup_logging()

#models.Base.metadata.drop_all(bind=engine)
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logger.exception(f"Unhandled exception occurred: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred."}
        )

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to Reconthing API"}

# Include subdomain router
app.include_router(subdomain.router, prefix="/api/v1", tags=["subdomains"])

# Include DNS resolution router
app.include_router(dns.router, prefix="/api/v1/dns", tags=["dns"])

# Include HTTP probing router
app.include_router(http.router, prefix="/api/v1/http", tags=["http"])

# Basic Recon Implementation
app.include_router(automation.router, prefix="/api/v1/automation", tags=["automation"])



if __name__ == "__main__":
    import uvicorn
    logger.info("Starting BBRF API server")
    uvicorn.run(app, host="0.0.0.0", port=8000)