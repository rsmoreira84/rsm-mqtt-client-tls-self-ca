# Local PKI (intermediate-issued server certs, ECDSA)

Shell scripts and OpenSSL `config/*.cnf` live here. Generated keys and certificates (`private/`, `certs/`, `csr/`) and `../truststore/` are **gitignored**. After **`06-assemble-chain-and-truststore.sh`**, `../truststore/ca-bundle.pem` is the **root CA** (for the Python client’s TLS verify).

**Runbook and RabbitMQ notes:** [docs/PKI_TLS_POLICY_A_RABBITMQ.md](../../docs/PKI_TLS_POLICY_A_RABBITMQ.md)

**One-shot (runs 01 → 06):** `scripts/run-all-pki.sh` — e.g. `bash run-all-pki.sh` from `scripts/`.

**Order (manual):** `scripts/01-*.sh` … `06-*.sh` (see the doc).

**Wipe generated keys/certs** (from `local-broker/pki/scripts/`):

- `bash 99-clean-certs.sh` (works without the executable bit)
- or `chmod +x 99-clean-certs.sh` then `./99-clean-certs.sh`
- add `-y` to skip the confirmation prompt
