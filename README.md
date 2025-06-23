# Telemetry System

> A robust and efficient system designed to collect data from distributed sensors. It consists of two main components: `sensor_node` for sending data and `telemetry_sink` for receiving, processing, and securely storing it.

The system is developed using an asynchronous approach, gRPC for network communication, and supports secure connections via TLS and mTLS.

---

## 📋 Requirements

* A Unix-like Operating System (Linux, macOS)
* `bash`
* `openssl`
* `python 3.13`
* [`uv`](https://docs.astral.sh/uv/)

---

## 🚀 Setup & Running

### 1. Project Preparation

First, you need to set up the environment and generate the necessary files.

**a) Make Scripts Executable**

This command will grant execution permissions to all scripts in the `scripts/` directory.

```bash
chmod +x scripts/*.sh
```

**b) Run the Setup Script**

This script will automatically create virtual environments for both components, install all dependencies, generate certificates, and copy the `.env` file.

```bash
./scripts/local_setup.sh
```

### 2. Running the Services

Run the `telemetry_sink` (server) and `sensor_node` (client) in two separate terminal windows.

---

### Insecure Connection

The simplest way to run for local development.

**a) Run the Telemetry Sink**
```bash
cd telemetry_sink
uv run -m src --log-file telemetry.log
```

**b) Run the Sensor Node**
```bash
cd sensor_node
uv run -m src --name test_node
```

---

### TLS Connection (Client verifies Server)

This mode secures the communication channel, allowing the client to ensure it's connecting to the authentic server.

**a) Run the Telemetry Sink**
```bash
cd telemetry_sink
uv run -m src --log-file telemetry.log \
    --use-tls \
    --server-cert ../certs/server.crt \
    --server-key ../certs/server.key
```

**b) Run the Sensor Node**
> For a TLS connection, the client only needs the CA certificate to verify the server.
```bash
cd sensor_node
uv run -m src --name tls_node \
    --use-tls \
    --ca-cert ../certs/ca.crt
```

---

### mTLS Connection (Mutual Authentication)

The most secure mode, where the server and client verify each other's certificates.

**a) Run the Telemetry Sink**
```bash
cd telemetry_sink
uv run -m src --log-file telemetry.log \
    --use-tls \
    --use-mtls \
    --server-cert ../certs/server.crt \
    --server-key ../certs/server.key \
    --ca-cert ../certs/ca.crt
```

**b) Run the Sensor Node**
```bash
cd sensor_node
uv run -m src --name mtls_node \
    --use-tls \
    --use-mtls \
    --ca-cert ../certs/ca.crt \
    --client-cert ../certs/client.crt \
    --client-key ../certs/client.key
```

---

## ⚙️ Command-Line Arguments

### Telemetry Sink

| Argument | Environment Variable | Description | Default |
|:---|:---|:---|:---|
| `--bind-address` | - | The address and port for the server | `0.0.0.0:50051` |
| `--log-file` | - | Path to the output log file **(required)** | - |
| `--buffer-size` | - | Buffer size in bytes | `1024` (1 kB) |
| `--flush-interval`| - | Buffer flush interval in seconds | `30` |
| `--rate-limit` | - | Max input rate in bytes/sec | `1024` (1 kB/s) |
| `--encryption-key`| `ENCRYPTION_KEY` | 32-byte encryption key (hex) | - |
| `--use-tls` | - | Enable TLS connection | `false` |
| `--server-cert` | - | Path to the server certificate file | - |
| `--server-key` | - | Path to the server private key file | - |
| `--use-mtls` | - | Enable mutual TLS | `false` |
| `--ca-cert` | - | Path to the CA certificate file | - |

### Sensor Node

| Argument | Environment Variable | Description | Default |
|:---|:---|:---|:---|
| `--sink-address` | - | Address of the `telemetry_sink` server | `localhost:50051` |
| `--name` | - | Unique name for the sensor **(required)** | - |
| `--rate` | - | Number of messages to send per second | `1` |
| `--encryption-key`| `ENCRYPTION_KEY` | 32-byte encryption key (hex) | - |
| `--use-tls` | - | Enable TLS connection | `false` |
| `--ca-cert` | - | Path to the CA certificate file | - |
| `--use-mtls` | - | Enable mutual TLS | `false` |
| `--client-cert` | - | Path to the client certificate file | - |
| `--client-key` | - | Path to the client private key file | - |
