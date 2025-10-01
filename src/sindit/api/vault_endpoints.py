from fastapi import HTTPException, Depends
from sindit.initialize_vault import secret_vault
from sindit.util.log import logger
from sindit.api.authentication_endpoints import User, get_current_active_user

from sindit.api.api import app


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
    secret_path: str,
    secret_value: str,
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Store a secret in the vault.
    """
    try:
        result = secret_vault.storeSecret(secret_path, secret_value)
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
        return {"secret_paths": secret_vault.listSecretPaths()}
    except Exception as e:
        logger.error(f"Error listing secret paths: {e}")
        raise HTTPException(status_code=400, detail=str(e))
