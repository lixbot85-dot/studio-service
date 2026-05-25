from flask import Flask, jsonify, request, render_template_string, redirect, url_for, abort
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
    def __init__(self, id, role='user', is_banned=False, session_version=1):
        self.id = id
        self.role = role
        self.is_banned = is_banned
        self.session_version = session_version

@login_manager.user_loader
def load_user(user_id):
    if user_id == "admin":
        return User("admin", role="adm")
    
    if supabase_client:
        try:
            res = supabase_client.table("users_service").select("*").eq("username", user_id).execute()
            if res.data and len(res.data) > 0:
                u = res.data[0]
                if u.get('is_banned', False):
                    return None
                return User(u['username'], role=u.get('role', 'user'), is_banned=False, session_version=u.get('session_version', 1))
        except Exception as e:
            print(f"Erro ao carregar usuário: {e}")
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
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #121212; color: #e0e0e0; text-align: center; padding: 30px 10px; margin: 0; }
            .container { max-width: 850px; margin: auto; background: #1e1e1e; padding: 25px; border-radius: 12px; box-shadow: 0px 4px 20px rgba(0,0,0,0.6); border: 1px solid #2d2d2d; }
            h1, h2, h3, h4 { color: #fff; margin-top: 0; }
            input[type="text"], input[type="password"], input[type="file"], textarea, select { width: 100%; max-width: 420px; padding: 12px; margin: 8px 0; border-radius: 6px; border: 1px solid #3d3d3d; background: #2a2a2a; color: #fff; box-sizing: border-box; }
            textarea { max-width: 100%; height: 180px; font-family: 'Courier New', Courier, monospace; }
            input[type="submit"], .btn { background: #06b6d4; color: white; padding: 10px 18px; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; display: inline-block; font-weight: bold; transition: background 0.2s; margin: 4px; }
            input[type="submit"]:hover, .btn:hover { background: #0891b2; }
            .btn-logout { background: #ef4444; } .btn-logout:hover { background: #dc2626; }
            .btn-del { background: #b91c1c; padding: 4px 10px; font-size: 13px; } .btn-del:hover { background: #991b1b; }
            .btn-edit { background: #eab308; color: #000; padding: 4px 10px; font-size: 13px; } .btn-edit:hover { background: #ca8a04; }
            .btn-copy { background: #4b5563; padding: 4px 10px; font-size: 13px; }
            .badge { padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; display: inline-block; margin: 2px; }
            .badge-adm { background: #a855f7; color: #fff; }
            .badge-pub { background: #2563eb; color: #fff; }
            .badge-priv { background: #4b5563; color: #fff; }
            .badge-tag { background: #14b8a6; color: #000; }
            .badge-featured { background: #eab308; color: #000; animation: pulse 2s infinite; }
            @keyframes pulse { 0% { opacity: 0.7; } 50% { opacity: 1; } 100% { opacity: 0.7; } }
            .err { color: #ef4444; font-weight: bold; } .sucesso { color: #22c55e; font-weight: bold; }
            hr { border: 0; height: 1px; background: #2d2d2d; margin: 20px 0; }
            .file-item, .user-item { display: flex; justify-content: space-between; align-items: center; background: #262626; padding: 12px 16px; margin: 8px 0; border-radius: 6px; border: 1px solid #333; }
            .file-name { font-weight: 500; color: #06b6d4; text-decoration: none; word-break: break-all; text-align: left; }
            .navbar { margin-bottom: 20px; display: flex; justify-content: center; gap: 8px; flex-wrap: wrap; }
            .grid-featured { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 12px; margin-bottom: 20px; }
            .card-featured { background: linear-gradient(135deg, #1e1b4b, #2e1065); border: 1px solid #eab308; padding: 15px; border-radius: 8px; text-align: left; position: relative; }
        </style>
        <script>
            function copiarTexto(txt) { navigator.clipboard.writeText(txt); alert("URL copiada!"); }
        </script>
    </head>
    <body>
        <div class="container">
            <div class="navbar">
                <a href="/" class="btn" style="background:#0284c7;">🏠 Home</a>
                <a href="/explore" class="btn" style="background:#2563eb;">🌐 Explore Marketplace</a>
                {% if current_user.is_authenticated %}
                    <a href="/publish" class="btn" style="background:#16a34a;">📤 Publicar Script</a>
                    {% if current_user.role == 'adm' %}
                        <a href="/panel" class="btn" style="background:#7c3aed;">⚙️ Painel de Admin</a>
                    {% endif %}
                {% endif %}
            </div>
    """ + conteudo_interno + """
        </div>
    </body>
    </html>
    """
    return render_template_string(html_completo, **contexto)

# --- ROTAS ---

@app.route('/', methods=['GET'])
def home():
    arquivos_normais = []
    arquivos_destaque = []
    
    if supabase_client:
        try:
            res_storage = supabase_client.storage.from_(BUCKET_NAME).list()
            arquivos_storage = [item['name'] for item in res_storage if item['name'] != '.emptyFolderPlaceholder']
            
            res_perm = supabase_client.table("arquivos_permissao").select("*").execute()
            perm_dict = {item['filename']: item for item in res_perm.data} if res_perm.data else {}
            
            for f in arquivos_storage:
                info = perm_dict.get(f, {"is_public": False, "tags": "script", "description": "", "owner": "admin", "is_featured": False})
                
                # Regra de exibição na Home: Admin vê tudo. Dono vê o seu. Usuários veem se for público.
                pode_ver = False
                if current_user.is_authenticated:
                    if current_user.role == 'adm' or info.get('owner') == current_user.id or info.get('is_public'):
                        pode_ver = True
                elif info.get('is_public'):
                    pode_ver = True
                    
                if pode_ver:
                    dados = {
                        "name": f,
                        "is_public": info.get('is_public', False),
                        "tag": info.get('tags', 'script'),
                        "desc": info.get('description', ''),
                        "owner": info.get('owner', 'Desconhecido'),
                        "is_featured": info.get('is_featured', False)
                    }
                    if dados['is_featured']:
                        arquivos_destaque.append(dados)
                    else:
                        arquivos_normais.append(dados)
        except Exception as e:
            print(f"Erro na home: {e}")
            
    conteudo_home = """
    <h1>Studio Service 🛠️</h1>
    <p>Status: <span style="color:#22c55e; font-weight:bold;">Servidor Ativo ☁️</span></p>
    
    {% if destaques %}
    <h3>⭐ Scripts em Destaque Moderação</h3>
    <div class="grid-featured">
        {% for arq in destaques %}
        <div class="card-featured">
            <span class="badge badge-featured">EM DESTAQUE</span>
            <h4 style="margin: 8px 0 4px 0; color:#06b6d4; word-break:break-all;">{{ arq.name }}</h4>
            <p style="font-size:12px; color:#ccc; margin: 4px 0;">{{ arq.desc }}</p>
            <div style="font-size:11px; margin-bottom:8px;">
                <span class="badge badge-tag">{{ arq.tag }}</span>
                <span style="color:#aaa;">Por: <b>{{ arq.owner }}</b></span>
            </div>
            <button class="btn btn-copy" style="width:100%;" onclick="copiarTexto(window.location.origin + '/uploads/{{ arq.name }}')">Pegar Link</button>
        </div>
        {% endfor %}
    </div>
    {% endif %}
    
    <hr>
    <h3>Arquivos do Sistema ({{ arquivos|length }})</h3>
    <div>
        {% for arq in arquivos %}
            <div class="file-item">
                <div style="text-align: left;">
                    <a class="file-name" href="/uploads/{{ arq.name }}" target="_blank">📄 {{ arq.name }}</a>
                    <span class="badge badge-tag">{{ arq.tag }}</span>
                    {% if arq.is_public %}<span class="badge badge-pub">Público</span>{% else %}<span class="badge badge-priv">Privado</span>{% endif %}
                    <br><small style="color:#aaa;">Dono: <b>{{ arq.owner }}</b> {% if arq.desc %}| {{ arq.desc }}{% endif %}</small>
                </div>
                <div class="actions">
                    <button class="btn btn-copy" onclick="copiarTexto(window.location.origin + '/uploads/{{ arq.name }}')">Copiar</button>
                    {% if current_user.is_authenticated and (current_user.role == 'adm' or arq.owner == current_user.id) %}
                        <a href="/edit-file/{{ arq.name }}" class="btn btn-edit">Editar/Visibilidade</a>
                        <a href="/delete/{{ arq.name }}" class="btn btn-del" onclick="return confirm('Excluir?')">Deletar</a>
                    {% endif %}
                </div>
            </div>
        {% endfor %}
    </div>
    """
    return renderizar_pagina(conteudo_home, arquivos=arquivos_normais, destaques=arquivos_destaque)

@app.route('/explore', methods=['GET'])
def explore():
    filtro_tag = request.args.get('filter', 'all')
    arquivos_publicos = []
    if supabase_client:
        try:
            query = supabase_client.table("arquivos_permissao").select("*").eq("is_public", True)
            if filtro_tag != 'all':
                query = query.eq("tags", filtro_tag)
            res = query.execute()
            if res.data:
                arquivos_publicos = res.data
        except Exception as e:
            print(f"Erro no explore: {e}")
            
    conteudo_explore = """
    <h1>🌐 Explore Marketplace</h1>
    <div class="filter-container" style="margin-bottom:15px;">
        <a href="/explore?filter=all" class="btn">Tudo</a>
        <a href="/explore?filter=Para Minecraft" class="btn" style="background:#15803d;">Para Minecraft ⛏️</a>
        <a href="/explore?filter=Para servidor" class="btn" style="background:#1d4ed8;">Para Servidor 🖥️</a>
        <a href="/explore?filter=Para local" class="btn" style="background:#b45309;">Para Local 💻</a>
    </div>
    {% for arq in arquivos %}
        <div class="file-item">
            <div style="text-align: left;">
                <strong style="color:#06b6d4;">{{ arq.filename }}</strong>
                <span class="badge badge-tag">{{ arq.tags }}</span>
                <br><small style="color:#aaa;">Publicado por: <b>{{ arq.owner }}</b><br>{{ arq.description }}</small>
            </div>
            <button class="btn btn-copy" onclick="copiarTexto(window.location.origin + '/uploads/{{ arq.filename }}')">Copiar Link</button>
            {% if current_user.is_authenticated and current_user.role == 'adm' %}
                <a href="/delete/{{ arq.filename }}" class="btn btn-del" style="margin-left:8px;">Moderação: Excluir</a>
            {% endif %}
        </div>
    {% endfor %}
    """
    return renderizar_pagina(conteudo_explore, arquivos=arquivos_publicos)

# --- SISTEMA DE PUBLISH PEDIDO ---
@app.route('/publish', methods=['GET', 'POST'])
@login_required
def publish():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '')
        tag = request.form.get('tag', 'Para local')
        code = request.form.get('code', '')
        
        if not title or not code:
            return renderizar_pagina("<h3>Erro: Título e Código são obrigatórios.</h3>")
            
        filename = secure_filename(title)
        if not filename.endswith(('.lua', '.txt', '.py')):
            filename += ".lua"
            
        try:
            # Sobe arquivo para o bucket
            supabase_client.storage.from_(BUCKET_NAME).upload(path=filename, file=code.encode('utf-8'), file_options={"cache-control":"3600","upsert":"true"})
            # Configura metadados públicos e vincula ao criador
            supabase_client.table("arquivos_permissao").upsert({
                "filename": filename, "is_public": True, "tags": tag, "description": description, "owner": current_user.id
            }).execute()
            return redirect(url_for('home'))
        except Exception as e:
            return renderizar_pagina(f"<h3>Erro ao publicar: {e}</h3>")
            
    return renderizar_pagina("""
    <h2>📤 Publicar Novo Script Externo</h2>
    <form method="POST">
        <input type="text" name="title" placeholder="Nome do arquivo (Ex: anti-lag ou script_local.lua)" required><br>
        <textarea name="description" placeholder="Escreva a descrição do que o seu script faz..."></textarea><br>
        <label><b>Destinação/Tag:</b></label><br>
        <select name="tag">
            <option value="Para local">Para local 💻</option>
            <option value="Para Minecraft">Para Minecraft ⛏️</option>
            <option value="Para servidor">Para servidor 🖥️</option>
        </select><br><br>
        <textarea name="code" placeholder="Cole o código fonte aqui..." style="height:250px;" required></textarea><br>
        <input type="submit" value="Publicar no Marketplace" style="background:#16a34a;">
    </form>
    """)

# --- PAINEL DE ADMINISTRAÇÃO AVANÇADO (/panel) ---
@app.route('/panel', methods=['GET', 'POST'])
@login_required
def panel():
    if current_user.role != 'adm':
        abort(403)
        
    usuarios = []
    reportes = []
    msg_sucesso = None
    
    if supabase_client:
        # Ações do Admin via formulários POST
        if request.method == 'POST':
            action = request.form.get('action')
            target_user = request.form.get('target_user')
            
            if action == 'ban':
                supabase_client.table("users_service").update({"is_banned": True, "session_version": supabase_client.table("users_service").select("session_version").eq("username", target_user).execute().data[0]['session_version']+1}).eq("username", target_user).execute()
                msg_sucesso = f"Usuário {target_user} foi banido com sucesso!"
            elif action == 'unban':
                supabase_client.table("users_service").update({"is_banned": False}).eq("username", target_user).execute()
                msg_sucesso = f"Usuário {target_user} foi desbanido!"
            elif action == 'changepass':
                nova_senha = request.form.get('new_password')
                supabase_client.table("users_service").update({"password": nova_senha}).eq("username", target_user).execute()
                msg_sucesso = f"Senha de {target_user} redefinida!"
            elif action == 'logout_user':
                # Incrementa o número da sessão, deslogando o token dele automaticamente em qualquer IP
                supabase_client.table("users_service").update({"session_version": supabase_client.table("users_service").select("session_version").eq("username", target_user).execute().data[0].get('session_version', 1)+1}).eq("username", target_user).execute()
                msg_sucesso = f"Forçado encerramento de sessão de {target_user}!"
            elif action == 'toggle_featured':
                filename = request.form.get('filename')
                estado_atual = request.form.get('current_state') == 'true'
                supabase_client.table("arquivos_permissao").update({"is_featured": not estado_atual}).eq("filename", filename).execute()
                msg_sucesso = f"Status de destaque do arquivo {filename} modificado!"
                
        # Coleta de informações para renderizar o painel
        try:
            usuarios = supabase_client.table("users_service").select("*").execute().data or []
            reportes = supabase_client.table("reports_service").select("*").execute().data or []
        except Exception as e:
            print(f"Erro ao carregar painel admin: {e}")
            
    conteudo_panel = """
    <h2>⚙️ Painel do Administrador (Controle Geral)</h2>
    {% if msg %} <p class="sucesso">{{ msg }}</p> {% endif %}
    <hr>
    
    <h3>🔍 Explorador e Gerenciador de Usuários</h3>
    <input type="text" id="userInput" onkeyup="filtrarUsuarios()" placeholder="Procurar nome de usuário rapidamente..." style="max-width:100%;">
    <div id="userList" style="margin-top:10px;">
        {% for u in users %}
            <div class="user-item" data-username="{{ u.username }}">
                <div style="text-align:left;">
                    <strong>👤 {{ u.username }}</strong> [Cargo: {{ u.role }}] 
                    {% if u.is_banned %}<span class="badge" style="background:#ef4444;">BANIDO</span>{% endif %}
                </div>
                <div style="display:flex; gap:5px; flex-wrap:wrap;">
                    <form method="POST" style="display:inline;">
                        <input type="hidden" name="target_user" value="{{ u.username }}">
                        {% if u.is_banned %}
                            <input type="hidden" name="action" value="unban">
                            <input type="submit" value="Desbanir" style="background:#22c55e; padding:4px 8px; font-size:12px;">
                        {% else %}
                            <input type="hidden" name="action" value="ban">
                            <input type="submit" value="Banir" class="btn-del" style="padding:4px 8px; font-size:12px;">
                        {% endif %}
                    </form>
                    <form method="POST" style="display:inline;">
                        <input type="hidden" name="target_user" value="{{ u.username }}">
                        <input type="hidden" name="action" value="logout_user">
                        <input type="submit" value="Deslogar Sessão" style="background:#f97316; padding:4px 8px; font-size:12px;">
                    </form>
                    <button class="btn" style="padding:4px 8px; font-size:12px; background:#4b5563;" onclick="redefinirSenha('{{ u.username }}')">Senha</button>
                </div>
            </div>
        {% endfor %}
    </div>
    
    <hr>
    <h3>🚨 Menu de Monitoramento de Reportes</h3>
    <div style="text-align:left; background:#262626; padding:12px; border-radius:6px; border:1px solid #333;">
        {% for rep in reports %}
            <p>⚠️ <b>Acusado:</b> <span style="color:#ef4444;">{{ rep.reported_user }}</span> | <b>Por:</b> {{ rep.reporter }} <br> &nbsp;&nbsp;• Motivo: <i>{{ rep.reason }}</i></p>
        {% else %}
            <p style="color:#888; text-align:center;">Nenhum reporte aberto.</p>
        {% endfor %}
    </div>
    
    <script>
    function filtrarUsuarios() {
        let input = document.getElementById('userInput').value.toLowerCase();
        let items = document.querySelectorAll('#userList .user-item');
        items.forEach(item => {
            let user = item.getAttribute('data-username').toLowerCase();
            item.style.display = user.includes(input) ? 'flex' : 'none';
        });
    }
    function redefinirSenha(user) {
        let n = prompt("Digite a nova senha para o usuário " + user + ":");
        if(n) {
            let f = document.createElement('form'); f.method = 'POST';
            f.innerHTML = `<input type="hidden" name="action" value="changepass"><input type="hidden" name="target_user" value="${user}"><input type="hidden" name="new_password" value="${n}">`;
            document.body.appendChild(f); f.submit();
        }
    }
    </script>
    """
    return renderizar_pagina(conteudo_panel, users=usuarios, reports=reportes, msg=msg_sucesso)

# --- EDIDOR DE VISIBILIDADE / CODE ---
@app.route('/edit-file/<filename>', methods=['GET', 'POST'])
@login_required
def edit_file(filename):
    info_atual = {"is_public": False, "tags": "Para local", "description": "", "owner": "admin", "is_featured": False}
    
    # Valida se o arquivo existe e busca dono original
    if supabase_client:
        res_perm = supabase_client.table("arquivos_permissao").select("*").eq("filename", filename).execute()
        if res_perm.data:
            info_atual = res_perm.data[0]
            
    # Trava de segurança: Apenas o ADMIN ou o DONO do arquivo podem gerenciar a visibilidade ou editar
    if current_user.role != 'adm' and info_atual.get('owner') != current_user.id:
        abort(403)
        
    if request.method == 'POST':
        novo_conteudo = request.form.get('code_content', '')
        tag = request.form.get('tag', 'Para local')
        is_public = request.form.get('is_public', 'false') == 'true'
        description = request.form.get('description', '')
        
        # Admin pode gerenciar destaques, usuários comuns mantêm o valor padrão
        destaque = info_atual.get('is_featured', False)
        if current_user.role == 'adm':
            destaque = request.form.get('is_featured', 'false') == 'true'
            
        try:
            supabase_client.storage.from_(BUCKET_NAME).upload(path=filename, file=novo_conteudo.encode('utf-8'), file_options={"cache-control": "3600", "upsert": "true"})
            supabase_client.table("arquivos_permissao").upsert({
                "filename": filename, "is_public": is_public, "tags": tag, "description": description, "owner": info_atual.get('owner'), "is_featured": destaque
            }).execute()
            return redirect(url_for('home'))
        except Exception as e:
            print(f"Erro ao salvar: {e}")
            
    conteudo_arquivo = ""
    try:
        conteudo_arquivo = supabase_client.storage.from_(BUCKET_NAME).download(filename).decode('utf-8')
    except:
        conteudo_arquivo = "-- Arquivo binário ou sem suporte a texto plano."

    return renderizar_pagina("""
    <h2>📝 Configurar & Editar Código</h2>
    <form method="POST">
        <textarea name="code_content" spellcheck="false" style="height:220px;">{{ conteudo }}</textarea><br>
        
        <label><b>Destinação/Tag do Script:</b></label><br>
        <select name="tag">
            <option value="Para local" {% if info.tags == 'Para local' %}selected{% endif %}>Para local 💻</option>
            <option value="Para Minecraft" {% if info.tags == 'Para Minecraft' %}selected{% endif %}>Para Minecraft ⛏️</option>
            <option value="Para servidor" {% if info.tags == 'Para servidor' %}selected{% endif %}>Para servidor 🖥️</option>
        </select><br>
        
        <label><b>Visibilidade Segura:</b></label><br>
        <select name="is_public">
            <option value="false" {% if not info.is_public %}selected{% endif %}>Privado (Apenas você e Admins veem)</option>
            <option value="true" {% if info.is_public %}selected{% endif %}>Público (Enviar para o /explore)</option>
        </select><br>
        
        {% if current_user.role == 'adm' %}
        <label><b>Moderação - Destacar na Home:</b></label><br>
        <select name="is_featured">
            <option value="false" {% if not info.is_featured %}selected{% endif %}>Não destacar</option>
            <option value="true" {% if info.is_featured %}selected{% endif %}>Colocar em Destaque ⭐</option>
        </select><br>
        {% endif %}
        
        <input type="text" name="description" value="{{ info.description }}" placeholder="Descrição explicativa do script"><br>
        <input type="submit" value="Salvar Mudanças" style="background:#22c55e;">
        <a href="/" class="btn" style="background:#4b5563;">Cancelar</a>
    </form>
    """, conteudo=conteudo_arquivo, info=info_atual)

# --- ROTAS RESTANTES (LOGIN, LOGOUT, REGISTRO, ETC) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == "admin" and password == "studio123":
            login_user(User("admin", role="adm"))
            return redirect(url_for('home'))
        if supabase_client:
            res = supabase_client.table("users_service").select("*").eq("username", username).execute()
            if res.data and res.data[0]['password'] == password:
                if res.data[0].get('is_banned', False):
                    return renderizar_pagina("<h3 class='err'>Sua conta está banida permanentemente por infração.</h3>")
                login_user(User(res.data[0]['username'], role=res.data[0].get('role', 'user')))
                return redirect(url_for('home'))
    return renderizar_pagina("<h2>Entrar no Sistema</h2><form method='POST'><input type='text' name='username' placeholder='Usuário' required><br><input type='password' name='password' placeholder='Senha' required><br><input type='submit' value='Entrar'></form><br><a href='/users-service'>Criar conta</a>")

@app.route('/users-service', methods=['GET', 'POST'])
def users_service():
    if request.method == 'POST':
        u = request.form.get('username').strip()
        p = request.form.get('password')
        if supabase_client:
            chk = supabase_client.table("users_service").select("*").eq("username", u).execute()
            if not chk.data:
                supabase_client.table("users_service").insert({"username":u, "password":p, "role":"user", "is_banned":False}).execute()
                return renderizar_pagina("<h3>Conta criada! <a href='/login'>Fazer login</a></h3>")
    return renderizar_pagina("<h2>Registro (Users Service)</h2><form method='POST'><input type='text' name='username' placeholder='Escolha o Usuário' required><br><input type='password' name='password' placeholder='Senha' required><br><input type='submit' value='Registrar'></form>")

@app.route('/delete/<filename>')
@login_required
def delete_file(filename):
    if supabase_client:
        res = supabase_client.table("arquivos_permissao").select("*").eq("filename", filename).execute()
        if res.data and (current_user.role == 'adm' or res.data[0]['owner'] == current_user.id):
            supabase_client.storage.from_(BUCKET_NAME).remove([filename])
            supabase_client.table("arquivos_permissao").delete().eq("filename", filename).execute()
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
