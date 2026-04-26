#!/usr/bin/env bash
# Remove generated keys, CSRs, certificates, chain files, OpenSSL serials (.srl),
# and the client trust bundle (policy A). Does NOT delete committed config/*.cnf or scripts.
#
# If zsh says "permission denied" on ./99-clean-certs.sh, the file is not executable:
#   chmod +x 99-clean-certs.sh
# or run without +x:  bash 99-clean-certs.sh
#
# Usage:
#   ./99-clean-certs.sh           # interactive confirmation
#   ./99-clean-certs.sh -y        # no prompt (for automation)

set -euo pipefail
cd "$(dirname "$0")"
# shellcheck source=00-pki-paths.sh
source ./00-pki-paths.sh

FORCE=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    -y|--yes) FORCE=1 ;;
    -h|--help)
      echo "Usage: $0 [-y|--yes]" >&2
      exit 0
      ;;
    *)
      echo "[ERROR] Unknown option: $1 (use -h)" >&2
      exit 1
      ;;
  esac
  shift
done

clean_dir() {
  local d=$1
  if [[ ! -d "$d" ]]; then
    return 0
  fi
  shopt -s nullglob
  local f
  for f in "$d"/*; do
    rm -rf "$f"
  done
  shopt -u nullglob
}

echo "This will delete generated material under:"
echo "  $PRIVATE_DIR"
echo "  $CERTS_DIR"
echo "  $CSR_DIR"
echo "  $CLIENT_CA_BUNDLE (if present)"
echo ""
if [[ "$FORCE" -eq 0 ]]; then
  read -r -p "Type yes to continue: " ans
  if [[ "$ans" != "yes" ]]; then
    echo "[INFO] Aborted."
    exit 0
  fi
fi

clean_dir "$PRIVATE_DIR"
clean_dir "$CERTS_DIR"
clean_dir "$CSR_DIR"
if [[ -f "$CLIENT_CA_BUNDLE" ]]; then
  rm -f "$CLIENT_CA_BUNDLE"
fi

echo "[INFO] PKI artifacts removed. Re-run 01–06 to issue a new chain."
