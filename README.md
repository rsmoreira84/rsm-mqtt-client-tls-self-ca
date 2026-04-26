# ACM MQTT Client

```
Yes, there is a RUNNING THE SERVICE section inside this Readme file, good luck finding that.
```

This project runs a small **Python MQTT 3.1.1 client** against a **local RabbitMQ** instance (Docker) to exercise **connection and TLS options** using a split config: **credentials** in one JSON file and **host / transport** settings in another.

---

## Configuration (`local-broker/`)

All connection files live under **`local-broker/`** at the repo root:

```
local-broker/
├── credential-params.json    ← required; create yourself (not auto-generated)
└── host-params-local.json    ← host, port, protocol, TLS settings
```

For **MQTTS** (e.g. port **8883**), you need a generated `truststore/ca-bundle.pem` and server chain under `local-broker/pki/`. The quick path is in [§ Generating PKI for MQTTS](#generating-pki-for-mqtts-optional); the CA hierarchy, file layout, and RabbitMQ details are in [docs/PKI_TLS_POLICY_A_RABBITMQ.md](docs/PKI_TLS_POLICY_A_RABBITMQ.md).

### Files

| File | Purpose |
|------|---------|
| `credential-params.json` | `client_id`, `username`, `password`. The client reads these only; it does not change the file. |
| `host-params-*.json` (e.g. `host-params-local.json`, `host-params-local-tls.json`) | `host`, `port`, `protocol`, and when using TLS: `tls_cert_verification_enabled`, `tls_ca_bundle` (path relative to `local-broker/`). |

Default Docker Compose runs **two** separate RabbitMQ nodes: plain MQTT on **1883** and MQTTS on **8883** (the latter needs PKI material under `local-broker/pki/…`). Each has the **management UI** on **http://localhost:15672** (plain broker) and **http://localhost:15673** (TLS broker). AMQP **5672** stays disabled in config. Use **`guest` / `guest`** unless you create other users.

---

## Prerequisites

- Docker and Docker Compose  
- Python 3.x  

---

## TLS / trust store (optional)

If you point `host-params-*.json` at port **8883** and enable verification, set `tls_ca_bundle` to a PEM file (for example `truststore/ca-bundle.pem`) under `local-broker/`. The bundle is the **root CA** produced by [Generating PKI for MQTTS](#generating-pki-for-mqtts-optional); see [docs/PKI_TLS_POLICY_A_RABBITMQ.md](docs/PKI_TLS_POLICY_A_RABBITMQ.md) for details.

| Field | Description |
|-------|-------------|
| `tls_cert_verification_enabled` | `true` — verify the server cert with the CA bundle. `false` — insecure (testing only). |
| `tls_ca_bundle` | Relative path, e.g. `"truststore/ca-bundle.pem"`. |

Example:

```json
"tls_cert_verification_enabled": true,
"tls_ca_bundle": "truststore/ca-bundle.pem"
```

---

## Generating PKI for MQTTS (optional)

**Full reference:** [docs/PKI_TLS_POLICY_A_RABBITMQ.md](docs/PKI_TLS_POLICY_A_RABBITMQ.md) — root → intermediate → server leaf, `broker-chain.pem`, and `truststore/ca-bundle.pem` (root CA for the Python client).

**One-shot (generates or refreshes the whole chain):** from the repo root:

```bash
cd local-broker/pki/scripts
bash _run-all-pki_gen-all.sh
```

The script runs `01-…` through `06-…` in order. If any key or cert already exists, the corresponding step stops without overwriting; remove old material first (below) and run again.

**Wipe all generated keys, CSRs, certs, and the trust store** (then regenerate):

```bash
cd local-broker/pki/scripts
bash 99-clean-certs.sh        # confirm when prompted
# or: bash 99-clean-certs.sh -y  # no prompt
```

**After a new set of certificates**, restart the TLS broker from the **repository root** so RabbitMQ reloads the mounted `broker-chain.pem` and key:

```bash
docker compose restart rabbitmq-mqtt-tls
```

(If the container was not running, `docker compose up -d` is enough; use restart when the broker is already up with old cert files in memory or cached mounts.)

---

## RUNNING THE SERVICE

### 1. Start RabbitMQ (plain MQTT 1883 and MQTTS 8883)

From the repo root, complete [Generating PKI for MQTTS](#generating-pki-for-mqtts-optional) first if you want the MQTTS node:

```bash
# Plain MQTT only (no broker-chain / key on disk)
docker compose up -d rabbitmq-mqtt-plain

# Or both: requires local-broker/pki/certs/broker-chain.pem and private/rabbitmq-server.key
docker compose up -d
```

- **1883** — `rabbitmq-mqtt-plain`, `mqtt://` (no TLS); management **http://localhost:15672**  
- **8883** — `rabbitmq-mqtt-tls`, `mqtts://` with verification against `local-broker/truststore/ca-bundle.pem`; management **http://localhost:15673** (host port maps to each container’s listener on 15672)

The compose file uses **`rabbitmq:3.13-management`** with the **MQTT** and **management** plugins enabled; published AMQP **5672** is still off (core `listeners.tcp = none` in `docker/rabbitmq/*.conf`), so from the host you get MQTT plus the dashboard only.

### 2. Python client

```bash
cd python-mqtt-client
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create **`local-broker/credential-params.json`** if it is not already there, for example:

```json
{
  "client_id": "wobbly-penguin",
  "username": "guest",
  "password": "guest"
}
```

Run (with a single `host-params-*.json` present, the client picks it automatically):

```bash
python mqtt_client.py ../local-broker
```

Or pass the file or nickname explicitly:

```bash
python mqtt_client.py ../local-broker host-params-local.json
python mqtt_client.py ../local-broker local
```

**MQTTS (TLS on port 8883):** use the `local-tls` host profile (or `host-params-local-tls.json`) after PKI and broker are in place:

```bash
cd python-mqtt-client
source .venv/bin/activate   # if you use the venv
python mqtt_client.py ../local-broker local-tls
```

If more than one `host-params-*.json` exists and you omit the second argument, the client prints the list and exits.

### 3. Unit tests

```bash
cd python-mqtt-client
source .venv/bin/activate
pytest test_mqtt_client.py -v
```

Expect **20** tests to pass (no broker required).

---

## Automation / agent notes

See [`Agents.md`](./Agents.md) for tooling and security expectations when using AI or scripted helpers in this repo.
