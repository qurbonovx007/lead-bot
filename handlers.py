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

# Groq mijozini xavfsiz chaqirish
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MAKTAB_DATA = """
Sen "Mudarris Xalqaro maktabi"ning samimiy vakilisan. Bot emassan, maktab vakilisan.

BILIMLAR BAZASI:
- Nomi: Mudarris Xalqaro maktabi.
- Ta'lim: 0-11 sinf, pullik.
- Fanlar: IT, robototexnika, arab tili, ingliz tili.
- Tayyorlov: IELTS, CEFR, SAT guruhlari bor.
- Sharoit: 4 mahal issiq ovqat.
- Filiallar: Sergeli, Qo'yliq, Katta Qa'ni.
- Telefon: 55-513-75-75.
- Oylik to'lov: "To'lovlar sinf va bosqichga qarab farq qiladi, aniq ma'lumotni 55-513-75-75 raqamidan bilib olishingiz mumkin" deb ayt.

QOIDALAR:
1. Agar foydalanuvchi "salom" desa: "Assalomu alaykum! Mudarris Xalqaro maktabi yordamchisiman. Qanday savollaringiz bor?" deb javob ber.
2. Savol bersa: Salomlashma, tanishtirma, xuddi insondek qisqa va aniq javob ber.
3. Javobni bilmasang: "Bu bo'yicha aniq ma'lumotga ega emasman, 55-513-75-75 raqamiga qo'ng'iroq qilsangiz, batafsil tushuntirishadi" deb ayt.
4. "Nega?" kabi savollarga: "Chunki bizda ta'lim sifati va qulaylik birinchi o'rinda turadi" deb ayt.
"""

class LeadForm(StatesGroup):
    waiting_name = State()
    waiting_contact = State()

class ClearConfirm(StatesGroup):
    waiting_confirm = State()

PHONE_REGEX = re.compile(r"^(\+?998)?\s?\(?\d{2}\)?\s?\d{3}\s?\d{2}\s?\d{2}$|^9\d{8}$")

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await add_user_start(message.from_user.id, message.from_user.username or "")
    about_text = "😊 Assalomu alaykum! Mudarris Xalqaro maktabiga xush kelibsiz. Ro'yxatdan o'tish yoki savollaringiz uchun yordam berishga tayyorman."
    await message.answer(about_text, reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📝 Ro'yxatdan o'tish")]], resize_keyboard=True))

@router.message(F.text == "📝 Ro'yxatdan o'tish")
async def ask_name(message: Message, state: FSMContext):
    await state.set_state(LeadForm.waiting_name)
    await message.answer("📝 Ismingizni kiriting:", reply_markup=ReplyKeyboardRemove())

@router.message(LeadForm.waiting_name)
async def ask_contact(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text.strip())
    await state.set_state(LeadForm.waiting_contact)
    await message.answer("📱 Telefon raqamingizni yuboring:", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📞 Kontaktni ulash", request_contact=True)]], resize_keyboard=True))

@router.message(LeadForm.waiting_contact)
async def save_lead(message: Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text
    data = await state.get_data()
    await update_user_lead(message.from_user.id, data.get("full_name"), phone)
    await state.clear()
    await message.answer("🎉 Rahmat! Mutaxassislarimiz bog'lanishadi.", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📝 Ro'yxatdan o'tish")]], resize_keyboard=True))

@router.message(F.text)
async def handle_ai_chat(message: Message):
    if message.text in ["📝 Ro'yxatdan o'tish", "📅 Kunlik", "📆 Haftalik", "🗓 Oylik", "📊 Umumiy", "✅ Ha, o'chiraman", "❌ Bekor qilish"]:
        return
    
    try:
        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "system", "content": MAKTAB_DATA}, {"role": "user", "content": message.text.strip()}],
            model="llama-3.1-8b-instant",
            temperature=0.2, 
        )
        await message.answer(chat_completion.choices[0].message.content)
    except Exception:
        await message.answer("Mudarris Xalqaro maktabi: Telefon 55-513-75-75. Iltimos, raqamga qo'ng'iroq qiling.")
