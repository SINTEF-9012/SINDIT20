from fastapi import HTTPException
from initialize_objects import secret_vault
from util.log import logger

from api.api import app


@app.post("/vault/secret", tags=["Vault"])
async def store_secret(secret_path: str, secret_value: str) -> dict:
    """
    Store a secret in the vault.
    """
    try:
        # check if the secret path is already in the vault
        if secret_vault.resolveSecret(secret_path) is not None:
            raise HTTPException(
                status_code=400, detail=f"Secret {secret_path} already exists"
            )
        result = secret_vault.storeSecret(secret_path, secret_value)
        return {"result": result}
    except Exception as e:
        logger.error(f"Error storing secret {secret_path}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
