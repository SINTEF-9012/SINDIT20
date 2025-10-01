from sindit.api.api import app


from typing import Annotated


from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm


from sindit.authentication.models import User, Token


from sindit.initialize_kg_connectors import sindit_kg_connector


from sindit.initialize_authentication import authService, workspaceService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    return authService.verify_token(token)


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    current_workspace = workspaceService.get_current_workspace(current_user)
    sindit_kg_connector.set_graph_uri(current_workspace.uri.strip())
    return current_user


@app.post("/token", tags=["Vault"])
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    access_token = authService.create_access_token(
        username=form_data.username, password=form_data.password
    )
    return access_token


@app.get("/users/me/", response_model=User, tags=["Vault"])
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user
