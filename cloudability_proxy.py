"""
Cloudability Proxy Wrapper para Watsonx Orchestrate - Production Version
Este servidor actúa como intermediario entre Orchestrate y Cloudability.
Optimizado para IBM Code Engine.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# URLs de Cloudability
FRONTDOOR_URL = "https://frontdoor.apptio.com"
CLOUDABILITY_API_URL = "https://api.cloudability.com"
CUSTOMER_ID = "prismamediosdepago.com"
ENVIRONMENT_NAME = "poc"


@app.route('/', methods=['GET'])
def home():
    """Endpoint raíz"""
    return jsonify({
        "service": "Cloudability Proxy API",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "login": "/api/auth/login",
            "organizations": "/api/organizations",
            "business_mappings": "/api/business-mappings"
        }
    }), 200


@app.route('/health', methods=['GET'])
def health():
    """Endpoint de health check"""
    return jsonify({"status": "ok", "service": "cloudability-proxy"}), 200


@app.route('/api/auth/login', methods=['POST'])
def authenticate():
    """
    Autentica con Cloudability y devuelve token + environment ID en el body.
    """
    try:
        data = request.get_json()
        
        if not data or 'publicKey' not in data or 'privateKey' not in data:
            logger.warning("Missing credentials in request")
            return jsonify({
                "success": False,
                "error": "publicKey y privateKey son requeridos"
            }), 400
        
        public_key = data['publicKey']
        private_key = data['privateKey']
        
        logger.info(f"Attempting authentication for user")
        
        # Paso 1: Autenticar con Frontdoor
        auth_response = requests.post(
            f"{FRONTDOOR_URL}/service/apikeylogin",
            json={
                "keyAccess": public_key,
                "keySecret": private_key
            },
            timeout=30
        )
        
        if auth_response.status_code != 200:
            logger.error(f"Authentication failed: {auth_response.status_code}")
            return jsonify({
                "success": False,
                "error": "Credenciales inválidas",
                "details": auth_response.text
            }), 401
        
        # Extraer token del header
        token = auth_response.headers.get("apptio-opentoken")
        
        if not token:
            logger.error("Token not received in response headers")
            return jsonify({
                "success": False,
                "error": "No se recibió el token de autenticación"
            }), 500
        
        logger.info("Authentication successful, fetching environment ID")
        
        # Paso 2: Obtener Environment ID
        env_response = requests.get(
            f"{FRONTDOOR_URL}/api/environment/{CUSTOMER_ID}/{ENVIRONMENT_NAME}",
            headers={
                "Content-Type": "application/json",
                "apptio-opentoken": token
            },
            timeout=30
        )
        
        if env_response.status_code != 200:
            logger.error(f"Failed to get environment ID: {env_response.status_code}")
            return jsonify({
                "success": False,
                "error": "No se pudo obtener el Environment ID",
                "details": env_response.text
            }), 500
        
        env_data = env_response.json()
        environment_id = env_data.get("id")
        
        if not environment_id:
            logger.error("Environment ID not found in response")
            return jsonify({
                "success": False,
                "error": "Environment ID no encontrado en la respuesta"
            }), 500
        
        logger.info(f"Successfully authenticated and got environment ID")
        
        # Devolver ambos en el body
        return jsonify({
            "success": True,
            "token": token,
            "environmentId": environment_id,
            "customer": CUSTOMER_ID,
            "environment": ENVIRONMENT_NAME
        }), 200
        
    except requests.exceptions.Timeout:
        logger.error("Request timeout")
        return jsonify({
            "success": False,
            "error": "Timeout al conectar con Cloudability"
        }), 504
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/organizations', methods=['GET'])
def list_organizations():
    """Lista las organizaciones de Cloudability."""
    try:
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
        
        logger.info("Fetching organizations")
        
        response = requests.get(
            f"{CLOUDABILITY_API_URL}/v3/organizations",
            headers={
                "Content-Type": "application/json",
                "apptio-opentoken": token,
                "apptio-current-environment": environment_id
            },
            timeout=30
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to get organizations: {response.status_code}")
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
        logger.error(f"Error in list_organizations: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/business-mappings', methods=['GET'])
def list_business_mappings():
    """Lista los Business Mappings de Cloudability."""
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
        
        logger.info("Fetching business mappings")
        
        response = requests.get(
            f"{CLOUDABILITY_API_URL}/v3/business-mappings",
            headers={
                "Content-Type": "application/json",
                "apptio-opentoken": token,
                "apptio-current-environment": environment_id
            },
            timeout=30
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to get business mappings: {response.status_code}")
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
        logger.error(f"Error in list_business_mappings: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/business-mappings', methods=['POST'])
def create_business_mapping():
    """Crea un Business Mapping en Cloudability."""
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
        
        logger.info("Creating business mapping")
        
        response = requests.post(
            f"{CLOUDABILITY_API_URL}/v3/business-mappings",
            json=mapping_data,
            headers={
                "Content-Type": "application/json",
                "apptio-opentoken": token,
                "apptio-current-environment": environment_id
            },
            timeout=30
        )
        
        if response.status_code not in [200, 201]:
            logger.error(f"Failed to create business mapping: {response.status_code}")
            return jsonify({
                "success": False,
                "error": "Error al crear business mapping",
                "details": response.text
            }), response.status_code
        
        logger.info("Business mapping created successfully")
        
        return jsonify({
            "success": True,
            "data": response.json()
        }), 201
        
    except Exception as e:
        logger.error(f"Error in create_business_mapping: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == '__main__':
    # Code Engine usa la variable de entorno PORT (default 8080)
    port = int(os.getenv('PORT', 8080))
    
    logger.info(f"Starting Cloudability Proxy Server on port {port}")
    
    app.run(host='0.0.0.0', port=port, debug=False)
