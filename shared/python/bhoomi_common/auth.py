"""
bhoomi_common.auth – JWT verification middleware and Keycloak integration.

Verifies RS256 JWTs issued by the Bhoomi Dhrishti Keycloak realm.
Extracts roles, purpose-bound claims, and actor metadata.

Usage:
    from bhoomi_common.auth import require_roles, get_current_actor

    @router.get("/parcels/{id}")
    async def get_parcel(
        id: UUID,
        actor: Actor = Depends(get_current_actor),
        _: None = Depends(require_roles(["revenue_officer", "district_collector"])),
    ):
        ...
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Dict, List, Optional, Set

import httpx
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwt
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

KEYCLOAK_JWKS_URL     = os.environ.get("KEYCLOAK_JWKS_URL", "")
KEYCLOAK_REALM        = os.environ.get("KEYCLOAK_REALM", "bhoomi-dhrishti")
KEYCLOAK_HOST         = os.environ.get("KEYCLOAK_HOST", "keycloak")
KEYCLOAK_PORT         = os.environ.get("KEYCLOAK_PORT", "8080")
JWT_ALGORITHM         = os.environ.get("JWT_ALGORITHM", "RS256")
JWT_AUDIENCE          = os.environ.get("KEYCLOAK_CLIENT_ID", "service-account")

_BEARER_SCHEME = HTTPBearer(auto_error=False)


# ─────────────────────────────────────────────────────────────────────────────
# Actor model
# ─────────────────────────────────────────────────────────────────────────────

class Actor(BaseModel):
    """Authenticated principal extracted from the JWT."""
    subject: str                    # Keycloak subject (UUID)
    email: Optional[str] = None
    name: Optional[str] = None
    roles: Set[str] = set()
    preferred_username: Optional[str] = None
    state_code: Optional[str] = None    # From custom Keycloak claim 'state_lgd_code'
    district_code: Optional[str] = None
    purpose: Optional[str] = None       # Purpose-bound access claim
    session_id: Optional[str] = None

    model_config = {"arbitrary_types_allowed": True}

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def has_any_role(self, roles: List[str]) -> bool:
        return bool(self.roles.intersection(set(roles)))

    def has_all_roles(self, roles: List[str]) -> bool:
        return set(roles).issubset(self.roles)


# ─────────────────────────────────────────────────────────────────────────────
# JWKS key cache
# ─────────────────────────────────────────────────────────────────────────────

_jwks_cache: Optional[Dict] = None


async def _fetch_jwks() -> Dict:
    """Fetch and cache JWKS from Keycloak."""
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache

    jwks_url = KEYCLOAK_JWKS_URL or (
        f"http://{KEYCLOAK_HOST}:{KEYCLOAK_PORT}"
        f"/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs"
    )
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(jwks_url)
            response.raise_for_status()
            _jwks_cache = response.json()
            return _jwks_cache
    except Exception as exc:
        logger.error("Failed to fetch JWKS from %s: %s", jwks_url, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        ) from exc


def _invalidate_jwks_cache() -> None:
    """Force re-fetch of JWKS on next request (call after key rotation)."""
    global _jwks_cache
    _jwks_cache = None


# ─────────────────────────────────────────────────────────────────────────────
# Token verification
# ─────────────────────────────────────────────────────────────────────────────

async def _verify_token(token: str) -> Actor:
    """
    Verify a JWT bearer token against Keycloak's JWKS.
    Returns an Actor on success; raises HTTPException on failure.
    """
    try:
        jwks = await _fetch_jwks()

        # Decode header to find key ID
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        # Find matching public key
        rsa_key = None
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                rsa_key = key
                break

        if rsa_key is None:
            # Kid not found – key may have rotated; invalidate cache and retry once
            _invalidate_jwks_cache()
            jwks = await _fetch_jwks()
            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    rsa_key = key
                    break

        if rsa_key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find appropriate signing key",
            )

        issuer = (
            f"http://{KEYCLOAK_HOST}:{KEYCLOAK_PORT}/realms/{KEYCLOAK_REALM}"
        )
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=[JWT_ALGORITHM],
            issuer=issuer,
            options={"verify_aud": False},  # Audience verified per endpoint
        )

        # Extract realm roles from Keycloak token structure
        realm_access = payload.get("realm_access", {})
        roles: Set[str] = set(realm_access.get("roles", []))

        return Actor(
            subject=payload["sub"],
            email=payload.get("email"),
            name=payload.get("name"),
            preferred_username=payload.get("preferred_username"),
            roles=roles,
            state_code=payload.get("state_lgd_code"),
            district_code=payload.get("district_lgd_code"),
            purpose=payload.get("purpose"),
            session_id=payload.get("sid"),
        )

    except ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        ) from exc
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        ) from exc


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI dependencies
# ─────────────────────────────────────────────────────────────────────────────

async def get_current_actor(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_BEARER_SCHEME),
) -> Actor:
    """
    FastAPI dependency: verify bearer token and return the authenticated Actor.
    Raises HTTP 401 if no valid token is present.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await _verify_token(credentials.credentials)


async def get_optional_actor(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_BEARER_SCHEME),
) -> Optional[Actor]:
    """
    FastAPI dependency: return Actor if valid bearer token provided, else None.
    Use for endpoints that are public but provide additional data when authenticated.
    """
    if credentials is None:
        return None
    try:
        return await _verify_token(credentials.credentials)
    except HTTPException:
        return None


def require_roles(required_roles: List[str]):
    """
    FastAPI dependency factory: raise HTTP 403 if the actor does not have
    at least one of the required roles.

    Usage:
        @router.delete("/parcels/{id}", dependencies=[Depends(require_roles(["system_admin"]))])
    """
    async def _check_roles(actor: Actor = Depends(get_current_actor)) -> Actor:
        if not actor.has_any_role(required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {required_roles}. Actor has: {list(actor.roles)}",
            )
        return actor
    return _check_roles


def require_purpose(allowed_purposes: List[str]):
    """
    FastAPI dependency factory: enforce purpose-bound access.
    Purpose-bound tokens carry a 'purpose' claim (e.g. 'LOAN_VERIFICATION').
    """
    async def _check_purpose(actor: Actor = Depends(get_current_actor)) -> Actor:
        if actor.purpose is None or actor.purpose not in allowed_purposes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This endpoint requires a purpose-bound token with purpose in {allowed_purposes}",
            )
        return actor
    return _check_purpose
