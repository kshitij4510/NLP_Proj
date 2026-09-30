# ─────────────────────────────────────────────
# ResearchMind Frontend Dockerfile
# Multi-stage: development | production
# ─────────────────────────────────────────────

FROM node:20-alpine AS base

WORKDIR /app

# ─────────────────────────────────────────────
# Development stage
# ─────────────────────────────────────────────
FROM base AS development

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ─────────────────────────────────────────────
# Build stage
# ─────────────────────────────────────────────
FROM base AS builder

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build

# ─────────────────────────────────────────────
# Production stage — serve with nginx
# ─────────────────────────────────────────────
FROM nginx:1.25-alpine AS production

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
