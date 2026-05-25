from flask import Flask, jsonify, request, render_template_string, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from supabase import create_client, Client
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "uma-chave-secreta-muito-segura")

# Conexão com o Supabase Storage Permanente
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
        <title>Studio Service - Painel</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #121212; color: #e0e0e0; text-align: center; padding: 40px 20px; margin: 0; }
            .container { max-width: 750px; margin: auto; background: #1e1e1e; padding: 30px; border-radius: 12px; box-shadow: 0px 4px 20px rgba(0,0,0,0.6); border: 1px solid #2d2d2d; }
            h1, h2, h3, h4 { color: #fff; margin-top: 0; }
            input[type="text"], input[type="password"], input[type="file"] { width: 100%; max-width: 400px; padding: 12px; margin: 10px 0; border-radius: 6px; border: 1px solid #3d3d3d; background: #2a2a2a; color: #fff; box-sizing: border-box; }
            input[type="submit"], .btn { background: #06b6d4; color: white; padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; display: inline-block; font-weight: bold; transition: background 0.2s; margin: 5px; }
            input[type="submit"]:hover, .btn:hover { background: #0891b2; }
            .btn-logout { background: #ef4444; }
            .btn-logout:hover { background: #dc2626; }
            .btn-del { background: #b91c1c; padding: 4px 10px; font-size: 13px; }
            .btn-del:hover { background: #991b1b; }
            .btn-copy { background: #4b5563; padding: 4px 10px; font-size: 13px; }
            .btn-copy:hover { background: #374151; }
            .err { color: #ef4444; margin: 10px 0; font-weight: bold; }
            hr { border: 0; height: 1px; background: #2d2d2d; margin: 25px 0; }
            .file-item { display: flex; justify-content: space-between; align-items: center; background: #262626; padding: 12px 16px; margin: 8px 0; border-radius: 6px; border: 1px solid #333; }
            .file-name { font-weight: 500; color: #06b6d4; text-decoration: none; word-break: break-all; text-align: left; flex-grow: 1; margin-right: 15px; }
            .file-name:hover { text-decoration: underline; }
            .actions { display: flex; gap: 8px; flex-shrink: 0; }
        </style>
        <script>
            function copiarTexto(txt) {
                navigator.clipboard.writeText(txt);
                alert("URL copiada com sucesso!");
            }
        </script>
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

@app.route('/', methods=['GET'])
def home():
    arquivos_no_servidor = []
    
    if supabase_client:
        try:
            res = supabase_client.storage.from_(BUCKET_NAME).list()
            arquivos_no_servidor = [item['name'] for item in res if item['name'] != '.emptyFolderPlaceholder']
        except Exception as e:
            print(f"Erro ao listar arquivos do Supabase: {e}")
            
    conteudo_home = """
    <h1>Studio Service 🛠️</h1>
    <p>Status do Armazenamento: <span style="color:#22c55e; font-weight: bold;">Nuvem Permanente ☁️</span></p>
    <hr>
    
    {% if current_user.is_authenticated %}
        <h3>Painel de Gerenciamento</h3>
        <p>Desenvolvedor: <b style="color:#06b6d4;">{{ current_user.id }}</b></p>
        
        <form method="POST" action="/upload" enctype="multipart/form-data" style="background: #262626; padding: 20px; border-radius: 8px; border: 1px solid #333; display: inline-block; width: 100%; max-width: 500px; box-sizing: border-box;">
            <strong style="display:block; margin-bottom:8px;">Subir Novo Arquivo</strong>
            <input type="file" name="file" required><br>
            <input type="submit" value="Fazer Upload">
        </form>
        <br><br>
        <a href="/logout" class="btn btn-logout">Sair do Painel</a>
    {% else %}
        <h3>Menu de Acesso</h3>
        <p>Faça login para gerenciar, fazer upload ou deletar arquivos.</p>
        <a href="/login" class="btn">Login do Desenvolvedor</a>
    {% endif %}
    
    <hr>
    <h3>Arquivos Controlados no Sistema ({{ arquivos|length }})</h3>
    <div style="margin-top: 15px;">
        {% for arquivo in arquivos %}
            <div class="file-item">
                <a class="file-name" href="/uploads/{{ arquivo }}" target="_blank">📄 {{ arquivo }}</a>
                <div class="actions">
                    <button class="btn btn-copy" onclick="copiarTexto(window.location.origin + '/uploads/{{ arquivo }}')">Copiar Link</button>
                    {% if current_user.is_authenticated %}
                        <a href="/delete/{{ arquivo }}" class="btn btn-del" onclick="return confirm('Tem certeza que deseja deletar permanentemente o arquivo {{ arquivo }}?')">Deletar</a>
                    {% endif %}
                </div>
            </div>
        {% else %}
            <p style="color: #888;">Nenhum arquivo encontrado no bucket.</p>
        {% endfor %}
    </div>
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
    <h2>Acesso ao Painel</h2>
    {% if erro %} <p class="err">{{ erro }}</p> {% endif %}
    <form method="POST">
        <input type="text" name="username" placeholder="Usuário" required><br>
        <input type="password" name="password" placeholder="Senha" required><br>
        <input type="submit" value="Entrar no Painel">
    </form>
    <br>
    <a href="/" style="color:#aaa; text-decoration: none;">← Voltar ao Início</a>
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
            supabase_client.storage.from_(BUCKET_NAME).upload(
                path=filename,
                file=file_bytes,
                file_options={"cache-control": "3600", "upsert": "true"}
            )
        except Exception as e:
            print(f"Erro no upload para o Supabase: {e}")
            
        return redirect(url_for('home'))
    
    return "Extensão de arquivo não permitida!", 400

# NOVA ROTA: Deletar arquivo de forma controlada através do painel
@app.route('/delete/<filename>')
@login_required
def delete_file(filename):
    if supabase_client:
        try:
            # Remove o arquivo diretamente do bucket do Supabase
            supabase_client.storage.from_(BUCKET_NAME).remove([filename])
        except Exception as e:
            print(f"Erro ao deletar arquivo do Supabase: {e}")
            
    return redirect(url_for('home'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    if supabase_client:
        public_url = supabase_client.storage.from_(BUCKET_NAME).get_public_url(filename)
        return redirect(public_url)
    return "Erro na nuvem", 500

# --- ROTAS DA API ---
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
