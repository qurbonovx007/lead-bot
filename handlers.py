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
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# AI uchun yo'riqnoma (faqat bitta marta yozilgan)
MAKTAB_DATA = """Siz "Mudarris Xalqaro maktabi"ning juda xushmuomala va aqlli virtual yordamchisiz.
Maktab haqida savol berishsa, quyidagi ma'lumotlarga tayanib javob bering:
- Qabul: 0-11 sinf.
- Yo'nalishlar: IT, robototexnika, arab tili, ingliz tili.
- Sharoit: 4 mahal issiq ovqat.
- Filiallar: Sergeli, Qo'yliq, Katta Qa'ni.
- Telefon: 55-513-75-75.
Ro'yxatdan o'tish uchun pastdagi tugmani bosing."""

class LeadForm(StatesGroup):
    waiting_name = State()
    waiting_contact = State()

# Asosiy qismlar
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await add_user_start(message.from_user.id, message.from_user.username or "")
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📝 Ro'yxatdan o'tish")]], resize_keyboard=True)
    await message.answer("Assalomu alaykum! Mudarris Xalqaro maktabi yordamchisiman.", reply_markup=kb)

@router.message(F.text == "📝 Ro'yxatdan o'tish")
async def ask_name(message: Message, state: FSMContext):
    await state.set_state(LeadForm.waiting_name)
    await message.answer("Ismingizni kiriting:", reply_markup=ReplyKeyboardRemove())

@router.message(LeadForm.waiting_name)
async def ask_contact(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await state.set_state(LeadForm.waiting_contact)
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📞 Kontaktni ulash", request_contact=True)]], resize_keyboard=True)
    await message.answer("Telefon raqamingizni yuboring:", reply_markup=kb)

@router.message(LeadForm.waiting_contact)
async def save_lead(message: Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text
    data = await state.get_data()
    await update_user_lead(message.from_user.id, data.get("full_name"), phone)
    await state.clear()
    await message.answer("Rahmat! Mutaxassislarimiz bog'lanishadi.")

@router.message(F.text)
async def handle_ai_chat(message: Message):
    if message.text == "📝 Ro'yxatdan o'tish": return
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "system", "content": MAKTAB_DATA}, {"role": "user", "content": message.text}],
            model="llama-3.1-8b-instant",
            temperature=0.4,
        )
        await message.answer(chat_completion.choices[0].message.content)
    except Exception as e:
        print(f"Xatolik: {e}")
