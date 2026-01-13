from fastapi import Response
from sindit.api.api import app


@app.get("/health/live", tags=["Health"], status_code=204)
async def get_live_status():
    return Response(status_code=204)


@app.get("/health/ready", tags=["Health"], status_code=204)
async def get_ready_status():
    return Response(status_code=204)
