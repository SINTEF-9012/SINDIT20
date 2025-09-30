from datetime import datetime, timedelta, timezone
from sindit.authentication.models import TokenData, User, UserInDB
from sindit.util.log import logger
from sindit.initialize_vault import secret_vault
from sindit.util.environment_and_configuration import (
    get_environment_variable,
)
import base64
from sindit.authentication.authentication_service import AuthService
import jwt
import os
from passlib.context import CryptContext
from jwt.exceptions import InvalidTokenError
from fastapi import HTTPException, status


class InMemoryAuthService(AuthService):
    def __init__(self):
        self.SECRET_KEY = get_environment_variable(
            "SECRET_KEY", optional=True, default=None
        )
        if not self.SECRET_KEY:
            # Generate a random secret key
            self.SECRET_KEY = base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8")
            logger.info(
                "Secret key not set for token generation, using random key: %s",
                self.SECRET_KEY,
            )
            logger.info("Secret key was stored to the vault, path: SECRET_KEY")
            secret_vault.storeSecret("SECRET_KEY", self.SECRET_KEY)

        self.ALGORITHM = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 30

        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        self.USER_PATH = get_environment_variable(
            "USER_PATH",
            optional=True,
            default="environment_and_configuration/user.json",
        )
        self.WORKSPACE_PATH = get_environment_variable(
            "WORKSPACE_PATH",
            optional=True,
            default="environment_and_configuration/workspace.json",
        )
        # read users from file, create file if it does not exist
        if os.path.exists(self.USER_PATH):
            import json

            with open(self.USER_PATH, "r") as f:
                try:
                    self.users_db = json.load(f)
                except json.JSONDecodeError:
                    logger.error("Error decoding JSON from %s", self.USER_PATH)
                    self.users_db = {}
        else:
            logger.warning(
                "User file %s does not exist, creating empty file", self.USER_PATH
            )
            with open(self.USER_PATH, "w") as f:
                f.write("{}")
            self.users_db = {}

    def verify_password(self, plain_password, hashed_password):
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password):
        return self.pwd_context.hash(password)

    def get_user(self, db, username: str):
        if username in db:
            user_dict = db[username]
            return UserInDB(**user_dict)

    # TODO: replace by real database
    def authenticate_user(self, fake_db, username: str, password: str):
        user = self.get_user(fake_db, username)
        if not user:
            return False
        if not self.verify_password(password, user.hashed_password):
            return False
        return user

    def create_token(self, data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        if expires_delta is not None:
            if expires_delta:
                expire = datetime.now(timezone.utc) + expires_delta
            else:
                expire = datetime.now(timezone.utc) + timedelta(minutes=15)
            to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_jwt

    def create_access_token(self, username: str, password: str) -> str:
        user = self.authenticate_user(self.users_db, username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return access_token

    def verify_token(self, token: str) -> User:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            username = payload.get("sub")
            if username is None:
                raise credentials_exception
            token_data = TokenData(username=username)
        except InvalidTokenError:
            raise credentials_exception
        user = self.get_user(self.users_db, username=token_data.username)
        if user is None:
            raise credentials_exception
        return user
