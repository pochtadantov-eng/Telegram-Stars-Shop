FROM node:22-alpine AS web
WORKDIR /web
COPY webapp/package.json webapp/package-lock.json* ./
RUN npm install
COPY webapp/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY bot ./bot
COPY --from=web /web/dist ./webapp/dist
RUN mkdir -p /data
ENV PORT=8080
ENV DB_PATH=/data/exchange.db
EXPOSE 8080
CMD ["python", "-m", "bot.main"]
