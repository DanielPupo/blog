# Auditoria e guia de manutenção

## Resumo executivo

O projeto original é Flask/Python + MySQL, não React/Next.js. A refatoração preserva essa arquitetura e corrige primeiro os riscos que poderiam causar invasão, perda de dados ou falha de deploy. O domínio informado `blog-2sk5.vercel.app` retornava `404 NOT_FOUND` durante a auditoria; portanto, além do código, o projeto da Vercel precisa ser ligado ao repositório/branch correto.

Prioridades encontradas:

1. **Crítico — segredos:** `.env` estava versionado no GitHub. Revogue e troque imediatamente todos os valores antigos, inclusive banco, `SECRET_KEY` e senha administrativa. Apagar o arquivo no commit atual não remove o histórico.
2. **Crítico — autorização e CSRF:** exclusão, bloqueio e reset usavam `GET`, algumas rotas verificavam apenas se havia qualquer sessão e não existia token CSRF.
3. **Alto — SQL e senhas:** consultas montadas com f-string permitiam injeção; o reset de senha chamava a função de verificação em vez da função de geração; a senha de admin era comparada em texto puro.
4. **Alto — deploy:** faltavam `requirements.txt` e uma configuração explícita/reproduzível para Vercel. Upload em disco local não persiste em Functions.
5. **Médio — HTML e UX:** HTML inválido no `<head>`, links contendo botões, estilos inline, ausência de labels e pouca hierarquia de leitura.
6. **Médio — SEO e performance:** não havia página individual de artigo, canonical/Open Graph dinâmicos, sitemap, robots, política de cache ou script de progresso de leitura.

## Etapa 1 — Segurança e Vercel

### `settings.py` e `.env.example`

**O que fazem:** centralizam toda configuração em variáveis de ambiente. O código não contém credenciais reais.

**Por que:** facilita separar desenvolvimento, preview e produção e evita segredos no Git.

**Como personalizar:** `ANONYMOUS_MODE=true` e `DATABASE_ENABLED=false` publicam uma versão segura somente para leitura, sem MySQL. Para reativar contas, use um banco externo, inverta essas duas opções e gere um `ADMIN_PASSWORD_HASH`; nunca salve a senha em texto puro.

### `app.py`

**O que faz:** aplica CSRF a toda requisição que altera dados, exige usuário/admin nas rotas corretas, limita e normaliza entradas, valida a assinatura real de imagens e aplica headers de segurança. As sessões usam cookies seguros na Vercel.

**Por que:** esconder botões não protege rotas. A autorização precisa ocorrer no servidor; token CSRF impede que outro site envie formulários em nome do usuário.

**Como personalizar:** limites de texto estão nas chamadas `clean_text`; tamanho total do request e cookies ficam em `Config`. Ao adicionar um formulário `POST`, sempre inclua o input `csrf_token`.

### `db.py`

**O que faz:** concentra operações MySQL e usa `%s` com tuplas de parâmetros. Senhas antigas em texto puro são regravadas como hash no primeiro login válido.

**Por que:** parâmetros bloqueiam injeção SQL e uma camada única reduz duplicação e erros de transação.

**Como personalizar:** crie funções pequenas para novas consultas. Nunca concatene input em SQL; use placeholders do driver.

### `vercel.json`, `requirements.txt` e `public/static`

**O que fazem:** fixam dependências, excluem artefatos de desenvolvimento do bundle, adicionam headers na borda e colocam assets no diretório servido pela CDN da Vercel.

**Por que:** o deploy passa a ser reproduzível e CSS/JS/imagens podem ser cacheados por um ano por terem nome estável no projeto.

**Como personalizar:** ao mudar frequentemente um asset, altere o nome do arquivo ou adicione versionamento à URL para invalidar o cache. Não adicione rewrite legado: Flask é detectado automaticamente por `app.py`.

### Uploads

