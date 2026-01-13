from sindit.connectors.setup_connectors import (
    initialize_connections_and_properties,
    refresh_connection,
    refresh_property,
)

from sindit.util.log import logger
from sindit.api.api import app
from sindit.api.authentication_endpoints import User, get_current_active_user
from fastapi import Depends, BackgroundTasks, HTTPException
import threading

# Global flag to track if refresh is running
_refresh_running = False
_refresh_lock = threading.Lock()


@app.post(
    "/connections/refresh",
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
    Refresh all connections and properties in the background.

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
    "/connections/refresh/status",
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
    Check if any refresh operation is currently running.
    """
    global _refresh_running

    with _refresh_lock:
        running = _refresh_running

    return {"status": "running" if running else "idle", "running": running}


@app.post(
    "/connection/refresh",
    tags=["Connection"],
    responses={
        200: {
            "description": "Connection refreshed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Connection refresh started",
                        "connection_uri": "http://example.com/connection/123",
                    }
                }
            },
        },
        400: {
            "description": "Missing connection_uri parameter",
            "content": {
                "application/json": {
                    "example": {"detail": "connection_uri parameter is required"}
                }
            },
        },
        404: {
            "description": "Connection not found",
            "content": {
                "application/json": {"example": {"detail": "Connection not found"}}
            },
        },
    },
)
async def refresh_connection_by_uri(
    connection_uri: str,
    replace: bool = False,
    current_user: User = Depends(get_current_active_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """
    Refresh a specific connection by its URI.

    Parameters:
    - connection_uri: The URI of the connection to refresh (query parameter)
        - replace: If True, stop and restart the connection.
            If False, only start if not running.
    """
    global _refresh_running

    if not connection_uri:
        raise HTTPException(
            status_code=400, detail="connection_uri parameter is required"
        )

    # Check if any refresh is running
    with _refresh_lock:
        if _refresh_running:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Another refresh operation is running. "
                    "Please wait for it to complete."
                ),
            )
        _refresh_running = True

    def refresh_with_cleanup():
        try:
            logger.info(f"Refreshing connection {connection_uri} (replace={replace})")
            refresh_connection(connection_uri, replace=replace, async_start=True)
            logger.info(f"Connection {connection_uri} refresh completed")
        except Exception as e:
            logger.error(f"Error refreshing connection {connection_uri}: {e}")
        finally:
            global _refresh_running
            with _refresh_lock:
                _refresh_running = False

    background_tasks.add_task(refresh_with_cleanup)

    return {
        "message": "Connection refresh started",
        "connection_uri": connection_uri,
        "replace": replace,
    }


@app.post(
    "/property/refresh",
    tags=["Connection"],
    responses={
        200: {
            "description": "Property refreshed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Property refresh started",
                        "property_uri": "http://example.com/property/456",
                    }
                }
            },
        },
        400: {
            "description": "Missing property_uri parameter",
            "content": {
                "application/json": {
                    "example": {"detail": "property_uri parameter is required"}
                }
            },
        },
        404: {
            "description": "Property not found",
            "content": {
                "application/json": {"example": {"detail": "Property not found"}}
            },
        },
    },
)
async def refresh_property_by_uri(
    property_uri: str,
    replace: bool = False,
    current_user: User = Depends(get_current_active_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """
    Refresh a specific property by its URI.

    Parameters:
    - property_uri: The URI of the property to refresh (query parameter)
        - replace: If True, recreate the property.
            If False, only create if it doesn't exist.
    """
    global _refresh_running

    if not property_uri:
        raise HTTPException(
            status_code=400, detail="property_uri parameter is required"
        )

    # Check if any refresh is running
    with _refresh_lock:
        if _refresh_running:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Another refresh operation is running. "
                    "Please wait for it to complete."
                ),
            )
        _refresh_running = True

    def refresh_with_cleanup():
        try:
            logger.info(f"Refreshing property {property_uri} (replace={replace})")
            refresh_property(property_uri, replace=replace, async_start=True)
            logger.info(f"Property {property_uri} refresh completed")
        except Exception as e:
            logger.error(f"Error refreshing property {property_uri}: {e}")
        finally:
            global _refresh_running
            with _refresh_lock:
                _refresh_running = False

    background_tasks.add_task(refresh_with_cleanup)

    return {
        "message": "Property refresh started",
        "property_uri": property_uri,
        "replace": replace,
    }
