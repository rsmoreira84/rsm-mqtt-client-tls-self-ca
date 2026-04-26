# Plan: TLS for local RabbitMQ (CA hierarchy, chain, client truststore)

Development plan for running RabbitMQ in Docker with **MQTTS** using certificates issued under a **custom CA hierarchy** (root → intermediate → server leaf), with the Python MQTT client **verifying the server certificate** via a **`ca-bundle.pem`** that includes the **root CA** (see §9.1). The **intermediate** still performs day-to-day signing; the plan’s “policy A” label refers to that issuance split, not to intermediate-only client PEMs.

This document is a **plan only**; implementation happens after review and approval.

---

## 1. Goals and success criteria

**Goal:** Run RabbitMQ in Docker with **MQTTS** (e.g. port **8883**), using a **server certificate** issued under **your CA hierarchy** (root → intermediate → server leaf). The Python client must **verify the server certificate** during TLS using a **`ca-bundle.pem`**.

**Done when:**

- TLS handshake completes with **verification enabled** (`tls_cert_verification_enabled: true`).
- The server presents a **correct chain** (leaf + intermediate(s) as required).
- The client truststore is sufficient for the **verifier in use** (this repo: **root CA in `ca-bundle.pem`** for OpenSSL 3 / Python PKIX; see §9.1).
- Private keys and signing keys are **not committed**; layout and docs are clear.

---

## 2. PKI model ("root not shared")

Many organizations:

- Keep the **root CA** in a **highly controlled** place (HSM, offline ceremony, few people).
- Use one or more **intermediate CAs** for day-to-day signing (RabbitMQ cert, device certs, etc.).
- Distribute to relying parties a **trust bundle** that often includes **intermediate CA cert(s)** and sometimes **not** the root, depending on whether the root is already in a corporate trust store or the intermediate is explicitly pinned as an anchor.

For **local simulation**, we still **create** a root and intermediate (otherwise there is no realistic chain), but we **decide what goes in the client truststore** to match your company's rule:

| Policy flavor | What RabbitMQ sends (chain file / config) | What client `ca-bundle.pem` contains |
|---------------|--------------------------------------------|--------------------------------------|
| **A. Intermediate as operational anchor** (intermediate issues leaves; root may stay offline) | Leaf + **intermediate** (intermediate signs leaf) | *Idealized:* intermediate only — **does not** work with stock **Python + OpenSSL** path validation for this hierarchy (fails: *unable to get issuer certificate*). |
| **B. PKIX to root in the client file** (this repo) | Leaf + intermediate(s) | **Root CA** — server chain completes validation (same pattern as trusting a public CA root). |

**Operational “policy A” in this project** still means: the **intermediate** signs the server cert; the **root** only signs the intermediate. **Client** `ca-bundle.pem` follows row **B**: copy of **`root-ca.crt`**, so `mqtt_client.py` can verify the broker’s **leaf + intermediate** chain. A future corporate deployment might install the root in a **system** store instead of this file, but the anchor is still the root for PKIX.

---

## 3. Certificate details (must be correct or TLS fails)

- **Key algorithm:** RSA 3072+ or **EC P-256/P-384** (pick one stack-wide; confirm RabbitMQ/Erlang OpenSSL compatibility).
- **Server leaf:**
  - **Subject Alternative Name (SAN):** must include the hostname the client uses (`localhost` if you connect to `localhost`, and/or Docker service name if you connect by name). **CN-only is insufficient** for modern verifiers.
  - **EKU:** serverAuth (typical for TLS server certs).
  - **Key usage:** digitalSignature, keyEncipherment (RSA) or appropriate for EC.
- **CA certs:** `CA:TRUE`, `pathlen` set correctly on root vs intermediate.
- **Validity:** short-ish for leaf (e.g. 30–90 days in prod mindset); longer for CA in lab is OK but document it.
- **Chain order:** when configuring the broker, **leaf first**, then **intermediate(s)** (per RabbitMQ/Erlang TLS expectations).

---

## 4. Artifact layout (repo-friendly, secrets-safe)

Proposed directories (exact names TBD at implementation):

- `local-broker/pki/` or top-level `pki/` — **gitignored** entirely, or only `public/` committed.
  - `private/` — root key, intermediate key, server key (**never commit**).
  - `certs/` — PEMs: `root-ca.crt`, `intermediate-ca.crt`, `rabbitmq-server.crt`, `rabbitmq-server.key`, **`rabbitmq-chain.pem`** (leaf + intermediate).
  - `truststore/` — **`ca-bundle.pem`** for the client: per policy **A** or **B** above.

**`.gitignore`:** ensure `pki/private/`, `*.key`, and any generated PEMs you don't want shared are excluded; optionally allow **only** a `README` under `pki/` explaining generation.

---

## 5. Docker / RabbitMQ TLS

