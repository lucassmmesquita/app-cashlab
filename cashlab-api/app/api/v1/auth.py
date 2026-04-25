"""CashLab — Auth endpoints (register, login, social, refresh, me)"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db, get_current_user
from app.schemas.auth import (
    LoginRequest, LoginResponse,
    RegisterRequest,
    SocialLoginRequest,
    TokenRefreshRequest, TokenRefreshResponse,
    UserResponse,
)
from app.services.auth_service import (
    register_user, authenticate_user,
    authenticate_social,
    refresh_access_token, generate_tokens,
)

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Cadastro de usuário com email/senha.
    Cria automaticamente um FamilyGroup e membros padrão.
    Retorna tokens JWT para login imediato.
    """
    try:
        user = await register_user(db, request.name, request.email, request.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    tokens = generate_tokens(user)
    return LoginResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Login com email/senha. Retorna access_token + refresh_token.
    """
    try:
        user = await authenticate_user(db, request.email, request.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    tokens = generate_tokens(user)
    return LoginResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        user=UserResponse.model_validate(user),
    )


@router.post("/social", response_model=LoginResponse)
async def social_login(request: SocialLoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Login via Google ou Apple.
    
    O frontend (Expo) faz o OAuth e envia o id_token.
    O backend valida o token com o provedor, cria o usuário se não existir,
    e retorna tokens JWT.
    
    Providers suportados: "google", "apple"
    """
    try:
        user = await authenticate_social(db, request.provider, request.id_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    tokens = generate_tokens(user)
    return LoginResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(request: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    """
    Renovar access token usando o refresh token.
    O refresh token continua válido — não é rotacionado.
    """
    try:
        new_access_token, user = await refresh_access_token(db, request.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return TokenRefreshResponse(access_token=new_access_token)


@router.get("/me", response_model=UserResponse)
async def me(user=Depends(get_current_user)):
    """
    Retorna dados do usuário autenticado.
    Requer Bearer token no header Authorization.
    """
    return UserResponse.model_validate(user)
