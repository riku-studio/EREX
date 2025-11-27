from fastapi import FastAPI

from app.routes import health, index_rules, pipeline
from app.utils.config import Config
from app.utils.logging import logger

app = FastAPI(title=Config.APP_NAME)


@app.on_event("startup")
async def startup_event():
    logger.info(f"{Config.APP_NAME} starting in {Config.APP_ENV} mode...")


@app.get("/")
async def read_root():
    logger.info("Root endpoint accessed")
    return {"message": f"Hello from {Config.APP_NAME}!"}


app.include_router(health.router)
app.include_router(index_rules.router)
app.include_router(pipeline.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=Config.PORT, reload=Config.DEBUG)
