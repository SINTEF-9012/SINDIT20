from fastapi import HTTPException, status
from keycloak.exceptions import KeycloakAuthenticationError

from keycloak import KeycloakOpenID

from sindit.authentication.models import User
from sindit.util.environment_and_configuration import get_environment_variable, get_environment_variable_bool

USE_KEYCLOAK = get_environment_variable_bool("USE_KEYCLOAK", optional=True, default=False)
if USE_KEYCLOAK:
    keycloak_openid = KeycloakOpenID(
        server_url=get_environment_variable("KEYCLOAK_SERVER_URL"),
        client_id=get_environment_variable("KEYCLOAK_CLIENT_ID"),
        realm_name=get_environment_variable("KEYCLOAK_REALM"),
        client_secret_key=get_environment_variable("KEYCLOAK_CLIENT_SECRET"),
    )

class AuthService:
    @staticmethod
    def create_access_token(username: str, password: str) -> str:
        """
        Authenticate the user using Keycloak and return an access token.
        """
        try:
            token = keycloak_openid.token(username, password)
            return token["access_token"]
        except KeycloakAuthenticationError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

    @staticmethod
    def verify_token(token: str) -> User:
        """
        Verify the given token and return user information.
        """
        try:
            user_info = keycloak_openid.userinfo(token)
            print(user_info)
            if not user_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
                )
            return User(
                username=user_info["preferred_username"],
                email=user_info.get("email"),
                full_name=user_info.get("name"),
            )
        except KeycloakAuthenticationError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )