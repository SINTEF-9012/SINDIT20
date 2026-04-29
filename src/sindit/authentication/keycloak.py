from fastapi import HTTPException, status
from keycloak.exceptions import KeycloakAuthenticationError

from keycloak import KeycloakOpenID

from sindit.authentication.authentication_service import AuthService
from sindit.authentication.models import Token, User
from sindit.util.environment_and_configuration import get_environment_variable


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
            return Token(access_token=token["access_token"], token_type="bearer")

        except (KeycloakAuthenticationError, Exception):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

    def mint_service_token(
        self, username: str, ttl_minutes: int | None = None
    ) -> Token | None:
        """Keycloak-issued JWTs cannot be minted in-process.

        Returning ``None`` signals to the caller (typically the dataspace
        connector) that no bearer can be auto-minted for this user. To make
        the dataspace integration work with Keycloak you need to either:

        - configure a Keycloak service account with the client_credentials
          grant and replace this implementation, or
        - keep the legacy ``sinditServiceUserPasswordPath`` flow alive in a
          separate code path.
        """
        from sindit.util.log import logger

        logger.warning(
            "Keycloak auth service cannot mint a service token for '%s' "
            "in-process; configure a Keycloak service account if you need "
            "the dataspace connector to call SINDIT under that identity.",
            username,
        )
        return None

    def verify_token(self, token: str) -> User:
        """
        Verify the given token and return user information.
        """
        try:
            user_info = self.keycloak_openid.userinfo(token)
            # print(user_info)
            if not user_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
                )
            return User(
                username=user_info["preferred_username"],
                email=user_info.get("email"),
                full_name=user_info.get("name"),
            )
        except (KeycloakAuthenticationError, Exception):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
