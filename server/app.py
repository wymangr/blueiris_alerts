from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from blueiris_alerts.server.routes import slack_routes, blueiris_routes
from blueiris_alerts.server.settings import BI_LOGGER

BI_LOGGER.info("Starting Server")

app = FastAPI()
app.include_router(blueiris_routes.router)
app.include_router(slack_routes.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    BI_LOGGER.error(
        f"Unhandled exception on {request.method} {request.url}: {exc}",
        exc_info=True,
    )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
