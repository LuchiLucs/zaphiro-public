from typing import Annotated
from fastapi import Depends, Security

from sqlmodel import Session
from db import get_session

from auth.utils import get_current_user
from auth import Scopes

# Database dependencies
SessionDep = Annotated[Session, Depends(get_session)]

# Auth dependencies
UserDep = Security(get_current_user, scopes=[Scopes.USER.value])
ManagerDep = Security(get_current_user, scopes=[Scopes.MANAGER.value])
