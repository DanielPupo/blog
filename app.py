"""Aplicação principal do Pupo's Blog.

O projeto continua em Flask, mas concentra aqui apenas regras HTTP, sessão e
validação. O acesso ao MySQL permanece isolado em ``db.py``.
"""

from __future__ import annotations

import secrets
import unicodedata
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    Response,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

import db
from settings import Config


app = Flask(__name__, static_folder="public/static", static_url_path="/static")
app.config.from_object(Config)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

PROJECT_ROOT = Path(__file__).resolve().parent
BUNDLED_UPLOAD_FOLDER = PROJECT_ROOT / "public" / "static" / "uploads"
UPLOAD_FOLDER = Path(app.config["UPLOAD_FOLDER"])
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_SIGNATURES = {
    "jpg": lambda data: data.startswith(b"\xff\xd8\xff"),
    "jpeg": lambda data: data.startswith(b"\xff\xd8\xff"),
    "png": lambda data: data.startswith(b"\x89PNG\r\n\x1a\n"),
    "webp": lambda data: data.startswith(b"RIFF") and data[8:12] == b"WEBP",
}


def clean_text(value: str, *, max_length: int) -> str:
    """Normaliza entrada de texto e impõe o limite aceito pelo banco."""
    normalized = unicodedata.normalize("NFKC", value or "").strip()
    return normalized[:max_length]


def csrf_token() -> str:
    """Cria um token por sessão para proteger formulários de terceiros."""
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


app.jinja_env.globals["csrf_token"] = csrf_token


@app.context_processor
def inject_template_globals():
    return {
        "now_year": datetime.now(timezone.utc).year,
        "anonymous_mode": app.config["ANONYMOUS_MODE"],
        "database_enabled": app.config["DATABASE_ENABLED"],
    }


@app.before_request
def protect_mutating_requests():
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return None
    supplied = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token", "")
    expected = session.get("_csrf_token", "")
    if not expected or not secrets.compare_digest(expected, supplied):
        abort(400, description="Token de segurança ausente ou inválido.")
    return None


@app.after_request
def apply_security_and_cache_headers(response: Response) -> Response:
    """Aplica defesa em profundidade também fora da infraestrutura da Vercel."""
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "img-src 'self' data:; font-src 'self'; connect-src 'self'; "
        "object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
    )
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    if request.is_secure:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    if request.path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    elif request.endpoint in {"login", "cadastro", "perfil", "dashboard", "novasenha"} or session:
        response.headers["Cache-Control"] = "no-store"
    elif request.method == "GET":
        response.headers["Cache-Control"] = "public, max-age=0, s-maxage=60, stale-while-revalidate=300"
    return response


