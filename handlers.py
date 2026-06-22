import re
import os
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, BufferedInputFile
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
from groq import Groq

from config import ADMIN_IDS, LEADS_CHAT_ID
from database import (
    add_user_start, update_user_lead, get_stats, get_user,
    get_all_leads, get_leads_count, clear_all_leads, export_leads_csv
)

router = Router()

# Groq mijozini Railway'dagi GROQ_API_KEY orqali ishga tushiramiz
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# AI uchun mukammal va samimiy yo'riqnoma (Prompt)
MAKTAB_DATA = """
Siz "Mudarris Xalqaro maktabi"ning juda xushmuomala, samimiy va aqlli virtual yordamchisiz. 

Sizning vazifalaringiz va muloqot qoidalaringiz:
1. Agar foydalanuvchi salom bersa (masalan: "salom", "assalomu alaykum"), juda samimiy alik oling va maktab haqida qanday savollari borligini so'rang. (Masalan: "Vaalaykum assalom! Mudarris Xalqaro maktabi virtual yordamchisiman. Maktabimiz haqida qanday ma'lumotlar sizni qiziqtiryapti? 😊").
2. Agar foydalanuvchi rahmat aytsa (masalan: "rahmat", "sog' bo'ling"), xursandchilik bilan javob qaytaring (Masalan: "Arziydi! Sizga va farzandingizga muvaffaqiyatlar tilayman! ✨").
3. Maktab haqida savol berishsa, faqat quyidagi ma'lumotlarga tayanib qisqa va aniq javob bering:
   - Qabul: 0-sinfdan 11-sinfgacha bo'lgan o'quvchilar.
   - Yo'nalishlar: IT, robototexnika, arab tili va ingliz tili.
   - Ustunlik: Arab tili darslarini chet ellik malakali ustozlar o'tadilar. IELTS, CEFR va SAT tayyorlov guruhlari bor.
   - Sharoit: Kun davomida 4 mahal issiq ovqat beriladi.
   - Filiallar: Sergeli, Qo'yliq, Katta Qa'ni.
   - Telefon: 55-513-75-75.
4. Foydalanuvchi darsga yozilmoqchi bo'lsa yoki "ro'yxatdan o'tish uchun nima qilishim kerak?" deb so'rasa, unga pastdagi tugmani bosishi kerakligini muloyimlik bilan ayting (Masalan: "Ro'yxatdan o'tish uchun pastdagi '📝 Ro'yxatdan o'tish' tugmasini bossangiz kifoya, sizdan ismingiz va raqamingizni so'rayman xolos! 👇").
"""

class LeadForm(StatesGroup):
    waiting_name = State()
    waiting_contact = State()

class ClearConfirm(StatesGroup):
    waiting_confirm = State()

# Telefon raqamni tekshirish uchun Regex
PHONE_REGEX = re.compile(r"^(\+?998)?\s?\(?\d{2}\)?\s?\d{3}\s?\d{2}\s?\d{2}$|^9\d{8}$")

# ===================== /start =====================
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    
    user = message.from_user
    await add_user_start(user.id, user.username or "")

    args = message.text.split()
    is_direct_reg = len(args) > 1 and args[1] == "reg"

    about_text = (
        "😊 *Assalomu alaykum!*\n\n"
        "Mudarris Xalqaro maktabi 0-sinfdan 11-sinfgacha bo‘lgan o‘quvchilarni qabul qiladi. "
        "Maktabimiz IT, robototexnika, arab tili va ingliz tili yo‘nalishlariga ixtisoslashtirilgan.\n\n"
        "👨‍🏫 *Arab tili darslarini chet ellik malakali ustozlar olib boradilar.*\n\n"
        "🏆 Farzandingiz maktabni bitirmasdan turib IELTS, CEFR va SAT kabi sertifikatlardan yuqori ball "
        "olish imkoniyatiga ega bo‘ladi, chunki bizda ushbu sertifikatlar uchun maxsus tayyorlov guruhlari ham muxim.\n\n"
        "🍽️ *Maktabda kun davomida 4 mahal ovqat beriladi.*\n\n"
        "✍️ Batafsil ma’lumot olish uchun ro‘yxatdan o'tish tugmasini bosing."
    )

    if is_direct_reg:
        await message.answer(about_text, parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
        await state.set_state(LeadForm.waiting_name)
        await message.answer("📝 *Ismingizni kiriting:*", parse_mode="Markdown")
    else:
        about_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📝 Ro'yxatdan o'tish")]],
            resize_keyboard=True
        )
        await message.answer(about_text, parse_mode="Markdown", reply_markup=about_keyboard)

