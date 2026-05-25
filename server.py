from flask import Flask, jsonify, request, render_template_string, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from supabase import create_client, Client
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "uma-chave-secreta-muito-segura")

# Conexão com o Supabase
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

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, role='user'):
        self.id = id
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    if user_id == "admin":
        return User("admin", role="adm")
    
    if supabase_client:
        try:
            res = supabase_client.table("users_service").select("*").eq("username", user_id).execute()
            if res.data and len(res.data) > 0:
                dados_user = res.data[0]
                return User(dados_user['username'], role=dados_user.get('role', 'user'))
        except Exception as e:
            print(f"Erro ao carregar usuário do banco: {e}")
            
    return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def renderizar_pagina(conteudo_interno, **contexto):
    html_completo = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Studio Service - Dashboard</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #121212; color: #e0e0e0; text-align: center; padding: 40px 20px; margin: 0; }
            .container { max-width: 800px; margin: auto; background: #1e1e1e; padding: 30px; border-radius: 12px; box-shadow: 0px 4px 20px rgba(0,0,0,0.6); border: 1px solid #2d2d2d; }
            h1, h2, h3, h4 { color: #fff; margin-top: 0; }
            input[type="text"], input[type="password"], input[type="file"], textarea, select { width: 100%; max-width: 400px; padding: 12px; margin: 10px 0; border-radius: 6px; border: 1px solid #3d3d3d; background: #2a2a2a; color: #fff; box-sizing: border-box; }
            textarea { max-width: 100%; height: 200px; font-family: 'Courier New', Courier, monospace; font-size: 14px; }
            input[type="submit"], .btn { background: #06b6d4; color: white; padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; display: inline-block; font-weight: bold; transition: background 0.2s; margin: 5px; }
            input[type="submit"]:hover, .btn:hover { background: #0891b2; }
            .btn-logout { background: #ef4444; }
            .btn-logout:hover { background: #dc2626; }
            .btn-del { background: #b91c1c; padding: 4px 10px; font-size: 13px; }
            .btn-del:hover { background: #991b1b; }
            .btn-edit { background: #eab308; color: #000; padding: 4px 10px; font-size: 13px; }
            .btn-edit:hover { background: #ca8a04; }
            .btn-copy { background: #4b5563; padding: 4px 10px; font-size: 13px; }
            .btn-copy:hover { background: #374151; }
            .badge { background: #22c55e; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; vertical-align: middle; }
            .badge-adm { background: #a855f7; }
            .badge-pub { background: #2563eb; font-size: 11px; margin-left: 5px; }
            .badge-priv { background: #4b5563; font-size: 11px; margin-left: 5px; }
            .badge-tag { background: #14b8a6; font-size: 11px; margin-left: 5px; color: #000; }
            hr { border: 0; height: 1px; background: #2d2d2d; margin: 25px 0; }
            .file-item { display: flex; justify-content: space-between; align-items: center; background: #262626; padding: 12px 16px; margin: 8px 0; border-radius: 6px; border: 1px solid #333; }
            .file-name { font-weight: 500; color: #06b6d4; text-decoration: none; word-break: break-all; text-align: left; flex-grow: 1; margin-right: 15px; }
            .file-name:hover { text-decoration: underline; }
            .actions { display: flex; gap: 8px; flex-shrink: 0; }
            .filter-container { margin-bottom: 20px; display: flex; justify-content: center; gap: 10px; align-items: center; flex-wrap: wrap; }
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
    arquivos_finais = []
    if supabase_client:
        try:
            res_storage = supabase_client.storage.from_(BUCKET_NAME).list()
            arquivos_storage = [item['name'] for item in res_storage if item['name'] != '.emptyFolderPlaceholder']
            
            res_perm = supabase_client.table("arquivos_permissao").select("*").execute()
            perm_dict = {item['filename']: item for item in res_perm.data} if res_perm.data else {}
            
            for f in arquivos_storage:
                # Se o usuário for ADM, ele vê tudo na Home. Se for Membro, ele só vê os arquivos dele ou públicos aqui.
                info = perm_dict.get(f, {"is_public": False, "tags": "script", "description": ""})
                if current_user.is_authenticated and (current_user.role == 'adm' or info['is_public']):
                    arquivos_finais.append({
                        "name": f,
                        "is_public": info['is_public'],
                        "tag": info['tags'],
                        "desc": info['description']
                    })
        except Exception as e:
            print(f"Erro ao listar arquivos: {e}")
            
    conteudo_home = """
    <h1>Studio Service 🛠️</h1>
    <div style="margin: 10px 0;">
        <a href="/" class="btn" style="background:#06b6d4;">🏠 Home</a>
        <a href="/explore" class="btn" style="background:#2563eb;">🌐 Explore Marketplace</a>
    </div>
    <hr>
    
    {% if current_user.is_authenticated %}
        <h3>Painel de Gerenciamento</h3>
        <p>Usuário: <b style="color:#06b6d4;">{{ current_user.id }}</b> 
           {% if current_user.role == 'adm' %} <span class="badge badge-adm">ADMINISTRADOR</span> {% else %} <span class="badge">Membro</span> {% endif %}
        </p>
        
        {% if current_user.role == 'adm' %}
        <form method="POST" action="/upload" enctype="multipart/form-data" style="background: #262626; padding: 20px; border-radius: 8px; border: 1px solid #333; display: inline-block; width: 100%; max-width: 500px; box-sizing: border-box; text-align: left;">
            <strong style="display:block; margin-bottom:8px; text-align:center;">Subir Novo Arquivo</strong>
            <input type="file" name="file" required><br>
            
            <label><b>Filtro / Tipo:</b></label><br>
            <select name="tag">
                <option value="script">Script (Lua/Python)</option>
                <option value="asset">Asset (Model/RBXL)</option>
                <option value="chat">Chat Log / TXT</option>
            </select><br>
            
            <label><b>Visibilidade:</b></label><br>
            <select name="is_public">
                <option value="false">Privado (Apenas Admin)</option>
                <option value="true">Público (Aparece no /explore)</option>
            </select><br>
            
            <input type="text" name="description" placeholder="Descrição curta do arquivo (opcional)"><br>
            <div style="text-align:center;"><input type="submit" value="Fazer Upload"></div>
        </form>
        <br><br>
        {% endif %}
        <a href="/logout" class="btn btn-logout">Sair do Painel</a>
    {% else %}
        <h3>Menu de Acesso</h3>
        <a href="/login" class="btn">Login de Usuário</a>
        <a href="/users-service" class="btn" style="background:#4b5563;">Criar uma Conta</a>
    {% endif %}
    
    <hr>
    <h3>Seus Arquivos Disponíveis ({{ arquivos|length }})</h3>
    <div>
        {% for arq in arquivos %}
            <div class="file-item">
                <div style="text-align: left;">
                    <a class="file-name" href="/uploads/{{ arq.name }}" target="_blank">📄 {{ arq.name }}</a>
                    <span class="badge badge-tag">{{ arq.tag }}</span>
                    {% if arq.is_public %}<span class="badge badge-pub">Público</span>{% else %}<span class="badge badge-priv">Privado</span>{% endif %}
                    {% if arq.desc %}<br><small style="color:#aaa;">{{ arq.desc }}</small>{% endif %}
                </div>
                <div class="actions">
                    <button class="btn btn-copy" onclick="copiarTexto(window.location.origin + '/uploads/{{ arq.name }}')">Copiar Link</button>
                    {% if current_user.is_authenticated and current_user.role == 'adm' %}
                        <a href="/edit-file/{{ arq.name }}" class="btn btn-edit">Editar</a>
                        <a href="/delete/{{ arq.name }}" class="btn btn-del" onclick="return confirm('Deletar permanentemente?')">Deletar</a>
                    {% endif %}
                </div>
            </div>
        {% else %}
            <p style="color: #888;">Nenhum arquivo listado para sua conta.</p>
        {% endfor %}
    </div>
    """
    return renderizar_pagina(conteudo_home, arquivos=arquivos_finais)

# --- NOVA ROTA PEDIDA: /explore com Sistema de Filtros ---
@app.route('/explore', methods=['GET'])
def explore():
    filtro_tag = request.args.get('filter', 'all')
    arquivos_publicos = []
    
    if supabase_client:
        try:
            # Puxa apenas os registros definidos como PÚBLICOS (is_public = true)
            query = supabase_client.table("arquivos_permissao").select("*").eq("is_public", True)
            if filtro_tag != 'all':
                query = query.eq("tags", filtro_tag)
                
            res = query.execute()
            if res.data:
                arquivos_publicos = res.data
        except Exception as e:
            print(f"Erro ao carregar o Explore: {e}")
            
    conteudo_explore = """
    <h1>🌐 Explore Marketplace</h1>
    <p style="color:#aaa;">Estes são os arquivos e assets que a comunidade liberou para acesso livre</p>
    <div style="margin: 10px 0;">
        <a href="/" class="btn" style="background:#4b5563;">← Voltar para a Home</a>
    </div>
    <hr>
    
    <div class="filter-container">
        <strong>Filtrar por Tipo:</strong>
        <a href="/explore?filter=all" class="btn" style="background: {% if current_filter == 'all' %}#06b6d4{% else %}#2a2a2a{% endif %}; font-size:13px;">Tudo</a>
        <a href="/explore?filter=script" class="btn" style="background: {% if current_filter == 'script' %}#06b6d4{% else %}#2a2a2a{% endif %}; font-size:13px;">Scripts (.lua / .py)</a>
        <a href="/explore?filter=asset" class="btn" style="background: {% if current_filter == 'asset' %}#06b6d4{% else %}#2a2a2a{% endif %}; font-size:13px;">Assets (.rbxl / Models)</a>
        <a href="/explore?filter=chat" class="btn" style="background: {% if current_filter == 'chat' %}#06b6d4{% else %}#2a2a2a{% endif %}; font-size:13px;">Chats (.txt)</a>
    </div>
    
    <h3>Recursos Disponíveis ({{ arquivos|length }})</h3>
    <div style="margin-top: 15px;">
        {% for arq in arquivos %}
            <div class="file-item">
                <div style="text-align: left;">
                    <a class="file-name" href="/uploads/{{ arq.filename }}" target="_blank">📦 {{ arq.filename }}</a>
                    <span class="badge badge-tag">{{ arq.tags }}</span>
                    {% if arq.description %}<br><small style="color:#aaa;">{{ arq.description }}</small>{% endif %}
                </div>
                <div class="actions">
                    <button class="btn btn-copy" onclick="copiarTexto(window.location.origin + '/uploads/{{ arq.filename }}')">Copiar Link</button>
                </div>
            </div>
        {% else %}
            <p style="color: #888;">Nenhum arquivo público encontrado para esta categoria.</p>
        {% endfor %}
    </div>
    """
    return renderizar_pagina(conteudo_explore, arquivos=arquivos_publicos, current_filter=filtro_tag)

@app.route('/login', methods=['GET', 'POST'])
def login():
    erro = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == "admin" and password == "studio123":
            user = User("admin", role="adm")
            login_user(user)
            return redirect(url_for('home'))
            
        if supabase_client:
            try:
                res = supabase_client.table("users_service").select("*").eq("username", username).execute()
                if res.data and len(res.data) > 0:
                    dados_user = res.data[0]
                    if dados_user['password'] == password:
                        user = User(dados_user['username'], role=dados_user.get('role', 'user'))
                        login_user(user)
                        return redirect(url_for('home'))
            except Exception as e:
                print(f"Erro ao autenticar: {e}")
        erro = "Usuário ou senha incorretos."
    return renderizar_pagina("""
    <h2>Acesso ao Painel</h2>
    {% if erro %} <p class="err">{{ erro }}</p> {% endif %}
    <form method="POST">
        <input type="text" name="username" placeholder="Usuário" required><br>
        <input type="password" name="password" placeholder="Senha" required><br>
        <input type="submit" value="Entrar no Painel">
    </form>
    <br><a href="/users-service" style="color:#06b6d4; text-decoration:none;">Registrar-se aqui</a>
    """, erro=erro)

@app.route('/users-service', methods=['GET', 'POST'])
def users_service():
    erro = None
    sucesso = None
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        
        if username == "admin":
            erro = "O nome de usuário 'admin' é reservado."
        elif supabase_client:
            try:
                check = supabase_client.table("users_service").select("*").eq("username", username).execute()
                if check.data and len(check.data) > 0:
                    erro = "Usuário já cadastrado!"
                else:
                    supabase_client.table("users_service").insert({"username": username, "password": password, "role": "user"}).execute()
                    sucesso = "Conta criada com sucesso!"
            except Exception as e:
                erro = f"Erro no banco: {e}"
    return renderizar_pagina("""
    <h2>⚙️ Users Service - Cadastro</h2>
    {% if erro %} <p class="err">{{ erro }}</p> {% endif %}
    {% if sucesso %} <p class="sucesso">{{ sucesso }}</p> {% endif %}
    <form method="POST">
        <input type="text" name="username" placeholder="Usuário" required><br>
        <input type="password" name="password" placeholder="Senha" required><br>
        <input type="submit" value="Registrar Credencial" style="background:#22c55e;">
    </form>
    <br><a href="/login" style="color:#06b6d4; text-decoration:none;">Ir para o Login</a>
    """, erro=erro, sucesso=sucesso)

@app.route('/edit-file/<filename>', methods=['GET', 'POST'])
@login_required
def edit_file(filename):
    if current_user.role != 'adm':
        return "Acesso Negado", 403
        
    if request.method == 'POST':
        novo_conteudo = request.form.get('code_content', '')
        tag = request.form.get('tag', 'script')
        is_public = request.form.get('is_public', 'false') == 'true'
        description = request.form.get('description', '')
        try:
            supabase_client.storage.from_(BUCKET_NAME).upload(path=filename, file=novo_conteudo.encode('utf-8'), file_options={"cache-control": "3600", "upsert": "true"})
            supabase_client.table("arquivos_permissao").upsert({"filename": filename, "is_public": is_public, "tags": tag, "description": description}).execute()
            return redirect(url_for('home'))
        except Exception as e:
            print(f"Erro ao salvar: {e}")
            
    conteudo_arquivo = ""
    info_atual = {"is_public": False, "tags": "script", "description": ""}
    if supabase_client:
        try:
            conteudo_arquivo = supabase_client.storage.from_(BUCKET_NAME).download(filename).decode('utf-8')
            res_perm = supabase_client.table("arquivos_permissao").select("*").eq("filename", filename).execute()
            if res_perm.data:
                info_atual = res_perm.data[0]
        except Exception as e:
            conteudo_arquivo = f"-- Arquivo binário ou de configuração: {e}"

    return renderizar_pagina("""
    <h2>📝 Editando Configurações e Código: {{ filename }}</h2>
    <form method="POST">
        <textarea name="code_content" spellcheck="false">{{ conteudo }}</textarea><br>
        <label><b>Filtro / Tipo:</b></label><br>
        <select name="tag">
            <option value="script" {% if info.tags == 'script' %}selected{% endif %}>Script (.lua / .py)</option>
            <option value="asset" {% if info.tags == 'asset' %}selected{% endif %}>Asset (.rbxl / Models)</option>
            <option value="chat" {% if info.tags == 'chat' %}selected{% endif %}>Chat Log / TXT</option>
        </select><br>
        <label><b>Visibilidade:</b></label><br>
        <select name="is_public">
            <option value="false" {% if not info.is_public %}selected{% endif %}>Privado</option>
            <option value="true" {% if info.is_public %}selected{% endif %}>Público (Ir para o /explore)</option>
        </select><br>
        <input type="text" name="description" value="{{ info.description }}" placeholder="Descrição"><br>
        <input type="submit" value="Salvar Alterações" style="background:#22c55e;">
        <a href="/" class="btn" style="background:#4b5563;">Cancelar</a>
    </form>
    """, filename=filename, conteudo=conteudo_arquivo, info=info_atual)

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if current_user.role != 'adm':
        return "Acesso Negado", 403
    file = request.files.get('file')
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        tag = request.form.get('tag', 'script')
        is_public = request.form.get('is_public', 'false') == 'true'
        description = request.form.get('description', '')
        try:
            supabase_client.storage.from_(BUCKET_NAME).upload(path=filename, file=file.read(), file_options={"cache-control": "3600", "upsert": "true"})
            supabase_client.table("arquivos_permissao").upsert({"filename": filename, "is_public": is_public, "tags": tag, "description": description}).execute()
        except Exception as e:
            print(f"Erro no upload: {e}")
    return redirect(url_for('home'))

@app.route('/delete/<filename>')
@login_required
def delete_file(filename):
    if current_user.role != 'adm':
        return "Acesso Negado", 403
    if supabase_client:
        try:
            supabase_client.storage.from_(BUCKET_NAME).remove([filename])
            supabase_client.table("arquivos_permissao").delete().eq("filename", filename).execute()
        except Exception as e:
            print(f"Erro ao deletar: {e}")
    return redirect(url_for('home'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    if supabase_client:
        return redirect(supabase_client.storage.from_(BUCKET_NAME).get_public_url(filename))
    return "Erro", 500

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
