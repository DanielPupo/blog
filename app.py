from flask import Flask, render_template, request, redirect, flash, session
from db import *
import mysql.connector
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from config import *

#Acessar as variáveis de ambiente
secret_key = SECRET_KEY
usuario_admin = USUARIO_ADMIN
senha_admin = SENHA_ADMIN

app = Flask(__name__)
app.secret_key = SECRET_KEY #CHAVE SECRETA

app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)   # cria pasta se não existir

# Rota para a página inicial
@app.route('/')
def index():
    postagens = listar_post()
    return render_template('index.html', posts=postagens)

@app.route('/novopost', methods=['GET', 'POST'])
def novopost():
    if request.method == 'GET':
        return redirect('/')
    else:
        title = request.form['title'].strip()
        content = request.form['content'].strip()
        idUser = session['idUser']
        
        if not title or not content:
            flash("Preencha todos os campos!")
            return redirect('/')
        
        sucesso = adicionar_post(title, content, idUser)
        if sucesso:
            flash("Post adicionado com sucesso!")
        else:
            flash("Erro ao adicionar post! Tente novamente.")

        #Encaminhar para a rota da página inicial
        return redirect('/')
    
#Rota para editar post
@app.route('/editarpost/<int:idPost>', methods=['GET','POST'])
def editarpost(idPost):
    if 'user' not in session or 'admin' in session:
        return redirect('/')
    
    #checar autoria
    with conectar() as conexao:
        cursor = conexao.cursor(dictionary=True)
        cursor.execute(f"SELECT idUser FROM posts WHERE idPost = {idPost}")
        autor = cursor.fetchone()
        if not autor or autor['idUser'] != session['idUser']:
            print("Tentativa de acessar a postagem de outra autoria!")
            return redirect('/')
    
    if request.method == "GET":
        try:
            with conectar() as conexao:
                cursor = conexao.cursor(dictionary=True)
                cursor.execute("SELECT * FROM posts WHERE idPost = %s", (idPost,))
                post = cursor.fetchone()
                postagens = listar_post()
                return render_template('index.html', posts=postagens, post=post)
        except mysql.connector.Error as erro:
            print(f"Erro de BD! Erro: {erro}")
            flash("Houve um erro! Tente mais tarde!")
            return []

#Gravar edição do post
    if request.method == "POST":
        title = request.form['title'].strip()
        content = request.form['content'].strip()
        
        if not title or not content:
            flash("Preencha todos os campos!")
            return redirect(f'/editarpost/{idPost}')
        
        sucesso = atualizar_post(idPost, title, content)
        
        if sucesso:
            flash("Post atualizado com sucesso!")
        else:
            flash("Erro ao atualizar post! Tente novamente.")
        return redirect('/')
    
#Rota para excluir post       
@app.route('/excluirpost/<int:idPost>')
def excluirpost(idPost):
    if not session:
        print("Usuário não autorizado acessando rota exluir.")
        return redirect('/')
    
# 1ª verificação: Checar se o usuário é o autor do post
    try:
        with conectar() as conexao:
            cursor = conexao.cursor(dictionary=True)
            if 'admin' not in session:
                cursor.execute(f"SELECT idUser FROM posts WHERE idPost = {idPost}")
                autor_post = cursor.fetchone()
                
                if not autor_post or autor_post ['idUser'] != session.get('idUser'):
                    print("Tentativa de exclusão não autorizada!")
                    return redirect('/')
            
            cursor.execute(f"DELETE FROM posts WHERE idPost = {idPost}")
            conexao.commit()
            flash("Post excluído com sucesso!")
        
            if 'admin' in session:
                return redirect ('/dashboard')
            else:
                return redirect('/')
        
    except mysql.connector.Error as erro:
        conexao.rollback()
        print(f"Erro de BD! Erro: {erro}")
        flash("Houve um erro! Tente mais tarde!")
        return redirect('/')

    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    

    elif request.method == 'POST':
        user = request.form['user'].lower()
        password = request.form['password']
        
        if not user or not password:    
            flash("Preencha todos os campos!")
            return redirect('/login')
        
        # 1º Primeiro verificamos se o usuário é o ADMIN
        if user == USUARIO_ADMIN and password == SENHA_ADMIN:
            session['admin'] = True
            return redirect('/dashboard')
        
        # 2º Verificamos se é um usuário cadastrado
        valido, usuario_encontrado, precisa_alterar = verificar_usuario(user, password)
        if valido:
            if usuario_encontrado['ativo'] == 0:
                flash("Usuário bloqueado! Fale com o ADM!")
                return redirect('/login')

            # guarda id na sessão (necessário para permitir alteração de senha)
            session['idUser'] = usuario_encontrado['idUser']
            session['user'] = usuario_encontrado['user']
            session['foto'] = usuario_encontrado['picture']

            if precisa_alterar:
                # senha é a padrão -> forçar alteração
                return render_template('nova_senha.html')

            # login normal
            return redirect('/')
        
        # 3º Nenhum usuário ou ADMIN foram encontrados
        flash("Usuário ou senha inválidos!")
        return redirect('/login')
    
#Rota para o dashboard
@app.route('/dashboard')
def dashboard():
    if not session or "admin" not in session:
            return redirect('/')
    
    usuarios = listar_usuarios()
    posts = listar_post()
    total_posts, total_usuarios = totais()
    return render_template('dashboard.html', posts=posts, usuarios=usuarios, total_posts=total_posts, total_usuarios=total_usuarios)

