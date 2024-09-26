from fastapi import HTTPException
from initialize_vault import secret_vault
from util.log import logger

from api.api import app


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
async def store_secret(secret_path: str, secret_value: str) -> dict:
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
async def list_secret_paths() -> dict:
    """
    List all secret paths in the vault.
    """
    try:
        return {"secret_paths": secret_vault.listSecretPaths()}
    except Exception as e:
        logger.error(f"Error listing secret paths: {e}")
        raise HTTPException(status_code=400, detail=str(e))
