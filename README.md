# Blog PBE

Bem-vindo ao projeto **Blog PBE**!

Este é um sistema de blog desenvolvido em Python utilizando o framework Flask, com autenticação de usuários, painel administrativo, upload de imagens e gerenciamento de postagens. O projeto foi desenvolvido por Daniel Pupo.

## Deploy e Repositório

- **GitHub do Projeto:** [https://github.com/danielpupo/blog-pbe](https://github.com/danielpupo/blog-pbe)
- **Vercel do Projeto:** [https://blog-pbe-danielpupo.vercel.app](https://blog-pbe-danielpupo.vercel.app)

Para clonar o projeto:
```bash
git clone https://github.com/danielpupo/blog-pbe.git
```

## Índice
- [Sobre o Projeto](#sobre-o-projeto)
- [Funcionalidades](#funcionalidades)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Como Usar](#como-usar)
- [Estrutura de Pastas](#estrutura-de-pastas)
- [Créditos](#créditos)

---

## Sobre o Projeto
O Blog PBE é uma aplicação web para publicação de postagens, com autenticação de usuários, painel administrativo, upload de fotos de perfil e gerenciamento de posts. O sistema permite que usuários criem contas, façam login, publiquem, editem e excluam postagens, além de alterar informações do perfil e redefinir senhas.

## Funcionalidades
- Cadastro e login de usuários
- Autenticação de administrador
- Publicação, edição e exclusão de postagens
- Upload de imagem de perfil
- Painel administrativo com visão geral de usuários e posts
- Reset e alteração de senha
- Mensagens de feedback para ações do usuário
- Tratamento de erros 404 e 500

## Tecnologias Utilizadas
- **Python 3.x**
- **Flask**
- **MySQL** (banco de dados)
- **Werkzeug** (hash de senha e upload seguro)
- **HTML5, CSS3** (templates e estilos)

## Instalação
1. Clone este repositório:
   ```bash
   git clone <url-do-repositorio>
   ```
2. Instale as dependências necessárias:
   ```bash
   pip install flask mysql-connector-python werkzeug
   ```
3. Configure o banco de dados MySQL utilizando o script `scriptBD.sql`.
4. Configure as variáveis de ambiente em `config.py`:
   - `SECRET_KEY`
   - `USUARIO_ADMIN`
   - `SENHA_ADMIN`
   - Dados de conexão do banco

## Configuração
- Certifique-se de que o banco de dados está rodando e as credenciais estão corretas em `config.py`.
- O diretório `static/uploads` será criado automaticamente para armazenar as imagens de perfil.

## Como Usar
1. Execute o arquivo principal:
   ```bash
   python app.py
   ```
2. Acesse o sistema pelo navegador em `http://localhost:5000`
3. Cadastre-se ou faça login como administrador para acessar o painel.

## Estrutura de Pastas
```
app.py
config.py
db.py
scriptBD.sql
teste.py
static/
    style.css
    img/
        Nova pasta/
    uploads/
        images.jfif
templates/
    base.html
    dashboard.html
    e404.html
    e500.html
    index.html
    login.html
    nova_senha.html
    profile.html
    sign-up.html
```

- **app.py**: Arquivo principal da aplicação Flask
- **config.py**: Configurações e variáveis de ambiente
- **db.py**: Funções de acesso ao banco de dados
- **scriptBD.sql**: Script para criação das tabelas no MySQL
- **static/**: Arquivos estáticos (CSS, imagens, uploads)
- **templates/**: Templates HTML do sistema

## Créditos
Desenvolvido por **Daniel Pupo**

- [GitHub: danielpupo](https://github.com/danielpupo)
- [Vercel: blog-pbe-danielpupo.vercel.app](https://blog-pbe-danielpupo.vercel.app)

---

Sinta-se à vontade para contribuir ou sugerir melhorias!