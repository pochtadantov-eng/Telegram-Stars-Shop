import time
from decimal import Decimal

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY, username TEXT, ref_by INTEGER, created INTEGER);
CREATE TABLE IF NOT EXISTS orders(
  id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
  kind TEXT NOT NULL,            -- stars | ton
  qty TEXT NOT NULL,             -- кол-во звёзд / TON
  target TEXT NOT NULL,          -- @username или TON-адрес
  rub TEXT NOT NULL, rate TEXT,
  status TEXT NOT NULL DEFAULT 'new',  -- new | review | done | rejected | cancelled
  created INTEGER NOT NULL);
"""


class DB:
    def __init__(self, path: str):
        self.path = path
        self.conn: aiosqlite.Connection

    async def init(self):
        import os
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        self.conn = await aiosqlite.connect(self.path)
        self.conn.row_factory = aiosqlite.Row
        await self.conn.executescript(SCHEMA)
        await self.conn.commit()

    async def upsert_user(self, uid: int, username: str | None, ref_by: int | None = None):
        ref = ref_by if ref_by and ref_by != uid else None
        if ref:
            c = await self.conn.execute("SELECT 1 FROM users WHERE id=?", (ref,))
            ref = ref if await c.fetchone() else None
        # атомарно: параллельные /start не вызывают конфликта
        await self.conn.execute(
            "INSERT INTO users(id,username,ref_by,created) VALUES(?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET username=excluded.username",
            (uid, username, ref, int(time.time())))
        await self.conn.commit()

    async def create_order(self, uid, kind, qty, target, rub: Decimal, rate: Decimal | None) -> int:
        cur = await self.conn.execute(
            "INSERT INTO orders(user_id,kind,qty,target,rub,rate,created) VALUES(?,?,?,?,?,?,?)",
            (uid, kind, str(qty), target, str(rub), str(rate) if rate else None, int(time.time())))
        await self.conn.commit()
        return cur.lastrowid

    async def order(self, oid: int):
        cur = await self.conn.execute("SELECT * FROM orders WHERE id=?", (oid,))
        return await cur.fetchone()

    async def set_status(self, oid: int, status: str, only_from: tuple[str, ...] | None = None) -> bool:
        q, args = "UPDATE orders SET status=? WHERE id=?", [status, oid]
        if only_from:
            q += f" AND status IN ({','.join('?' * len(only_from))})"
            args += list(only_from)
        cur = await self.conn.execute(q, args)
        await self.conn.commit()
        return cur.rowcount > 0

    async def user(self, uid: int):
        cur = await self.conn.execute("SELECT * FROM users WHERE id=?", (uid,))
        return await cur.fetchone()

    async def stats(self, uid: int) -> dict:
        c = await self.conn.execute("SELECT COUNT(*) n, COALESCE(SUM(CAST(rub AS REAL)),0) s FROM orders WHERE user_id=? AND status='done'", (uid,))
        r = await c.fetchone()
        c = await self.conn.execute("SELECT COUNT(*) FROM users WHERE ref_by=?", (uid,))
        invited = (await c.fetchone())[0]
        c = await self.conn.execute(
            "SELECT COALESCE(SUM(CAST(o.rub AS REAL)),0) FROM orders o JOIN users u ON u.id=o.user_id "
            "WHERE u.ref_by=? AND o.status='done'", (uid,))
        ref_turnover = (await c.fetchone())[0]
        return {"orders": r["n"], "spent": Decimal(str(r["s"])), "invited": invited, "ref_turnover": Decimal(str(ref_turnover))}

    async def review_orders(self):
        cur = await self.conn.execute("SELECT * FROM orders WHERE status='review' ORDER BY id")
        return await cur.fetchall()
