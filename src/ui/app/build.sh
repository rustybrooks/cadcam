set -e 

docker exec -it flannelcat-buildui npm run build
# docker run -it flannelcat-buildui --entrypoint "npm run build"

rsync -avP --delete index.html dist/ flannelcat:static/

ssh flannelcat "cd flannelcat; git pull; sudo systemctl restart gunicorn gunicorn.socket"
