#!/usr/bin/env bash
# Create the INTERMEDIATE CA: ECDSA key, CSR, signed by ROOT. Role: signs server
# leaf certs. Under policy A, only intermediate-ca.crt is distributed to the MQTT
# client (ca-bundle.pem / truststore).

set -euo pipefail
cd "$(dirname "$0")"
# shellcheck source=00-pki-paths.sh
source ./00-pki-paths.sh
pki_ensure_config_dir

if [[ ! -f "$ROOT_CRT" || ! -f "$ROOT_KEY" ]]; then
  echo "[ERROR] Run 01-create-root-ca.sh first (missing $ROOT_CRT or $ROOT_KEY)" >&2
  exit 1
fi

if [[ -f "$INT_KEY" ]]; then
  echo "[ERROR] Intermediate key already exists: $INT_KEY" >&2
  exit 1
fi

mkdir -p "$PRIVATE_DIR" "$CERTS_DIR" "$CSR_DIR"

openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out "$INT_KEY"
chmod 600 "$INT_KEY"
openssl req -config "${CONFIG_DIR}/intermediate-req.cnf" -key "$INT_KEY" -new -out "$INT_CSR" -sha256
openssl x509 -req -in "$INT_CSR" -CA "$ROOT_CRT" -CAkey "$ROOT_KEY" -CAcreateserial \
  -out "$INT_CRT" -days 1825 -sha256 \
  -extfile "${CONFIG_DIR}/intermediate-sign-v3.cnf" -extensions v3_intermediate

echo "[INFO] Intermediate CA: $INT_CRT"
echo "[INFO] Intermediate key: $INT_KEY (keep on the signing machine, not on brokers if policy says so)"
echo "[INFO] (Optional) verify: openssl x509 -in $INT_CRT -text -noout | head -n 40"
