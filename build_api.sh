cp -r ~/lib/python/ ./python
docker build -f Dockerfile.api -t cadcam-api:latest .
