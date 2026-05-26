#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# provision.sh  —  One-time Azure resource setup for SEP4 MAL service
#
# Run once before first deploy:
#   chmod +x .azure/provision.sh
#   ./.azure/provision.sh
#
# Prerequisites:
#   - az CLI installed and logged in  (az login)
#   - Contributor rights on the target subscription
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── EDIT THESE ────────────────────────────────────────────────────────────────
RESOURCE_GROUP="sep4-rg"
LOCATION="westeurope"
ACR_NAME="sep4malacr"             # globally unique, lowercase, no hyphens
CONTAINER_APP_ENV="sep4-env"
CONTAINER_APP_NAME="sep4-mal-app"
IMAGE_NAME="sep4-mal"

# PostgreSQL
PG_SERVER_NAME="sep4-db"          # globally unique
PG_ADMIN_USER="sep4admin"
PG_ADMIN_PASSWORD="${PG_ADMIN_PASSWORD:-}"   # pass via env var (see below)
PG_DB_NAME="sep4"

# Бэкенд другой команды — пока заглушка, обновишь позже
BACKEND_BASE_URL="${BACKEND_BASE_URL:-http://placeholder-update-me}"
# ── END EDIT ─────────────────────────────────────────────────────────────────

# Проверка пароля
if [[ -z "$PG_ADMIN_PASSWORD" ]]; then
  echo "❌  Укажи пароль для БД:"
  echo "    PG_ADMIN_PASSWORD='МойПароль123!' bash .azure/provision.sh"
  exit 1
fi

echo "==> [1/7] Creating resource group: $RESOURCE_GROUP"
az group create \
  --name "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --output none

echo "==> [2/7] Creating PostgreSQL Flexible Server: $PG_SERVER_NAME"
az postgres flexible-server create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$PG_SERVER_NAME" \
  --location "$LOCATION" \
  --admin-user "$PG_ADMIN_USER" \
  --admin-password "$PG_ADMIN_PASSWORD" \
  --sku-name "Standard_B1ms" \
  --tier "Burstable" \
  --storage-size 32 \
  --version 16 \
  --public-access "0.0.0.0" \
  --output none

echo "==> [3/7] Creating database: $PG_DB_NAME"
az postgres flexible-server db create \
  --resource-group "$RESOURCE_GROUP" \
  --server-name "$PG_SERVER_NAME" \
  --database-name "$PG_DB_NAME" \
  --output none

# Собираем connection string автоматически
DATABASE_URL="postgresql+psycopg2://${PG_ADMIN_USER}:${PG_ADMIN_PASSWORD}@${PG_SERVER_NAME}.postgres.database.azure.com:5432/${PG_DB_NAME}?sslmode=require"

echo "==> [4/7] Creating Azure Container Registry: $ACR_NAME"
az acr create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$ACR_NAME" \
  --sku Basic \
  --admin-enabled true \
  --output none

echo "==> [5/7] Creating Container Apps environment: $CONTAINER_APP_ENV"
az containerapp env create \
  --name "$CONTAINER_APP_ENV" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --output none

echo "==> [6/7] Building and pushing initial image (local Docker)"
az acr login --name "$ACR_NAME"
docker build -t "$ACR_NAME.azurecr.io/$IMAGE_NAME:initial" .
docker push "$ACR_NAME.azurecr.io/$IMAGE_NAME:initial"

echo "==> [7/7] Creating Container App: $CONTAINER_APP_NAME"
az containerapp create \
  --name "$CONTAINER_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --environment "$CONTAINER_APP_ENV" \
  --image "$ACR_NAME.azurecr.io/$IMAGE_NAME:initial" \
  --registry-server "$ACR_NAME.azurecr.io" \
  --registry-identity system \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --env-vars \
      ENVIRONMENT=production \
      DATABASE_URL="$DATABASE_URL" \
      BACKEND_BASE_URL="$BACKEND_BASE_URL" \
  --output none

echo "==> Granting Container App pull access to ACR"
APP_PRINCIPAL=$(az containerapp show \
  --name "$CONTAINER_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query "identity.principalId" -o tsv)

ACR_ID=$(az acr show \
  --name "$ACR_NAME" \
  --query "id" -o tsv)

az role assignment create \
  --assignee "$APP_PRINCIPAL" \
  --role "AcrPull" \
  --scope "$ACR_ID" \
  --output none

FQDN=$(az containerapp show \
  --name "$CONTAINER_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.configuration.ingress.fqdn" -o tsv)

echo ""
echo "✅  Всё готово!"
echo "────────────────────────────────────────────"
echo "  Resource group : $RESOURCE_GROUP"
echo "  PostgreSQL     : $PG_SERVER_NAME.postgres.database.azure.com"
echo "  Database       : $PG_DB_NAME"
echo "  ACR            : $ACR_NAME.azurecr.io"
echo "  Container App  : $CONTAINER_APP_NAME"
echo "  App URL        : https://$FQDN"
echo "────────────────────────────────────────────"
echo ""
echo "  DATABASE_URL (сохрани — нужен для DevOps variables):"
echo "  $DATABASE_URL"
echo ""
echo "  Когда получишь URL бэкенда от другой команды:"
echo "  az containerapp update \\"
echo "    --name $CONTAINER_APP_NAME \\"
echo "    --resource-group $RESOURCE_GROUP \\"
echo "    --set-env-vars BACKEND_BASE_URL=\"https://их-url.com\""