1. **Enable TLS listeners** in RabbitMQ for **MQTT over TLS** (port **8883**; must match `host-params`).
2. Mount **server private key** + **certificate chain** (and any additional PEM paths required by RabbitMQ config style).
3. **Do not** rely on a lone self-signed leaf without chain; always configure **chain** so clients can build a path to the trust anchor.
4. **Management UI (15672):** optional separate TLS scope; **MQTT TLS first** reduces initial work.

**Deliverable:** updated **`docker-compose.yml`** (volumes, env, `rabbitmq.conf` / advanced config) or a small init pattern (config file mounted read-only).

---

## 6. Client (`mqtt_client.py` / config)

1. Add **`host-params-*.json`** for MQTTS, e.g. `host-params-local-tls.json`:
   - `port`: **8883**
   - `protocol`: `mqtts://` (if used for documentation; TLS behavior follows port + client `tls_set`).
   - `tls_cert_verification_enabled`: **true**
   - `tls_ca_bundle`: path relative to `local-broker/`, e.g. `truststore/ca-bundle.pem`
2. Confirm **hostname in SAN** matches **`host`** (e.g. `localhost` in SAN if `host` is `localhost`).
3. Validate: verification **on** succeeds; wrong or missing **root** in the bundle (or a wrong chain on the server) **fails** (proves real validation).

---

## 7. Automation vs manual

**Phase 1 — Manual OpenSSL:** transparent, good for learning/audit; document exact commands for root → intermediate → leaf, chain file, bundle.

**Phase 2 — Script:** e.g. `generate-pki.sh` with safe defaults, non-interactive, writes to gitignored `pki/`. Optional: `openssl verify` and `openssl s_client` checks.

Implement scripts **after** this plan is approved and policy choices are fixed.

---

## 8. Security practices checklist

- **No private keys in git**; `.gitignore` + optional secret scanning.
- **Least privilege:** CA keys only where issuance happens; RabbitMQ gets **only** server key + chain.
- **Separate concerns:** root *private key* never on clients; root *certificate* is in the client `ca-bundle.pem` here so the TLS stack can verify the chain (or use a system-wide trust store in production).
- **Rotation:** document re-issue and RabbitMQ reload.
- **Audit:** committed `README-pki.md` (optional) describing **roles** of each PEM—**no** key material.

---

## 9. Execution phases (when approved)

1. **Align client bundle with the TLS verifier** — this repo uses **root in `ca-bundle.pem`** (see §9.1); issuance model remains intermediate-signs-leaf.
2. **Define SANs and `host`** for Docker (`localhost` vs hostname).
3. **Generate PKI** (manual or script) into gitignored tree.
4. **Configure RabbitMQ** for MQTTS + chain; verify with `openssl s_client`.
5. **Place `truststore/ca-bundle.pem`** under `local-broker/` (or symlink from `pki/`) and add TLS `host-params`.
6. **Run `mqtt_client.py`** with verification on; adjust tests if new helpers are added.

### 9.1 Client truststore and issuance model

**Issuance (policy A):** the **intermediate** issues the server (and other) leaf certificates; the **root** only issues the intermediate. That keeps day-to-day signing on the intermediate key, as in many enterprises.

**Client `ca-bundle.pem` (required for this Python client):** contains the **root CA** certificate (written by `06-assemble-chain-and-truststore.sh` from `root-ca.crt`). **Reason:** the broker presents **leaf + intermediate**; OpenSSL 3 and Python build a path to a trust anchor. An **intermediate-only** PEM in `tls_set` / `load_verify_locations` does **not** complete PKIX validation to an anchor in this setup and yields **`[SSL: CERTIFICATE_VERIFY_FAILED] ... unable to get issuer certificate`**. The root in the file is the standard fix; operationally, that root could instead live in a **system trust store** in production. Details: [PKI_TLS_POLICY_A_RABBITMQ.md](./PKI_TLS_POLICY_A_RABBITMQ.md).

---

## 10. Open decisions (fill in before implementation)

| Topic | Status | Recorded choice / note |
|-------|--------|------------------------|
| **Client `ca-bundle.pem`** | **Decided** | **Root CA** — see §9.1; **issuance** still intermediate-signs-leaf. |
| **Hostname / SAN** | **Decided (lab default)** | **DNS `localhost`** in `local-broker/pki/config/server-req.cnf`; `host` in JSON = **`localhost`**. Revisit if clients use IP or other names. |
| **RSA vs EC (internal standard)** | **Decided (lab scripts)** | **ECDSA P-256** in provided scripts. |
| **TLS policy** (min version, ciphers) | **Open** | Set in RabbitMQ and OS TLS stacks when you harden; not fixed in the shell scripts. |
| **Plain MQTT 1883 vs MQTTS only** | **Open** | docker-compose can expose both during migration. |

---

*Last updated: 2026-04-26 — client bundle = root CA for Python/OpenSSL; PKI runbook [PKI_TLS_POLICY_A_RABBITMQ.md](./PKI_TLS_POLICY_A_RABBITMQ.md).*
