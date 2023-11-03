from fastapi import FastAPI
from blueiris_alerts.server.routes import slack_routes

app = FastAPI()
app.include_router(slack_routes.router)
