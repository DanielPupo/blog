# Pupo's Blog — versão refatorada

Blog editorial em Flask, preparado para execução local e deploy na Vercel. Em produção ele pode operar em modo visitante sem banco de dados; MySQL, cadastro e publicação podem ser ativados depois.

Repositório: `https://github.com/DanielPupo/blog`

```bash
git clone https://github.com/DanielPupo/blog.git
```

## Rodar localmente

1. Crie e ative um ambiente virtual Python 3.13.
2. Instale as dependências: `pip install -r requirements.txt`.
3. Copie `.env.example` para `.env` e preencha os valores. O Flask não carrega `.env` sozinho; exporte as variáveis no terminal ou instale `python-dotenv` apenas no ambiente local.
4. Para usar contas e publicações, defina `DATABASE_ENABLED=true`, `ANONYMOUS_MODE=false` e crie o banco com `scriptBD.sql`.
5. Para testar apenas a interface pública, mantenha `DATABASE_ENABLED=false` e `ANONYMOUS_MODE=true`.
6. Execute `flask --app app run --debug`.

Para testar: `python -m unittest discover -s tests -v`.

## Deploy na Vercel

1. Importe este diretório/repositório no painel da Vercel.
2. Não configure Build Command nem Output Directory; a Vercel detecta `app.py`.
3. Para o modo visitante, cadastre `SECRET_KEY`, `ANONYMOUS_MODE=true`, `DATABASE_ENABLED=false`, `ENABLE_LOCAL_UPLOADS=false` e `FLASK_DEBUG=false`.
4. Um MySQL externo só é necessário para habilitar contas e conteúdo persistente. Nesse caso, preencha as variáveis `DB_*`, use `DATABASE_ENABLED=true` e `ANONYMOUS_MODE=false`.
5. Após o deploy, teste `/healthz` e `/sitemap.xml`. O healthcheck informa explicitamente o modo e o estado do banco.

Arquivos estáticos ficam em `public/static`, o diretório recomendado pela Vercel. O Flask usa o mesmo diretório localmente, mantendo as URLs em `/static/...`.

## Uploads na Vercel

O sistema desativa uploads locais quando `VERCEL` está presente, porque o filesystem de uma Function não é armazenamento persistente. Para produção, conecte Vercel Blob, Cloudinary, S3 ou serviço equivalente e grave apenas a URL no campo `picture`. A edição de nome e usuário continua funcionando.

## Segurança

- formulários protegidos por token CSRF;
- ações destrutivas apenas com `POST`;
- consultas SQL parametrizadas;
- saída HTML escapada automaticamente pelo Jinja;
- conteúdo dos posts tratado como texto, sem `safe` e sem HTML/Markdown arbitrário;
- headers CSP, frame, MIME, referrer e permissions;
- senha administrativa armazenada apenas como hash em variável de ambiente;
- modo visitante sem acesso ao banco e sem formulário de credenciais;
- cookies `HttpOnly`, `SameSite=Lax` e `Secure` na Vercel.

Leia `AUDITORIA_E_GUIA.md` para entender e personalizar cada etapa.
