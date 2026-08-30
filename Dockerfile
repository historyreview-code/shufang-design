FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html /usr/share/nginx/html/index.html
COPY blender/ /usr/share/nginx/html/blender/
COPY preview/ /usr/share/nginx/html/preview/
EXPOSE 80
