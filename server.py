from flask import Flask, jsonify, request, render_template_string, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "uma-chave-secreta-muito-segura")

# Configurações para upload de arquivos
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'rbxl', 'txt', 'lua', 'py'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Configuração do Sistema de Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Usuário temporário para o painel
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

# --- TEMPLATES HTML EM LINHA ---
HTML_LAYOUT = """
<!DOCTYPE html>
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

@app.route('/', methods=['GET', 'POST'])
def home():
    arquivos_no_servidor = os.listdir(app.config['UPLOAD_FOLDER'])
    
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
            <ul style="text-align: left; list-style-type: square;">
                {% for arquivo in arquivos %}
                    <li><a href="/uploads/{{ arquivo }}" style="color:#06b6d4;" download>{{ arquivo }}</a></li>
                {% endfor %}
            </ul>
        {% endblock %}
    """, arquivos=arquivos_no_servidor)

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

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('home'))
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('home'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('home'))
    
    return "Extensão de arquivo não permitida!", 400

# Rota para permitir baixar os arquivos enviados de forma estática
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- SUAS ROTAS ANTIGAS DA API ---

@app.route('/api/studio-check', methods=['GET', 'POST'])
def studio_check():
    if request.method == 'POST':
        dados_recebidos = request.json or {}
        return jsonify({"sucesso": True, "retorno": dados_recebidos}), 200
    
    return jsonify({
        "sucesso": True,
        "versao_obrigatoria
