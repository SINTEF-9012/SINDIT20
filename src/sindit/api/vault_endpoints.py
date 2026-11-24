from fastapi import Body, HTTPException, Depends, Query
from pydantic import BaseModel
from sindit.initialize_vault import vault_service
from sindit.util.log import logger
from sindit.api.authentication_endpoints import User, get_current_active_user

from sindit.api.api import app


class StoreSecretRequest(BaseModel):
    secret_path: str
    secret_value: str


@app.post(
    "/vault/secret",
    tags=["Vault"],
    responses={
        200: {
            "description": "Successful response",
            "content": {"application/json": {"example": {"result": "true"}}},
        },
        400: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to store secret: error message"}
                }
            },
        },
    },
)
async def store_secret(
    payload: StoreSecretRequest | None = Body(None),
    secret_path: str
    | None = Query(
        None, deprecated=True, description="Deprecated: send in the JSON body"
    ),
    secret_value: str
    | None = Query(
        None, deprecated=True, description="Deprecated: send in the JSON body"
    ),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Store a secret in the vault.

    Send ``{"secret_path": ..., "secret_value": ...}`` as the JSON body. Passing them
    as query parameters still works for older clients but is deprecated: URLs end up
    in access logs and proxies, which exposes the secret.
    """
    if payload is not None:
        secret_path, secret_value = payload.secret_path, payload.secret_value
    elif secret_path is not None and secret_value is not None:
        logger.warning(
            "Secret '%s' was sent as a URL query parameter (deprecated); "
            "send it in the JSON body instead",
            secret_path,
        )
    else:
        raise HTTPException(
            status_code=422,
            detail="secret_path and secret_value are required in the JSON body",
        )
    try:
        result = vault_service.get_vault(current_user.username).storeSecret(
            secret_path, secret_value
        )
        return {"result": result}
    except Exception as e:
        logger.error(f"Error storing secret {secret_path}: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get(
    "/vault/path",
    tags=["Vault"],
    responses={
        200: {
            "description": "Successful response",
            "content": {
                "application/json": {"example": {"secret_paths": ["path1", "path2"]}}
            },
        },
        400: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to get secret: error message"}
                }
            },
        },
    },
)
async def list_secret_paths(
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    List all secret paths in the vault.
    """
    try:
        return {
            "secret_paths": vault_service.get_vault(
                current_user.username
            ).listSecretPaths()
        }
    except Exception as e:
        logger.error(f"Error listing secret paths: {e}")
        raise HTTPException(status_code=400, detail=str(e))
