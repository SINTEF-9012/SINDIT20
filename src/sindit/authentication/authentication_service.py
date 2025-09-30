from sindit.authentication.models import User, Token


class AuthService:
    def create_access_token(self, username: str, password: str) -> Token:
        pass

    def verify_token(self, token: str) -> User:
        pass
