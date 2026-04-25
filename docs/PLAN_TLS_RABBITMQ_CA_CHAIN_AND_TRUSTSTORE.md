# Plan: TLS for local RabbitMQ (CA hierarchy, chain, client truststore)

Development plan for running RabbitMQ in Docker with **MQTTS** using certificates issued under a **custom CA hierarchy** (root → intermediate → server leaf), with the Python MQTT client **verifying the server certificate** via a **`ca-bundle.pem`** truststore—aligned with common enterprise practice (operational trust on **intermediates**, root often tightly controlled).

This document is a **plan only**; implementation happens after review and approval.

---

## 1. Goals and success criteria

**Goal:** Run RabbitMQ in Docker with **MQTTS** (e.g. port **8883**), using a **server certificate** issued under **your CA hierarchy** (root → intermediate → server leaf). The Python client must **verify the server certificate** during TLS using a **`ca-bundle.pem`** that reflects how your company thinks about trust (typically **intermediate-focused**, root optional on the client depending on policy).

**Done when:**

- TLS handshake completes with **verification enabled** (`tls_cert_verification_enabled: true`).
- The server presents a **correct chain** (leaf + intermediate(s) as required).
- The client truststore contains only what policy allows (often **intermediate(s)** as trust anchor, sometimes + root for local parity).
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
| **A. Intermediate as trust anchor** (common when root isn't shipped) | Leaf + **intermediate** (intermediate signs leaf) | **Intermediate CA cert** (and optionally extra intermediates if you had a ladder) |
| **B. Full chain validation to root** (simpler mentally, less like "no root shared") | Leaf + intermediate(s) | **Root + intermediate(s)** |

**Recommendation for strong security *and* company-like behavior:** implement **A** as the primary path: client trusts the **intermediate**; server sends **leaf + intermediate**; root exists only on the **CA signing workstation / vault simulation**, not in the repo or client image unless you explicitly want parity with a specific team's bundle.

We can still generate a root locally to **sign the intermediate**; we simply **don't deploy** the root to the client if policy says so.

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
3. Validate: verification **on** succeeds; wrong/missing intermediate in bundle **fails** (proves real validation).

---

## 7. Automation vs manual

**Phase 1 — Manual OpenSSL:** transparent, good for learning/audit; document exact commands for root → intermediate → leaf, chain file, bundle.

**Phase 2 — Script:** e.g. `generate-pki.sh` with safe defaults, non-interactive, writes to gitignored `pki/`. Optional: `openssl verify` and `openssl s_client` checks.

Implement scripts **after** this plan is approved and policy choices are fixed.

---

## 8. Security practices checklist

- **No private keys in git**; `.gitignore` + optional secret scanning.
- **Least privilege:** CA keys only where issuance happens; RabbitMQ gets **only** server key + chain.
- **Separate concerns:** root key not copied into client/runtime unless policy **B** requires it for local parity.
- **Rotation:** document re-issue and RabbitMQ reload.
- **Audit:** committed `README-pki.md` (optional) describing **roles** of each PEM—**no** key material.

---

## 9. Execution phases (when approved)

1. **Confirm policy A vs B** for `ca-bundle.pem`.
2. **Define SANs and `host`** for Docker (`localhost` vs hostname).
3. **Generate PKI** (manual or script) into gitignored tree.
4. **Configure RabbitMQ** for MQTTS + chain; verify with `openssl s_client`.
5. **Place `truststore/ca-bundle.pem`** under `local-broker/` (or symlink from `pki/`) and add TLS `host-params`.
6. **Run `mqtt_client.py`** with verification on; adjust tests if new helpers are added.

---

## 10. Open decisions (fill in before implementation)

- **Trust anchor:** client bundle = **intermediate only**, or **intermediate + root**?
- **Hostname:** client connects to **`localhost`**, **`127.0.0.1`**, or **Docker DNS name**? (SANs must match.)
- **TLS policy:** minimum version (e.g. TLS 1.2+), cipher preferences?
- **RSA vs EC:** internal standard?

---

*Last updated: plan drafted for review; execution pending stakeholder approval.*
