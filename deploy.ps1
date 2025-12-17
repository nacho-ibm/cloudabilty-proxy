# Script de deployment a IBM Code Engine para Windows PowerShell

# Colores no disponibles en PowerShell básico, usamos Write-Host

Write-Host "╔═══════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   IBM Code Engine Deployment Script                  ║" -ForegroundColor Green
Write-Host "║   Cloudability Proxy API                              ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

# Variables (modificar según tu configuración)
$PROJECT_NAME = "cloudability-proxy"
$APP_NAME = "cloudability-api"
$REGION = "us-south"  # Cambiar si usas otra región
$REGISTRY = "icr.io"  # IBM Container Registry
$NAMESPACE = "cr-itz-k006ub1s"  # Cambiar por tu namespace

# Verificar que estás logueado en IBM Cloud
Write-Host "1. Verificando autenticación en IBM Cloud..." -ForegroundColor Yellow
try {
    $null = ibmcloud target 2>&1
    Write-Host "✓ Autenticación OK" -ForegroundColor Green
} catch {
    Write-Host "Error: No estás autenticado en IBM Cloud" -ForegroundColor Red
    Write-Host "Ejecuta: ibmcloud login"
    exit 1
}
Write-Host ""

# Seleccionar o crear proyecto de Code Engine
Write-Host "2. Configurando Code Engine project..." -ForegroundColor Yellow
$projectExists = ibmcloud ce project select --name $PROJECT_NAME 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Proyecto no existe, creando..."
    ibmcloud ce project create --name $PROJECT_NAME
    ibmcloud ce project select --name $PROJECT_NAME
}
Write-Host "✓ Proyecto: $PROJECT_NAME" -ForegroundColor Green
Write-Host ""

# Build de la imagen
Write-Host "3. Construyendo imagen Docker..." -ForegroundColor Yellow
$IMAGE_NAME = "$REGISTRY/$NAMESPACE/$APP_NAME`:latest"

Write-Host "Construyendo con Code Engine build..."

# Crear build si no existe
ibmcloud ce build create `
    --name "$APP_NAME-build" `
    --source . `
    --strategy dockerfile `
    --dockerfile Dockerfile `
    --image $IMAGE_NAME `
    --registry-secret icr-secret 2>$null

# Ejecutar build
ibmcloud ce buildrun submit --build "$APP_NAME-build" --wait

Write-Host "✓ Imagen construida: $IMAGE_NAME" -ForegroundColor Green
Write-Host ""

# Desplegar aplicación
Write-Host "4. Desplegando aplicación..." -ForegroundColor Yellow

$appExists = ibmcloud ce application get --name $APP_NAME 2>&1
if ($LASTEXITCODE -ne 0) {
    # Crear aplicación
    ibmcloud ce application create `
        --name $APP_NAME `
        --image $IMAGE_NAME `
        --port 8080 `
        --min-scale 1 `
        --max-scale 3 `
        --cpu 0.25 `
        --memory 0.5G `
        --registry-secret icr-secret
} else {
    # Actualizar aplicación existente
    ibmcloud ce application update `
        --name $APP_NAME `
        --image $IMAGE_NAME
}

Write-Host "✓ Aplicación desplegada" -ForegroundColor Green
Write-Host ""

# Obtener URL
Write-Host "5. Obteniendo URL de la aplicación..." -ForegroundColor Yellow
$appInfo = ibmcloud ce application get --name $APP_NAME --output json | ConvertFrom-Json
$APP_URL = $appInfo.status.url

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   DEPLOYMENT COMPLETADO                               ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "URL de la aplicación:" -ForegroundColor Green
Write-Host $APP_URL -ForegroundColor Yellow
Write-Host ""
Write-Host "Endpoints disponibles:" -ForegroundColor Green
Write-Host "  - $APP_URL/health"
Write-Host "  - $APP_URL/api/auth/login"
Write-Host "  - $APP_URL/api/organizations"
Write-Host "  - $APP_URL/api/business-mappings"
Write-Host ""
Write-Host "Próximos pasos:" -ForegroundColor Yellow
Write-Host "1. Actualiza cloudability-proxy-api.yaml con esta URL"
Write-Host "2. Reimporta el OpenAPI en Orchestrate"
Write-Host "3. Prueba los endpoints"
Write-Host ""

