"""CashLab — Auth service (register, login, social login, tokens)"""
import logging
from typing import Optional, Tuple

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)
from app.models import User, FamilyGroup, Member

logger = logging.getLogger(__name__)


# ── Tokens ─────────────────────────────────────────────────────────

def generate_tokens(user: User) -> dict:
    """Gera par de tokens (access + refresh) para o usuário"""
    token_data = {"sub": str(user.id), "email": user.email}
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
    }


# ── Register (email/senha) ────────────────────────────────────────

async def register_user(
    db: AsyncSession,
    name: str,
    email: str,
    password: str,
) -> User:
    """
    Registra novo usuário com email/senha.
    Também cria um FamilyGroup e os membros padrão.
    """
    # Verificar se email já existe
    result = await db.execute(select(User).where(User.email == email))
    existing = result.scalar_one_or_none()
    if existing:
        raise ValueError("Email já cadastrado")

    # Criar family group
    family = FamilyGroup(name=f"Família de {name}")
    db.add(family)
    await db.flush()

    # Criar membros padrão
    members_data = [
        {"name": "LUCAS", "color": "#4A90D9"},
        {"name": "JURA", "color": "#E94E77"},
        {"name": "JOICE", "color": "#50C878"},
    ]
    for m_data in members_data:
        member = Member(family_group_id=family.id, **m_data)
        db.add(member)

    # Criar usuário
    user = User(
        email=email,
        password_hash=hash_password(password),
        name=name,
        family_group_id=family.id,
        auth_provider="email",
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


# ── Login (email/senha) ───────────────────────────────────────────

async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> User:
    """
    Autentica por email/senha. Retorna User ou levanta ValueError.
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise ValueError("Credenciais inválidas")

    if not user.password_hash:
        raise ValueError(
            f"Esta conta usa login social ({user.auth_provider}). "
            "Use o botão correspondente para entrar."
        )

    if not verify_password(password, user.password_hash):
        raise ValueError("Credenciais inválidas")

    if not user.is_active:
        raise ValueError("Usuário inativo")

    return user


# ── Social Login (Google / Apple) ──────────────────────────────────

async def authenticate_social(
    db: AsyncSession,
    provider: str,
    id_token: str,
) -> User:
    """
    Autentica via social login (Google ou Apple).
    - Valida o id_token com o provedor
    - Se o usuário já existe → retorna
    - Se não existe → cria automaticamente (auto-register)
    """
    if provider == "google":
        user_info = await _verify_google_token(id_token)
    elif provider == "apple":
        user_info = await _verify_apple_token(id_token)
    else:
        raise ValueError(f"Provedor não suportado: {provider}")

    email = user_info["email"]
    name = user_info.get("name", email.split("@")[0])
    provider_id = user_info.get("sub", "")
    avatar_url = user_info.get("picture")

    # Buscar usuário existente por email
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user:
        # Atualizar info do provedor se mudou
        if user.provider_id != provider_id and provider_id:
            user.provider_id = provider_id
        if avatar_url and user.avatar_url != avatar_url:
            user.avatar_url = avatar_url
        await db.commit()
        await db.refresh(user)
    else:
        # Auto-register: criar usuário + family group
        family = FamilyGroup(name=f"Família de {name}")
        db.add(family)
        await db.flush()

        # Criar membros padrão
        members_data = [
            {"name": "LUCAS", "color": "#4A90D9"},
            {"name": "JURA", "color": "#E94E77"},
            {"name": "JOICE", "color": "#50C878"},
        ]
        for m_data in members_data:
            member = Member(family_group_id=family.id, **m_data)
            db.add(member)

        user = User(
            email=email,
            name=name,
            password_hash=None,  # Social users não têm senha local
            family_group_id=family.id,
            auth_provider=provider,
            provider_id=provider_id,
            avatar_url=avatar_url,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    if not user.is_active:
        raise ValueError("Usuário inativo")

    return user


# ── Refresh Token ──────────────────────────────────────────────────

async def refresh_access_token(
    db: AsyncSession,
    refresh_token: str,
) -> Tuple[str, User]:
    """
    Valida o refresh token e gera novo access token.
    Retorna (novo_access_token, user).
    """
    payload = decode_token(refresh_token)
    if payload is None:
        raise ValueError("Refresh token inválido ou expirado")

    if payload.get("type") != "refresh":
        raise ValueError("Token fornecido não é um refresh token")

    user_id = payload.get("sub")
    if not user_id:
        raise ValueError("Token sem identificação de usuário")

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise ValueError("Usuário não encontrado")

    if not user.is_active:
        raise ValueError("Usuário inativo")

    new_access_token = create_access_token(
        {"sub": str(user.id), "email": user.email}
    )
    return new_access_token, user


# ── Provider Token Verification ────────────────────────────────────

async def _verify_google_token(id_token: str) -> dict:
    """
    Valida Google id_token chamando o endpoint tokeninfo do Google.
    Retorna dict com email, name, sub, picture.
    
    Em produção, usa GOOGLE_CLIENT_ID para verificar audience.
    Em dev (sem CLIENT_ID configurado), apenas decodifica o token.
    """
    try:
        # Chamar Google tokeninfo para validar
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": id_token},
            )

        if response.status_code != 200:
            raise ValueError(f"Google rejeitou o token: {response.text}")

        data = response.json()

        # Verificar audience se GOOGLE_CLIENT_ID está configurado
        if settings.GOOGLE_CLIENT_ID:
            if data.get("aud") != settings.GOOGLE_CLIENT_ID:
                raise ValueError("Token não é destinado a esta aplicação (audience inválido)")

        # Verificar se o email foi validado pelo Google
        if data.get("email_verified") != "true":
            raise ValueError("Email não verificado pelo Google")

        return {
            "email": data["email"],
            "name": data.get("name", data["email"].split("@")[0]),
            "sub": data.get("sub", ""),
            "picture": data.get("picture"),
        }

    except httpx.RequestError as e:
        logger.error(f"Erro ao contatar Google: {e}")
        raise ValueError("Erro ao validar token com Google. Tente novamente.")


async def _verify_apple_token(id_token: str) -> dict:
    """
    Valida Apple id_token decodificando o JWT com as chaves públicas da Apple.
    Retorna dict com email, name, sub.
    
    Em produção, usa APPLE_BUNDLE_ID para verificar audience.
    Em dev (sem config), apenas decodifica as claims.
    """
    try:
        from jose import jwt as jose_jwt

        # Buscar chaves públicas da Apple
        async with httpx.AsyncClient() as client:
            response = await client.get("https://appleid.apple.com/auth/keys")

        if response.status_code != 200:
            raise ValueError("Erro ao buscar chaves da Apple")

        apple_keys = response.json()

        # Decodificar header do token para encontrar o kid
        unverified_header = jose_jwt.get_unverified_header(id_token)
        kid = unverified_header.get("kid")

        if not kid:
            raise ValueError("Token Apple sem key ID (kid)")

        # Encontrar a chave correta
        key_data = None
        for key in apple_keys.get("keys", []):
            if key["kid"] == kid:
                key_data = key
                break

        if not key_data:
            raise ValueError("Chave pública da Apple não encontrada para este token")

        # Decodificar e validar o token
        audience = settings.APPLE_BUNDLE_ID if settings.APPLE_BUNDLE_ID else None
        decode_options = {}
        if not audience:
            decode_options["verify_aud"] = False

        payload = jose_jwt.decode(
            id_token,
            key_data,
            algorithms=["RS256"],
            audience=audience,
            issuer="https://appleid.apple.com",
            options=decode_options,
        )

        email = payload.get("email")
        if not email:
            raise ValueError("Token Apple não contém email")

        return {
            "email": email,
            "name": email.split("@")[0],  # Apple nem sempre envia o nome
            "sub": payload.get("sub", ""),
            "picture": None,  # Apple não fornece foto
        }

    except Exception as e:
        if isinstance(e, ValueError):
            raise
        logger.error(f"Erro ao validar token Apple: {e}")
        raise ValueError("Erro ao validar token com Apple. Tente novamente.")
