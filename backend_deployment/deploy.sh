#!/usr/bin/env bash
# deploy.sh — Build and deploy VoiceScribe Lambda backend via AWS SAM
#
# Usage:
#   ./deploy.sh              # Build + deploy (reads .env for secrets)
#   ./deploy.sh --guided     # First-time guided deploy
#   ./deploy.sh --debug      # Print parsed overrides then exit
#
# Prerequisites:
#   - AWS CLI configured (aws configure)
#   - AWS SAM CLI installed (brew install aws-sam-cli)
#   - .env file in project root with all secrets

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"

echo ""
echo "  VoiceScribe — Lambda Deployment"
echo ""

# ── Load .env and build parameter overrides ──────────────────────────────────
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: .env file not found at: $ENV_FILE"
    echo "   Create it with your secrets before deploying."
    exit 1
fi

echo "Loading secrets from $ENV_FILE"

# Map .env key -> SAM parameter name (bash 3.2 compatible)
map_env_to_param() {
    case "$1" in
        POSTGRES_USER)                  echo "PostgresUser" ;;
        POSTGRES_PASSWORD)              echo "PostgresPassword" ;;
        POSTGRES_SERVER)                echo "PostgresServer" ;;
        POSTGRES_PORT)                  echo "PostgresPort" ;;
        POSTGRES_DB)                    echo "PostgresDb" ;;
        JWT_PRIVATE_KEY_B64)            echo "JwtPrivateKeyB64" ;;
        JWT_PUBLIC_KEY_B64)             echo "JwtPublicKeyB64" ;;
        TRANSCRIPTION_ENDPOINT_NAME)    echo "TranscriptionEndpointName" ;;
        TRANSLITERATION_ENDPOINT_NAME)  echo "TransliterationEndpointName" ;;
        MAIL_USERNAME)                  echo "MailUsername" ;;
        MAIL_PASSWORD)                  echo "MailPassword" ;;
        MAIL_FROM)                      echo "MailFrom" ;;
        MAIL_SERVER)                    echo "MailServer" ;;
        ESEWA_CLIENT_ID)               echo "EsewaClientId" ;;
        ESEWA_SECRET_KEY)              echo "EsewaSecretKey" ;;
        ALLOWED_ORIGINS)               echo "AllowedOrigins" ;;
        SUBNET_IDS)                    echo "SubnetIds" ;;
        SECURITY_GROUP_IDS)            echo "SecurityGroupIds" ;;
        *)                              echo "" ;;
    esac
}

OVERRIDES=""
PARAM_COUNT=0
while IFS='=' read -r key value || [ -n "$key" ]; do
    # Skip comments and blank lines
    key="$(echo "$key" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [ -z "$key" ] && continue
    case "$key" in \#*) continue ;; esac

    # Strip leading/trailing whitespace and quotes from value
    value="$(echo "$value" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//;s/^"//;s/"$//')"

    param_name="$(map_env_to_param "$key")"
    if [ -n "$param_name" ]; then
        OVERRIDES="$OVERRIDES $param_name=\"$value\""
        PARAM_COUNT=$((PARAM_COUNT + 1))
    fi
done < "$ENV_FILE"

echo "Parsed $PARAM_COUNT parameter(s) from .env"

# ── Debug mode: print what was parsed and exit ────────────────────────────────
if [ "${1:-}" = "--debug" ]; then
    echo ""
    echo "=== DEBUG: Parsed parameter overrides ==="
    echo ""
    # Print each override, masking sensitive values
    for override in $OVERRIDES; do
        param_key="$(echo "$override" | cut -d'=' -f1)"
        case "$param_key" in
            *Password*|*Secret*|*Key*|*B64*)
                echo "  $param_key = ****"
                ;;
            *)
                echo "  $override"
                ;;
        esac
    done
    echo ""
    echo "=== Required parameters check ==="
    echo "$OVERRIDES" | grep -q "SubnetIds" && echo "  SubnetIds: FOUND" || echo "  SubnetIds: MISSING - add SUBNET_IDS to .env"
    echo "$OVERRIDES" | grep -q "SecurityGroupIds" && echo "  SecurityGroupIds: FOUND" || echo "  SecurityGroupIds: MISSING - add SECURITY_GROUP_IDS to .env"
    echo "$OVERRIDES" | grep -q "PostgresUser" && echo "  PostgresUser: FOUND" || echo "  PostgresUser: MISSING"
    echo "$OVERRIDES" | grep -q "PostgresPassword" && echo "  PostgresPassword: FOUND" || echo "  PostgresPassword: MISSING"
    echo "$OVERRIDES" | grep -q "JwtPrivateKeyB64" && echo "  JwtPrivateKeyB64: FOUND" || echo "  JwtPrivateKeyB64: MISSING"
    echo "$OVERRIDES" | grep -q "JwtPublicKeyB64" && echo "  JwtPublicKeyB64: FOUND" || echo "  JwtPublicKeyB64: MISSING"
    echo ""
    exit 0
fi

# ── Build ────────────────────────────────────────────────────────────────────
echo ""
echo "Building with SAM..."
cd "$SCRIPT_DIR"

# Add project venv to PATH so SAM finds Python 3.12
export PATH="$PROJECT_ROOT/.venv/bin:$PATH"

sam build

# ── Deploy ───────────────────────────────────────────────────────────────────
echo ""
echo "Deploying..."

if [ "${1:-}" = "--guided" ]; then
    eval sam deploy --guided --parameter-overrides $OVERRIDES
else
    eval sam deploy --parameter-overrides $OVERRIDES
fi

echo ""
echo "Deployment complete!"
echo ""
echo "Next steps:"
echo "  1. Note the ApiUrl from the output above"
echo "  2. Update ALLOWED_ORIGINS to include your GitHub Pages URL"
echo "  3. Update frontend JS to point API calls to the ApiUrl"
