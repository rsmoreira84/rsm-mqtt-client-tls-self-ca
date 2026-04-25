"""
RabbitMQ MQTT Client
--------------------
Connects to a RabbitMQ MQTT broker using MQTT 3.1.1 protocol.

Usage:
    python mqtt_client.py <broker_folder> <host_params_file>
    python mqtt_client.py <broker_folder>   # if exactly one host-params-*.json exists

    Example:
    python mqtt_client.py ../local-broker host-params-local.json

Required files under <broker_folder>:
    - credential-params.json  : client_id, username, password (must exist; not auto-created)
    - host-params-*.json        : host, port, protocol, TLS settings (pick one via arg or auto-select when only one)

Outputs:
    Prints connection status and basic publish/subscribe test results.

"""
import sys
import os
import json
import time
import random
import string
import paho.mqtt.client as mqtt


def load_credential_params(broker_folder):
    """Load credential-params.json. The file must already exist."""
    config_path = os.path.join(broker_folder, "credential-params.json")
    if not os.path.exists(config_path):
        print(f"[ERROR] credential-params.json not found: {config_path}")
        print("[ERROR] Create this file before running the client.")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_host_params(broker_folder):
    """Print available host-params files in the broker folder as a nickname table."""
    import glob as _glob
    files = sorted(_glob.glob(os.path.join(broker_folder, "host-params-*.json")))
    if not files:
        print(f"[INFO] No host-params-*.json files found in {broker_folder}")
        return
    print("\nAvailable host configurations:")
    for f in files:
        filename = os.path.basename(f)
        nickname = filename[len("host-params-"):-len(".json")]
        print(f"  {nickname:<25}  →  {filename}")
    print(f"\nUsage: python mqtt_client.py {broker_folder} <nickname or filename>")


def load_host_params(broker_folder, host_params_arg):
    """Load host connection params. Accepts a filename or a nickname (without host-params- prefix)."""
    # If it doesn't look like a filename, treat it as a nickname
    if not host_params_arg.endswith(".json"):
        host_params_arg = f"host-params-{host_params_arg}.json"
    path = os.path.join(broker_folder, host_params_arg)
    if not os.path.exists(path):
        print(f"[ERROR] Host params file not found: {path}")
        list_host_params(broker_folder)
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[INFO] Connected to RabbitMQ MQTT broker successfully.")
        client.connected_flag = True
    else:
        print(f"[ERROR] Connection failed with code {rc}")
        client.connected_flag = False

def on_message(client, userdata, msg):
    print(f"[INFO] Received message: topic={msg.topic}, payload={msg.payload.decode()}")

def main():
    if len(sys.argv) == 3:
        # Split-config mode: credentials + host params in separate files
        broker_folder = sys.argv[1]
        host_params_file = sys.argv[2]
        cred_config = load_credential_params(broker_folder)
        host_config = load_host_params(broker_folder, host_params_file)
        config = {**cred_config, **host_config}
    elif len(sys.argv) == 2:
        broker_folder = sys.argv[1]
        cred_file = os.path.join(broker_folder, "credential-params.json")
        if not os.path.exists(cred_file):
            print(f"[ERROR] credential-params.json not found: {cred_file}")
            print("[ERROR] Create this file before running the client.")
            sys.exit(1)
        import glob as _glob
        host_files = sorted(_glob.glob(os.path.join(broker_folder, "host-params-*.json")))
        if len(host_files) == 1:
            host_params_file = os.path.basename(host_files[0])
            print(f"[INFO] Auto-selected host params: {host_params_file}")
            cred_config = load_credential_params(broker_folder)
            host_config = load_host_params(broker_folder, host_params_file)
            config = {**cred_config, **host_config}
        elif not host_files:
            print(f"[ERROR] No host-params-*.json files found in {broker_folder}")
            sys.exit(1)
        else:
            print(f"[INFO] Multiple host configurations in {broker_folder}; pick one:")
            list_host_params(broker_folder)
            sys.exit(0)
    else:
        print("Usage:")
        print("  python mqtt_client.py <broker_folder> <host_params_file>")
        print("  python mqtt_client.py <broker_folder>")
        sys.exit(1)

    broker_folder = sys.argv[1]

    mqtt.Client.connected_flag = False
    client = mqtt.Client(client_id=config["client_id"], protocol=mqtt.MQTTv311,
                         callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
    client.username_pw_set(config["username"], config["password"])
    client.on_connect = on_connect
    client.on_message = on_message

    host = config["host"]
    port = int(config["port"])

    # Enable TLS for port 8883 (MQTTS)
    if port == 8883:
        import ssl
        tls_verify = config.get("tls_cert_verification_enabled", True)
        if tls_verify:
            ca_bundle = config.get("tls_ca_bundle", None)
            if ca_bundle:
                ca_bundle = os.path.join(broker_folder, ca_bundle)
            if not ca_bundle or not os.path.exists(ca_bundle):
                print(f"[ERROR] TLS cert verification is enabled but ca_bundle not found at: {ca_bundle}")
                print(f"[ERROR] Populate truststore/ca-bundle.pem or set tls_cert_verification_enabled to false.")
                sys.exit(1)
            client.tls_set(ca_certs=ca_bundle, cert_reqs=ssl.CERT_REQUIRED)
            print(f"[INFO] TLS enabled with cert verification using: {ca_bundle}")
        else:
            client.tls_set(cert_reqs=ssl.CERT_NONE)
            client.tls_insecure_set(True)
            print("[WARN] TLS enabled but certificate verification is disabled.")

    print(f"[INFO] Connecting to {host}:{port} as {config['username']}...")
    client.connect(host, port, keepalive=60)
    client.loop_start()

    timeout = 10
    while not client.connected_flag and timeout > 0:
        time.sleep(1)
        timeout -= 1
    if not client.connected_flag:
        print("[ERROR] Could not connect to broker.")
        client.loop_stop()
        sys.exit(2)

    # Publish/subscribe test: 20 messages, 3s interval, Ctrl+C to stop
    test_topic = "test/topic"
    # client.subscribe(test_topic)
    # print(f"[INFO] Subscribed to {test_topic}")
    print(f"[INFO] Simulating the Subscription to {test_topic}")
    time.sleep(1)
    try:
        for i in range(1, 21):
            test_payload = f"hello-rabbitmq-{i}-" + ''.join(random.choices(string.ascii_lowercase, k=5))
            # client.publish(test_topic, test_payload)
            # print(f"[INFO] Published test message {i}: {test_payload}")
            print(f"[INFO] Simulating the publish of message {i}: {test_payload}")
            time.sleep(3)
    except KeyboardInterrupt:
        print("[INFO] Interrupted by user. Stopping...")
    client.loop_stop()
    client.disconnect()
    print("[INFO] Disconnected.")

if __name__ == "__main__":
    main()