# ===================== Ro'yxatdan o'tish =====================
@router.message(F.text == "📝 Ro'yxatdan o'tish")
async def ask_name(message: Message, state: FSMContext):
    await state.set_state(LeadForm.waiting_name)
    await message.answer(
        "📝 *Ismingizni kiriting:*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )

# ===================== Ism qabul qilish =====================
@router.message(LeadForm.waiting_name)
async def ask_contact(message: Message, state: FSMContext):
    name = message.text.strip()

    await state.update_data(full_name=name)
    await state.set_state(LeadForm.waiting_contact)

    contact_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📞 Kontaktni ulash", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer(
        f"🤝 *Rahmat, {name}!*\n\n"
        "📱 Telefon raqamingizni pastdagi tugmani bosib yuboring yoki *o'zingiz qo'lda yozib qoldiring*:\n\n"
        "📌 Namuna: `+998901234567` yoki `901234567`",
        parse_mode="Markdown",
        reply_markup=contact_keyboard
    )

# ===================== Kontakt qabul qilish =====================
@router.message(LeadForm.waiting_contact)
async def save_lead(message: Message, state: FSMContext):
    if message.contact:
        phone = message.contact.phone_number
    elif message.text:
        phone_input = message.text.strip()
        if not PHONE_REGEX.match(phone_input.replace(" ", "")):
            await message.answer(
                "⚠️ *Xato telefon raqam kiritildi!*\n\n"
                "Iltimos, raqamni to'g'ri formatda kiriting yoki tugma orqali yuboring.\n"
                "📌 Namuna: `+998901234567`",
                parse_mode="Markdown"
            )
            return
        phone = phone_input
    else:
        return

    data = await state.get_data()
    full_name = data.get("full_name")
    user = message.from_user

    await update_user_lead(user.id, full_name, phone)
    await state.clear()

    # Ro'yxatdan o'tib bo'lgach, foydalanuvchiga doimiy tugmani qaytarib qo'yamiz
    reg_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📝 Ro'yxatdan o'tish")]],
        resize_keyboard=True
    )

    await message.answer(
        "🎉 *Rahmat! Ro'yxatdan muvaffaqiyatli o'tdingiz.*\n\n"
        "📞 Yaqin orada mutaxassislarimiz siz bilan bog'lanishadi.",
        reply_markup=reg_keyboard
    )

    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    username_text = f"@{user.username}" if user.username else "Mavjud emas"

    lead_message = (
        "⚡️ <b>YANGI ARIZA KELDI!</b>\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        f"👤 <b>Ismi:</b> {full_name}\n"
        f"📞 <b>Telefon:</b> {phone}\n"
        f"🌐 <b>Username:</b> {username_text}\n"
        f"🆔 <b>Telegram ID:</b> <code>{user.id}</code>\n"
        f"🕒 <b>Vaqt:</b> {now}\n\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
    )

    if message.bot:
        try:
            await message.bot.send_message(chat_id=LEADS_CHAT_ID, text=lead_message, parse_mode="HTML")
        except Exception as e:
            for admin_id in ADMIN_IDS:
                try:
                    await message.bot.send_message(
                        chat_id=admin_id, 
                        text=f"⚠️ <b>Guruhga ariza yuborishda xatolik!</b>\n\nXato turi: <code>{e}</code>",
                        parse_mode="HTML"
                    )
                except:
                    pass

