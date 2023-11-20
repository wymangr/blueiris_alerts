from fastapi import FastAPI
from blueiris_alerts.server.routes import slack_routes, blueiris_routes
from blueiris_alerts.server.settings import LOGGER

LOGGER.info("Starting Server")

app = FastAPI()
app.include_router(blueiris_routes.router)
app.include_router(slack_routes.router)
