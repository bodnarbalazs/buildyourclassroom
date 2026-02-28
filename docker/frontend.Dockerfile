# Context: repo root
FROM node:22-alpine AS build
WORKDIR /app
COPY src/frontend/package.json src/frontend/package-lock.json ./
RUN npm ci
COPY src/frontend/ .
RUN npm run build

FROM nginx:alpine
COPY src/frontend/nginx.conf /etc/nginx/nginx.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
EXPOSE 443
