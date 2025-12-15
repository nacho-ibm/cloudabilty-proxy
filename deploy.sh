#!/bin/bash

# Script de deployment a IBM Code Engine
# Este script construye y despliega el proxy de Cloudability

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   IBM Code Engine Deployment Script                  ║${NC}"
echo -e "${GREEN}║   Cloudability Proxy API                              ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

# Variables (modificar según tu configuración)
PROJECT_NAME="cloudability-proxy"
APP_NAME="cloudability-api"
REGION="us-south"  # Cambiar si usas otra región
REGISTRY="icr.io"  # IBM Container Registry
NAMESPACE="your-namespace"  # Cambiar por tu namespace

# Verificar que estás logueado en IBM Cloud
echo -e "${YELLOW}1. Verificando autenticación en IBM Cloud...${NC}"
if ! ibmcloud target > /dev/null 2>&1; then
    echo -e "${RED}Error: No estás autenticado en IBM Cloud${NC}"
    echo "Ejecuta: ibmcloud login"
    exit 1
fi
echo -e "${GREEN}✓ Autenticación OK${NC}"
echo ""

# Seleccionar o crear proyecto de Code Engine
echo -e "${YELLOW}2. Configurando Code Engine project...${NC}"
if ! ibmcloud ce project select --name ${PROJECT_NAME} > /dev/null 2>&1; then
    echo "Proyecto no existe, creando..."
    ibmcloud ce project create --name ${PROJECT_NAME}
    ibmcloud ce project select --name ${PROJECT_NAME}
fi
echo -e "${GREEN}✓ Proyecto: ${PROJECT_NAME}${NC}"
echo ""

# Build de la imagen
echo -e "${YELLOW}3. Construyendo imagen Docker...${NC}"
IMAGE_NAME="${REGISTRY}/${NAMESPACE}/${APP_NAME}:latest"

echo "Construyendo con Code Engine build..."
ibmcloud ce build create \
    --name ${APP_NAME}-build \
    --source . \
    --strategy dockerfile \
    --dockerfile Dockerfile \
    --image ${IMAGE_NAME} \
    --registry-secret icr-secret || true

ibmcloud ce buildrun submit --build ${APP_NAME}-build --wait

echo -e "${GREEN}✓ Imagen construida: ${IMAGE_NAME}${NC}"
echo ""

# Desplegar aplicación
echo -e "${YELLOW}4. Desplegando aplicación...${NC}"
ibmcloud ce application create \
    --name ${APP_NAME} \
    --image ${IMAGE_NAME} \
    --port 8080 \
    --min-scale 1 \
    --max-scale 3 \
    --cpu 0.25 \
    --memory 0.5G \
    --registry-secret icr-secret || \
ibmcloud ce application update \
    --name ${APP_NAME} \
    --image ${IMAGE_NAME}

echo -e "${GREEN}✓ Aplicación desplegada${NC}"
echo ""

# Obtener URL
echo -e "${YELLOW}5. Obteniendo URL de la aplicación...${NC}"
APP_URL=$(ibmcloud ce application get --name ${APP_NAME} --output json | grep -o '"url":"[^"]*' | cut -d'"' -f4)

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   DEPLOYMENT COMPLETADO                               ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}URL de la aplicación:${NC}"
echo -e "${YELLOW}${APP_URL}${NC}"
echo ""
echo -e "${GREEN}Endpoints disponibles:${NC}"
echo "  - ${APP_URL}/health"
echo "  - ${APP_URL}/api/auth/login"
echo "  - ${APP_URL}/api/organizations"
echo "  - ${APP_URL}/api/business-mappings"
echo ""
echo -e "${YELLOW}Próximos pasos:${NC}"
echo "1. Actualiza cloudability-proxy-api.yaml con esta URL"
echo "2. Reimporta el OpenAPI en Orchestrate"
echo "3. Prueba los endpoints"
echo ""
