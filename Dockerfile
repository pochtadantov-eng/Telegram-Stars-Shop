FROM node:22-alpine AS web
WORKDIR /web
COPY webapp/package.json webapp/package-lock.json* ./
RUN npm install
COPY webapp/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY bot ./bot
COPY --from=web /web/dist ./webapp/dist
RUN mkdir -p data
ENV PORT=8080
EXPOSE 8080
CMD ["python", "-m", "bot.main"]
