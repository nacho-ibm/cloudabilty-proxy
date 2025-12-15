# 🚀 Deploy a IBM Code Engine - Guía Completa

## 📋 Pre-requisitos

1. **IBM Cloud CLI instalado**
   ```powershell
   # Descargar e instalar desde:
   # https://cloud.ibm.com/docs/cli
   ```

2. **Plugin de Code Engine**
   ```powershell
   ibmcloud plugin install code-engine
   ```

3. **Autenticación en IBM Cloud**
   ```powershell
   ibmcloud login --sso
   # O con API key:
   ibmcloud login --apikey YOUR-API-KEY
   ```

4. **Container Registry configurado**
   ```powershell
   # Crear namespace si no tienes uno
   ibmcloud cr namespace-add cloudability-proxy
   ```

---

## 🔧 Configuración antes de deployar

### 1. Edita el script de deploy

Abre `deploy.ps1` y modifica estas variables:

```powershell
$PROJECT_NAME = "cloudability-proxy"      # Nombre de tu proyecto
$APP_NAME = "cloudability-api"            # Nombre de la app
$REGION = "us-south"                      # us-south, eu-gb, jp-tok, etc.
$NAMESPACE = "cloudability-proxy"         # Tu namespace en Container Registry
```

### 2. Verifica tu namespace

```powershell
ibmcloud cr namespace-list
```

Si no tienes uno, créalo:
```powershell
ibmcloud cr namespace-add cloudability-proxy
```

---

## 🚀 Deployment

### Opción A: PowerShell (Windows)

1. **Navega a la carpeta deploy**
   ```powershell
   cd "c:\Users\IgnacioAyerbe\Desktop\Proyectos\Orchestrate + Cloudability\deploy"
   ```

2. **Ejecuta el script**
   ```powershell
   .\deploy.ps1
   ```

### Opción B: Bash (Linux/Mac)

1. **Navega a la carpeta deploy**
   ```bash
   cd deploy
   ```

2. **Da permisos al script**
   ```bash
   chmod +x deploy.sh
   ```

3. **Ejecuta el script**
   ```bash
   ./deploy.sh
   ```

### Opción C: Manual (paso a paso)

```powershell
# 1. Login a IBM Cloud
ibmcloud login --sso

# 2. Seleccionar región
ibmcloud target -r us-south

# 3. Crear/Seleccionar proyecto Code Engine
ibmcloud ce project create --name cloudability-proxy
ibmcloud ce project select --name cloudability-proxy

# 4. Build de la imagen
ibmcloud ce build create \
    --name cloudability-build \
    --source . \
    --strategy dockerfile \
    --image icr.io/cloudability-proxy/cloudability-api:latest \
    --registry-secret icr-secret

ibmcloud ce buildrun submit --build cloudability-build --wait

# 5. Desplegar aplicación
ibmcloud ce application create \
    --name cloudability-api \
    --image icr.io/cloudability-proxy/cloudability-api:latest \
    --port 8080 \
    --min-scale 1 \
    --max-scale 3 \
    --cpu 0.25 \
    --memory 0.5G

# 6. Obtener URL
ibmcloud ce application get --name cloudability-api
```

---

## 📊 Después del deployment

### 1. Obtén la URL de tu aplicación

La URL se mostrará al final del script, algo como:
```
https://cloudability-api.abc123.us-south.codeengine.appdomain.cloud
```

### 2. Prueba que funciona

```powershell
# Health check
curl https://TU-URL-AQUI/health

# Test de autenticación
curl -X POST https://TU-URL-AQUI/api/auth/login `
  -H "Content-Type: application/json" `
  -d '{"publicKey":"16d82ca9-22d2-407a-a70e-96e25843cb1e","privateKey":"y9m0l7GKT8I90f4tWQFQztWJlu9XbXrqTaxwiR1mKTIZOapgxl9Qs0PW589H"}'
```

### 3. Actualiza el OpenAPI

Edita `cloudability-proxy-api.yaml` en la carpeta raíz:

```yaml
servers:
  - url: https://TU-URL-DE-CODE-ENGINE
    description: IBM Code Engine (Producción)
```

### 4. Reimporta en Orchestrate

1. Ve a Watsonx Orchestrate
2. Elimina el conector anterior
3. Importa el `cloudability-proxy-api.yaml` actualizado
4. Prueba los endpoints

---

## 🔍 Monitoreo y troubleshooting

### Ver logs de la aplicación

```powershell
ibmcloud ce application logs --name cloudability-api
```

### Ver estado de la aplicación

```powershell
ibmcloud ce application get --name cloudability-api
```

### Listar todas las apps

```powershell
ibmcloud ce application list
```

### Actualizar la aplicación

Si haces cambios al código:

```powershell
# Rebuild
ibmcloud ce buildrun submit --build cloudability-build --wait

# Update app
ibmcloud ce application update --name cloudability-api
```

### Ver métricas

```powershell
ibmcloud ce application events --name cloudability-api
```

---

## 💰 Costos

Code Engine tiene un tier gratuito que incluye:
- 100,000 vCPU-segundos/mes
- 200,000 GB-segundos/mes
- Suficiente para desarrollo y pruebas

Para uso en producción, revisa: https://cloud.ibm.com/codeengine/pricing

---

## 🔒 Seguridad

### Variables de entorno (si necesitas)

```powershell
ibmcloud ce application update --name cloudability-api \
    --env VAR_NAME=value
```

### Secrets (para datos sensibles)

```powershell
# Crear secret
ibmcloud ce secret create --name cloudability-secrets \
    --from-literal PUBLIC_KEY=value

# Usar en la app
ibmcloud ce application update --name cloudability-api \
    --env-from-secret cloudability-secrets
```

---

## 🗑️ Limpieza (eliminar recursos)

```powershell
# Eliminar aplicación
ibmcloud ce application delete --name cloudability-api

# Eliminar proyecto completo
ibmcloud ce project delete --name cloudability-proxy
```

---

## ✅ Checklist de deployment

- [ ] IBM Cloud CLI instalado
- [ ] Plugin Code Engine instalado
- [ ] Autenticado en IBM Cloud
- [ ] Namespace en Container Registry creado
- [ ] Variables en deploy.ps1 configuradas
- [ ] Script de deploy ejecutado exitosamente
- [ ] URL de la aplicación obtenida
- [ ] Health check respondiendo OK
- [ ] Endpoint /api/auth/login probado
- [ ] OpenAPI actualizado con la nueva URL
- [ ] Reimportado en Orchestrate
- [ ] Skills funcionando correctamente

---

## 🆘 Problemas comunes

### Error: "Registry secret not found"

```powershell
# Crear secret para Container Registry
ibmcloud ce registry create --name icr-secret \
    --server icr.io \
    --username iamapikey \
    --password YOUR-IBM-CLOUD-API-KEY
```

### Error: "Project not found"

```powershell
# Listar proyectos
ibmcloud ce project list

# Seleccionar proyecto correcto
ibmcloud ce project select --name cloudability-proxy
```

### Error: "Not enough CPU/Memory"

Ajusta los recursos en el script:
```powershell
--cpu 0.5 --memory 1G
```

---

## 📚 Recursos adicionales

- [IBM Code Engine Docs](https://cloud.ibm.com/docs/codeengine)
- [Code Engine CLI Reference](https://cloud.ibm.com/docs/codeengine?topic=codeengine-cli)
- [Container Registry Docs](https://cloud.ibm.com/docs/Registry)

---

**¡Listo! Tu proxy de Cloudability estará disponible 24/7 en IBM Code Engine** 🚀
