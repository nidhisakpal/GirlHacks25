import os
import jwt
from typing import Dict, Any
from fastapi import HTTPException, status
import httpx

async def verify_token(token: str) -> Dict[str, Any]:
    """Verify Auth0 JWT token and return user information"""
    try:
        # Get Auth0 domain from environment
        auth0_domain = os.getenv("AUTH0_DOMAIN")
        if not auth0_domain:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Auth0 domain not configured"
            )
        
        # Get Auth0 public key
        jwks_url = f"https://{auth0_domain}/.well-known/jwks.json"
        
        async with httpx.AsyncClient() as client:
            jwks_response = await client.get(jwks_url)
            jwks = jwks_response.json()
        
        # Decode and verify token
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = None
        
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
                break
        
        if rsa_key:
            try:
                payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=["RS256"],
                    audience=os.getenv("AUTH0_AUDIENCE"),
                    issuer=f"https://{auth0_domain}/"
                )
                return payload
            except jwt.ExpiredSignatureError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired"
                )
            except jwt.JWTClaimsError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token claims"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find appropriate key"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}"
        )
