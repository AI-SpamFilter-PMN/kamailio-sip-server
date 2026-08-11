FROM alpine:3.20

RUN apk add --no-cache \
    kamailio \
    kamailio-extras \
    kamailio-json \
    kamailio-sqlite \
    sqlite \
    kamailio-outbound \
    kamailio-utils

COPY config/kamailio.cfg /etc/kamailio/kamailio.cfg

EXPOSE 5066/udp

CMD ["kamailio", "-DD", "-E"]