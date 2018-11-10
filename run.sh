#socat TCP-LISTEN:6000,reuseaddr,fork UNIX-CLIENT:\"$DISPLAY\" &
export DISPLAY=192.168.0.3:0
docker-compose run cadcam
