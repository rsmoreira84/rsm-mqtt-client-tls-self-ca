#!/usr/bin/env bash
# Sign the server CSR with the intermediate CA, producing the leaf cert used by
# RabbitMQ for MQTTS. Extensions come from config/server-req.cnf section [v3_server].

set -euo pipefail
cd "$(dirname "$0")"
# shellcheck source=00-pki-paths.sh
source ./00-pki-paths.sh
pki_ensure_config_dir

if [[ ! -f "$INT_CRT" || ! -f "$INT_KEY" ]]; then
  echo "[ERROR] Missing intermediate cert/key. Run 02-create-intermediate-ca.sh first." >&2
  exit 1
fi
if [[ ! -f "$SERVER_CSR" ]]; then
  echo "[ERROR] Missing CSR. Run 04-create-server-csr.sh first." >&2
  exit 1
fi
if [[ -f "$SERVER_CRT" ]]; then
  echo "[ERROR] Server cert already exists: $SERVER_CRT" >&2
  exit 1
fi

mkdir -p "$CERTS_DIR"
openssl x509 -req -in "$SERVER_CSR" -CA "$INT_CRT" -CAkey "$INT_KEY" -CAcreateserial \
  -out "$SERVER_CRT" -days 90 -sha256 \
  -extfile "${CONFIG_DIR}/server-req.cnf" -extensions v3_server

echo "[INFO] Server certificate: $SERVER_CRT"
echo "[INFO] (Optional) verify: openssl x509 -in $SERVER_CRT -text -noout | grep -A3 'Subject Alternative'"
