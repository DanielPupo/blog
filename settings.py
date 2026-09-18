"""Configuração exclusivamente por variáveis de ambiente."""

from __future__ import annotations

import os
from pathlib import Path


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_value(name: str, default: str = "") -> str:
    """Ignora variáveis vazias, comuns em configurações parciais da Vercel."""
    value = os.getenv(name)
    return value.strip() if value and value.strip() else default


def env_int(name: str, default: int) -> int:
    value = env_value(name, str(default))
    try:
        return int(value)
    except ValueError as error:
        raise RuntimeError(f"A variável {name} precisa ser um número inteiro.") from error


ROOT = Path(__file__).resolve().parent
IS_VERCEL = bool(os.getenv("VERCEL"))


class Config:
    SECRET_KEY = env_value("SECRET_KEY", "dev-only-change-me")
    ADMIN_USERNAME = env_value("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD_HASH = env_value("ADMIN_PASSWORD_HASH")
    DATABASE_ENABLED = env_bool("DATABASE_ENABLED", not IS_VERCEL)
    ANONYMOUS_MODE = env_bool("ANONYMOUS_MODE", not DATABASE_ENABLED) or not DATABASE_ENABLED
    AUTH_ENABLED = DATABASE_ENABLED and not ANONYMOUS_MODE
    DB_HOST = env_value("DB_HOST", "localhost")
    DB_PORT = env_int("DB_PORT", 3306)
    DB_USER = env_value("DB_USER", "root")
    DB_PASSWORD = env_value("DB_PASSWORD")
    DB_NAME = env_value("DB_NAME", "blog_pupo")
    DEBUG = env_bool("FLASK_DEBUG") and not IS_VERCEL
    MAX_CONTENT_LENGTH = 3 * 1024 * 1024
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = IS_VERCEL or env_bool("SESSION_COOKIE_SECURE")
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 12
    ENABLE_LOCAL_UPLOADS = env_bool("ENABLE_LOCAL_UPLOADS", not IS_VERCEL)
    UPLOAD_FOLDER = os.getenv(
        "UPLOAD_FOLDER",
        str(Path(os.getenv("TEMP", "/tmp")) / "blog-uploads" if IS_VERCEL else ROOT / "public" / "static" / "uploads"),
    )


if IS_VERCEL:
    required = {"SECRET_KEY": Config.SECRET_KEY if Config.SECRET_KEY != "dev-only-change-me" else ""}
    if Config.DATABASE_ENABLED:
        required.update(
            DB_HOST=env_value("DB_HOST"),
            DB_USER=env_value("DB_USER"),
            DB_PASSWORD=env_value("DB_PASSWORD"),
            DB_NAME=env_value("DB_NAME"),
        )
    if Config.AUTH_ENABLED:
        required["ADMIN_PASSWORD_HASH"] = Config.ADMIN_PASSWORD_HASH
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError(f"Variáveis obrigatórias ausentes na Vercel: {', '.join(missing)}")
