from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.auth import (
    LoginRequest, 
    TokenResponse, 
    RefreshTokenRequest, 
    UserResponse
)
from app.services.auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    verify_token
)
from app.dependencies.access_control import get_current_user
from app.schemas.auth import TokenData

router = APIRouter(prefix="/api", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    """
    Authenticate user and return access + refresh tokens
    """
    user = authenticate_user(credentials.username, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    token_data = {
        "sub": user["username"],
        "role": user["role"]
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/logout")
async def logout(current_user: TokenData = Depends(get_current_user)):
    """
    Logout user (client should delete tokens)
    """
    return {
        "message": "Successfully logged out",
        "username": current_user.username
    }


@router.get("/verify", response_model=UserResponse)
async def verify(current_user: TokenData = Depends(get_current_user)):
    """
    Verify current access token and return user info
    """
    return UserResponse(
        username=current_user.username,
        role=current_user.role
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token
    """
    payload = verify_token(request.refresh_token, expected_type="refresh")
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new tokens
    token_data = {
        "sub": payload["username"],
        "role": payload["role"]
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )