gunicorn xsd_gui:server --daemon --name XSD_GUI --workers 4 --user=root --group=root --bind=0.0.0.0:443 --certfile=/etc/letsencrypt/live/xsd.cimtools.eu/fullchain.pem --keyfile=/etc/letsencrypt/live/xsd.cimtools.eu/privkey.pem