**O que faz:** localmente, salva em `public/static/uploads`. Na Vercel, bloqueia persistência local e mostra uma mensagem clara.

**Por que:** o filesystem de uma Function é efêmero. Uma implementação que “parece funcionar” pode perder a imagem após outra execução.

**Como personalizar:** substitua o bloco `pending_upload.save(...)` por upload para Blob/S3/Cloudinary e guarde a URL. Faça isso antes de habilitar fotos em produção.

## Etapa 2 — Código e estrutura

O projeto mantém `app.py`, `db.py`, `templates/` e o schema MySQL. A única mudança estrutural intencional foi mover assets para `public/static`, atendendo ao modelo atual da Vercel sem alterar as URLs usadas pelos templates.

- `app.py`: HTTP, sessão, validação e respostas.
- `db.py`: somente persistência.
- `settings.py`: somente ambiente/configuração. O `config.py` local antigo é preservado e ignorado.
- `templates/`: marcação sem estilos ou JavaScript inline.
- `public/static/`: CSS, JavaScript e imagens públicas.
- `tests/`: regressões de segurança e rotas essenciais.

Ao criar uma funcionalidade, comece pela função de banco, depois a rota e por fim o template. Isso mantém responsabilidades previsíveis.

## Etapa 3 — Design UI/UX

### Tipografia e identidade

O design usa serifas do sistema em títulos e sans-serif do sistema em interfaces. Isso cria contraste editorial sem baixar Google Fonts, reduzindo conexões, bloqueio de renderização e complexidade da CSP.

Personalize cores no começo de `public/static/style.css`. As variáveis `--paper`, `--ink`, `--accent` e `--moss` definem quase toda a identidade.

### Tema e responsividade

O tema inicial segue `prefers-color-scheme`; o botão salva a escolha em `localStorage`. Grids viram uma coluna abaixo de 760 px, tabelas ganham scroll horizontal e alvos interativos mantêm tamanho confortável.

Personalize breakpoints nos dois blocos `@media` finais. Preserve `prefers-reduced-motion` para acessibilidade.

### Leitura

Cada post agora tem URL própria (`/post/<id>`), metadados sociais, largura de linha controlada, corpo com ritmo tipográfico e barra de progresso no topo. O conteúdo continua texto puro e escapado, o que previne XSS.

Se adicionar Markdown no futuro, faça a conversão no servidor e sanitize a saída com uma allowlist rigorosa; nunca use `|safe` diretamente em conteúdo do usuário.

## Etapa 4 — SEO, cache e Core Web Vitals

- `base.html`: description, canonical, Open Graph e Twitter Card.
- `sitemap.xml` e `robots.txt`: descoberta pelos buscadores.
- dimensões explícitas em avatares: reduzem CLS.
- fontes do sistema: evitam FOIT e melhoram LCP.
- JavaScript pequeno com `defer`: protege INP.
- cache longo para assets e curto no conteúdo público; páginas com sessão usam `no-store`.

Para evoluir, adicione uma imagem Open Graph 1200×630 estática e monitore dados reais no Vercel Speed Insights antes de fazer micro-otimizações.

## Checklist de publicação

1. Revogar todos os segredos que apareceram no GitHub e limpar o histórico com ferramenta apropriada.
2. Aplicar `migration_existing_database.sql` primeiro em backup/homologação. Se um índice já existir, remova apenas a linha correspondente.
3. Configurar as variáveis da Vercel para Production e Preview.
4. Conectar o repositório e branch corretos; confirmar que Root Directory aponta para a pasta contendo `app.py`.
5. Fazer deploy e testar `/healthz`.
6. No modo visitante, validar navegação, `/healthz` e ausência dos formulários de senha. Com banco habilitado, validar também cadastro, login, publicação, edição, exclusão e painel.
7. Conectar armazenamento externo antes de liberar upload de avatar.
8. Atualizar o domínio do README e enviar `sitemap.xml` ao Google Search Console.
