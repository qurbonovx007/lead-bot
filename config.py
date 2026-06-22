import os

# Bot token - @BotFather dan oling
BOT_TOKEN = os.getenv("BOT_TOKEN", "8873850157:AAHtoOjzwVgicLLxDdcM-KlBX5IwsydbCuA")

# Admin Telegram ID - @userinfobot dan oling
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", " 6454387575").split(",")))

# Leads yuboriluvchi guruh/kanal ID (minus bilan, masalan: -1001234567890)
LEADS_CHAT_ID = int(os.getenv("LEADS_CHAT_ID", "-5367270112"))

# Bot haqida matn
BOT_ABOUT = """
🏢 *Biznesimiz haqida*

Biz professional xizmatlar ko'rsatuvchi kompaniyamiz.

✅ Yuqori sifatli xizmat
✅ Tez va ishonchli
✅ 24/7 qo'llab-quvvatlash

Ma'lumotlaringizni qoldiring — mutaxassisimiz siz bilan bog'lanadi!
"""
