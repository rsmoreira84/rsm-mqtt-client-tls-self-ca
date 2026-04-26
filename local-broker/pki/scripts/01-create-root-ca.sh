#!/usr/bin/env bash
# Create the offline-style ROOT CA: ECDSA P-256 private key + self-signed cert.
# Role: only signs the intermediate. NOT shipped to MQTT clients (policy A).

set -euo pipefail
cd "$(dirname "$0")"
# shellcheck source=00-pki-paths.sh
source ./00-pki-paths.sh
pki_ensure_config_dir

mkdir -p "$PRIVATE_DIR" "$CERTS_DIR" "$CSR_DIR"
if [[ -f "$ROOT_KEY" ]]; then
  echo "[ERROR] Root key already exists: $ROOT_KEY" >&2
  echo "[ERROR] Delete it only if you intend to re-create the entire PKI." >&2
  exit 1
fi

openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out "$ROOT_KEY"
chmod 600 "$ROOT_KEY"
openssl req -config "${CONFIG_DIR}/root-ca.cnf" -key "$ROOT_KEY" -new -x509 -days 3650 -sha256 -out "$ROOT_CRT"

echo "[INFO] Root CA: $ROOT_CRT"
echo "[INFO] Root key: $ROOT_KEY (restrict access; not used on RabbitMQ or in client trust store)"
