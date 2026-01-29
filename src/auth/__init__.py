from fastapi.security import OAuth2PasswordBearer
from enum import StrEnum


# NOTE: Scopes derived from domain functional requirements
class Scopes(StrEnum):
    USER = "user"
    MANAGER = "manager"


# NOTE: in-memory storage dict to mock a database with users
fake_users_db = {
    "user": {
        "username": "user",
        "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$bTSlYukGcc15MFSJhvxv5g$W0TfoMrciKzDY+YUyZb4+NXLDOLSDB6Wn2dzjNpPGiw",
        "manager": False,
    },
    "manager": {
        "username": "manager",
        "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$/GQTCZwrcdJ39IfrkrrSKA$7ch/Dup1fyiAt6ul8SzzCzY22wr28Iz1SDiDM71BLTA",
        "manager": True,
    },
}

# NOTE: the tokenUrl is the relative path of the API to get the token
# so it should see the router prefix and handle it automatically
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/token",
    scopes={
        Scopes.USER.value: "Private APIs available to authenticated users.",
        Scopes.MANAGER.value: "Private APIs available to authenticated managers.",
    },
)
