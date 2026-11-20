# SwiftEx — Telegram Mini App для продажи крипты

Бот + Mini App: клиент продаёт **USDT** (TRC20 / TON) или **TON**, получает рубли на СБП/карту.
Оформление в стиле glassmorphism, плавные переходы, клики со звуком и haptic.

## Возможности
- Mini App: главная, создание обмена, профиль, заявки, топ недели
- Курсы USDT/TON задаются в `.env` или командой `/rate`
- Рефералка: бонус за первый успешный обмен реферала
- Админам приходит заявка с кнопками «Выплачено / Отклонить»

## Быстрый старт
```bash
# Backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # BOT_TOKEN, ADMIN_IDS, WEBAPP_URL, кошельки

# Mini App
cd webapp && npm install && npm run build && cd ..

python -m bot.main
```

`WEBAPP_URL` — публичный HTTPS URL, который смотрит на этот же сервис (порт `PORT`).
В Telegram BotFather → Bot Settings → Menu Button / Web App укажите тот же URL.

### Команды админа
- `/rate USDT 96` / `/rate TON 550` — курс
- `/orders` — открытые заявки (ожидают / в работе)
- `/app` — открыть Mini App

### Жизненный цикл заявки
1. Клиент создаёт заявку в Mini App → тебе в бот
2. **Принять** или **Отклонить**
3. После принятия: сам договариваешься о переводе крипты
4. **Закрыть успешно** или **Отменить** (бот спросит причину)


## Деплой бесплатно (Koyeb)

Koyeb free instance **не засыпает** (в отличие от Render free) — удобно для Telegram-бота.

1. Зайди с телефона на [app.koyeb.com](https://app.koyeb.com) → Sign up через **GitHub**
2. **Create App** → Import `Telegram-Stars-Shop`
3. Builder: **Dockerfile**
4. Environment variables:
   - `BOT_TOKEN` = токен бота
   - `ADMIN_IDS` = твой Telegram ID
   - `WEBAPP_URL` = пока оставь пустым, после первого деплоя вставь выданный `https://….koyeb.app`
   - `USDT_RATE_RUB`, `TON_RATE_RUB` по желанию
5. Deploy → скопируй публичный URL → впиши в `WEBAPP_URL` → Redeploy
6. BotFather → `/mybots` → бот → **Bot Settings** → **Menu Button** / **Configure Mini App** → тот же URL

База SQLite на free без постоянного диска может сбрасываться при редеплое — для старта ок; при росте лучше внешняя БД или VPS (~300–500₽/мес).

## Docker
```bash
docker build -t swiftex .
docker run --env-file .env -p 8080:8080 swiftex
```

## Dev Mini App
```bash
# терминал 1
BOT_TOKEN=... ADMIN_IDS=1 WEBAPP_URL=http://127.0.0.1:8080 python -m bot.main
# терминал 2
cd webapp && npm run dev
```
В dev без Telegram API шлёт заголовок `X-Dev-User`.
