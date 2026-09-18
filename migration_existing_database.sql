-- Execute somente em uma cópia/backup do banco já existente.
USE blog_pupo;

ALTER TABLE users
  MODIFY name VARCHAR(50) NOT NULL,
  MODIFY user VARCHAR(15) NOT NULL,
  MODIFY password VARCHAR(255) NOT NULL,
  MODIFY picture VARCHAR(100) NOT NULL DEFAULT 'placeholder.svg',
  MODIFY ativo BOOLEAN NOT NULL DEFAULT TRUE;

UPDATE users SET picture = 'placeholder.svg' WHERE picture IS NULL OR picture = '';

CREATE INDEX idx_users_ativo ON users (ativo);
CREATE INDEX idx_posts_date ON posts (datePost);
CREATE INDEX idx_posts_user ON posts (idUser);
