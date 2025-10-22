from sindit.connectors.setup_connectors import (
    initialize_connections_and_properties,
)

from sindit.util.log import logger
from sindit.api.api import app
from sindit.api.authentication_endpoints import User, get_current_active_user
from fastapi import Depends, BackgroundTasks, HTTPException
import threading

# Global flag to track if refresh is running
_refresh_running = False
_refresh_lock = threading.Lock()


@app.get(
    "/connection/refresh",
    tags=["Connection"],
    responses={
        200: {
            "description": "Successful response",
            "content": {
                "application/json": {
                    "example": {
                        "message": ("Connections and properties refresh started"),
                        "status": "running",
                    }
                }
            },
        },
        409: {
            "description": "Refresh already in progress",
            "content": {
                "application/json": {
                    "example": {"detail": "Refresh is already running"}
                }
            },
        },
    },
)
async def refresh_connections_and_properties(
    replace: bool = False,
    current_user: User = Depends(get_current_active_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """
    Refresh connections and properties in the background.

    This endpoint starts the refresh process asynchronously and returns
    immediately. Only one refresh can run at a time to prevent conflicts.

    Parameters:
    - replace: If True, existing connections will be stopped and restarted.
               If False (default), existing connections are kept running and
               only new connections/properties are initialized.
    """
    global _refresh_running

    with _refresh_lock:
        if _refresh_running:
            raise HTTPException(
                status_code=409,
                detail="Refresh is already running. " "Please wait for it to complete.",
            )
        _refresh_running = True

    def refresh_with_cleanup():
        try:
            logger.info(f"Starting connections/properties refresh (replace={replace})")
            initialize_connections_and_properties(replace=replace, async_start=True)
            logger.info("Connections and properties refresh completed")
        except Exception as e:
            logger.error(f"Error refreshing connections and properties: {e}")
        finally:
            global _refresh_running
            with _refresh_lock:
                _refresh_running = False

    background_tasks.add_task(refresh_with_cleanup)

    return {
        "message": "Connections and properties refresh started",
        "status": "running",
        "replace": replace,
    }


@app.get(
    "/connection/refresh/status",
    tags=["Connection"],
    responses={
        200: {
            "description": "Refresh status",
            "content": {
                "application/json": {"example": {"status": "idle", "running": False}}
            },
        }
    },
)
async def get_refresh_status(
    current_user: User = Depends(get_current_active_user),
):
    """
    Check if a connections/properties refresh is currently running.
    """
    with _refresh_lock:
        running = _refresh_running

    return {"status": "running" if running else "idle", "running": running}
