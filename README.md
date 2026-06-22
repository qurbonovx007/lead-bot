# 🤖 Telegram Lead Bot — O'rnatish Qo'llanmasi

## 📁 Fayl Tuzilmasi
```
telegram_lead_bot/
├── bot.py           # Asosiy fayl
├── handlers.py      # Barcha komandalar
├── database.py      # Ma'lumotlar bazasi
├── config.py        # Sozlamalar
├── requirements.txt # Kutubxonalar
└── railway.toml     # Hosting sozlamasi
```

---

## ✅ 1-QADAM: Bot token olish

1. Telegramda **@BotFather** ga o'ting
2. `/newbot` yuboring
3. Bot nomini kiriting (masalan: `Mening Biznesim`)
4. Bot username kiriting (masalan: `mening_biznes_bot`)
5. **Token** oling — ko'rinishi: `7123456789:AAHxxx...`

---

## ✅ 2-QADAM: Admin ID olish

1. Telegramda **@userinfobot** ga o'ting
2. `/start` bosing
3. Sizning **ID** raqamingiz chiqadi — masalan: `987654321`

---

## ✅ 3-QADAM: Leads guruhi yaratish

1. Telegramda yangi **guruh** yarating (masalan: "Leads")
2. **Botingizni** guruhga admin qilib qo'shing
3. Guruh ID olish uchun **@getmyid_bot** ni guruhga qo'shing
4. Guruh ID ni oling — ko'rinishi: `-1001234567890`

---

## ✅ 4-QADAM: Railway.app da joylash (24/7 bepul)

### 4.1 — GitHub ga yuklash
```bash
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/SIZNING_USERNAME/lead-bot.git
git push -u origin main
```

### 4.2 — Railway.app da deploy
1. **railway.app** ga kiring → GitHub bilan ro'yxatdan o'ting
2. **"New Project"** → **"Deploy from GitHub repo"**
3. Repozitoriyangizni tanlang
4. **"Variables"** bo'limiga o'ting va quyidagilarni qo'shing:

| Variable | Qiymati |
|----------|---------|
| `BOT_TOKEN` | `7123456789:AAHxxx...` |
| `ADMIN_IDS` | `987654321` |
| `LEADS_CHAT_ID` | `-1001234567890` |

5. **Deploy** tugmasini bosing ✅

---

## 📊 Statistika ko'rish

Botga `/stats` yuboring va tanlang:
- 📅 **Kunlik** — bugun
- 📆 **Haftalik** — so'nggi 7 kun
- 🗓 **Oylik** — so'nggi 30 kun
- 📊 **Umumiy** — hammasi

---

## 🔧 Bot matnini o'zgartirish

`config.py` faylida `BOT_ABOUT` qismini o'zgartiring:
```python
BOT_ABOUT = """
🏢 Sizning kompaniyangiz haqida ma'lumot...
"""
```

---

## ❓ Yordam kerakmi?

Muammo bo'lsa, Railway logs ni tekshiring:
- Railway → Sizning proyektingiz → **Logs** bo'limi
