from sindit.authentication.models import User


class AuthService:
    def create_access_token(self, username: str, password: str) -> str:
        pass

    def verify_token(self, token: str) -> User:
        pass
