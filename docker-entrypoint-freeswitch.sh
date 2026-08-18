#!/bin/sh
set -e

: "${HOST_IP:?HOST_IP must be set in .env or as an environment variable}"

echo "=== [ENTRYPOINT] Configuring FreeSWITCH with HOST_IP=${HOST_IP} ==="

sed -i "s/\$\${local_ip_v4}/${HOST_IP}/g" \
    /etc/freeswitch/sip_profiles/internal.xml \
    /etc/freeswitch/sip_profiles/external.xml \
    /etc/freeswitch/vars.xml 2>/dev/null || true

if [ -f /etc/freeswitch/.last_host_ip ]; then
    OLD_IP=$(cat /etc/freeswitch/.last_host_ip)

    if [ "$OLD_IP" != "$HOST_IP" ]; then
        echo "=== [ENTRYPOINT] Changing IP from ${OLD_IP} to ${HOST_IP} ==="

        sed -i "s/${OLD_IP}/${HOST_IP}/g" \
            /etc/freeswitch/sip_profiles/internal.xml \
            /etc/freeswitch/sip_profiles/external.xml \
            /etc/freeswitch/vars.xml
    fi
fi

echo "${HOST_IP}" > /etc/freeswitch/.last_host_ip

echo "=== [ENTRYPOINT] Starting FreeSWITCH ==="

exec /usr/bin/freeswitch -nc -nf