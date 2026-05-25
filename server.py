from flask import Flask, jsonify, request, render_template_string, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from supabase import create_client, Client
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "uma-chave-secreta-muito-segura")

# Conexão automática com o Supabase Storage Permanente usando as chaves do Render
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
BUCKET_NAME = "studio-files"

supabase_client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Erro ao conectar no Supabase: {e}")

ALLOWED_EXTENSIONS = {'rbxl', 'txt', 'lua', 'py'}

# Configuração do Sistema de Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

USER_CREDENTIALS = {
    "admin": "studio123"
}

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    if user_id in USER_CREDENTIALS:
        return User(user_id)
    return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def renderizar_pagina(conteudo_interno, **contexto):
    html_completo = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Studio Service</title>
        <style>
            body { font-family: Arial, sans-serif; background: #121212; color: #fff; text-align: center; padding: 50px; }
            .container { max-width: 500px; margin: auto; background: #1e1e1e; padding: 20px; border-radius: 10px; box-shadow: 0px 0px 10px rgba(0,0,0,0.5); }
            input[type="text"], input[type="password"], input[type="file"] { width: 90%; padding: 10px; margin: 10px 0; border-radius: 5px; border: none; background: #2d2d2d; color: #fff; }
            input[type="submit"], .btn { background: #06b6d4; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; margin: 5px; }
            .btn-logout { background: #ef4444; }
            .err { color: #ef4444; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
    """ + conteudo_interno + """
        </div>
    </body>
    </html>
    """
    return render_template_string(html_completo, **contexto)

# --- ROTAS WEB PRINCIPAIS ---

@app.route('/', methods=['GET', 'POST'])
def home():
    arquivos_no_servidor = []
    
    # Busca a lista de arquivos direto do Supabase de forma dinâmica
    if supabase_client:
        try:
            res = supabase_client.storage.from_(BUCKET_NAME).list()
            arquivos_no_servidor = [item['name'] for item in res if item['name'] != '.emptyFolderPlaceholder']
        except Exception as e:
            print(f"Erro ao listar arquivos do Supabase: {e}")
            
    conteudo_home = """
    <h1>Studio Service 🛠️</h1>
    <p>Status do Sistema: <span style="color:#22c55e;">Online (Permanente ☁️)</span></p>
    <hr>
    
    {% if current_user.is_authenticated %}
        <h3>Painel do Desenvolvedor</h3>
        <p>Logado como: <b>{{ current_user.id }}</b></p>
        
        <form method="POST" action="/upload" enctype="multipart/form-data">
            <label>Postar arquivo (.rbxl, .txt, .lua, .py):</label><br>
            <input type="file" name="file" required><br>
            <input type="submit" value="Enviar para Nuvem">
        </form>
        <br>
        <a href="/logout" class="btn btn-logout">Sair da Conta</a>
    {% else %}
        <h3>Menu do Sistema</h3>
        <p>Você precisa estar logado para enviar arquivos ou scripts.</p>
        <a href="/login" class="btn">Fazer Login de Desenvolvedor</a>
    {% endif %}
    
    <hr>
    <h4>Arquivos Disponíveis no Servidor:</h4>
    <ul style="text-align: left; list-style-type: square;">
        {% for arquivo in arquivos %}
            <li><a href="/uploads/{{ arquivo }}" style="color:#06b6d4;" target="_blank">{{ arquivo }}</a></li>
        {% endfor %}
    </ul>
    """
    return renderizar_pagina(conteudo_home, arquivos=arquivos_no_servidor)

@app.route('/login', methods=['GET', 'POST'])
def login():
    erro = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for('home'))
        else:
            erro = "Usuário ou senha incorretos."
            
    conteudo_login = """
    <h2>Login de Desenvolvedor</h2>
    {% if erro %} <p class="err">{{ erro }}</p> {% endif %}
    <form method="POST">
        <input type="text" name="username" placeholder="Usuário" required><br>
        <input type="password" name="password" placeholder="Senha" required><br>
        <input type="submit" value="Entrar">
    </form>
    <br>
    <a href="/" style="color:#aaa;">Voltar ao Menu</a>
    """
    return renderizar_pagina(conteudo_login, erro=erro)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files or not supabase_client:
        return redirect(url_for('home'))
    
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('home'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_bytes = file.read()
        
        try:
            # Envia o arquivo direto para o Bucket do Supabase, substituindo se já existir
            supabase_client.storage.from_(BUCKET_NAME).upload(
                path=filename,
                file=file_bytes,
                file_options={"cache-control": "3600", "upsert": "true"}
            )
        except Exception as e:
            print(f"Erro no upload para o Supabase: {e}")
            
        return redirect(url_for('home'))
    
    return "Extensão de arquivo não permitida!", 400

# Redireciona o Roblox ou o navegador direto para o link seguro do Supabase
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    if supabase_client:
        public_url = supabase_client.storage.from_(BUCKET_NAME).get_public_url(filename)
        return redirect(public_url)
    return "Erro na nuvem", 500

# --- SUAS ROTAS DA API DO STUDIO ---

@app.route('/api/studio-check', methods=['GET', 'POST'])
def studio_check():
    if request.method == 'POST':
        dados_recebidos = request.json or {}
        return jsonify({"sucesso": True, "retorno": dados_recebidos}), 200
    
    return jsonify({
        "sucesso": True,
        "versao_obrigatoria": "Future-Is-Bright-v2",
        "scripts_disponiveis": [
            {"id": 1, "nome": "Base_Ajustes", "autor": "ZX"},
            {"id": 2, "nome": "Anti_Lag_Shaders", "autor": "ZX"}
        ]
    }), 200

@app.route('/toolbox', methods=['GET'])
def get_custom_toolbox():
    return jsonify({
        "sucesso": True,
        "itens": [
            {"id": 1, "nome": "Spawn Point Oficial", "tipo": "Model", "asset_id": 1716327318},
            {"id": 2, "nome": "Bloco Neon Verde", "tipo": "Model", "asset_id": 511061730},
            {"id": 3, "nome": "Modelo de Teste ZX", "tipo": "Model", "asset_id": 60790132}
        ]
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
