FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html /usr/share/nginx/html/index.html
COPY blender/chair.glb /usr/share/nginx/html/blender/chair.glb
COPY preview/cycles-cover.jpg /usr/share/nginx/html/preview/cycles-cover.jpg
COPY preview/cycles-cover-moody.jpg /usr/share/nginx/html/preview/cycles-cover-moody.jpg
COPY preview/portfolio.jpg /usr/share/nginx/html/preview/portfolio.jpg
EXPOSE 80
