from sindit.authentication.models import User, Token


class AuthService:
    def create_access_token(self, username: str, password: str) -> Token:
        pass

    def verify_token(self, token: str) -> User:
        pass

    def mint_service_token(
        self, username: str, ttl_minutes: int | None = None
    ) -> Token | None:
        """Mint a bearer token for ``username`` without password verification.

        Intended for trusted in-process callers (e.g. the dataspace connector)
        that need to act on behalf of an already-authenticated SINDIT user
        without re-prompting for a password. Implementations that cannot
        safely mint tokens (because the signing key lives in an external IdP
        such as Keycloak) should return ``None`` and log a warning; the
        caller is expected to handle the no-bearer case.

        Args:
            username: Identity to embed in the token's ``sub`` claim. Should
                belong to an existing SINDIT user.
            ttl_minutes: Optional override for the token TTL. Defaults to
                whatever the implementation's regular access-token TTL is.
        """
        return None
