from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import aiosqlite

# pending → accepted → done
# pending → rejected
# accepted → cancelled (с причиной)
OPEN_STATUSES = ("pending", "accepted")
TERMINAL_STATUSES = ("done", "rejected", "cancelled")


class DB:
    def __init__(self, path: str):
        self.path = path

    async def init(self) -> None:
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.path) as db:
            await db.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    photo_url TEXT,
                    referrer_id INTEGER,
                    bonus_balance REAL NOT NULL DEFAULT 0,
                    usdt_sold REAL NOT NULL DEFAULT 0,
                    ton_sold REAL NOT NULL DEFAULT 0,
                    deals INTEGER NOT NULL DEFAULT 0,
                    turnover REAL NOT NULL DEFAULT 0,
                    ref_count INTEGER NOT NULL DEFAULT 0,
                    ref_earned REAL NOT NULL DEFAULT 0,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    asset TEXT NOT NULL,
                    method TEXT NOT NULL,
                    amount REAL NOT NULL,
                    rate REAL NOT NULL,
                    payout REAL NOT NULL,
                    bonus_used REAL NOT NULL DEFAULT 0,
                    phone TEXT NOT NULL,
                    bank TEXT NOT NULL,
                    full_name TEXT,
                    card_number TEXT,
                    want_pdf INTEGER NOT NULL DEFAULT 1,
                    status TEXT NOT NULL,
                    cancel_reason TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    completed_at REAL
                );

                CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
                CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
                CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at);
                """
            )
            # миграция для уже существующих БД
            cur = await db.execute("PRAGMA table_info(orders)")
            cols = {row[1] for row in await cur.fetchall()}
            if "cancel_reason" not in cols:
                await db.execute("ALTER TABLE orders ADD COLUMN cancel_reason TEXT")
            await db.commit()

    async def upsert_user(
        self,
        *,
        user_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
        photo_url: str | None = None,
        referrer_id: int | None = None,
    ) -> dict[str, Any]:
        now = time.time()
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM users WHERE id=?", (user_id,))
            row = await cur.fetchone()
            if row:
                await db.execute(
                    """
                    UPDATE users SET username=?, first_name=?, last_name=?,
                    photo_url=COALESCE(?, photo_url), updated_at=?
                    WHERE id=?
                    """,
                    (username, first_name, last_name, photo_url, now, user_id),
                )
            else:
                ref = referrer_id if referrer_id and referrer_id != user_id else None
                await db.execute(
                    """
                    INSERT INTO users (
                        id, username, first_name, last_name, photo_url, referrer_id,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, username, first_name, last_name, photo_url, ref, now, now),
                )
                if ref:
                    await db.execute(
                        "UPDATE users SET ref_count = ref_count + 1, updated_at=? WHERE id=?",
                        (now, ref),
                    )
            await db.commit()
            cur = await db.execute("SELECT * FROM users WHERE id=?", (user_id,))
            return dict(await cur.fetchone())

    async def get_user(self, user_id: int) -> dict[str, Any] | None:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM users WHERE id=?", (user_id,))
            row = await cur.fetchone()
            return dict(row) if row else None

    async def set_setting(self, key: str, value: str) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT INTO settings(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )
            await db.commit()

    async def get_setting(self, key: str) -> str | None:
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute("SELECT value FROM settings WHERE key=?", (key,))
            row = await cur.fetchone()
            return row[0] if row else None

    async def last_order_at(self, user_id: int) -> float | None:
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                "SELECT created_at FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 1",
                (user_id,),
            )
            row = await cur.fetchone()
            return float(row[0]) if row else None

    async def create_order(self, data: dict[str, Any]) -> dict[str, Any]:
        now = time.time()
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                """
                INSERT INTO orders (
                    user_id, asset, method, amount, rate, payout, bonus_used,
                    phone, bank, full_name, card_number, want_pdf, status,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                """,
                (
                    data["user_id"],
                    data["asset"],
                    data["method"],
                    data["amount"],
                    data["rate"],
                    data["payout"],
                    data["bonus_used"],
                    data["phone"],
                    data["bank"],
                    data.get("full_name"),
                    data.get("card_number"),
                    1 if data.get("want_pdf", True) else 0,
                    now,
                    now,
                ),
            )
            order_id = cur.lastrowid
            if data["bonus_used"] > 0:
                await db.execute(
                    "UPDATE users SET bonus_balance = bonus_balance - ?, updated_at=? WHERE id=?",
                    (data["bonus_used"], now, data["user_id"]),
                )
            await db.commit()
            cur = await db.execute("SELECT * FROM orders WHERE id=?", (order_id,))
            return dict(await cur.fetchone())

    async def list_orders(self, user_id: int, limit: int = 50) -> list[dict[str, Any]]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT * FROM orders WHERE user_id=? ORDER BY id DESC LIMIT ?",
                (user_id, limit),
            )
            return [dict(r) for r in await cur.fetchall()]

    async def list_open(self, limit: int = 50) -> list[dict[str, Any]]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                """
                SELECT * FROM orders
                WHERE status IN ('pending', 'accepted')
                ORDER BY id ASC LIMIT ?
                """,
                (limit,),
            )
            return [dict(r) for r in await cur.fetchall()]

    async def list_pending(self, limit: int = 50) -> list[dict[str, Any]]:
        return await self.list_open(limit)

    async def get_order(self, order_id: int) -> dict[str, Any] | None:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM orders WHERE id=?", (order_id,))
            row = await cur.fetchone()
            return dict(row) if row else None

    async def set_order_status(
        self,
        order_id: int,
        status: str,
        *,
        ref_bonus: float = 0,
        cancel_reason: str | None = None,
    ) -> dict[str, Any] | None:
        """Смена статуса с проверкой переходов. Возвращает заказ или None."""
        now = time.time()
        allowed = {
            "pending": {"accepted", "rejected"},
            "accepted": {"done", "cancelled"},
        }
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM orders WHERE id=?", (order_id,))
            order = await cur.fetchone()
            if not order:
                return None
            order = dict(order)
            current = order["status"]
            if status not in allowed.get(current, set()):
                return order  # недопустимый переход — вернём как есть

            completed = now if status in ("done", "rejected", "cancelled") else None
            await db.execute(
                """
                UPDATE orders
                SET status=?, updated_at=?, completed_at=?,
                    cancel_reason=COALESCE(?, cancel_reason)
                WHERE id=?
                """,
                (status, now, completed, cancel_reason, order_id),
            )

            if status == "done":
                await db.execute(
                    """
                    UPDATE users SET
                        deals = deals + 1,
                        turnover = turnover + ?,
                        usdt_sold = usdt_sold + ?,
                        ton_sold = ton_sold + ?,
                        updated_at=?
                    WHERE id=?
                    """,
                    (
                        order["payout"],
                        order["amount"] if order["asset"] == "USDT" else 0,
                        order["amount"] if order["asset"] == "TON" else 0,
                        now,
                        order["user_id"],
                    ),
                )
                cur = await db.execute(
                    "SELECT referrer_id FROM users WHERE id=?", (order["user_id"],)
                )
                ref_row = await cur.fetchone()
                referrer_id = ref_row[0] if ref_row else None
                if referrer_id and ref_bonus > 0:
                    cur = await db.execute(
                        "SELECT deals FROM users WHERE id=?", (order["user_id"],)
                    )
                    deals_row = await cur.fetchone()
                    if deals_row and deals_row[0] == 1:
                        await db.execute(
                            """
                            UPDATE users SET
                                bonus_balance = bonus_balance + ?,
                                ref_earned = ref_earned + ?,
                                updated_at=?
                            WHERE id=?
                            """,
                            (ref_bonus, ref_bonus, now, referrer_id),
                        )
            elif status in ("rejected", "cancelled") and order["bonus_used"] > 0:
                await db.execute(
                    "UPDATE users SET bonus_balance = bonus_balance + ?, updated_at=? WHERE id=?",
                    (order["bonus_used"], now, order["user_id"]),
                )

            await db.commit()
            cur = await db.execute("SELECT * FROM orders WHERE id=?", (order_id,))
            return dict(await cur.fetchone())

    async def leaderboard(self, since: float, limit: int = 50) -> list[dict[str, Any]]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                """
                SELECT u.id, u.username, u.first_name, u.photo_url,
                       COALESCE(SUM(o.payout), 0) AS week_turnover
                FROM orders o
                JOIN users u ON u.id = o.user_id
                WHERE o.status='done' AND o.completed_at >= ?
                GROUP BY u.id
                ORDER BY week_turnover DESC
                LIMIT ?
                """,
                (since, limit),
            )
            return [dict(r) for r in await cur.fetchall()]

    async def user_week_stats(self, user_id: int, since: float) -> dict[str, Any]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                """
                SELECT COALESCE(SUM(payout), 0) AS week_turnover
                FROM orders
                WHERE user_id=? AND status='done' AND completed_at >= ?
                """,
                (user_id, since),
            )
            row = dict(await cur.fetchone())
            board = await self.leaderboard(since, limit=500)
            place = None
            for i, item in enumerate(board, start=1):
                if item["id"] == user_id:
                    place = i
                    break
            return {"week_turnover": float(row["week_turnover"]), "place": place}

    async def totals(self) -> dict[str, int]:
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                "SELECT COUNT(*) FROM orders WHERE status='done'"
            )
            done = (await cur.fetchone())[0]
            cur = await db.execute("SELECT COUNT(*) FROM users")
            users = (await cur.fetchone())[0]
            return {"done_orders": int(done), "users": int(users)}
