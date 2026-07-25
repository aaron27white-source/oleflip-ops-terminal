# Web image — multi-stage Next.js standalone build.
# Build context is packages/web.
FROM node:20-slim AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
RUN npm run build

FROM node:20-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
# Next standalone bundle + static assets + public dir. Copied as the built-in
# non-root `node` user (uid 1000) so the runtime never runs as root.
COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static
COPY --from=builder --chown=node:node /app/public ./public
USER node
EXPOSE 3000
# API_BASE points at the backend service; the rewrite proxy uses it.
ENV API_BASE=http://backend:8000
CMD ["node", "server.js"]
