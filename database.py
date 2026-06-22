import aiosqlite
import csv
import io
from datetime import datetime

DB_PATH = "leads.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT,
                phone TEXT,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                is_completed INTEGER DEFAULT 0
            )
        """)
        await db.commit()

async def add_user_start(telegram_id: int, username: str):
    async with aiosqlite.connect(DB_PATH) as db:
        now = datetime.now().isoformat()
        await db.execute("""
            INSERT OR IGNORE INTO users (telegram_id, username, started_at)
            VALUES (?, ?, ?)
        """, (telegram_id, username, now))
        await db.commit()

async def update_user_lead(telegram_id: int, full_name: str, phone: str):
    async with aiosqlite.connect(DB_PATH) as db:
        now = datetime.now().isoformat()
        await db.execute("""
            UPDATE users
            SET full_name = ?, phone = ?, completed_at = ?, is_completed = 1
            WHERE telegram_id = ?
        """, (full_name, phone, now, telegram_id))
        await db.commit()

async def get_stats(period: str) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        if period == "day":
            date_filter = "date(started_at) = date('now')"
            completed_filter = "date(completed_at) = date('now')"
        elif period == "week":
            date_filter = "started_at >= datetime('now', '-7 days')"
            completed_filter = "completed_at >= datetime('now', '-7 days')"
        elif period == "month":
            date_filter = "started_at >= datetime('now', '-30 days')"
            completed_filter = "completed_at >= datetime('now', '-30 days')"
        else:
            date_filter = "1=1"
            completed_filter = "1=1"

        cursor = await db.execute(
            f"SELECT COUNT(*) FROM users WHERE {date_filter}"
        )
        total_started = (await cursor.fetchone())[0]

        cursor = await db.execute(
            f"SELECT COUNT(*) FROM users WHERE is_completed = 1 AND {completed_filter}"
        )
        total_completed = (await cursor.fetchone())[0]

        return {
            "started": total_started,
            "completed": total_completed,
            "not_completed": total_started - total_completed
        }

async def get_user(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        return await cursor.fetchone()

# ============ YANGI FUNKSIYALAR ============

async def get_all_leads(limit: int = 50, offset: int = 0) -> list:
    """Barcha to'ldirilgan leadlarni qaytaradi (sahifalab)"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT telegram_id, username, full_name, phone, completed_at
            FROM users
            WHERE is_completed = 1
            ORDER BY completed_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        rows = await cursor.fetchall()
        return rows

async def get_leads_count() -> int:
    """Jami leadlar soni"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM users WHERE is_completed = 1"
        )
        return (await cursor.fetchone())[0]

async def clear_all_leads() -> int:
    """Barcha foydalanuvchilarni o'chiradi, o'chirilgan sonni qaytaradi"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        count = (await cursor.fetchone())[0]
        await db.execute("DELETE FROM users")
        await db.commit()
        return count

async def export_leads_csv() -> bytes:
    """Barcha leadlarni CSV formatida qaytaradi"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT telegram_id, username, full_name, phone, started_at, completed_at
            FROM users
            WHERE is_completed = 1
            ORDER BY completed_at DESC
        """)
        rows = await cursor.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Telegram ID", "Username", "Ism-Familiya", "Telefon", "Boshlagan vaqt", "Tugatgan vaqt"])
    for row in rows:
        writer.writerow(row)

    return output.getvalue().encode("utf-8-sig")  # Excel uchun BOM