#Rota para logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/sign-up', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'GET':
        return render_template('sign-up.html')
    elif request.method == 'POST':
        name = request.form['name'].strip()
        user = request.form['user'].lower().strip()
        password = request.form['password'].strip()
        
        if not name or not user or not password:
            flash("Preencha todos os campos!")
            return redirect('/sign-up')

        senha_hash = generate_password_hash(password)
        foto = "placeholder.jpg" #foto padrão
        resultado, erro = adicionar_usuarios (name, user, senha_hash, foto)
        
        if resultado:
            flash("Usuário cadastrado com sucesso! Faça o login.")
            return redirect('/login')
        else:
            if erro.errno == 1062:
                flash("Esse user já existe! Tente outro.")
            else: 
                flash("Erro ao cadastrar! Procure o suporte.")
            return redirect('/sign-up')

@app.route('/usuario/status/<int:idUser>')
def status_usuario(idUser):
    if not session:
        return redirect ('/')
    sucesso = alterar_status(idUser)
    if sucesso:
        flash('Status alterado com sucesso')
    else:
        flash('Erro na alteração do status!')
    return redirect('/dashboard')

@app.route('/usuario/excluir/<int:idUser>', methods=['POST'])
def excluir_usuario(idUser):
    # somente admin pode excluir
    if 'admin' not in session:
        return redirect('/')
    # impedir admin apagar a si mesmo 
    if 'admin' in session and session.get('idUser') == idUser:
        flash("Admin não pode excluir a si mesmo.")

    sucesso = delete_usuario(idUser)
    if sucesso:
        flash('Usuário excluído com sucesso')
    else:
        flash('Erro na exclusão do usuário!')
    return redirect('/dashboard')

@app.route('/usuario/reset/<int:idUser>')
def reset(idUser):
    if 'admin' not in session:
        return redirect('/')
    
    sucesso = reset_senha(idUser)
    
    if sucesso:
        flash("Senha resetada com sucesso!")
    else:
        flash("Falha ao resetar a senha!")
    return redirect ('/dashboard')

@app.route('/usuario/novasenha', methods=['GET','POST'])
def novasenha():
    if 'idUser' not in session:
        return redirect('/')
    
    if request.method == 'GET':
        return render_template('nova_senha.html')
    
    if request.method == 'POST':
        senha = request.form['senha']
        confirmacao = request.form['confirmacao']
        
        if not senha or not confirmacao:
            flash('Preencha corretamente as senhas!')
            return render_template('nova_senha.html')
        
        if senha != confirmacao:
            flash('As senha não são iguais!')
            return render_template('nova_senha.html')
        
        if senha == '1234':
            flash('A senha precisa ser alterada!')
            return render_template('nova_senha.html')
        
        senha_hash = generate_password_hash(senha)
        idUser = session['idUser']
        sucesso = alterar_senha(senha_hash, idUser)
        if sucesso:
            flash('Senha alterada com sucesso!')
            if 'user' in session:
                return redirect('/perfil')
            
            return redirect('/login')
        else:
            flash('Erro no cadastro da nova senha!')
            return render_template('nova_senha.html')
        
@app.route('/perfil', methods=['GET','POST'])
def perfil():
    if 'idUser' not in session:
        return redirect('/')

    if request.method == 'GET':
        usuarios = listar_usuarios()
        usuario = next((u for u in usuarios if u['idUser'] == session['idUser']), None)

        if not usuario:
            flash("Usuário não encontrado!")
            return redirect('/')

        return render_template(
            'profile.html',
            nome=usuario['name'],
            user=usuario['user'],
            foto=usuario['picture']
        )

    # POST (atualizar)
    name = request.form['name'].strip()
    user = request.form['user'].strip()
    foto = request.files.get('foto')
    idUser = session['idUser']

    if not name or not user:
        flash("Os campos Nome e User não podem estar vazios.")
        return redirect('/perfil')

    # --- pegar foto atual ---
    usuarios = listar_usuarios()
    usuario = next((u for u in usuarios if u['idUser'] == idUser), None)
    nome_atual = usuario['picture'] if usuario else "placeholder.jpg"

    nome_foto = nome_atual

    # --- se enviou nova foto ---
    if foto and foto.filename:
        filename = secure_filename(foto.filename)
        ext = filename.rsplit('.', 1)[-1].lower()

        if ext not in ('png','jpg','webp'):
            flash("Extensão inválida!")
            return redirect('/perfil')

        foto.seek(0)
        if len(foto.read()) > 2 * 1024 * 1024:
            flash("Arquivo acima de 2MB não é aceito!")
            return redirect('/perfil')

        foto.seek(0)
        nome_foto = f"{idUser}.{ext}"

    sucesso = editar_perfil(name, user, nome_foto, idUser)

    if sucesso:
        if foto and foto.filename:
            caminho_completo = os.path.join(app.config['UPLOAD_FOLDER'], nome_foto)
            foto.save(caminho_completo)
            session['foto'] = nome_foto
            print(f"Foto salva em: {caminho_completo}")
        flash("Dados alterados com sucesso!")
    else:
        flash("Erro ao atualizar dados!")

    return redirect('/perfil')

#ERRO 404
@app.errorhandler(404)
def page_not_found(error):
    return render_template('e404.html'), 404

#ERRO 500 
@app.errorhandler(500)
def erro_interno(error):
    return render_template('e500.html')

# SEMPRE NO FINAL DO ARQUIVO
if __name__ == "__main__":
    app.run(debug=True)