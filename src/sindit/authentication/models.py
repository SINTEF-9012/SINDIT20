from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = False


class UserInDB(User):
    hashed_password: str


class Workspace(BaseModel):
    name: str
    uri: str
    is_default: bool = False
