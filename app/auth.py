"""Auth module — JWT helpers, password hashing, FastAPI role dependency (C4).

Near-verbatim reuse of bibliotek ``src/auth.py`` (I7 reuse rule); the only
deliberate differences from the reuse source are:

  * config imports come from ``app.config`` (affärssystemet) not ``src.config``
  * the ``ROLES`` tuple is declared here (closed set C-F) and matches the User
    model's ROLES in ``app/models/user.py`` exactly
  * a ``get_current_user`` dependency is added (token + live DB read, NO role
    check) to back the public ``GET /api/auth/me`` endpoint (C6 requires "me"
    to be role-agnostic).
  * MC 11468 (audit rank 5, JWT revocation): both dependencies re-read the
    User row from the DB per request — a JWT is a login receipt, not a
    standing grant, so deactivation/demotion works immediately. One SQLite
    read per request is deliberate at this scale; no cache by design.

Functions:
    hash_password(password)      → bcrypt hash string
    check_password(password, h)  → bool
    create_access_token(id, role)→ signed JWT (expires ACCESS_TOKEN_EXPIRE_MINUTES)
    verify_token(token)          → dict(user_id, role) or None
    require_role(allowed)        → FastAPI dependency: 401 / 403 / live user
    get_current_user             → FastAPI dependency: 401 or live user
"""

from datetime import UTC, datetime, timedelta

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, SECRET_KEY
from app.database import get_session
from app.models import User

# C-F fixed point: the closed set of user roles. Same names the User model uses.
ROLES: tuple[str, ...] = ("admin", "sales", "finance", "procurement", "customer")

# ---------------------------------------------------------------------------
# Password hashing (bcrypt directly — avoids passlib 1.7 / bcrypt 5 compat)
# ---------------------------------------------------------------------------


def hash_password(password: str) -> str:
    """Return a ``$2b$...`` bcrypt hash of *password*."""
    return bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")


def check_password(password: str, hashed: str) -> bool:
    """Return True if *password* matches *hashed*."""
    return bcrypt.checkpw(
        password.encode("utf-8"), hashed.encode("utf-8")
    )


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def create_access_token(user_id: int, role: str) -> str:
    """Create a signed JWT that expires after ACCESS_TOKEN_EXPIRE_MINUTES."""
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),       # subject = user id
        "role": role,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": now,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict | None:
    """Decode and verify *token*; return {user_id, role} or None on failure."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return {
            "user_id": int(payload["sub"]),
            "role": payload["role"],
        }
    except JWTError:
        return None


# ---------------------------------------------------------------------------
# FastAPI dependencies — role gate  +  verify-only (public "me")
# ---------------------------------------------------------------------------

_scheme = HTTPBearer(auto_error=False)


def _unauthorized(detail: str) -> None:
    """Raise the module's one 401 shape (Bearer challenge always included)."""
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _authenticate(
    credentials: HTTPAuthorizationCredentials, db: Session
) -> dict:
    """Resolve the Bearer token to the live User row: {user_id, role} from DB.

    MC 11468: the User row is re-read on every request, so a deleted or
    deactivated user — or a changed role — takes effect immediately.
    Unknown/inactive users get the same 401 semantics as an invalid token;
    the returned role is the DB role, never the token claim.
    """
    if credentials is None:
        _unauthorized("Not authenticated")
    claims = verify_token(credentials.credentials)
    if claims is None:
        _unauthorized("Invalid or expired token")
    user = db.query(User).filter(User.id == claims["user_id"]).first()
    if user is None or not user.is_active:
        _unauthorized("Invalid or expired token")  # revocation is indistinguishable
    return {"user_id": user.id, "role": user.role}


def require_role(allowed_roles: list[str]):
    """Return a FastAPI dependency rejecting requests whose current DB role
    is not one of *allowed_roles*.

    Usage::

        @router.get("/secret")
        def secret_view(current_user = require_role(["admin"])):
            ...

    Raises 401 when the token is missing/invalid/expired or the user no
    longer exists / was deactivated; 403 when the live DB role is not in
    *allowed_roles*.
    """

    def _dep(
        credentials: HTTPAuthorizationCredentials = Depends(_scheme),
        db: Session = Depends(get_session),
    ) -> dict:
        """Inner dep — called by FastAPI for every protected route."""
        user = _authenticate(credentials, db)
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return _dep


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_scheme),
    db: Session = Depends(get_session),
) -> dict:
    """FastAPI dependency resolving the Bearer JWT to the live User row,
    WITHOUT a role check (public ``GET /api/auth/me``, C6 role-agnostic).

    Raises 401 with the same semantics as an invalid token when the token is
    missing/invalid/expired or the user no longer exists / was deactivated.
    """
    return _authenticate(credentials, db)
