FROM node:24-bookworm-slim

WORKDIR /home/node/app
RUN chown node:node /home/node/app
USER node

COPY --chown=node:node apps/web/package.json apps/web/package-lock.json ./
RUN npm ci

COPY --chown=node:node apps/web/ ./
# Keep shared synthetic test corpora canonical in their Django apps. The web
# test imports resolve the same relative paths inside the image and checkout.
COPY --chown=node:node apps/backend/ingestion/fixtures/kt117-fixtures.json /home/node/backend/ingestion/fixtures/kt117-fixtures.json
COPY --chown=node:node apps/backend/catalog/fixtures/kt119-connections.json /home/node/backend/catalog/fixtures/kt119-connections.json
RUN npm run build

CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "5173", "--strictPort"]
