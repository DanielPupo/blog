"""Camada de acesso a dados do blog com consultas parametrizadas."""

from __future__ import annotations

import hmac

import mysql.connector
from werkzeug.security import check_password_hash, generate_password_hash

from settings import Config


def conectar():
    if not Config.DATABASE_ENABLED:
        raise RuntimeError("O banco de dados está desativado neste ambiente.")
    return mysql.connector.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        connection_timeout=5,
    )


def _log_database_error(action: str, error: Exception) -> None:
    # Não registra SQL, senha nem dados pessoais.
    print(f"Falha de banco ao {action}: {type(error).__name__}")


def listar_posts():
    if not Config.DATABASE_ENABLED:
        return []
    try:
        with conectar() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """SELECT p.idPost, p.title, p.content, p.datePost, p.idUser,
                          u.user, u.picture
                   FROM posts p
                   INNER JOIN users u ON u.idUser = p.idUser
                   WHERE u.ativo = 1
                   ORDER BY p.datePost DESC, p.idPost DESC"""
            )
            return cursor.fetchall()
    except mysql.connector.Error as error:
        _log_database_error("listar posts", error)
        return []


def obter_post(post_id: int):
    if not Config.DATABASE_ENABLED:
        return None
    try:
        with conectar() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """SELECT p.idPost, p.title, p.content, p.datePost, p.idUser,
                          u.user, u.picture
                   FROM posts p
                   INNER JOIN users u ON u.idUser = p.idUser
                   WHERE p.idPost = %s AND u.ativo = 1""",
                (post_id,),
            )
            return cursor.fetchone()
    except mysql.connector.Error as error:
        _log_database_error("buscar post", error)
        return None


def adicionar_post(title: str, content: str, user_id: int) -> bool:
    if not Config.DATABASE_ENABLED:
        return False
    try:
        with conectar() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO posts (title, content, idUser) VALUES (%s, %s, %s)",
                (title, content, user_id),
            )
            connection.commit()
            return True
    except mysql.connector.Error as error:
        _log_database_error("adicionar post", error)
        return False


def atualizar_post(post_id: int, title: str, content: str) -> bool:
    if not Config.DATABASE_ENABLED:
        return False
    try:
        with conectar() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE posts SET title = %s, content = %s WHERE idPost = %s",
                (title, content, post_id),
            )
            connection.commit()
            return cursor.rowcount == 1
    except mysql.connector.Error as error:
        _log_database_error("atualizar post", error)
        return False


def excluir_post(post_id: int) -> bool:
    if not Config.DATABASE_ENABLED:
        return False
    try:
        with conectar() as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM posts WHERE idPost = %s", (post_id,))
            connection.commit()
            return cursor.rowcount == 1
    except mysql.connector.Error as error:
        _log_database_error("excluir post", error)
        return False


def listar_usuarios():
    if not Config.DATABASE_ENABLED:
        return []
    try:
        with conectar() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """SELECT idUser, name, user, picture, registrationDate, ativo
                   FROM users ORDER BY registrationDate DESC"""
            )
            return cursor.fetchall()
    except mysql.connector.Error as error:
        _log_database_error("listar usuários", error)
        return []


def obter_usuario(user_id: int):
    if not Config.DATABASE_ENABLED:
        return None
    try:
        with conectar() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT idUser, name, user, picture, registrationDate, ativo FROM users WHERE idUser = %s",
                (user_id,),
            )
            return cursor.fetchone()
    except mysql.connector.Error as error:
        _log_database_error("buscar usuário", error)
        return None


def adicionar_usuario(name: str, username: str, password_hash: str, picture: str):
    if not Config.DATABASE_ENABLED:
        return False, None
    try:
        with conectar() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """INSERT INTO users (name, user, password, picture, ativo)
                   VALUES (%s, %s, %s, %s, 1)""",
                (name, username, password_hash, picture),
            )
            connection.commit()
            return True, None
    except mysql.connector.Error as error:
        _log_database_error("adicionar usuário", error)
        return False, error


def verificar_usuario(username: str, password: str):
    if not Config.DATABASE_ENABLED:
        return False, None, False
    try:
        with conectar() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE user = %s", (username,))
            user = cursor.fetchone()
            if not user:
                return False, None, False

            stored = user.get("password") or ""
            is_hash = "$" in stored and ":" in stored
            valid = check_password_hash(stored, password) if is_hash else hmac.compare_digest(stored, password)
            if not valid:
                return False, None, False

            # Migração transparente de senhas antigas armazenadas em texto puro.
            if not is_hash:
                cursor.execute(
                    "UPDATE users SET password = %s WHERE idUser = %s",
                    (generate_password_hash(password), user["idUser"]),
                )
                connection.commit()
            return True, user, password == "1234"
    except (mysql.connector.Error, ValueError) as error:
        _log_database_error("verificar usuário", error)
        return False, None, False


def alterar_status(user_id: int) -> bool:
    if not Config.DATABASE_ENABLED:
        return False
    try:
        with conectar() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE users SET ativo = NOT ativo WHERE idUser = %s", (user_id,))
            connection.commit()
            return cursor.rowcount == 1
    except mysql.connector.Error as error:
        _log_database_error("alterar status", error)
        return False


def excluir_usuario(user_id: int) -> bool:
    if not Config.DATABASE_ENABLED:
        return False
    try:
        with conectar() as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM users WHERE idUser = %s", (user_id,))
            connection.commit()
            return cursor.rowcount == 1
    except mysql.connector.Error as error:
        _log_database_error("excluir usuário", error)
        return False


def totais():
    if not Config.DATABASE_ENABLED:
        return (0,), (0,)
    try:
        with conectar() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM posts p JOIN users u ON p.idUser = u.idUser WHERE u.ativo = 1")
            total_posts = cursor.fetchone()
            cursor.execute("SELECT COUNT(*) FROM users WHERE ativo = 1")
            total_users = cursor.fetchone()
            return total_posts, total_users
    except mysql.connector.Error as error:
        _log_database_error("calcular totais", error)
        return (0,), (0,)


def reset_senha(user_id: int) -> bool:
    return alterar_senha(generate_password_hash("1234"), user_id)


def alterar_senha(password_hash: str, user_id: int) -> bool:
    if not Config.DATABASE_ENABLED:
        return False
    try:
        with conectar() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE users SET password = %s WHERE idUser = %s", (password_hash, user_id))
            connection.commit()
            return cursor.rowcount == 1
    except mysql.connector.Error as error:
        _log_database_error("alterar senha", error)
        return False


def editar_perfil(name: str, username: str, picture: str, user_id: int) -> bool:
    if not Config.DATABASE_ENABLED:
        return False
    try:
        with conectar() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE users SET name = %s, user = %s, picture = %s WHERE idUser = %s",
                (name, username, picture, user_id),
            )
            connection.commit()
            return cursor.rowcount == 1
    except mysql.connector.Error as error:
        _log_database_error("editar perfil", error)
        return False
