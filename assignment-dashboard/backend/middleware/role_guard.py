from fastapi import Header, HTTPException


async def require_admin(x_role: str = Header(default="user")) -> str:
    """FastAPI dependency — injects the caller's role from the X-Role header.

    Returns the role string. Write endpoints that need admin access should
    declare this as a dependency and will receive a 403 for non-admin callers.
    """
    if x_role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return x_role.lower()


async def get_role(x_role: str = Header(default="user")) -> str:
    """Read-only role extraction — never raises, always returns a role string.

    Use on read endpoints where you want to know the role but don't need to
    block non-admins.
    """
    return x_role.lower()
