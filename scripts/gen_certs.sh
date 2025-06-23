#!/bin/bash

set -e

CERT_DIR="./certs"
DAYS=365
COUNTRY="UA"
STATE="Kyiv"
CITY="Kyiv"
ORG="VibeCoder LLC"

CA_SUBJ="/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/CN=TestCA"
SERVER_SUBJ="/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/CN=localhost"
CLIENT_SUBJ="/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/CN=TestClient"

echo "--- Creating certificate directory at $CERT_DIR ---"
mkdir -p "$CERT_DIR"

echo "--- Generating Certificate Authority (CA) ---"
openssl genrsa -out "$CERT_DIR/ca.key" 4096
openssl req -new -x509 -sha256 -days $DAYS -key "$CERT_DIR/ca.key" -out "$CERT_DIR/ca.crt" -subj "$CA_SUBJ"

echo "--- Generating Server Certificate ---"
openssl genrsa -out "$CERT_DIR/server.key" 4096
openssl req -new -sha256 -key "$CERT_DIR/server.key" -out "$CERT_DIR/server.csr" -subj "$SERVER_SUBJ"
openssl x509 -req -sha256 -days $DAYS -in "$CERT_DIR/server.csr" -CA "$CERT_DIR/ca.crt" -CAkey "$CERT_DIR/ca.key" -CAcreateserial -out "$CERT_DIR/server.crt"

echo "--- Generating Client Certificate ---"
openssl genrsa -out "$CERT_DIR/client.key" 4096
openssl req -new -sha256 -key "$CERT_DIR/client.key" -out "$CERT_DIR/client.csr" -subj "$CLIENT_SUBJ"
openssl x509 -req -sha256 -days $DAYS -in "$CERT_DIR/client.csr" -CA "$CERT_DIR/ca.crt" -CAkey "$CERT_DIR/ca.key" -CAcreateserial -out "$CERT_DIR/client.crt"

echo "--- Cleaning up Certificate Signing Request (CSR) files ---"
rm "$CERT_DIR"/*.csr

echo "--- Certificates generated successfully in $CERT_DIR ---"
ls -l "$CERT_DIR"

