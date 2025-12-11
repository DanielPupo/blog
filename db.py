import mysql.connector
from werkzeug.security import check_password_hash
from config import * # importando as variáveis do config.py


# Função para se conectar ao Banco de Dados SQL
def conectar():
    conexao = mysql.connector.connect(
        host=HOST,   # variável do config.py
        user=USER,   # variável do config.py
        password=PASSWORD,   # variável do config.py
        database=DATABASE   # variável do config.py
    )
    if conexao.is_connected():
        print("Conexão com BD OK!")
    
    return conexao

def listar_post():
    conexao = conectar()
    try:
        with conectar() as conexao:
            cursor = conexao.cursor(dictionary=True)
            cursor.execute("SELECT p.*, u.user, u.picture FROM posts p INNER JOIN users u ON u.idUser = p.idUser WHERE u.ativo = 1 ORDER BY idPost DESC")
            return cursor.fetchall()
    except mysql.connector.Error as erro:
        print(f"Erro de BD! Erro: {erro}")
        return []

        
def listar_usuarios():
    conexao = conectar()
    try:
        with conectar() as conexao:
            cursor = conexao.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users")
            usuarios = cursor.fetchall()
            return usuarios
    except mysql.connector.Error as erro:
        print(f"Erro de BD! Erro: {erro}")
        return []
        
def adicionar_post(title, content, idUser):
    conexao = conectar()
    try:
        with conectar() as conexao:
            cursor = conexao.cursor()
            sql = "INSERT INTO posts (title, content, idUser) VALUES (%s, %s, %s)"
            cursor.execute(sql, (title, content, idUser))
            conexao.commit()
            return True
    except mysql.connector.Error as erro:
        conexao.rollback()
        print(f"Erro de BD! Erro: {erro}")
        return False
   
def editar_post(idPost, title, content):
    conexao = conectar()
    try:
        with conectar() as conexao:
            cursor = conexao.cursor()
            sql = "UPDATE posts SET title = %s, content = %s WHERE idPost = %s"
            cursor.execute(sql, (title, content, idPost))
            conexao.commit()
            return True
    except mysql.connector.Error as erro:
        conexao.rollback()
        print(f"Erro de BD! Erro: {erro}")
        return False
   
def adicionar_usuarios(name, user, password_hash, foto):
    try:
        with conectar() as conexao:
            cursor = conexao.cursor()
            sql = "INSERT INTO users (`name`, `user`, `password`, `picture`, `ativo`) VALUES (%s,%s,%s,%s,1)"
            cursor.execute(sql, (name, user, password_hash, foto))
            conexao.commit()
            return True, None
    except mysql.connector.Error as err:
        print("DB error adicionar_usuarios:", err)
        return False, err
    except Exception as e:
        print("Unexpected error adicionar_usuarios:", e)
        return False, e
    
def verificar_usuario(user, password):
    try:
        with conectar() as conexao:
            cursor = conexao.cursor(dictionary=True)
            sql = "SELECT * FROM users WHERE user = %s;"
            cursor.execute(sql, (user,))
            usuario_encontrado = cursor.fetchone()
            if not usuario_encontrado:
                return False, None, False

            senha_armazenada = usuario_encontrado.get('password') or ''
            # detectar se a senha é a padrão '1234'
            padrao = False
            if senha_armazenada == '1234' or (senha_armazenada and check_password_hash(senha_armazenada, '1234')):
                padrao = True

            # validar credenciais:
            if senha_armazenada == password or (senha_armazenada and check_password_hash(senha_armazenada, password)):
                return True, usuario_encontrado, padrao

            return False, None, False
    except mysql.connector.Error as erro:
        print(f"Erro de BD! Erro: {erro}")
        return False, None, False

def alterar_status(idUser):
    try:
        with conectar() as conexao:
            cursor = conexao.cursor(dictionary=True)
            sql = "SELECT ativo FROM users WHERE idUser = %s;"
            cursor.execute(sql, (idUser,))
            status = cursor.fetchone()
            
            if status['ativo']:
                sql = "UPDATE users SET ativo = 0 WHERE idUser = %s"
            else:
                sql = "UPDATE users SET ativo = 1 WHERE idUser = %s"
                
            cursor.execute(sql, (idUser,))
            conexao.commit()
            return True
    except mysql.connector.Error as erro:
        conexao.rollback()
        print(f"ERRO DE BD! Erro: {erro}")
        return False, None
        
def delete_usuario(idUser):
    try: 
        with conectar() as conexao:
            cursor = conexao.cursor(dictionary=True)
            sql = "DELETE FROM users WHERE idUser = %s;"
            cursor.execute(sql, (idUser,))
            conexao.commit()
            return True
    except mysql.connector.Error as erro:
        conexao.rollback()
        print(f"ERRO DE BD! Erro: {erro}")
        return False
    
def atualizar_post(idPost, title, content):
    try:
        with conectar() as conexao:
            cursor = conexao.cursor()
            sql = "UPDATE posts SET title = %s, content = %s WHERE idPost = %s"
            cursor.execute(sql, (title, content, idPost))
            conexao.commit()
            return True
    except mysql.connector.Error as erro:
        conexao.rollback()
        print(f"Erro de BD! Erro: {erro}")
        return False
    
def totais():
    try:
        with conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute("SELECT * FROM vw_total_posts")
            total_posts = cursor.fetchone()

            cursor.execute("SELECT * FROM vw_usuarios")
            total_usuarios = cursor.fetchone()
            
            return total_posts, total_usuarios
        
    except mysql.connector.Error as erro:
        print(f"Erro de BD! Erro: {erro}")
        return None, None
    
def reset_senha(idUser):
    try:
        with conectar() as conexao:
            cursor = conexao.cursor()
            senha_hash = check_password_hash('1234')
            sql = "UPDATE users SET password = %s WHERE idUser = %s"
            cursor.execute(sql, (senha_hash, idUser))
            conexao.commit()
            return True
    except mysql.connector.Error as erro:
        print(f"Erro de BD! Erro: {erro}")
        conexao.rollback()
        return False
    
def alterar_senha(senha_hash, idUser):
    try:
        with conectar() as conexao:
            cursor = conexao.cursor(dictionary=True)
            sql = "UPDATE users SET password = %s WHERE idUser = %s"
            cursor.execute(sql, (senha_hash, idUser))
            conexao.commit()
            return True
    except mysql.connector.Error as erro:
        print(f"Erro de BD! Erro: {erro}")
        conexao.rollback()
        return False
    
def editar_perfil(name, user, nome_foto, idUser):
    try:
        with conectar() as conexao:
            cursor = conexao.cursor(dictionary=True)
            if nome_foto:
                sql = "UPDATE users SET name = %s, user = %s, picture = %s WHERE idUser = %s"
                cursor.execute(sql, (name, user, nome_foto, idUser))
            else: 
                sql = "UPDATE users SET name = %s, user = %s WHERE idUser = %s"
                cursor.execute(sql, (name, user,  idUser))
            conexao.commit()
            return True
    except mysql.connector.Error as erro:
        print(f"Erro de BD! Erro: {erro}")
        conexao.rollback()
        return False