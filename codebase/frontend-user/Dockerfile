FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ARG BACKEND_URL=http://backend:8000
ARG NEXT_PUBLIC_API_URL=
ARG NEXT_PUBLIC_USE_REAL_API=true
ARG NEXT_PUBLIC_DEFAULT_MODEL=openai/gpt-4o-mini
ARG NEXT_PUBLIC_MAX_STEPS=8
ENV BACKEND_URL=$BACKEND_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_USE_REAL_API=$NEXT_PUBLIC_USE_REAL_API
ENV NEXT_PUBLIC_DEFAULT_MODEL=$NEXT_PUBLIC_DEFAULT_MODEL
ENV NEXT_PUBLIC_MAX_STEPS=$NEXT_PUBLIC_MAX_STEPS

RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app

ARG BACKEND_URL=http://backend:8000
ENV NODE_ENV=production \
    PORT=3000 \
    HOSTNAME=0.0.0.0 \
    BACKEND_URL=${BACKEND_URL}

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000

CMD ["node", "server.js"]
