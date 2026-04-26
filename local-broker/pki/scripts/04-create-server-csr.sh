#!/usr/bin/env bash
# Create a CSR for the server leaf using server-req.cnf (includes SAN: DNS:localhost
# by default). Edit local-broker/pki/config/server-req.cnf if your MQTT host or SAN
# list changes (must stay aligned with your host-param JSON).

set -euo pipefail
cd "$(dirname "$0")"
# shellcheck source=00-pki-paths.sh
source ./00-pki-paths.sh
pki_ensure_config_dir

if [[ ! -f "$SERVER_KEY" ]]; then
  echo "[ERROR] Run 03-create-server-key-ecdsa.sh first (missing $SERVER_KEY)" >&2
  exit 1
fi

if [[ -f "$SERVER_CSR" ]]; then
  echo "[ERROR] CSR already exists: $SERVER_CSR" >&2
  exit 1
fi

mkdir -p "$CSR_DIR"
openssl req -new -key "$SERVER_KEY" -out "$SERVER_CSR" -config "${CONFIG_DIR}/server-req.cnf" -sha256
echo "[INFO] CSR: $SERVER_CSR (safe to archive; public)"
echo "[INFO] Next: run 05-sign-server-csr-with-intermediate.sh"
