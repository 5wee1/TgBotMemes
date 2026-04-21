import json
import logging
import random
import string
import aiosqlite
from datetime import date, datetime
from typing import Optional

from config import config
from database.models import CREATE_TABLES_SQL

logger = logging.getLogger(__name__)


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(config.db_path)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    return db


async def init_db():
    async with aiosqlite.connect(config.db_path) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA journal_mode=WAL")
        for statement in CREATE_TABLES_SQL.split(";"):
            stmt = statement.strip()
            if stmt:
                await db.execute(stmt)
        await db.commit()


def _gen_ref_code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


# ── Users ──────────────────────────────────────────────────────────────────

async def get_or_create_user(user_id: int, username: Optional[str] = None, referred_by: Optional[int] = None) -> dict:
    async with aiosqlite.connect(config.db_path) as db:
        db.row_factory = aiosqlite.Row
        row = await (await db.execute("SELECT * FROM users WHERE user_id=?", (user_id,))).fetchone()
        if row:
            await db.execute("UPDATE users SET last_active_at=datetime('now'), username=COALESCE(?,username) WHERE user_id=?", (username, user_id))
            await db.commit()
            return dict(row)
        ref_code = _gen_ref_code()
        await db.execute(
            "INSERT INTO users (user_id, username, ref_code, referred_by) VALUES (?,?,?,?)",
            (user_id, username, ref_code, referred_by),
        )
        await db.commit()
        # activate referrer bonus
        if referred_by:
            await _add_credits(db, referred_by, 10)
            await _log_event(db, referred_by, "ref_activation", {"new_user": user_id})
        row = await (await db.execute("SELECT * FROM users WHERE user_id=?", (user_id,))).fetchone()
        return dict(row)


async def get_user(user_id: int) -> Optional[dict]:
    async with aiosqlite.connect(config.db_path) as db:
        db.row_factory = aiosqlite.Row
        row = await (await db.execute("SELECT * FROM users WHERE user_id=?", (user_id,))).fetchone()
        return dict(row) if row else None


async def ban_user(user_id: int, banned: bool = True):
    async with aiosqlite.connect(config.db_path) as db:
        await db.execute("UPDATE users SET is_banned=? WHERE user_id=?", (int(banned), user_id))
        await db.commit()


async def _add_credits(db: aiosqlite.Connection, user_id: int, amount: int):
    await db.execute("UPDATE users SET credits_balance=credits_balance+? WHERE user_id=?", (amount, user_id))


async def add_credits(user_id: int, amount: int):
    async with aiosqlite.connect(config.db_path) as db:
        cursor = await db.execute(
            "UPDATE users SET credits_balance=credits_balance+? WHERE user_id=?", (amount, user_id)
        )
        if cursor.rowcount == 0:
            logger.error("add_credits: user %s not found — credits not added!", user_id)
        await db.commit()


async def set_plan(user_id: int, plan: str, credits: int):
    async with aiosqlite.connect(config.db_path) as db:
        await db.execute(
            "UPDATE users SET plan=?, credits_balance=credits_balance+? WHERE user_id=?",
            (plan, credits, user_id),
        )
        await db.commit()


async def can_generate(user_id: int) -> tuple[bool, str]:
    """Returns (allowed, reason). Resets daily counter if needed."""
    if user_id in config.admin_ids:
        return True, "admin"
    async with aiosqlite.connect(config.db_path) as db:
        db.row_factory = aiosqlite.Row
        row = await (await db.execute("SELECT * FROM users WHERE user_id=?", (user_id,))).fetchone()
        if not row:
            return False, "user_not_found"
        user = dict(row)
        if user["is_banned"]:
            return False, "banned"
        today = date.today().isoformat()
        if user["daily_reset_date"] != today:
            await db.execute(
                "UPDATE users SET daily_free_used=0, daily_reset_date=? WHERE user_id=?",
                (today, user_id),
            )
            await db.commit()
            user["daily_free_used"] = 0
        # Paid credits take priority regardless of plan
        if user["credits_balance"] > 0:
            return True, "credits"
        # Free daily allowance (only if no paid credits left)
        if user["plan"] == "free":
            if user["daily_free_used"] >= config.free_daily_limit:
                return False, "daily_limit"
            return True, "free"
        # Subscriber ran out of credits
        return False, "no_credits"


async def consume_generation(user_id: int, reason: str):
    if reason == "admin":
        return
    async with aiosqlite.connect(config.db_path) as db:
        if reason == "free":
            await db.execute("UPDATE users SET daily_free_used=daily_free_used+1 WHERE user_id=?", (user_id,))
        else:
            await db.execute("UPDATE users SET credits_balance=credits_balance-1 WHERE user_id=?", (user_id,))
        await db.commit()


# ── Memes ──────────────────────────────────────────────────────────────────

