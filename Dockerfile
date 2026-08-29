FROM nginx:alpine
COPY index.html /usr/share/nginx/html/index.html
COPY blender/chair.glb /usr/share/nginx/html/blender/chair.glb
EXPOSE 80
