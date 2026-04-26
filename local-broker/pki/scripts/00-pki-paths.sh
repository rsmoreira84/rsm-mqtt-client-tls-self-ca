#!/usr/bin/env bash
# shellcheck shell=bash
# Shared path layout for 01-06. Other scripts: source this file in the *same* bash process
#   source ./00-pki-paths.sh
# If you run ./00-pki-paths.sh instead, a child process is created: exports are lost when
# that process exits, so your shell will not have PKI_DIR, etc. (That is expected.)

: "${BASH_VERSION:?This project expects bash}"

# When the script is executed (./00-pki-paths.sh or bash 00-pki-paths.sh), $0 and
# BASH_SOURCE[0] are the same; when it is sourced, $0 is the caller and differs.
# shellcheck disable=SC2128
if [[ -n "${BASH_SOURCE[0]:-}" && "${BASH_SOURCE[0]}" == "$0" ]]; then
  echo "[INFO] This file was run as a program, not sourced — variables do not stay in your terminal." >&2
  _here="${BASH_SOURCE[0]}"
  echo "[INFO] In this same folder, use:  source \"${_here}\"" >&2
  echo "[INFO] For PKI, you usually run:  ./01-create-root-ca.sh  (it sources this file for you.)" >&2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:?}")" && pwd)"
export PKI_DIR="${PKI_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
export CONFIG_DIR="${PKI_DIR}/config"
export PRIVATE_DIR="${PKI_DIR}/private"
export CERTS_DIR="${PKI_DIR}/certs"
export CSR_DIR="${PKI_DIR}/csr"
# Client truststore (ca-bundle) uses root CA — see 06-assemble-chain-and-truststore.sh
export TRUST_DIR="${PKI_DIR}/../truststore"
export BROKER_DIR="${BROKER_DIR:-$(cd "$PKI_DIR/.." && pwd)}"

export ROOT_KEY="${PRIVATE_DIR}/root.key"
export ROOT_CRT="${CERTS_DIR}/root-ca.crt"
export INT_KEY="${PRIVATE_DIR}/intermediate.key"
export INT_CSR="${CSR_DIR}/intermediate.csr"
export INT_CRT="${CERTS_DIR}/intermediate-ca.crt"
export SERVER_KEY="${PRIVATE_DIR}/rabbitmq-server.key"
export SERVER_CSR="${CSR_DIR}/rabbitmq-server.csr"
export SERVER_CRT="${CERTS_DIR}/rabbitmq-server.crt"
export BROKER_CHAIN="${CERTS_DIR}/broker-chain.pem"
export CLIENT_CA_BUNDLE="${TRUST_DIR}/ca-bundle.pem"

pki_ensure_config_dir() {
  if [[ ! -d "$CONFIG_DIR" ]]; then
    echo "[ERROR] OpenSSL config directory not found: $CONFIG_DIR" >&2
    exit 1
  fi
}