async def save_meme(user_id: int, query: str, style: str, prompt_hash: str, file_id: str = "", image_url: str = "") -> int:
    async with aiosqlite.connect(config.db_path) as db:
        cursor = await db.execute(
            "INSERT INTO memes (user_id, query, style, prompt_hash, file_id, image_url) VALUES (?,?,?,?,?,?)",
            (user_id, query, style, prompt_hash, file_id, image_url),
        )
        await db.commit()
        return cursor.lastrowid


async def update_meme_file_id(meme_id: int, file_id: str):
    async with aiosqlite.connect(config.db_path) as db:
        await db.execute("UPDATE memes SET file_id=? WHERE id=?", (file_id, meme_id))
        await db.commit()


async def toggle_favorite(meme_id: int, user_id: int) -> bool:
    async with aiosqlite.connect(config.db_path) as db:
        db.row_factory = aiosqlite.Row
        row = await (await db.execute("SELECT is_favorite FROM memes WHERE id=? AND user_id=?", (meme_id, user_id))).fetchone()
        if not row:
            return False
        new_val = 1 - row["is_favorite"]
        await db.execute("UPDATE memes SET is_favorite=? WHERE id=?", (new_val, meme_id))
        await db.commit()
        return bool(new_val)


async def get_favorites(user_id: int, limit: int = 20, offset: int = 0) -> list[dict]:
    async with aiosqlite.connect(config.db_path) as db:
        db.row_factory = aiosqlite.Row
        rows = await (await db.execute(
            "SELECT * FROM memes WHERE user_id=? AND is_favorite=1 ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (user_id, limit, offset),
        )).fetchall()
        return [dict(r) for r in rows]


async def get_user_memes(user_id: int, limit: int = 20, offset: int = 0) -> list[dict]:
    async with aiosqlite.connect(config.db_path) as db:
        db.row_factory = aiosqlite.Row
        rows = await (await db.execute(
            "SELECT * FROM memes WHERE user_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (user_id, limit, offset),
        )).fetchall()
        return [dict(r) for r in rows]


async def delete_meme(meme_id: int, user_id: int):
    async with aiosqlite.connect(config.db_path) as db:
        await db.execute("DELETE FROM memes WHERE id=? AND user_id=?", (meme_id, user_id))
        await db.commit()


# ── Payments ───────────────────────────────────────────────────────────────

async def create_payment(user_id: int, provider: str, amount: int, currency: str, payload: dict) -> int:
    async with aiosqlite.connect(config.db_path) as db:
        cursor = await db.execute(
            "INSERT INTO payments (user_id, provider, amount, currency, payload_json) VALUES (?,?,?,?,?)",
            (user_id, provider, amount, currency, json.dumps(payload)),
        )
        await db.commit()
        return cursor.lastrowid


async def confirm_payment(payment_id: int):
    async with aiosqlite.connect(config.db_path) as db:
        await db.execute("UPDATE payments SET status='confirmed' WHERE id=?", (payment_id,))
        await db.commit()


# ── Events & Stats ─────────────────────────────────────────────────────────

async def _log_event(db: aiosqlite.Connection, user_id: Optional[int], event_type: str, meta: dict):
    await db.execute(
        "INSERT INTO events (user_id, event_type, meta_json) VALUES (?,?,?)",
        (user_id, event_type, json.dumps(meta)),
    )


async def log_event(user_id: Optional[int], event_type: str, meta: dict = {}):
    async with aiosqlite.connect(config.db_path) as db:
        await _log_event(db, user_id, event_type, meta)
        await db.commit()


async def get_stats() -> dict:
    async with aiosqlite.connect(config.db_path) as db:
        db.row_factory = aiosqlite.Row
        total_users = (await (await db.execute("SELECT COUNT(*) as c FROM users")).fetchone())["c"]
        dau = (await (await db.execute(
            "SELECT COUNT(*) as c FROM users WHERE last_active_at >= datetime('now','-1 day')"
        )).fetchone())["c"]
        generated_today = (await (await db.execute(
            "SELECT COUNT(*) as c FROM memes WHERE created_at >= date('now')"
        )).fetchone())["c"]
        revenue = (await (await db.execute(
            "SELECT COALESCE(SUM(amount),0) as s FROM payments WHERE status='confirmed'"
        )).fetchone())["s"]
        return {
            "total_users": total_users,
            "dau": dau,
            "generated_today": generated_today,
            "revenue": revenue,
        }


async def find_user_by_username(username: str) -> Optional[dict]:
    async with aiosqlite.connect(config.db_path) as db:
        db.row_factory = aiosqlite.Row
        username = username.lstrip("@")
        row = await (await db.execute("SELECT * FROM users WHERE username=?", (username,))).fetchone()
        return dict(row) if row else None
