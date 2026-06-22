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

MAKTAB_DATA = """Siz "Mudarris Xalqaro maktabi"ning juda xushmuomala, samimiy va aqlli virtual yordamchisiz. 

Sizning vazifalaringiz va muloqot qoidalaringiz:
1. SALOMLASHISH: Agar foydalanuvchi birinchi marta salom bersa, samimiy alik oling. Agar foydalanuvchi salomlashmasdan savol bersa yoki ikkinchi marta murojaat qilayotgan bo'lsa, QAYTA SALOMLASHIB O'TIRMANG! Srazu savolning o'ziga aniq javob bering.
2. RAHMAT: Agar foydalanuvchi rahmat aytsa, xursandchilik bilan javob qaytaring.
3. MAKTAB MA'LUMOTLARI:
   - Qabul: 0-11 sinf.
   - Yo'nalishlar: IT, robototexnika, arab tili, ingliz tili.
   - Ustunlik: Arab tili darslari chet ellik ustozlar tomonidan o'tiladi. IELTS, CEFR, SAT guruhlari mavjud.
   - Sharoit: 4 mahal issiq ovqat.
   - Filiallar: Sergeli, Qo'yliq, Katta Qa'ni.
   - Telefon: 55-513-75-75.
4. RO'YXATDAN O'TISH: Agar foydalanuvchi yozilishni xohlasa, "Ro'yxatdan o'tish uchun pastdagi '📝 Ro'yxatdan o'tish' tugmasini bossangiz kifoya!" deb ayting."""

class LeadForm(StatesGroup):
    waiting_name = State()
    waiting_contact = State()

class ClearConfirm(StatesGroup):
    waiting_confirm = State()

PHONE_REGEX = re.compile(r"^(\+?998)?\s?\(?\d{2}\)?\s?\d{3}\s?\d{2}\s?\d{2}$|^9\d{8}$")

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    await add_user_start(user.id, user.username or "")
    args = message.text.split()
    is_direct_reg = len(args) > 1 and args[1] == "reg"
    about_text = ("😊 *Assalomu alaykum!*\n\nMudarris Xalqaro maktabiga xush kelibsiz. Batafsil ma’lumot olish uchun ro‘yxatdan o'tish tugmasini bosing.")
    
    if is_direct_reg:
        await message.answer(about_text, parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
        await state.set_state(LeadForm.waiting_name)
        await message.answer("📝 *Ismingizni kiriting:*", parse_mode="Markdown")
    else:
        kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📝 Ro'yxatdan o'tish")]], resize_keyboard=True)
        await message.answer(about_text, parse_mode="Markdown", reply_markup=kb)

@router.message(F.text == "📝 Ro'yxatdan o'tish")
async def ask_name(message: Message, state: FSMContext):
    await state.set_state(LeadForm.waiting_name)
    await message.answer("📝 *Ismingizni kiriting:*", parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())

@router.message(LeadForm.waiting_name)
async def ask_contact(message: Message, state: FSMContext):
    name = message.text.strip()
    await state.update_data(full_name=name)
    await state.set_state(LeadForm.waiting_contact)
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📞 Kontaktni ulash", request_contact=True)]], resize_keyboard=True, one_time_keyboard=True)
    await message.answer(f"🤝 *Rahmat, {name}!* Telefon raqamingizni yuboring:", parse_mode="Markdown", reply_markup=kb)

@router.message(LeadForm.waiting_contact)
async def save_lead(message: Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text
    data = await state.get_data()
    await update_user_lead(message.from_user.id, data.get("full_name"), phone)
    await state.clear()
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📝 Ro'yxatdan o'tish")]], resize_keyboard=True)
    await message.answer("🎉 *Rahmat! Mutaxassislarimiz bog'lanishadi.*", parse_mode="Markdown", reply_markup=kb)
    # Lead xabar yuborish qismi... (qolgan qismlarni o'zgarishsiz qoldiring)

@router.message(F.text)
async def handle_ai_chat(message: Message):
    if message.text in ["📝 Ro'yxatdan o'tish", "📅 Kunlik", "📆 Haftalik", "🗓 Oylik", "📊 Umumiy", "✅ Ha, o'chiraman", "❌ Bekor qilish"]:
        return
    
    try:
        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "system", "content": MAKTAB_DATA}, {"role": "user", "content": message.text.strip()}],
            model="llama-3.1-8b-instant",
            temperature=0.4, 
        )
        await message.answer(chat_completion.choices[0].message.content, reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📝 Ro'yxatdan o'tish")]], resize_keyboard=True))
    except Exception as e:
        await message.answer("Tizimda vaqtincha xatolik. Operator bilan bog'lanish: 55-513-75-75.")
