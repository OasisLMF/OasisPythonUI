#!/usr/bin/env bash
# Create the TLS certificate Traefik serves for HTTPS.
#
# Writes certs/ui.crt and certs/ui.key for $OASIS_UI_HOSTNAME (plus localhost).
#   - If `mkcert` is installed, its locally trusted CA is used, so browsers
#     accept the certificate without a warning (run `mkcert -install` once).
#   - Otherwise a local CA is created with openssl (certs/oasis-local-ca.crt);
#     import that CA into your browser / OS trust store to remove the warning.
#
# Existing certificates covering the hostname are kept, so you can drop your
# own certs/ui.crt and certs/ui.key in place (e.g. from your organisation's CA).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)/certs"
HOSTNAME="${OASIS_UI_HOSTNAME:-ui.oasis.local}"
CRT="$CERT_DIR/ui.crt"
KEY="$CERT_DIR/ui.key"
CA_CRT="$CERT_DIR/oasis-local-ca.crt"
CA_KEY="$CERT_DIR/oasis-local-ca.key"

mkdir -p "$CERT_DIR"

if [ -f "$CRT" ] && [ -f "$KEY" ] \
   && openssl x509 -in "$CRT" -noout -checkend 604800 >/dev/null 2>&1 \
   && openssl x509 -in "$CRT" -noout -ext subjectAltName 2>/dev/null | grep -q "DNS:${HOSTNAME}\b"; then
    echo "  -> Using existing certificate for ${HOSTNAME} ($CRT)"
    exit 0
fi

if command -v mkcert >/dev/null 2>&1; then
    echo "  -> Creating certificate for ${HOSTNAME} with mkcert"
    mkcert -cert-file "$CRT" -key-file "$KEY" "$HOSTNAME" localhost 127.0.0.1 >/dev/null 2>&1
    echo "     If your browser still warns, run 'mkcert -install' once to trust mkcert's CA."
    exit 0
fi

if [ ! -f "$CA_CRT" ] || [ ! -f "$CA_KEY" ]; then
    echo "  -> Creating local certificate authority ($CA_CRT)"
    openssl req -x509 -new -nodes -newkey rsa:2048 -sha256 -days 3650 \
        -keyout "$CA_KEY" -out "$CA_CRT" -subj "/CN=Oasis local development CA" >/dev/null 2>&1
    chmod 600 "$CA_KEY"
fi

echo "  -> Creating certificate for ${HOSTNAME} signed by the local CA"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cat > "$TMP/ext.cnf" <<EOF
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = DNS:${HOSTNAME}, DNS:localhost, IP:127.0.0.1
EOF
openssl req -new -nodes -newkey rsa:2048 -keyout "$KEY" -out "$TMP/ui.csr" \
    -subj "/CN=${HOSTNAME}" >/dev/null 2>&1
openssl x509 -req -in "$TMP/ui.csr" -CA "$CA_CRT" -CAkey "$CA_KEY" -CAcreateserial \
    -out "$CRT" -days 825 -sha256 -extfile "$TMP/ext.cnf" >/dev/null 2>&1
chmod 600 "$KEY"

cat <<EOF
     Browsers will warn about this certificate until the local CA is trusted:
       - Chrome/Edge (Linux):  certutil -d sql:\$HOME/.pki/nssdb -A -t "C,," -n oasis-local -i $CA_CRT
       - Firefox:              Settings > Privacy & Security > Certificates > Import $CA_CRT
       - System (Ubuntu):      sudo cp $CA_CRT /usr/local/share/ca-certificates/oasis-local-ca.crt && sudo update-ca-certificates
     Or install mkcert, run 'mkcert -install', delete certs/ui.* and re-run the installer.
EOF
