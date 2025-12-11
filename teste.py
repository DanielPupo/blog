from werkzeug.security import generate_password_hash, check_password_hash

senha = "1234"
hash = generate_password_hash(senha)
print(hash)
senha_informada = "1234"

if check_password_hash(hash, senha):
    print("Senha correta!")
else:
    print("Senha incorreta!")