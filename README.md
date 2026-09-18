# Pupo's Blog — versão refatorada

Blog editorial em Flask e MySQL, preparado para execução local e deploy na Vercel.

Repositório: `https://github.com/DanielPupo/blog`

```bash
git clone https://github.com/DanielPupo/blog.git
```

## Rodar localmente

1. Crie e ative um ambiente virtual Python 3.13.
2. Instale as dependências: `pip install -r requirements.txt`.
3. Copie `.env.example` para `.env` e preencha os valores. O Flask não carrega `.env` sozinho; exporte as variáveis no terminal ou instale `python-dotenv` apenas no ambiente local.
4. Crie o banco com `scriptBD.sql`.
5. Execute `flask --app app run --debug`.

Para testar: `python -m unittest discover -s tests -v`.

## Deploy na Vercel

1. Importe este diretório/repositório no painel da Vercel.
2. Não configure Build Command nem Output Directory; a Vercel detecta `app.py`.
3. Cadastre todas as chaves de `.env.example` em **Settings → Environment Variables**.
4. Use um MySQL externo acessível por TLS e permita conexões da aplicação.
5. Após o deploy, teste `/healthz`, `/sitemap.xml`, login e uma leitura de artigo.

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
- cookies `HttpOnly`, `SameSite=Lax` e `Secure` na Vercel.

Leia `AUDITORIA_E_GUIA.md` para entender e personalizar cada etapa.
