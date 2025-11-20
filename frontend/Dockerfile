
FROM node:20-alpine as build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* /app/
RUN npm install
COPY frontend /app
RUN npm run build

FROM nginx:alpine
COPY frontend/docker-nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
