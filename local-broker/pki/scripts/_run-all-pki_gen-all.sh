#!/usr/bin/env bash
# Run the full issuance flow: 01 → 06 in order. Each step refuses to overwrite
# existing keys/certs; run 99-clean-certs.sh first if you need a fresh chain.
#
# Usage:
#   bash run-all-pki.sh
#   ./run-all-pki.sh    # after chmod +x

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:?}")" && pwd)"
cd "$SCRIPT_DIR"

STEPS=(
  01-create-root-ca.sh
  02-create-intermediate-ca.sh
  03-create-server-key-ecdsa.sh
  04-create-server-csr.sh
  05-sign-server-csr-with-intermediate.sh
  06-assemble-chain-and-truststore.sh
)

for step in "${STEPS[@]}"; do
  echo ""
  echo "==========> $step <=========="
  bash "$SCRIPT_DIR/$step"
done

echo ""
echo "[INFO] All steps finished. Trust store: local-broker/truststore/ca-bundle.pem"
