FROM node:22-alpine AS dev
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD wget -q -O /dev/null http://0.0.0.0:8080/ || exit 1
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

FROM node:22-alpine AS build
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine AS prod
WORKDIR /app
COPY --from=build /app/dist /usr/share/nginx/html
RUN apk add --no-cache python3 py3-pip
COPY --chown=nginx:nginx backend /app/backend
COPY --chown=nginx:nginx backend/manage.py /app/backend/manage.py
RUN if [ -f /app/backend/requirements.txt ]; then python3 -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir -r /app/backend/requirements.txt; fi
ENV PATH="/opt/venv/bin:$PATH"
RUN printf 'server {\n    listen 0.0.0.0:8080;\n    server_name _;\n    root /usr/share/nginx/html;\n    index index.html;\n    client_body_temp_path /tmp/nginx-cache/client_temp;\n    proxy_temp_path /tmp/nginx-cache/proxy_temp;\n    fastcgi_temp_path /tmp/nginx-cache/fastcgi_temp;\n    uwsgi_temp_path /tmp/nginx-cache/uwsgi_temp;\n    scgi_temp_path /tmp/nginx-cache/scgi_temp;\n    location / {\n        try_files $uri $uri/ /index.html;\n    }\n}\n' > /etc/nginx/conf.d/default.conf \
    && mkdir -p /tmp/nginx-cache \
    && chown -R nginx:nginx /tmp/nginx-cache /var/cache/nginx /usr/share/nginx/html
RUN sed -i -e 's#^[[:space:]]*pid[[:space:]].*#pid /tmp/nginx.pid;#' -e '/^[[:space:]]*user[[:space:]]/d' /etc/nginx/nginx.conf \
    && grep -q '^pid /tmp/nginx.pid;' /etc/nginx/nginx.conf
EXPOSE 8080
USER nginx
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q -O /dev/null http://0.0.0.0:8080/ || exit 1
CMD ["nginx", "-g", "daemon off;"]
