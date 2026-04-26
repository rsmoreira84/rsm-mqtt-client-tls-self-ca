#!/usr/bin/env bash
# Create the RABBITMQ SERVER end-entity ECDSA (P-256) private key only.
# Role: TLS private key for the broker; does NOT sign other certs. Paired with the
# server certificate produced after CSR and signing (04 + 05).

set -euo pipefail
cd "$(dirname "$0")"
# shellcheck source=00-pki-paths.sh
source ./00-pki-paths.sh

if [[ -f "$SERVER_KEY" ]]; then
  echo "[ERROR] Server key already exists: $SERVER_KEY" >&2
  exit 1
fi

mkdir -p "$PRIVATE_DIR"
openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out "$SERVER_KEY"
chmod 600 "$SERVER_KEY"
echo "[INFO] Server (leaf) private key: $SERVER_KEY"
echo "[INFO] Next: run 04-create-server-csr.sh"
