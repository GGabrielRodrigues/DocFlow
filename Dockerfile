# Etapa 1: Build da aplicação React + Vite
FROM node:22-alpine AS builder

WORKDIR /app

# Copia os arquivos de manifesto de dependências
COPY package.json package-lock.json ./

# Instala as dependências de forma determinística
RUN npm ci

# Copia o restante do código-fonte e gera a build de produção
COPY . .
RUN npm run build

# Etapa 2: Servidor web leve (Nginx) para servir os arquivos estáticos
FROM nginx:alpine AS runner

# Configuração SPA (redireciona rotas para o index.html)
RUN printf 'server {\n\
    listen 80;\n\
    server_name _;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
\n\
    location / {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf

# Copia os artefatos compilados da etapa de build
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
