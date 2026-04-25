"""
Unit Tests — mqtt_client.py
----------------------------
Tests helper functions in mqtt_client.py.
MQTT broker connection is not tested here (requires a live broker).

Run:
    pytest test_mqtt_client.py -v
"""
import json
import sys

import pytest
from unittest.mock import MagicMock, patch

import mqtt_client


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_cred_folder(tmp_path):
    """Broker folder with credential-params.json."""
    config = {
        "client_id": "wobbly-penguin",
        "username": "guest",
        "password": "guest",
    }
    (tmp_path / "credential-params.json").write_text(json.dumps(config), encoding="utf-8")
    return tmp_path, config


@pytest.fixture
def tmp_cred_example_only(tmp_path):
    """Folder with only credential-params-example.json (no credential-params.json)."""
    config = {
        "client_id": "wobbly-penguin",
        "username": "guest",
        "password": "guest",
    }
    (tmp_path / "credential-params-example.json").write_text(json.dumps(config), encoding="utf-8")
    return tmp_path, config


# ---------------------------------------------------------------------------
# load_credential_params
# ---------------------------------------------------------------------------

class TestLoadCredentialParams:

    def test_loads_existing(self, tmp_cred_folder):
        folder, expected = tmp_cred_folder
        config = mqtt_client.load_credential_params(str(folder))
        assert config["client_id"] == expected["client_id"]
        assert config["username"] == expected["username"]

    def test_exits_when_file_missing(self, tmp_path):
        with pytest.raises(SystemExit) as exc_info:
            mqtt_client.load_credential_params(str(tmp_path))
        assert exc_info.value.code == 1

    def test_exits_when_only_example_exists(self, tmp_cred_example_only):
        folder, _ = tmp_cred_example_only
        with pytest.raises(SystemExit) as exc_info:
            mqtt_client.load_credential_params(str(folder))
        assert exc_info.value.code == 1
        assert not (folder / "credential-params.json").exists()


# ---------------------------------------------------------------------------
# list_host_params
# ---------------------------------------------------------------------------

class TestListHostParams:

    def test_prints_message_when_no_host_files(self, tmp_path, capsys):
        mqtt_client.list_host_params(str(tmp_path))
        captured = capsys.readouterr()
        assert "No host-params" in captured.out

    def test_lists_nicknames(self, tmp_path, capsys):
        (tmp_path / "host-params-local.json").write_text("{}", encoding="utf-8")
        (tmp_path / "host-params-tls.json").write_text("{}", encoding="utf-8")
        mqtt_client.list_host_params(str(tmp_path))
        captured = capsys.readouterr()
        assert "local" in captured.out
        assert "tls" in captured.out
        assert "host-params-local.json" in captured.out


# ---------------------------------------------------------------------------
# load_host_params
# ---------------------------------------------------------------------------

class TestLoadHostParams:

    def test_loads_by_filename(self, tmp_path):
        host_config = {
            "tls_cert_verification_enabled": True,
            "protocol": "mqtts://",
            "host": "broker.example.com",
            "port": 8883,
            "tls_ca_bundle": "truststore/ca-bundle.pem",
        }
        (tmp_path / "host-params-tls.json").write_text(json.dumps(host_config), encoding="utf-8")
        result = mqtt_client.load_host_params(str(tmp_path), "host-params-tls.json")
        assert result["host"] == "broker.example.com"
        assert result["port"] == 8883

    def test_loads_by_nickname(self, tmp_path):
        host_config = {"host": "127.0.0.1", "port": 1883}
        (tmp_path / "host-params-local.json").write_text(json.dumps(host_config), encoding="utf-8")
        result = mqtt_client.load_host_params(str(tmp_path), "local")
        assert result["host"] == "127.0.0.1"

    def test_exits_when_missing(self, tmp_path):
        with pytest.raises(SystemExit) as exc_info:
            mqtt_client.load_host_params(str(tmp_path), "host-params-nonexistent.json")
        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# on_connect / on_message
# ---------------------------------------------------------------------------

class TestOnConnect:

    def test_sets_connected_flag_true_on_rc0(self):
        client = MagicMock()
        mqtt_client.on_connect(client, None, None, 0)
        assert client.connected_flag is True

    def test_sets_connected_flag_false_on_nonzero_rc(self):
        client = MagicMock()
        mqtt_client.on_connect(client, None, None, 4)
        assert client.connected_flag is False

    def test_prints_success_on_rc0(self, capsys):
        client = MagicMock()
        mqtt_client.on_connect(client, None, None, 0)
        captured = capsys.readouterr()
        assert "[INFO]" in captured.out

    def test_prints_error_on_nonzero_rc(self, capsys):
        client = MagicMock()
        mqtt_client.on_connect(client, None, None, 5)
        captured = capsys.readouterr()
        assert "[ERROR]" in captured.out


