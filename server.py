from flask import Flask, jsonify, request
import os

app = Flask(__name__)

# Rota base (Apenas teste de navegador)
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "online",
        "message": "Studio Service API ativa no Render."
    }), 200

# Rota antiga de checagem do estúdio
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

# ROTA NOVA: Envia a lista de itens para o Plugin do Studio
@app.route('/toolbox', methods=['GET'])
def get_custom_toolbox():
    return jsonify({
        "sucesso": True,
        "itens": [
            {
                "id": 1,
                "nome": "Spawn Point Oficial",
                "tipo": "Model",
                "asset_id": 1716327318  # ID de exemplo (pode ser qualquer ID de asset que funcione)
            },
            {
                "id": 2,
                "nome": "Bloco Neon Verde",
                "tipo": "Model",
                "asset_id": 511061730
            },
            {
                "id": 3,
                "nome": "Modelo de Teste ZX",
                "tipo": "Model",
                "asset_id": 60790132
            }
        ]
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
