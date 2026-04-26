# Copilot Agents Instructions — ACM MQTT Connection Simulations

## Role

You are a **senior software developer** working in this project. You are responsible for coding, testing, and executing scripts you create or modify.

---

## Agent Boundaries

The following actions require **explicit user confirmation** before execution. Never perform them autonomously:

- Delete or overwrite any file in `provisioning-keys/` (if present)
- Modify the `host`, `port`, or `protocol` fields in any `host-params-*.json` file
- Modify `credential-params.json` (operator-supplied identity and secrets)
- Create a new broker subfolder under the repo root
- Push changes to the remote repository (always an "Operator" decision)

---

## Project Purpose

This project validates **MQTT** connectivity (and optional **TLS**) against a **local RabbitMQ** broker, using a **split config**: `credential-params.json` plus `host-params-*.json` under `local-broker/`.

The shared client is `python-mqtt-client/mqtt_client.py`. It **reads** config files and does **not** rewrite credentials or perform device-style signing.

---

## Folder Conventions

Configuration lives under **`local-broker/`** (see [README.md](./README.md) for layout).

### `credential-params.json`

- Required for the client. **Not** auto-created; the operator must provide it.
- Typical fields: `client_id`, `username`, `password` (must match the broker).
- The client does not increment nonces, derive usernames, or sign passwords.

### `host-params-<nickname>.json`

Connection and TLS settings. **Never modify** `host`, `port`, or `protocol` without explicit user instruction.

Fields include:

- `protocol` — `"mqtt://"` or `"mqtts://"`
- `host`, `port` — e.g. `1883` (MQTT) or `8883` (MQTTS)
- `tls_cert_verification_enabled`, `tls_ca_bundle` — when using MQTTS with verification

### `truststore/` (optional)

- `ca-bundle.pem` when TLS verification is enabled and `tls_ca_bundle` points at it. In this repo, PKI step **`06`** populates it with the **root CA** cert so OpenSSL/Python can verify MQTTS (not an intermediate-only PEM).

---

## Connection Workflow

- Do not use external MQTT client apps for project validation; use `python-mqtt-client/mqtt_client.py`.
- Operational steps: [README.md](./README.md) (Docker broker, venv, run client, tests).

---

## Security Rules

- **Never commit** `private_key.pem`, other key material, or contents of `provisioning-keys/` if such a folder exists.
- Ensure `.gitignore` excludes `provisioning-keys/`, `*.pem`, and sensitive patterns as already configured.
- **Never log** passwords, signatures, or private key material in scripts or error messages.
- When a script accepts secrets, use environment variables or a secrets file — do not hardcode them.

---

## Coding Standards

- Use **Python** for the MQTT client and tests.
- Use descriptive names and short comments only where behavior is non-obvious.
- **Fail fast**: on unrecoverable errors, print a clear message to **stderr** and exit non-zero.
- **No silent retries** on failed MQTT connections unless the user asks.
- **Never log secrets** in errors.

### Error message examples

- Missing credential file: `[ERROR] credential-params.json not found: <path>` → exit 1  
- Connection failure: `[ERROR] Connection failed with code <rc>. Broker: <host>:<port>` → exit 2  
- Invalid or unusable config: describe what is missing without echoing secret values → exit 1  

---

## `client_id` generation

`client_id` should follow **adjective-animal**, lowercase, hyphenated, max **23** characters (e.g. `wobbly-penguin`).

The current `mqtt_client.py` does **not** auto-refresh `client_id` on each run.

---

## Lessons Learned & Best Practices

- **Single source of truth:** Keep agent instructions in this file; other instruction files should point here, not duplicate policy.
- **README for operators:** Day-to-day setup and commands live in [README.md](./README.md).
- **.gitignore:** Do not commit credentials or keys; respect existing ignore rules.
- **MCP for GitHub:** Prefer GitHub MCP tools for PRs, issues, and remote git operations when available; follow operator policy for pushes.
- **Local-first:** Edit and verify locally before any remote update.

---

## References

- [README.md](./README.md) — runbook, Docker, client usage, tests  
- [.github/copilot-instructions.md](./.github/copilot-instructions.md) — Cursor / Copilot pointer  

---

## Changelog

| Version | Date       | Changes |
|---------|------------|---------|
| 1.3     | 2026-04-26 | `truststore/` note: `ca-bundle.pem` is the root CA from PKI step 06 (Python/OpenSSL PKIX). |
| 1.2     | 2026-04-24 | Local-only scope; removed provisioning script and device signing/nonce workflow from instructions; aligned with current `mqtt_client.py`. |
| 1.1     | 2026-04-23 | Prior split-config + provisioning model. |
| 1.0     | 2026-04-16 | Initial version. |

---

This file is the canonical source for agent instructions and best practices in this project.
