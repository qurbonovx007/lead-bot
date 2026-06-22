from aiogram import Router, F, Bot
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

from config import ADMIN_IDS, LEADS_CHAT_ID, BOT_ABOUT
from database import add_user_start, update_user_lead, get_stats, get_user

router = Router()

class LeadForm(StatesGroup):
    waiting_name = State()
    waiting_contact = State()

# ===================== /start =====================
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    
    user = message.from_user
    await add_user_start(user.id, user.username or "")

    # Bot haqida ma'lumot
    about_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Ma'lumot qoldirish")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        f"👋 Assalomu alaykum, *{user.first_name}*!\n\n"
        f"{BOT_ABOUT}",
        parse_mode="Markdown",
        reply_markup=about_keyboard
    )

# ===================== Ma'lumot qoldirish =====================
@router.message(F.text == "📋 Ma'lumot qoldirish")
async def ask_name(message: Message, state: FSMContext):
    await state.set_state(LeadForm.waiting_name)

    await message.answer(
        "📝 *Ism va familiyangizni kiriting:*\n\n"
        "📌 Namuna: `Abdullayev Jasur`",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )

# ===================== Ism qabul qilish =====================
@router.message(LeadForm.waiting_name)
async def ask_contact(message: Message, state: FSMContext):
    name = message.text.strip()

    if len(name.split()) < 2:
        await message.answer(
            "⚠️ Iltimos, *ism va familiyangizni* to'liq kiriting.\n\n"
            "📌 Namuna: `Abdullayev Jasur`",
            parse_mode="Markdown"
        )
        return

    await state.update_data(full_name=name)
    await state.set_state(LeadForm.waiting_contact)

    contact_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 Kontaktni ulash", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer(
        f"✅ Rahmat, *{name}*!\n\n"
        "📱 Endi telefon raqamingizni ulang:\n"
        "👇 Pastdagi tugmani bosing",
        parse_mode="Markdown",
        reply_markup=contact_keyboard
    )

# ===================== Kontakt qabul qilish =====================
@router.message(LeadForm.waiting_contact, F.contact)
async def save_lead(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    full_name = data.get("full_name")
    phone = message.contact.phone_number
    user = message.from_user

    await update_user_lead(user.id, full_name, phone)
    await state.clear()

    # Foydalanuvchiga tasdiqlash
    await message.answer(
        "🎉 *Ma'lumotlaringiz muvaffaqiyatli qabul qilindi!*\n\n"
        "📞 Tez orada siz bilan bog'lanamiz.\n"
        "Rahmat! 🙏",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )

    # Leads guruhiga yuborish
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    username_text = f"@{user.username}" if user.username else "Username yo'q"

    lead_message = (
        "🔔 *YANGI LEAD!*\n"
        "━━━━━━━━━━━━━━━\n"
        f"👤 *Ism-Familiya:* {full_name}\n"
        f"📞 *Telefon:* `{phone}`\n"
        f"🆔 *Username:* {username_text}\n"
        f"🔗 *Telegram ID:* `{user.id}`\n"
        f"🕐 *Vaqt:* {now}\n"
        "━━━━━━━━━━━━━━━"
    )

    try:
        await bot.send_message(
            chat_id=LEADS_CHAT_ID,
            text=lead_message,
            parse_mode="Markdown"
        )
    except Exception as e:
        # Admin ga xato xabari
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(admin_id, f"⚠️ Guruhga yuborishda xato: {e}")
            except:
                pass

# ===================== Kontakt o'rniga matn yuborsa =====================
@router.message(LeadForm.waiting_contact)
async def wrong_contact(message: Message):
    contact_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 Kontaktni ulash", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(
        "⚠️ Iltimos, *tugmani bosib* kontaktingizni yuboring.",
        parse_mode="Markdown",
        reply_markup=contact_keyboard
    )

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
        "📊 *Statistika paneli*\n\nQaysi davrni ko'rishni xohlaysiz?",
        parse_mode="Markdown",
        reply_markup=stats_keyboard
    )

# ===================== Statistika tugmalari =====================
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

    if total > 0:
        conversion = round((completed / total) * 100, 1)
    else:
        conversion = 0.0

    # Progress bar
    filled = int(conversion / 10)
    bar = "🟩" * filled + "⬜" * (10 - filled)

    await message.answer(
        f"📊 *Statistika — {period_label}*\n"
        "━━━━━━━━━━━━━━━\n"
        f"👥 /start bosganlar: *{total}* ta\n"
        f"✅ Ma'lumot qoldirganlar: *{completed}* ta\n"
        f"❌ Qoldirmaganlar: *{not_completed}* ta\n"
        "━━━━━━━━━━━━━━━\n"
        f"📈 Konversiya: *{conversion}%*\n"
        f"{bar}",
        parse_mode="Markdown"
    )
