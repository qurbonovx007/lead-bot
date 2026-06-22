import aiosqlite
import csv
import io
from datetime import datetime

DB_PATH = "leads.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Foydalanuvchilar jadvali
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
        # O'chirilganlar statistikasini saqlash uchun jadval
        await db.execute("""
            CREATE TABLE IF NOT EXISTS deleted_stats (
                key TEXT PRIMARY KEY,
                count INTEGER DEFAULT 0
            )
        """)
        # Agar hisoblagich mavjud bo'lmasa, 0 qiymat bilan yaratamiz
        await db.execute("""
            INSERT OR IGNORE INTO deleted_stats (key, count) VALUES ('total_deleted', 0)
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
        now = datetime.now()
        if period == "day":
            date_str = now.strftime("%Y-%m-%d")
            sql = "WHERE started_at LIKE ?"
            params = (f"{date_str}%",)
            sql_comp = "WHERE is_completed = 1 AND completed_at LIKE ?"
            params_comp = (f"{date_str}%",)
        elif period == "week":
            sql = "WHERE datetime(started_at) >= datetime('now', '-7 days')"
            params = ()
            sql_comp = "WHERE is_completed = 1 AND datetime(completed_at) >= datetime('now', '-7 days')"
            params_comp = ()
        elif period == "month":
            sql = "WHERE datetime(started_at) >= datetime('now', '-30 days')"
            params = ()
            sql_comp = "WHERE is_completed = 1 AND datetime(completed_at) >= datetime('now', '-30 days')"
            params_comp = ()
        else:  # all
            sql = ""
            params = ()
            sql_comp = "WHERE is_completed = 1"
            params_comp = ()

        cursor = await db.execute(f"SELECT COUNT(*) FROM users {sql}", params)
        started = (await cursor.fetchone())[0]

        cursor = await db.execute(f"SELECT COUNT(*) FROM users {sql_comp}", params_comp)
        completed = (await cursor.fetchone())[0]

        not_completed = started - completed

        return {
            "started": started,
            "completed": completed,
            "not_completed": not_completed
        }

async def get_user(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        return await cursor.fetchone()

async def get_all_leads(limit: int, offset: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT telegram_id, username, full_name, phone, completed_at
            FROM users
            WHERE is_completed = 1
            ORDER BY completed_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        return await cursor.fetchall()

async def get_leads_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users WHERE is_completed = 1")
        return (await cursor.fetchone())[0]

async def get_deleted_count() -> int:
    """O'chirilgan arizalar umumiy sonini olish"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT count FROM deleted_stats WHERE key = 'total_deleted'")
        row = await cursor.fetchone()
        return row[0] if row else 0

async def clear_all_leads() -> int:
    """Barcha arizalarni o'chiradi va o'chirilganlar sonini hisoblagichga qo'shadi"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Faqat to'liq yakunlangan leadlar (arizalar) sonini olamiz
        cursor = await db.execute("SELECT COUNT(*) FROM users WHERE is_completed = 1")
        completed_count = (await cursor.fetchone())[0]
        
        # Barcha foydalanuvchilarni o'chiramiz
        await db.execute("DELETE FROM users")
        
        # O'chirilgan arizalar sonini doimiy hisoblagichga qo'shamiz
        await db.execute("""
            UPDATE deleted_stats 
            SET count = count + ? 
            WHERE key = 'total_deleted'
        """, (completed_count,))
        
        await db.commit()
        return completed_count

async def export_leads_csv() -> bytes:
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
    writer.writerow(["Telegram ID", "Username", "Ism-Familiya", "Telefon", "Boshlagan vaqti", "Topshirgan vaqti"])
    for row in rows:
        writer.writerow(row)
    return output.getvalue().encode('utf-8')
