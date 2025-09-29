from sindit.api.api import app


from typing import Annotated


from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm


from sindit.authentication.authentication_service import AuthService
from sindit.authentication.in_memory import InMemoryAuthService
from sindit.authentication.keycloak import KeycloakAuthService
from sindit.authentication.models import User, Token
from sindit.util.log import logger

from sindit.util.environment_and_configuration import (
    get_environment_variable_bool,
)


USE_KEYCLOAK = get_environment_variable_bool(
    "USE_KEYCLOAK", optional=True, default=False
)
if USE_KEYCLOAK:
    logger.info("Using Keycloak for authentication")
    authService: AuthService = KeycloakAuthService()
else:
    logger.info("Using in-memory authentication")
    authService: AuthService = InMemoryAuthService()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    return authService.verify_token(token)


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token", tags=["Vault"])
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    access_token = authService.create_access_token(
        username=form_data.username, password=form_data.password
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get("/users/me/", response_model=User, tags=["Vault"])
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user
