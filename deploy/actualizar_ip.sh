#!/bin/bash
# En AWS Academy la IP pública cambia cada vez que se inicia el laboratorio.
# Este script lee la IP actual de la instancia y la escribe en el .env.
# Lo ejecuta automáticamente el servicio "colegio" cada vez que arranca.

set -e

ARCHIVO_ENV="/home/ubuntu/ES1_Backend/.env"

# Servicio de metadatos de EC2 (IMDSv2): entrega datos de la propia instancia.
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" \
    -H "X-aws-ec2-metadata-token-ttl-seconds: 60")
IP_PUBLICA=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
    http://169.254.169.254/latest/meta-data/public-ipv4)

if [ -z "$IP_PUBLICA" ]; then
    echo "No se pudo obtener la IP pública; se mantiene el .env actual."
    exit 0
fi

sed -i "s|^ALLOWED_HOSTS=.*|ALLOWED_HOSTS=$IP_PUBLICA,localhost,127.0.0.1|" "$ARCHIVO_ENV"
sed -i "s|^CSRF_TRUSTED_ORIGINS=.*|CSRF_TRUSTED_ORIGINS=http://$IP_PUBLICA|" "$ARCHIVO_ENV"

echo "IP pública actualizada en .env: $IP_PUBLICA"
