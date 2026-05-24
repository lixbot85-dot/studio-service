from flask import Flask, jsonify, request, render_template_string, redirect, url_url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "uma-chave-secreta-muito-segura")

# Configurações para upload de arquivos
UPLOAD_FOLDER = 'uploads'
# Extensões permitidas que você pediu
ALLOWED_EXTENSIONS = {'rbxl', 'txt', 'lua', 'py'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Configuração do Sistema de Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Usuário temporário para o painel (Como é de graça e simples, definimos no código)
# IMPORTANTE: Altere essas credenciais ou use variáveis de ambiente no Render!
USER_CREDENTIALS = {
    "admin": "studio123"  # Usuario: admin | Senha: studio123
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

# --- TEMPLATES HTML EM LINHA (Para não precisar criar pastas no GitHub por enquanto) ---
HTML_LAYOUT = """
<!... html>
<html>
<head>
    <title>Studio Service</title>
    <style>
        body { font-family: Arial, sans-serif; background: #121212; color: #fff; text-align: center; padding: 50px; }
        .container { max-width: 500px; margin: auto; background: #1e1e1e; padding: 20px; border-radius: 10px; box-shadow: 0px 0px 10px rgba(0,0,0,0.5); }
        input[type="text"], input[type="password"], input[type="file"] { width: 90%; padding: 10px; margin: 10px 0; border-radius: 5px; border: none; }
        input[type="submit"], .btn { background: #06b6d4; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; }
        .btn-logout { background: #ef4444; }
        .msg { color: #22c55e; margin: 10px 0; }
        .err { color: #ef4444; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

# --- ROTAS WEB PRINCIPAIS ---

# Rota "/" agora é o Menu Principal. Se não estiver logado, mostra o menu público. 
# Se estiver logado, libera a área de upload.
@app.route('/', methods=['GET', 'POST'])
def home():
    # Listar os arquivos já enviados para mostrar no menu
    arquivos_no_servidor = os.listdir(app.config['UPLOAD_FOLDER'])
    
    # Renderiza a página principal
    return render_template_string(HTML_LAYOUT + """
        {% block content %}
            <h1>Studio Service 🛠️</h1>
            <p>Status do Sistema: <span style="color:#22c55e;">Online</span></p>
            <hr>
            
            {% if current_user.is_authenticated %}
                <h3>Painel do Desenvolvedor</h3>
                <p>Logado como: <b>{{ current_user.id }}</b></p>
                
                <form method="POST" action="/upload" enctype="multipart/form-data">
                    <label>Postar arquivo (.rbxl, .txt, .lua, .py):</label><br>
                    <input type="file" name="file" required><br>
                    <input type="submit" value="Enviar Arquivo">
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
            <ul>
                {% for arquivo in arquivos %}
                    <li><a href="/uploads/{{ arquivo }}" style="color:#06b6d4;">{{ arquivo }}</a></li>
                {% endfor %}
            </ul>
        {% endblock %}
    """, arquivos=arquivos_no_servidor)

# Rota de Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    erro = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            user = User(username)
            login_user(user)
            return redirect('/')
        else:
            erro = "Usuário ou senha incorretos."
            
    return render_template_string(HTML_LAYOUT + """
        {% block content %}
            <h2>Login de Desenvolvedor</h2>
            {% if erro %} <p class="err">{{ erro }}</p> {% endif %}
            <form method="POST">
                <input type="text" name="username" placeholder="Usuário" required><br>
                <input type="password" name="password" placeholder="Senha" required><br>
                <input type="submit" value="Entrar">
            </form>
            <br>
            <a href="/" style="color:#aaa;">Voltar ao Menu</a>
        {% endblock %}
    """, erro=erro)

# Rota para deslogar
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

# Rota protegida que recebe o upload do arquivo
@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return redirect('/')
    file = request.files['file']
    if file.filename == '':
        return redirect('/')
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect('/')
    
    return "Extensão de arquivo não permitida!", 400

# --- SUAS ROTAS ANTIGAS DA API (Permanecem funcionando igual para o seu plugin) ---

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