def user_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not app.config["AUTH_ENABLED"]:
            flash("O blog está em modo visitante. Login e alterações estão temporariamente desativados.", "warning")
            return redirect(url_for("index"))
        if "idUser" not in session or "user" not in session:
            flash("Faça login para continuar.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not app.config["AUTH_ENABLED"]:
            abort(403)
        if not session.get("admin"):
            abort(403)
        return view(*args, **kwargs)
    return wrapped


@app.get("/")
def index():
    return render_template(
        "index.html",
        posts=db.listar_posts(),
        page_title="Histórias sobre tecnologia e aprendizado",
        page_description="Artigos e notas de Daniel Pupo sobre desenvolvimento de software.",
    )


@app.get("/post/<int:post_id>")
def post_detail(post_id: int):
    post = db.obter_post(post_id)
    if not post:
        abort(404)
    return render_template(
        "post_detail.html",
        post=post,
        page_title=post["title"],
        page_description=post["content"][:155],
    )


@app.post("/novopost")
@user_required
def novopost():
    title = clean_text(request.form.get("title", ""), max_length=50)
    content = clean_text(request.form.get("content", ""), max_length=10_000)
    if not title or not content:
        flash("Preencha título e conteúdo.", "warning")
    elif db.adicionar_post(title, content, session["idUser"]):
        flash("Post publicado.", "success")
    else:
        flash("Não foi possível publicar agora.", "error")
    return redirect(url_for("index"))


@app.route("/editarpost/<int:post_id>", methods=["GET", "POST"])
@user_required
def editarpost(post_id: int):
    post = db.obter_post(post_id)
    if not post or post["idUser"] != session["idUser"]:
        abort(403)
    if request.method == "GET":
        return render_template("index.html", posts=db.listar_posts(), post=post)

    title = clean_text(request.form.get("title", ""), max_length=50)
    content = clean_text(request.form.get("content", ""), max_length=10_000)
    if not title or not content:
        flash("Preencha título e conteúdo.", "warning")
        return redirect(url_for("editarpost", post_id=post_id))
    success = db.atualizar_post(post_id, title, content)
    flash("Post atualizado." if success else "Falha ao atualizar o post.", "success" if success else "error")
    return redirect(url_for("index"))


@app.post("/excluirpost/<int:post_id>")
def excluirpost(post_id: int):
    if not app.config["AUTH_ENABLED"]:
        abort(403)
    if not session.get("admin") and "idUser" not in session:
        abort(401)
    post = db.obter_post(post_id)
    if not post:
        abort(404)
    if not session.get("admin") and post["idUser"] != session["idUser"]:
        abort(403)
    success = db.excluir_post(post_id)
    flash("Post excluído." if success else "Falha ao excluir o post.", "success" if success else "error")
    return redirect(url_for("dashboard" if session.get("admin") else "index"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", page_title="Entrar")

    if not app.config["AUTH_ENABLED"]:
        flash("Você entrou como visitante. A leitura pública não exige conta.", "success")
        return redirect(url_for("index"))

    username = clean_text(request.form.get("user", ""), max_length=15).lower()
    password = request.form.get("password", "")
    if not username or not password:
        flash("Preencha usuário e senha.", "warning")
        return redirect(url_for("login"))

    admin_hash = app.config.get("ADMIN_PASSWORD_HASH", "")
    if username == app.config.get("ADMIN_USERNAME") and admin_hash and check_password_hash(admin_hash, password):
        session.clear()
        session.permanent = True
        session["admin"] = True
        session["_csrf_token"] = secrets.token_urlsafe(32)
        return redirect(url_for("dashboard"))

    valid, found_user, must_change = db.verificar_usuario(username, password)
    if not valid:
        flash("Usuário ou senha inválidos.", "error")
        return redirect(url_for("login"))
    if not found_user["ativo"]:
        flash("Usuário bloqueado. Fale com o administrador.", "error")
        return redirect(url_for("login"))

    session.clear()
    session.permanent = True
    session.update(
        idUser=found_user["idUser"],
        user=found_user["user"],
        foto=found_user.get("picture") or "placeholder.svg",
        _csrf_token=secrets.token_urlsafe(32),
    )
    return redirect(url_for("novasenha" if must_change else "index"))


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/sign-up", methods=["GET", "POST"])
def cadastro():
    if not app.config["AUTH_ENABLED"]:
        flash("O cadastro está indisponível no modo visitante. Você pode ler o blog sem criar uma conta.", "warning")
        return redirect(url_for("index"))

    if request.method == "GET":
        return render_template("sign-up.html", page_title="Criar conta")

    name = clean_text(request.form.get("name", ""), max_length=50)
    username = clean_text(request.form.get("user", ""), max_length=15).lower()
    password = request.form.get("password", "")
    if not name or not username or len(password) < 8:
        flash("Informe nome, usuário e uma senha com pelo menos 8 caracteres.", "warning")
        return redirect(url_for("cadastro"))

    created, error = db.adicionar_usuario(name, username, generate_password_hash(password), "placeholder.svg")
    if created:
        flash("Conta criada. Agora faça login.", "success")
        return redirect(url_for("login"))
    if getattr(error, "errno", None) == 1062:
        flash("Esse nome de usuário já existe.", "warning")
    else:
        flash("Não foi possível criar a conta.", "error")
    return redirect(url_for("cadastro"))


@app.get("/dashboard")
@admin_required
def dashboard():
    total_posts, total_users = db.totais()
    return render_template(
        "dashboard.html",
        posts=db.listar_posts(),
        usuarios=db.listar_usuarios(),
        total_posts=total_posts,
        total_usuarios=total_users,
        page_title="Painel administrativo",
    )


@app.post("/usuario/status/<int:user_id>")
@admin_required
def status_usuario(user_id: int):
    success = db.alterar_status(user_id)
    flash("Status atualizado." if success else "Falha ao atualizar o status.", "success" if success else "error")
    return redirect(url_for("dashboard"))


@app.post("/usuario/excluir/<int:user_id>")
@admin_required
def excluir_usuario(user_id: int):
    success = db.excluir_usuario(user_id)
    flash("Usuário excluído." if success else "Falha ao excluir o usuário.", "success" if success else "error")
    return redirect(url_for("dashboard"))


@app.post("/usuario/reset/<int:user_id>")
@admin_required
def reset(user_id: int):
    success = db.reset_senha(user_id)
    flash("Senha redefinida." if success else "Falha ao redefinir a senha.", "success" if success else "error")
    return redirect(url_for("dashboard"))


@app.route("/usuario/novasenha", methods=["GET", "POST"])
@user_required
def novasenha():
    if request.method == "GET":
        return render_template("nova_senha.html", page_title="Alterar senha")

    password = request.form.get("senha", "")
    confirmation = request.form.get("confirmacao", "")
    if password != confirmation:
        flash("As senhas não coincidem.", "error")
    elif len(password) < 8 or password == "1234":
        flash("Use uma senha diferente da padrão e com pelo menos 8 caracteres.", "warning")
    elif db.alterar_senha(generate_password_hash(password), session["idUser"]):
        flash("Senha alterada.", "success")
        return redirect(url_for("perfil"))
    else:
        flash("Não foi possível alterar a senha.", "error")
    return render_template("nova_senha.html", page_title="Alterar senha")


def detect_image_extension(upload) -> str | None:
    filename = secure_filename(upload.filename or "")
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    header = upload.stream.read(16)
    upload.stream.seek(0)
    validator = ALLOWED_IMAGE_SIGNATURES.get(extension)
    if not validator or not validator(header):
        return None
    return "jpg" if extension == "jpeg" else extension


@app.route("/perfil", methods=["GET", "POST"])
@user_required
def perfil():
    user = db.obter_usuario(session["idUser"])
    if not user:
        abort(404)
    if request.method == "GET":
        return render_template("profile.html", usuario=user, page_title="Meu perfil")

    name = clean_text(request.form.get("name", ""), max_length=50)
    username = clean_text(request.form.get("user", ""), max_length=15).lower()
    upload = request.files.get("foto")
    picture = user.get("picture") or "placeholder.svg"
    if not name or not username:
        flash("Nome e usuário são obrigatórios.", "warning")
        return redirect(url_for("perfil"))

    pending_upload = None
    if upload and upload.filename:
        if not app.config["ENABLE_LOCAL_UPLOADS"]:
            flash("Uploads precisam de armazenamento externo na Vercel. Os demais dados foram salvos.", "warning")
        else:
            extension = detect_image_extension(upload)
            if not extension:
                flash("Envie uma imagem JPG, PNG ou WebP válida.", "error")
                return redirect(url_for("perfil"))
            picture = f"{session['idUser']}.{extension}"
            pending_upload = upload

    if not db.editar_perfil(name, username, picture, session["idUser"]):
        flash("Não foi possível salvar o perfil.", "error")
        return redirect(url_for("perfil"))
    if pending_upload:
        pending_upload.save(UPLOAD_FOLDER / picture)
    session.update(user=username, foto=picture)
    flash("Perfil atualizado.", "success")
    return redirect(url_for("perfil"))


@app.get("/uploads/<path:filename>")
def profile_image(filename: str):
    safe_name = secure_filename(filename)
    if not safe_name or safe_name != filename:
        abort(404)
    requested = UPLOAD_FOLDER / safe_name
    if requested.is_file():
        return send_from_directory(UPLOAD_FOLDER, safe_name, max_age=86_400)
    return send_from_directory(BUNDLED_UPLOAD_FOLDER, "placeholder.svg", max_age=86_400)


@app.get("/sitemap.xml")
def sitemap():
    return Response(render_template("sitemap.xml", posts=db.listar_posts()), mimetype="application/xml")


@app.get("/robots.txt")
def robots():
    return Response(render_template("robots.txt"), mimetype="text/plain")


@app.get("/healthz")
def healthz():
    return {
        "status": "ok",
        "mode": "anonymous" if app.config["ANONYMOUS_MODE"] else "authenticated",
        "database": "enabled" if app.config["DATABASE_ENABLED"] else "disabled",
    }


@app.errorhandler(400)
def bad_request(error):
    return render_template("error.html", code=400, title="Requisição inválida", message=error.description), 400


@app.errorhandler(403)
def forbidden(_error):
    return render_template("error.html", code=403, title="Acesso negado", message="Você não pode acessar esta página."), 403


@app.errorhandler(404)
def page_not_found(_error):
    return render_template("error.html", code=404, title="Página não encontrada", message="O endereço pode ter mudado."), 404


@app.errorhandler(500)
def internal_error(_error):
    return render_template("error.html", code=500, title="Erro interno", message="Tente novamente em alguns instantes."), 500


if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])