# ===================== /stats - faqat admin =====================
@router.message(Command("stats"))
async def show_stats(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Sizda bu buyruq uchun ruxsat yo'q.")
        return

    stats_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Kunlik"), KeyboardButton(text="📆 Haftalik")],
            [KeyboardButton(text="🗓 Oylik"), KeyboardButton(text="📊 Umumiy")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "📊 *Statistika boshqaruv paneli*\n\n"
        "Qaysi davr bo'yicha hisobotlarni ko'rishni istaysiz?",
        parse_mode="Markdown",
        reply_markup=stats_keyboard
    )

@router.message(F.text.in_(["📅 Kunlik", "📆 Haftalik", "🗓 Oylik", "📊 Umumiy"]))
async def show_period_stats(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    period_map = {
        "📅 Kunlik": ("day", "Bugun"),
        "📆 Haftalik": ("week", "So'nggi 7 kun"),
        "🗓 Oylik": ("month", "So'nggi 30 kun"),
        "📊 Umumiy": ("all", "Barcha vaqt"),
    }

    period_key, period_label = period_map[message.text]
    stats = await get_stats(period_key)

    total = stats["started"]
    completed = stats["completed"]
    not_completed = stats["not_completed"]

    conversion = round((completed / total) * 100, 1) if total > 0 else 0.0
    filled = int(conversion / 10)
    bar = "🟩" * filled + "⬜" * (10 - filled)

    await message.answer(
        f"📈 *Statistika — {period_label}*\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        f"👥  */start* bosganlar:  *{total}* ta\n\n"
        f"✅  Ro'yxatdan o'tganlar:  *{completed}* ta\n\n"
        f"❌  Yarimta tashlab ketganlar:  *{not_completed}* ta\n\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"📊  *Konversiya ko'rsatkichi:* *{conversion}%*\n{bar}",
        parse_mode="Markdown"
    )

# ===================== /leads - leadlar ro'yxati =====================
@router.message(Command("leads"))
async def show_leads(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Sizda bu buyruq uchun ruxsat yo'q.")
        return

    args = message.text.split()
    page = int(args[1]) if len(args) > 1 and args[1].isdigit() else 1
    per_page = 10
    offset = (page - 1) * per_page

    leads = await get_all_leads(limit=per_page, offset=offset)
    total = await get_leads_count()
    total_pages = max(1, (total + per_page - 1) // per_page)

    if not leads:
        await message.answer("📭 Hozircha bazada hech qanday arizalar mavjud emas.")
        return

    lines = [
        f"📋 *Kelib tushgan ariza leadlari*\n"
        f"_(Sahifa {page}/{total_pages} | Jami: {total} ta)_\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
    ]

    for i, (tg_id, username, full_name, phone, completed_at) in enumerate(leads, start=offset + 1):
        uname = f"@{username}" if username else "yo'q"
        date_str = completed_at[:10] if completed_at else "—"
        lines.append(f"\n* {i}. {full_name}*\n   ▫️ Telefon: `{phone}`\n   ▫️ Profil: {uname} | `{tg_id}`\n   ▫️ Sana: _{date_str}_")

    if total_pages > 1:
        nav = []
        if page > 1: nav.append(f"◀️ `/leads {page - 1}`")
        if page < total_pages: nav.append(f"`/leads {page + 1}` ▶️")
        lines.append("\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n" + "   ".join(nav))

    await message.answer("\n".join(lines), parse_mode="Markdown")

# ===================== /export - CSV yuklash =====================
@router.message(Command("export"))
async def export_leads(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Sizda bu buyruq uchun ruxsat yo'q.")
        return

    total = await get_leads_count()
    if total == 0:
        await message.answer("📭 Eksport qilish uchun hech qanday ma'lumot yo'q.")
        return

    await message.answer("⏳ *Excel (CSV) fayl shakllantirilmoqda, iltimos kuting...*")

    csv_bytes = await export_leads_csv()
    filename = f"leads_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

    if message.bot:
        await message.bot.send_document(
            chat_id=message.chat.id,
            document=BufferedInputFile(csv_bytes, filename=filename),
            caption=f"📊 *Eksport yakunlandi!*\n\nJami *{total}* ta lead ma'lumotlari Excel faylga yuklandi.",
            parse_mode="Markdown"
        )

# ===================== /clear_leads =====================
@router.message(Command("clear_leads"))
async def clear_leads_cmd(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Sizda bu buyruq uchun ruxsat yo'q.")
        return

    total = await get_leads_count()
    if total == 0:
        await message.answer("📭 Tozalash uchun bazada ma'lumot mavjud emas.")
        return

    confirm_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Ha, o'chiraman"), KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await state.set_state(ClearConfirm.waiting_confirm)
    await message.answer(
        f"⚠️ *DIQQAT!*\n\nBazada jami *{total}* ta foydalanuvchi ma'lumotlari bor. O'chirilsa ortga qaytarib bo'lmaydi!",
        parse_mode="Markdown",
        reply_markup=confirm_keyboard
    )

@router.message(ClearConfirm.waiting_confirm, F.text == "✅ Ha, o'chiraman")
async def confirm_clear(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await state.clear()
        return

    deleted = await clear_all_leads()
    await state.clear()

    await message.answer(f"🗑 Bazada mavjud bo'lgan *{deleted}* ta yozuv butunlay o'chirildi! ✅", parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())

@router.message(ClearConfirm.waiting_confirm, F.text == "❌ Bekor qilish")
async def cancel_clear(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("✅ *Bekor qilindi.*", parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())

# ===================== Groq AI orqali savollarga javob berish =====================
@router.message(F.text)
async def handle_ai_chat(message: Message):
    user_text = message.text.strip()

    # Belgilangan menyu tugmalari bosilganda AI ishlamaydi
    if user_text in ["📝 Ro'yxatdan o'tish", "📅 Kunlik", "📆 Haftalik", "🗓 Oylik", "📊 Umumiy", "✅ Ha, o'chiraman", "❌ Bekor qilish"]:
        return

    if message.bot:
        try:
            await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
        except:
            pass

    # Har qanday muloqotda pastda doim ko'rinib turuvchi tugma
    reg_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📝 Ro'yxatdan o'tish")]],
        resize_keyboard=True
    )

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": MAKTAB_DATA},
                {"role": "user", "content": user_text}
            ],
            model="llama-3.3-70b-specdec",
            temperature=0.5,
        )
        reply_text = chat_completion.choices[0].message.content
        await message.answer(reply_text, reply_markup=reg_keyboard)
    except Exception as e:
        print(f"Groq AI xatolik yuz berdi: {e}")
        await message.answer(
            "😊 Mudarris Xalqaro maktabi virtual yordamchisiman!\n\n"
            "Tizimda vaqtincha texnik yangilanish ketmoqda. Maktabimiz haqida batafsil ma'lumot olish yoki ro'yxatdan o'tish uchun "
            "to'g'ridan-to'g'ri operatorimiz bilan bog'lanishingiz mumkin: 📞 55-513-75-75.",
            reply_markup=reg_keyboard
        )
