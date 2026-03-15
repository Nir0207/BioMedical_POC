FROM node:22-bookworm-slim AS base
WORKDIR /app
COPY package.json ./
RUN npm install

FROM base AS dev
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

FROM base AS test
COPY . .
CMD ["npm", "run", "test"]

FROM base AS build
COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS prod
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
