"""Configuração exclusivamente por variáveis de ambiente."""

from __future__ import annotations

import os
from pathlib import Path


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


ROOT = Path(__file__).resolve().parent
IS_VERCEL = bool(os.getenv("VERCEL"))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "blog_pupo")
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
    required = {
        "SECRET_KEY": Config.SECRET_KEY if Config.SECRET_KEY != "dev-only-change-me" else "",
        "ADMIN_PASSWORD_HASH": Config.ADMIN_PASSWORD_HASH,
        "DB_HOST": os.getenv("DB_HOST", ""),
        "DB_USER": os.getenv("DB_USER", ""),
        "DB_PASSWORD": os.getenv("DB_PASSWORD", ""),
        "DB_NAME": os.getenv("DB_NAME", ""),
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError(f"Variáveis obrigatórias ausentes na Vercel: {', '.join(missing)}")
