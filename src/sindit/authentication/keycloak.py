from fastapi import HTTPException, status
from keycloak.exceptions import KeycloakAuthenticationError

from keycloak import KeycloakOpenID

from sindit.authentication.authentication_service import AuthService
from sindit.authentication.models import User
from sindit.util.environment_and_configuration import get_environment_variable, get_environment_variable_bool

class KeycloakAuthService(AuthService):

    def __init__(self):
        self.keycloak_openid = KeycloakOpenID(
            server_url=get_environment_variable("KEYCLOAK_SERVER_URL"),
            client_id=get_environment_variable("KEYCLOAK_CLIENT_ID"),
            realm_name=get_environment_variable("KEYCLOAK_REALM"),
            client_secret_key=get_environment_variable("KEYCLOAK_CLIENT_SECRET"),
        )

    def create_access_token(self, username: str, password: str) -> str:
        """
        Authenticate the user using Keycloak and return an access token.
        """
        try:
            token = self.keycloak_openid.token(username, password)
            return token["access_token"]
        except (KeycloakAuthenticationError, Exception) as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

    def verify_token(self, token: str) -> User:
        """
        Verify the given token and return user information.
        """
        try:
            user_info = self.keycloak_openid.userinfo(token)
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
        except (KeycloakAuthenticationError, Exception) as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )