from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import SecurityScopes
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from auth.schemas import UserInDB, TokenData, User
from auth import fake_users_db, oauth2_scheme
from pydantic import ValidationError
from core.utils import get_logger
from auth.config import settings

from . import Scopes

logger = get_logger("auth", "DEBUG")
password_hash = PasswordHash.recommended()


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_hash.hash(password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_KEY.get_secret_value(), algorithm=settings.JWT_ALG
    )
    return encoded_jwt


def get_user_scopes(user: UserInDB, requested_scopes: list[str]) -> str:
    # Mock the scopes associated with registered users
    # The data could also be saved directly on the storage database
    scopes = []

    # NOTE: mocked scopes associated with users in DB
    scopes.append(Scopes.USER.value)
    if user.manager and Scopes.MANAGER.value in requested_scopes:
        scopes.append(Scopes.MANAGER.value)

    # Compare requested scopes with available scopes associated with users
    not_auth_scopes = set(requested_scopes) - set(scopes)
    logger.debug(f"Logged user [{user.username}] received [{scopes}] scopes")
    if not_auth_scopes:
        logger.debug(
            f"Logged user [{user.username}] could not received additional [{not_auth_scopes}] scopes"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User [{user.username}] requested more scope than permitted: [{not_auth_scopes}]",
        )
    return " ".join(scopes)


async def get_current_user(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    try:
        payload = jwt.decode(
            token, settings.JWT_KEY.get_secret_value(), algorithms=[settings.JWT_ALG]
        )
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        scope: str = payload.get("scope", "")
        token_scopes = scope.split(" ")
        token_data = TokenData(scopes=token_scopes, username=username)
    except (InvalidTokenError, ValidationError):
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    return user


async def check_current_user_manager(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.manager:
        logger.debug("Authorize: user is also a manager")
    else:
        logger.debug("Authorize: user is just a user")
    return current_user


if __name__ == "__main__":
    print(get_password_hash("user"))
    print(get_password_hash("manager"))
