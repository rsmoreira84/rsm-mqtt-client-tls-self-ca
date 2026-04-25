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

For **MQTTS** (e.g. port **8883**), add a CA bundle under `local-broker/truststore/ca-bundle.pem` and reference it from the host params file (see below).

### Files

| File | Purpose |
|------|---------|
| `credential-params.json` | `client_id`, `username`, `password`. The client reads these only; it does not change the file. |
| `host-params-local.json` | `host`, `port`, `protocol`, and when using TLS: `tls_cert_verification_enabled`, `tls_ca_bundle` (path relative to `local-broker/`). |

Default Docker Compose setup uses plain MQTT on **1883** with **`guest` / `guest`**.

---

## Prerequisites

- Docker and Docker Compose  
- Python 3.x  

---

## TLS / trust store (optional)

If you point `host-params-*.json` at port **8883** and enable verification, set `tls_ca_bundle` to a PEM file (for example `truststore/ca-bundle.pem`) under `local-broker/`.

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

## RUNNING THE SERVICE

### 1. Start RabbitMQ (MQTT on 1883)

From the repo root:

```bash
docker-compose up -d
```

Management UI: **http://localhost:15672** (default `guest` / `guest`).

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