class TestOnMessage:

    def test_prints_topic_and_payload(self, capsys):
        msg = MagicMock()
        msg.topic = "test/topic"
        msg.payload = b"hello"
        mqtt_client.on_message(None, None, msg)
        captured = capsys.readouterr()
        assert "test/topic" in captured.out
        assert "hello" in captured.out


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------

def _write_plain_host(tmp_path):
    host = {"host": "127.0.0.1", "port": 1883}
    (tmp_path / "host-params-test.json").write_text(json.dumps(host), encoding="utf-8")


def _mock_client_that_connects():
    mock_client = MagicMock()
    mock_client.connected_flag = False

    def loop_start():
        mock_client.connected_flag = True

    mock_client.loop_start.side_effect = loop_start
    return mock_client


class TestMain:

    def test_usage_exits_on_wrong_argc(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["mqtt_client.py"])
        with pytest.raises(SystemExit) as exc_info:
            mqtt_client.main()
        assert exc_info.value.code == 1

    def test_exits_when_credential_missing_two_args(self, tmp_path, monkeypatch):
        _write_plain_host(tmp_path)
        monkeypatch.setattr(sys, "argv", ["mqtt_client.py", str(tmp_path)])
        with pytest.raises(SystemExit) as exc_info:
            mqtt_client.main()
        assert exc_info.value.code == 1

    def test_exits_when_no_host_params_two_args(self, tmp_cred_folder, monkeypatch):
        folder, _ = tmp_cred_folder
        monkeypatch.setattr(sys, "argv", ["mqtt_client.py", str(folder)])
        with pytest.raises(SystemExit) as exc_info:
            mqtt_client.main()
        assert exc_info.value.code == 1

    def test_lists_hosts_when_multiple_two_args(self, tmp_cred_folder, monkeypatch, capsys):
        folder, _ = tmp_cred_folder
        (folder / "host-params-a.json").write_text(json.dumps({"host": "a", "port": 1883}))
        (folder / "host-params-b.json").write_text(json.dumps({"host": "b", "port": 1883}))
        monkeypatch.setattr(sys, "argv", ["mqtt_client.py", str(folder)])
        with pytest.raises(SystemExit) as exc_info:
            mqtt_client.main()
        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        assert "Multiple host configurations" in out
        assert "host-params-a.json" in out

    def test_runs_plain_mqtt_three_args(self, tmp_cred_folder, monkeypatch):
        folder, _ = tmp_cred_folder
        _write_plain_host(folder)
        monkeypatch.setattr(
            sys,
            "argv",
            ["mqtt_client.py", str(folder), "host-params-test.json"],
        )
        mock_client = _mock_client_that_connects()
        with patch("mqtt_client.mqtt.Client", return_value=mock_client), patch(
            "mqtt_client.time.sleep"
        ):
            mqtt_client.main()
        mock_client.connect.assert_called_once_with("127.0.0.1", 1883, keepalive=60)
        mock_client.disconnect.assert_called_once()

    def test_auto_selects_single_host_two_args(self, tmp_cred_folder, monkeypatch):
        folder, _ = tmp_cred_folder
        _write_plain_host(folder)
        monkeypatch.setattr(sys, "argv", ["mqtt_client.py", str(folder)])
        mock_client = _mock_client_that_connects()
        with patch("mqtt_client.mqtt.Client", return_value=mock_client), patch(
            "mqtt_client.time.sleep"
        ):
            mqtt_client.main()
        mock_client.connect.assert_called_once()

    def test_exits_on_tls_verify_missing_ca(self, tmp_cred_folder, monkeypatch):
        folder, _ = tmp_cred_folder
        host = {
            "host": "broker.example.com",
            "port": 8883,
            "tls_cert_verification_enabled": True,
            "tls_ca_bundle": "truststore/missing.pem",
        }
        (folder / "host-params-tls.json").write_text(json.dumps(host))
        monkeypatch.setattr(
            sys,
            "argv",
            ["mqtt_client.py", str(folder), "host-params-tls.json"],
        )
        with pytest.raises(SystemExit) as exc_info:
            mqtt_client.main()
        assert exc_info.value.code == 1

