from pydantic import BaseModel

# Pydantic schemas...


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
    scopes: list[str] = []


class User(BaseModel):
    username: str
    manager: bool | None = None


# Database models...


class UserInDB(User):
    hashed_password: str
