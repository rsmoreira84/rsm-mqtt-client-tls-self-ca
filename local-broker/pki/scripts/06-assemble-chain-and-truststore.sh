#!/usr/bin/env bash
# Build broker full chain (server + intermediate) and client trust (ca-bundle).
# Output paths are stable for docker-compose and mqtt_client (truststore).
#
# broker-chain.pem: leaf first, then intermediate (RabbitMQ / Erlang expect chain order).
# truststore/ca-bundle.pem: **root** CA (required for OpenSSL/Python PKIX: the server
# sends leaf + intermediate; the client must trust the root to validate the chain.
# Intermediate-only trust files do not satisfy hostname verification in OpenSSL 3 / Python.

set -euo pipefail
cd "$(dirname "$0")"
# shellcheck source=00-pki-paths.sh
source ./00-pki-paths.sh

if [[ ! -f "$SERVER_CRT" || ! -f "$INT_CRT" || ! -f "$ROOT_CRT" ]]; then
  echo "[ERROR] Need server, intermediate, and root certs. Run 01-05 then retry." >&2
  exit 1
fi

mkdir -p "$CERTS_DIR" "$TRUST_DIR"
# cat order: end-entity, then issuers toward trust anchor
cat "$SERVER_CRT" "$INT_CRT" > "$BROKER_CHAIN"
cp "$ROOT_CRT" "$CLIENT_CA_BUNDLE"

echo "[INFO] Full chain (for RabbitMQ certfile or combined PEM): $BROKER_CHAIN"
echo "[INFO] Client trust (root CA for TLS verify — OpenSSL/Python): $CLIENT_CA_BUNDLE"
echo "[INFO] Set mqtt host params: host=localhost, port=8883, tls to $CLIENT_CA_BUNDLE"
