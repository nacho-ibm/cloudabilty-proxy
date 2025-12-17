"""
Cloudability Proxy Wrapper para Watsonx Orchestrate
Este servidor actúa como intermediario entre Orchestrate y Cloudability,
manejando la autenticación y devolviendo los datos en formato compatible.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)  # Permitir CORS para Orchestrate

# URLs de Cloudability
FRONTDOOR_URL = "https://frontdoor.apptio.com"
CLOUDABILITY_API_URL = "https://api.cloudability.com"
CUSTOMER_ID = "prismamediosdepago.com"
ENVIRONMENT_NAME = "poc"


@app.route('/health', methods=['GET'])
def health():
    """Endpoint de health check"""
    return jsonify({"status": "ok", "service": "cloudability-proxy"}), 200


@app.route('/api/auth/login', methods=['POST'])
def authenticate():
    """
    Autentica con Cloudability y devuelve token + environment ID en el body.
    
    Body esperado:
    {
        "publicKey": "tu-public-key",
        "privateKey": "tu-private-key"
    }
    
    Respuesta:
    {
        "success": true,
        "token": "jwt-token",
        "environmentId": "env-id"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'publicKey' not in data or 'privateKey' not in data:
            return jsonify({
                "success": false,
                "error": "publicKey y privateKey son requeridos"
            }), 400
        
        public_key = data['publicKey']
        private_key = data['privateKey']
        
        # Paso 1: Autenticar con Frontdoor
        auth_response = requests.post(
            f"{FRONTDOOR_URL}/service/apikeylogin",
            json={
                "keyAccess": public_key,
                "keySecret": private_key
            }
        )
        
        if auth_response.status_code != 200:
            return jsonify({
                "success": False,
                "error": "Credenciales inválidas",
                "details": auth_response.text
            }), 401
        
        # Extraer token del header
        token = auth_response.headers.get("apptio-opentoken")
        
        if not token:
            return jsonify({
                "success": False,
                "error": "No se recibió el token de autenticación"
            }), 500
        
        # Paso 2: Obtener Environment ID
        env_response = requests.get(
            f"{FRONTDOOR_URL}/api/environment/{CUSTOMER_ID}/{ENVIRONMENT_NAME}",
            headers={
                "Content-Type": "application/json",
                "apptio-opentoken": token
            }
        )
        
        if env_response.status_code != 200:
            return jsonify({
                "success": False,
                "error": "No se pudo obtener el Environment ID",
                "details": env_response.text
            }), 500
        
        env_data = env_response.json()
        environment_id = env_data.get("id")
        
        if not environment_id:
            return jsonify({
                "success": False,
                "error": "Environment ID no encontrado en la respuesta"
            }), 500
        
        # Devolver ambos en el body
        return jsonify({
            "success": True,
            "token": token,
            "environmentId": environment_id,
            "customer": CUSTOMER_ID,
            "environment": ENVIRONMENT_NAME
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/organizations', methods=['GET'])
def list_organizations():
    """
    Lista las organizaciones de Cloudability.
    
    Headers requeridos:
    - Authorization: Bearer {token}
    - X-Environment-Id: {environmentId}
    """
    try:
        # Obtener token del header Authorization
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                "success": False,
                "error": "Token de autenticación requerido en header Authorization"
            }), 401
        
        token = auth_header.replace('Bearer ', '')
        environment_id = request.headers.get('X-Environment-Id')
        
        if not environment_id:
            return jsonify({
                "success": False,
                "error": "Environment ID requerido en header X-Environment-Id"
            }), 400
        
        # Llamar a la API de Cloudability
        response = requests.get(
            f"{CLOUDABILITY_API_URL}/v3/organizations",
            headers={
                "Content-Type": "application/json",
                "apptio-opentoken": token,
                "apptio-current-environment": environment_id
            }
        )
        
        if response.status_code != 200:
            return jsonify({
                "success": False,
                "error": "Error al obtener organizaciones",
                "details": response.text
            }), response.status_code
        
        return jsonify({
            "success": True,
            "data": response.json()
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/business-mappings', methods=['GET'])
def list_business_mappings():
    """
    Lista los Business Mappings de Cloudability.
    
    Headers requeridos:
    - Authorization: Bearer {token}
    - X-Environment-Id: {environmentId}
    """
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                "success": False,
                "error": "Token de autenticación requerido"
            }), 401
        
        token = auth_header.replace('Bearer ', '')
        environment_id = request.headers.get('X-Environment-Id')
        
        if not environment_id:
            return jsonify({
                "success": False,
                "error": "Environment ID requerido"
            }), 400
        
        response = requests.get(
            f"{CLOUDABILITY_API_URL}/v3/business-mappings",
            headers={
                "Content-Type": "application/json",
                "apptio-opentoken": token,
                "apptio-current-environment": environment_id
            }
        )
        
        if response.status_code != 200:
            return jsonify({
                "success": False,
                "error": "Error al obtener business mappings",
                "details": response.text
            }), response.status_code
        
        return jsonify({
            "success": True,
            "data": response.json()
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/business-mappings', methods=['POST'])
def create_business_mapping():
    """
    Crea un Business Mapping en Cloudability.
    
    Headers requeridos:
    - Authorization: Bearer {token}
    - X-Environment-Id: {environmentId}
    
    Body: Estructura del Business Mapping
    """
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                "success": False,
                "error": "Token de autenticación requerido"
            }), 401
        
        token = auth_header.replace('Bearer ', '')
        environment_id = request.headers.get('X-Environment-Id')
        
        if not environment_id:
            return jsonify({
                "success": False,
                "error": "Environment ID requerido"
            }), 400
        
        mapping_data = request.get_json()
        
        if not mapping_data:
            return jsonify({
                "success": False,
                "error": "Body del Business Mapping requerido"
            }), 400
        
        # Validar que tenga el campo 'name' requerido
        if 'name' not in mapping_data or not mapping_data.get('name'):
            return jsonify({
                "success": False,
                "error": "El campo 'name' es requerido y no puede estar vacío"
            }), 400
        
        # Envolver en objeto 'result' como espera Cloudability
        cloudability_payload = {
            "result": mapping_data
        }
        
        response = requests.post(
            f"{CLOUDABILITY_API_URL}/v3/business-mappings",
            json=cloudability_payload,
            headers={
                "Content-Type": "application/json",
                "apptio-opentoken": token,
                "apptio-current-environment": environment_id
            }
        )
        
        if response.status_code not in [200, 201]:
            return jsonify({
                "success": False,
                "error": "Error al crear business mapping",
                "details": response.text
            }), response.status_code
        
        return jsonify({
            "success": True,
            "data": response.json()
        }), 201
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    print(f"""
    ╔═══════════════════════════════════════════════════════╗
    ║   Cloudability Proxy Server                           ║
    ║   Servidor corriendo en http://localhost:{port}       ║
    ╚═══════════════════════════════════════════════════════╝
    
    Endpoints disponibles:
    - GET  /health                      → Health check
    - POST /api/auth/login              → Autenticación completa
    - GET  /api/organizations           → Listar organizaciones
    - GET  /api/business-mappings       → Listar business mappings
    - POST /api/business-mappings       → Crear business mapping
    
    Presiona Ctrl+C para detener el servidor
    """)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
