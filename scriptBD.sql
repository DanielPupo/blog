DROP DATABASE IF EXISTS blog_pupo;

CREATE DATABASE blog_pupo;

USE blog_pupo;

CREATE TABLE users (
    idUser INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    user VARCHAR(15) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    picture VARCHAR(100),
    registrationDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status BOOLEAN NOT NULL DEFAULT 1
);
CREATE TABLE posts(
    idPost INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    datePost TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    idUser INT,
    FOREIGN KEY (idUser) REFERENCES users(idUser)
    ON DELETE CASCADE
);


ALTER TABLE users
ADD ativo BOOLEAN NOT NULL DEFAULT 1;


CREATE VIEW vw_total_posts AS
SELECT COUNT(*) AS total_posts FROM posts p
JOIN users u ON p.idUser = u.idUser
WHERE u.ativo = 1;

CREATE VIEW vw_usuarios AS
SELECT COUNT(*) AS total_usuarios FROM users u
WHERE ativo = 1;

--- AJUDAS ---

-- CADASTRAR USUÁRIO
-- INSERT INTO users (name, user, password) VALUES ('Nome do Usuário', 'usuario123', 'senha123');

-- PARA ZERAR A TABELA POSTS
-- TRUNCATE posts;

--UPDATE users SET picture = "fotouser.png" WHERE idUser = 1;