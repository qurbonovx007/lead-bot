import os

# Bot token - @BotFather dan oling
BOT_TOKEN = os.getenv("BOT_TOKEN", "8435237137:AAHPaHq_emn7cVpWe-7JLnfOOG_IM7zp0Mw")

# Admin Telegram ID - @userinfobot dan oling
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "6454387575").split(",")))

# Leads yuboriluvchi guruh/kanal ID (minus bilan, masalan: -1001234567890)
LEADS_CHAT_ID = int(os.getenv("LEADS_CHAT_ID", "-5341403054"))

# Bot haqida matn
BOT_ABOUT = """
😊 Assalomu alaykum!

Mudarris Xalqaro maktabi 0-sinfdan 11-sinfgacha bo‘lgan o‘quvchilarni qabul qiladi. Maktabimiz IT, robototexnika, arab tili va ingliz tili yo‘nalishlariga ixtisoslashtirilgan.

 👨‍🏫 Arab tili darslarini chet ellik malakali ustozlar olib boradilar.

🏆 Farzandingiz maktabni bitirmasdan turib IELTS, CEFR va SAT kabi sertifikatlardan yuqori ball olish imkoniyatiga ega bo‘ladi, chunki bizda ushbu sertifikatlar uchun maxsus tayyorlov guruhlari ham mavjud. 

🍽️ Maktabda kun davomida 4 mahal ovqat beriladi. 

✍️ Batafsil ma’lumot olish uchun ro‘yxatdan o‘ting.
"""
