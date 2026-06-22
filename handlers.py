from aiogram import Router, F, Bot
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, BufferedInputFile
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

from config import ADMIN_IDS, LEADS_CHAT_ID, BOT_ABOUT
from database import (
    add_user_start, update_user_lead, get_stats, get_user,
    get_all_leads, get_leads_count, clear_all_leads, export_leads_csv
)

router = Router()

class LeadForm(StatesGroup):
    waiting_name = State()
    waiting_contact = State()

class ClearConfirm(StatesGroup):
    waiting_confirm = State()

# ===================== /start =====================
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    
    user = message.from_user
    await add_user_start(user.id, user.username or "")

    about_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Ma'lumot qoldirish")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        f"👋 *Assalomu alaykum, {user.first_name}!*\n\n"
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
        "📌 Namuna: `Abdullayev Jasur` \n\n"
        "ℹ️ _Iltimos, ism va familiyangizni to'liq kiriting._",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )

# ===================== Ism qabul qilish =====================
@router.message(LeadForm.waiting_name)
async def ask_contact(message: Message, state: FSMContext):
    name = message.text.strip()

    if len(name.split()) < 2:
        await message.answer(
            "⚠️ *Xatolik:* Iltimos, ism va familiyangizni to'liq kiriting.\n\n"
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
        f"🤝 *Rahmat, {name}!*\n\n"
        "📱 Endi pastdagi tugmani bosish orqali *telefon raqamingizni* yuboring:",
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

    await message.answer(
        "🎉 *Rahmat! Ma'lumotlaringiz qabul qilindi.*\n\n"
        "📞 Yaqin orada mutaxassislarimiz siz bilan bog'lanishadi.",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )

    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    username_text = f"@{user.username}" if user.username else "Mavjud emas"

    # Guruhga tushadigan ariza dizayni (Kengaytirilgan va chiroyli)
    lead_message = (
        "⚡️ <b>YANGI ARIZA KELDI!</b>\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        f"👤 <b>Foydalanuvchi:</b> {full_name}\n"
        f"📞 <b>Telefon:</b> {phone}\n"
        f"🌐 <b>Username:</b> {username_text}\n"
        f"🆔 <b>Telegram ID:</b> <code>{user.id}</code>\n"
        f"🕒 <b>Vaqt:</b> {now}\n\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
    )

    try:
        await bot.send_message(chat_id=LEADS_CHAT_ID, text=lead_message, parse_mode="HTML")
    except Exception as e:
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
        "⚠️ *Iltimos, faqat pastdagi tugmani bosing!*\n\n"
        "Telefon raqamni qo'lda yozib yuborish mumkin emas.",
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
        "📊 *Statistika boshqaruv paneli*\n\n"
        "Qaysi davr bo'yicha hisobotlarni ko'rishni istaysiz? \n"
        "Pastdagi tugmalardan birini tanlang:",
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

    filled = int(conversion / 10)
    bar = "🟩" * filled + "⬜" * (10 - filled)

    # Statistika dizayni yangilandi
    await message.answer(
        f"📈 *Statistika — {period_label}*\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        f"👥  */start* bosganlar:  *{total}* ta\n\n"
        f"✅  Ma'lumot qoldirganlar:  *{completed}* ta\n\n"
        f"❌  Yarimta tashlab ketganlar:  *{not_completed}* ta\n\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"📊  *Konversiya ko'rsatkichi:* *{conversion}%*\n"
        f"{bar}",
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
        lines.append(
            f"\n* {i}. {full_name}*\n"
            f"   ▫️ Telefon: `{phone}`\n"
            f"   ▫️ Profil: {uname} | `{tg_id}`\n"
            f"   ▫️ Sana: _{date_str}_"
        )

    if total_pages > 1:
        nav = []
        if page > 1:
            nav.append(f"◀️ `/leads {page - 1}`")
        if page < total_pages:
            nav.append(f"`/leads {page + 1}` ▶️")
        lines.append("\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n" + "   ".join(nav))

    await message.answer("\n".join(lines), parse_mode="Markdown")

# ===================== /export - CSV yuklash =====================
@router.message(Command("export"))
async def export_leads(message: Message, bot: Bot):
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

    await bot.send_document(
        chat_id=message.chat.id,
        document=BufferedInputFile(csv_bytes, filename=filename),
        caption=f"📊 *Eksport yakunlandi!*\n\nJami *{total}* ta lead ma'lumotlari Excel faylga yuklandi.",
        parse_mode="Markdown"
    )

# ===================== /clear_leads - o'chirish =====================
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
        keyboard=[
            [KeyboardButton(text="✅ Ha, o'chiraman"), KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await state.set_state(ClearConfirm.waiting_confirm)
    await message.answer(
        f"⚠️ *DIQQAT! JIDDIY OGOHLANTIRISH*\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        f"Bazada jami *{total}* ta foydalanuvchi ma'lumotlari mavjud.\n\n"
        f"Haqiqatdan ham hammasini o'chirib, statistikani *0* ga tushirmoqchimisiz?\n\n"
        f"ℹ️ _Ushbu amalni ortga qaytarib bo'lmaydi!_",
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

    await message.answer(
        f"🗑 *Muvaffaqiyatli tozalandi!*\n\n"
        f"Bazada mavjud bo'lgan *{deleted}* ta yozuv butunlay o'chirildi va statistika 0 ga tushirildi. ✅",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )

@router.message(ClearConfirm.waiting_confirm, F.text == "❌ Bekor qilish")
async def cancel_clear(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "✅ *Bekor qilindi.* Ma'lumotlar bazasi o'zgarishsiz qoldirildi.",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )

@router.message(ClearConfirm.waiting_confirm)
async def clear_wrong_input(message: Message):
    await message.answer("⚠️ Iltimos, faqat taqdim etilgan tugmalardan birini bosing.")
