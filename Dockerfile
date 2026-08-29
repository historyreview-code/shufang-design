FROM nginx:alpine
COPY index.html /usr/share/nginx/html/index.html
COPY blender/chair.glb /usr/share/nginx/html/blender/chair.glb
COPY preview/cycles-cover.jpg /usr/share/nginx/html/preview/cycles-cover.jpg
EXPOSE 80
