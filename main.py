"""
Slayd / Referat / Mustaqil ish Telegram boti
aiogram 3.x (Router + FSM)
 
Ishga tushirish:
    pip install -r requirements.txt
    export BOT_TOKEN="123456:ABC..."
    export ADMIN_ID="123456789"
    python bot.py
"""
 
import asyncio
import html
import logging
import os
from dataclasses import dataclass
from itertools import count
 
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatMemberStatus, ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
 
# ============================== SOZLAMALAR ==============================
 
BOT_TOKEN = os.getenv("BOT_TOKEN", "9194668167:AAHGY0r7vfd6tdCyK8IcWFlMgc8TahH2V0g")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8052376816"))  # Admin Telegram ID
 
# Majburiy obuna kanallari (bot shu kanallarda ADMIN bo‘lishi shart!)
REQUIRED_CHANNELS = ["@norboyevbuilder", "@usatslayt"]
 
CARD_NUMBER = "4073 4200 7949 1878"
CARD_OWNER = "Norboyev Nazarbek"
 
# varoq soni -> narx (so‘m)
PACKAGES = {10: 2000, 15: 5000, 20: 7000}
 
# Ixtiyoriy: AI orqali "Gamma" uslubidagi reja yaratish.
# Kalit bo‘lmasa yoki xato bo‘lsa, bot tayyor shablon asosida reja tuzadi.
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
 
PLAN_TIMEOUT = 240  # soniya (5 daqiqadan kam)
 
MENU_BTN = "📄 Slayd / Referat / Mustaqil ish"
 
# ============================== DIZAYNLAR ==============================
 
DESIGNS = {
    1: ("Minimalist", "Oq fon, ko‘p bo‘sh joy, bitta aksent rang", "Oq #FFFFFF, qora #111111, aksent #2D6CDF", "Inter / Helvetica"),
    2: ("IT / Tech", "Qorong‘i fon, neon aksentlar, kod uslubidagi elementlar", "Qora-ko‘k #0B1220, neon #00E5FF, binafsha #7C4DFF", "Inter + JetBrains Mono"),
    3: ("Biznes / Korporativ", "Qat’iy, ishonchli, grafik va diagrammalarga boy", "To‘q ko‘k #0A2540, oltin #C9A227, kulrang #F2F4F7", "Montserrat / Open Sans"),
    4: ("Kreativ", "Yorqin gradientlar, yumaloq shakllar, dinamik kompozitsiya", "Pushti #FF4D8D, binafsha #7B2FF7, sariq #FFD60A", "Poppins"),
    5: ("Ilmiy / Akademik", "Sodda, aniq, formulalar, jadvallar va manbalar uchun qulay", "Oq, to‘q ko‘k #1F3A5F, kulrang #E9ECEF", "Cambria / Georgia"),
    6: ("Tabiat / Eko", "Yumshoq yashil ranglar, organik shakllar, tabiat rasmlari", "Yashil #2E7D32, bej #F4F1E8, jigarrang #6D4C41", "Nunito"),
    7: ("Ta’lim / Maktab", "Quvnoq, ikonkalar ko‘p, tushunarli bloklar", "Sariq #FFC107, ko‘k #1E88E5, oq", "Open Sans / Nunito"),
    8: ("Premium Dark", "Qora fon, oltin detallar, nafis tipografiya", "Qora #121212, oltin #D4AF37, oq #F5F5F5", "Playfair Display + Lato"),
    9: ("Retro / Vintage", "Qadimiy qog‘oz teksturasi, katta sarlavhalar", "Krem #F5E6C8, qizil #B23A48, to‘q jigarrang #3E2723", "Bebas Neue + Merriweather"),
    10: ("Tibbiyot / Salomatlik", "Toza, yengil, ishonch uyg‘otuvchi ranglar", "Oq, firuza #00A6A6, och ko‘k #E0F7FA", "Lato / Open Sans"),
}
 
# ============================== SHABLON REJA ==============================
 
# (sarlavha, [tezislar]) — {t} o‘rniga mavzu qo‘yiladi
SLIDE_TEMPLATES = [
    ("Sarlavha slaydi", ["Mavzu: «{t}»", "Muallif ismi, guruh/lavozim va sana", "Katta sifatli rasm yoki dizayn fonidagi gradient"]),
    ("Reja / Mundarija", ["Kirish va dolzarblik", "Asosiy tushunchalar va mexanizm", "Statistika, afzallik va xavflar", "Kelajak istiqbollari va xulosa"]),
    ("Kirish: nega «{t}» muhim?", ["Mavzuning bugungi kundagi o‘rni", "Auditoriya uchun qanday foyda beradi", "Taqdimot maqsadi: asosiy g‘oyani 1 jumlada ayting"]),
    ("Muammo va dolzarblik", ["«{t}» bilan bog‘liq asosiy muammo", "Muammoning kelib chiqish sabablari", "Yechim izlash nega zarur"]),
    ("Asosiy tushunchalar", ["«{t}» ning aniq ta’rifi", "2–3 ta kalit termin va ularning izohi", "Oddiy hayotiy misol"]),
    ("Tarixiy rivojlanish", ["Paydo bo‘lishi va dastlabki bosqichlar", "Muhim burilish nuqtalari (timeline ko‘rinishida)", "Bugungi holatgacha yo‘l"]),
    ("Turlari va tasnifi", ["Asosiy yo‘nalishlar / turlar", "Har bir turning qisqa tavsifi", "Sxema yoki ikonkalar bilan ko‘rsating"]),
    ("Ishlash tamoyili / mexanizmi", ["Jarayon bosqichma-bosqich", "Asosiy ishtirokchilar yoki komponentlar", "Oqim diagrammasi (flow chart)"]),
    ("Raqamlar va statistika", ["3–4 ta ishonchli raqam (katta shriftda)", "Dinamika: o‘sish yoki kamayish grafigi", "Ma’lumot manbasini ko‘rsating"]),
    ("Afzalliklari", ["Eng muhim 3–4 ta ijobiy jihat", "Har biriga qisqa dalil yoki misol", "Yashil ikonkalar / belgilar"]),
    ("Kamchiliklari va xavflari", ["Asosiy cheklovlar va muammolar", "Xavflarni kamaytirish yo‘llari", "Ogohlantiruvchi rangli urg‘u"]),
    ("Amaliy misol (Case study)", ["Real vaziyat yoki loyiha", "Qo‘llanilgan yondashuv", "Erishilgan natija"]),
    ("O‘zbekistonda holat", ["Mamlakatimizdagi joriy ahvol", "Qabul qilingan dasturlar yoki loyihalar", "Yutuqlar va hal etilmagan masalalar"]),
    ("Dunyo tajribasi", ["Yetakchi mamlakatlar tajribasi", "Muvaffaqiyat omillari", "Biz uchun saboqlar"]),
    ("Qiyoslash jadvali", ["2–3 ta variantni mezonlar bo‘yicha solishtiring", "Jadval: ustunlar — variantlar, qatorlar — mezonlar", "Eng yaxshi variantni belgilang"]),
    ("Zamonaviy tendensiyalar", ["Hozirgi eng muhim trendlar", "Yangi texnologiyalar ta’siri", "Qaysi yo‘nalish tez o‘smoqda"]),
    ("Kelajak istiqbollari", ["Kelgusi 5–10 yilda kutilayotgan o‘zgarishlar", "Imkoniyatlar va yangi yo‘nalishlar", "Tayyorgarlik uchun tavsiyalar"]),
    ("Xulosa va tavsiyalar", ["3 ta asosiy xulosa", "Amaliy tavsiyalar", "Yakuniy fikr: auditoriyani harakatga undang"]),
    ("Foydalanilgan manbalar", ["Kitoblar, maqolalar, rasmiy saytlar", "Havola yoki nomlari ro‘yxati", "Kichik shriftda, tartibli joylashtiring"]),
    ("E’tiboringiz uchun rahmat!", ["Savollar bormi?", "Aloqa: telefon / Telegram / email", "Chiroyli yakuniy rasm yoki QR-kod"]),
]
 
PLAN_INDEXES = {
    10: [0, 1, 2, 4, 7, 8, 9, 16, 17, 19],
    15: [0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 15, 16, 17, 19],
    20: list(range(20)),
}
 
# ============================== FSM / MA’LUMOTLAR ==============================
 
 
class Slide(StatesGroup):
    topic = State()
    package = State()
    payment = State()
    waiting_admin = State()
    design = State()
 
 
@dataclass
class Order:
    id: int
    user_id: int
    username: str | None
    full_name: str
    topic: str
    pages: int
    price: int
    status: str = "pending"  # pending | approved | rejected
 
 
orders: dict[int, Order] = {}
order_counter = count(1)
 
storage = MemoryStorage()  # Productionda RedisStorage tavsiya etiladi
router = Router()
 
# ============================== YORDAMCHI FUNKSIYALAR ==============================
 
 
def fmt_price(value: int) -> str:
    return f"{value:,}".replace(",", " ") + " so‘m"
 
 
def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=MENU_BTN)]],
        resize_keyboard=True,
    )
 
 
def sub_kb(missing: list[str]):
    kb = InlineKeyboardBuilder()
    for ch in missing:
        kb.button(text=f"📢 Obuna bo‘lish: {ch}", url=f"https://t.me/{ch.lstrip('@')}")
    kb.button(text="✅ Tekshirish", callback_data="check_sub")
    kb.adjust(1)
    return kb.as_markup()
 
 
def packages_kb():
    kb = InlineKeyboardBuilder()
    for pages, price in PACKAGES.items():
        kb.button(text=f"{pages} ta varoq — {fmt_price(price)}", callback_data=f"pkg:{pages}")
    kb.button(text="❌ Bekor qilish", callback_data="cancel")
    kb.adjust(1)
    return kb.as_markup()
 
 
def payment_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ To‘lov qildim", callback_data="paid")
    kb.button(text="❌ Bekor qilish", callback_data="cancel")
    kb.adjust(1)
    return kb.as_markup()
 
 
def admin_kb(order_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Tushdi", callback_data=f"adm_ok:{order_id}")
    kb.button(text="❌ Tushmadi", callback_data=f"adm_no:{order_id}")
    kb.adjust(2)
    return kb.as_markup()
 
 
def designs_kb():
    kb = InlineKeyboardBuilder()
    for num in DESIGNS:
        kb.button(text=str(num), callback_data=f"design:{num}")
    kb.adjust(5)
    return kb.as_markup()
 
 
def payment_text(topic: str, pages: int, price: int) -> str:
    return (
        "💳 <b>To‘lov ma’lumotlari</b>\n\n"
        f"📌 Mavzu: <b>{html.escape(topic)}</b>\n"
        f"📄 Varoqlar: <b>{pages} ta</b>\n"
        f"💵 Summa: <b>{fmt_price(price)}</b>\n\n"
        f"Karta: <code>{CARD_NUMBER}</code>\n"
        f"Egasi: <b>{CARD_OWNER}</b>\n\n"
        "To‘lovni amalga oshirgach, <b>«✅ To‘lov qildim»</b> tugmasini bosing."
    )
 
 
def designs_text() -> str:
    lines = ["🎨 <b>Slayd dizaynini tanlang (1–10):</b>\n"]
    for num, (name, desc, _, _) in DESIGNS.items():
        lines.append(f"<b>{num}. {name}</b> — {desc}")
    lines.append("\nQuyidagi tugmalardan o‘zingizga yoqqan raqamni bosing 👇")
    return "\n".join(lines)
 
 
def split_text(text: str, limit: int = 3800) -> list[str]:
    chunks: list[str] = []
    cur = ""
    for para in text.split("\n\n"):
        if cur and len(cur) + len(para) + 2 > limit:
            chunks.append(cur)
            cur = ""
        while len(para) > limit:
            chunks.append(para[:limit])
            para = para[limit:]
        cur = f"{cur}\n\n{para}" if cur else para
    if cur:
        chunks.append(cur)
    return chunks
 
 
async def get_missing_channels(bot: Bot, user_id: int) -> list[str]:
    missing = []
    for ch in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(ch, user_id)
            ok = member.status in (
                ChatMemberStatus.MEMBER,
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.CREATOR,
            ) or (member.status == ChatMemberStatus.RESTRICTED and getattr(member, "is_member", False))
            if not ok:
                missing.append(ch)
        except TelegramAPIError as e:
            logging.error("Kanalni tekshirib bo‘lmadi (%s): %s — bot kanalda adminmi?", ch, e)
            missing.append(ch)
    return missing
 
 
async def ensure_subscribed(message: Message, bot: Bot) -> bool:
    missing = await get_missing_channels(bot, message.from_user.id)
    if missing:
        await message.answer(
            "❗️ Botdan foydalanish uchun quyidagi kanallarga obuna bo‘ling, so‘ng «✅ Tekshirish» tugmasini bosing:",
            reply_markup=sub_kb(missing),
        )
        return False
    return True
 
 
# ============================== REJA GENERATSIYASI ==============================
 
 
def template_plan(topic: str, pages: int) -> str:
    safe_topic = html.escape(topic)
    indexes = PLAN_INDEXES[pages]
    blocks = []
    for n, idx in enumerate(indexes, start=1):
        title, bullets = SLIDE_TEMPLATES[idx]
        body = "\n".join(f"• {b.format(t=safe_topic)}" for b in bullets)
        blocks.append(f"<b>{n}-slayd. {title.format(t=safe_topic)}</b>\n{body}")
    return "\n\n".join(blocks)
 
 
async def ai_plan(topic: str, pages: int, design_num: int) -> str | None:
    """AI orqali reja (ixtiyoriy). Natija HTML-escape qilingan holda qaytariladi."""
    if not ANTHROPIC_API_KEY:
        return None
    try:
        from anthropic import AsyncAnthropic
    except ImportError:
        logging.warning("anthropic kutubxonasi o‘rnatilmagan — shablon ishlatiladi")
        return None
 
    name, desc, _, _ = DESIGNS[design_num]
    prompt = (
        "Sen professional taqdimot kontent-strategi va dizaynerisan (Gamma.app uslubida).\n"
        f"Mavzu: {topic}\n"
        f"Slaydlar soni: aynan {pages} ta\n"
        f"Dizayn uslubi: {name} — {desc}\n\n"
        "Vazifa: mukammal, strukturalashtirilgan slayd rejasini yoz. Har bir slayd uchun:\n"
        "1) sarlavha, 2) slaydga yoziladigan 3–4 ta qisqa tayyor tezis, 3) 'Vizual:' qatorida rasm/diagramma/ikonka tavsiyasi.\n"
        "Birinchi slayd — sarlavha, ikkinchisi — reja, oxirgisi — xulosa va 'Rahmat'.\n"
        "Format: har bir slayd 'N-slayd. Sarlavha' qatori bilan boshlansin, slaydlar orasida bo‘sh qator bo‘lsin. "
        "Tezislar '•' belgisi bilan. Markdown belgilarni (#, *, **) ishlatma. Til: o‘zbek (lotin). "
        "Kirish va xulosa gaplarini yozma, faqat reja."
    )
    try:
        client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY, timeout=180)
        resp = await client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=6000,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
        return html.escape(text) if text else None
    except Exception as e:  # noqa: BLE001
        logging.error("AI reja xatosi: %s", e)
        return None
 
 
async def build_plan(topic: str, pages: int, design_num: int) -> str:
    name, desc, palette, font = DESIGNS[design_num]
    header = (
        f"🎨 <b>Tanlangan dizayn: {design_num}. {name}</b>\n"
        f"Uslub: {desc}\n"
        f"Ranglar: {palette}\n"
        f"Shrift: {font}\n\n"
        f"📌 <b>Mavzu: {html.escape(topic)}</b>\n"
        f"📄 Slaydlar soni: {pages} ta"
    )
    body = await ai_plan(topic, pages, design_num) or template_plan(topic, pages)
    footer = (
        "💡 <b>Maslahat:</b> tayyor rejani Gamma.app, Canva yoki PowerPoint’ga qo‘yib, "
        "yuqoridagi ranglar va shriftlarni qo‘llang — slayd tayyor bo‘ladi."
    )
    return f"{header}\n\n{body}\n\n{footer}"
 
 
# ============================== 1. /START VA OBUNA ==============================
 
 
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    if not await ensure_subscribed(message, bot):
        return
    await message.answer(
        f"👋 Salom, <b>{html.escape(message.from_user.full_name)}</b>!\n"
        "Asosiy menyudan kerakli bo‘limni tanlang.",
        reply_markup=main_menu_kb(),
    )
 
 
@router.callback_query(F.data == "check_sub")
async def check_sub(call: CallbackQuery, bot: Bot):
    missing = await get_missing_channels(bot, call.from_user.id)
    if missing:
        await call.answer("❌ Hali barcha kanallarga obuna bo‘lmadingiz!", show_alert=True)
        return
    await call.answer("✅ Obuna tasdiqlandi!")
    try:
        await call.message.delete()
    except TelegramAPIError:
        pass
    await bot.send_message(
        call.from_user.id,
        "✅ Rahmat! Endi botdan foydalanishingiz mumkin.",
        reply_markup=main_menu_kb(),
    )
 
 
@router.callback_query(F.data == "cancel")
async def cancel(call: CallbackQuery, state: FSMContext, bot: Bot):
    await state.clear()
    await call.answer("Bekor qilindi")
    try:
        await call.message.delete()
    except TelegramAPIError:
        pass
    await bot.send_message(call.from_user.id, "Bekor qilindi. Asosiy menyu:", reply_markup=main_menu_kb())
 
 
# ============================== 2–3. MENYU, MAVZU, NARXLAR ==============================
 
 
@router.message(F.text == MENU_BTN)
async def slide_start(message: Message, state: FSMContext, bot: Bot):
    if not await ensure_subscribed(message, bot):
        return
    await state.clear()
    await state.set_state(Slide.topic)
    await message.answer(
        "📝 Slayd (referat / mustaqil ish) <b>mavzusini</b> yozib yuboring:\n"
        "<i>Masalan: Sun’iy intellekt va uning kelajagi</i>"
    )
 
 
@router.message(Slide.topic, F.text)
async def get_topic(message: Message, state: FSMContext):
    topic = message.text.strip()
    if len(topic) < 3 or len(topic) > 200:
        await message.answer("❗️ Mavzu 3 dan 200 tagacha belgidan iborat bo‘lsin. Qayta yozing:")
        return
    await state.update_data(topic=topic)
    await state.set_state(Slide.package)
    await message.answer(
        f"📌 Mavzu: <b>{html.escape(topic)}</b>\n\n"
        "Varoqlar sonini tanlang:",
        reply_markup=packages_kb(),
    )
 
 
@router.message(Slide.topic)
async def topic_not_text(message: Message):
    await message.answer("❗️ Iltimos, mavzuni matn ko‘rinishida yozing.")
 
 
@router.callback_query(Slide.package, F.data.startswith("pkg:"))
async def choose_package(call: CallbackQuery, state: FSMContext):
    pages = int(call.data.split(":")[1])
    if pages not in PACKAGES:
        await call.answer("Noto‘g‘ri tanlov", show_alert=True)
        return
    price = PACKAGES[pages]
    data = await state.get_data()
    await state.update_data(pages=pages, price=price)
    await state.set_state(Slide.payment)
    await call.answer()
    await call.message.edit_text(payment_text(data["topic"], pages, price), reply_markup=payment_kb())
 
 
# ============================== 4. TO‘LOV VA ADMIN ==============================
 
 
@router.callback_query(Slide.payment, F.data == "paid")
async def user_paid(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    user = call.from_user
    order = Order(
        id=next(order_counter),
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        topic=data["topic"],
        pages=data["pages"],
        price=data["price"],
    )
    admin_text = (
        "💰 <b>Yangi to‘lov!</b>\n\n"
        f"🧾 Buyurtma: <b>#{order.id}</b>\n"
        f"👤 Foydalanuvchi ID: <code>{order.user_id}</code>\n"
        f"🔗 Username: {'@' + user.username if user.username else 'yo‘q'}\n"
        f"📛 Ism: {html.escape(order.full_name)}\n"
        f"📌 Mavzu: {html.escape(order.topic)}\n"
        f"📄 Tanlangan varoq: <b>{order.pages} ta — {fmt_price(order.price)}</b>"
    )
    try:
        await bot.send_message(ADMIN_ID, admin_text, reply_markup=admin_kb(order.id))
    except TelegramAPIError as e:
        logging.error("Adminga xabar yuborilmadi: %s", e)
        await call.answer("⚠️ Hozir adminga xabar yuborib bo‘lmadi. Birozdan so‘ng qayta urinib ko‘ring.", show_alert=True)
        return
 
    orders[order.id] = order
    await state.set_state(Slide.waiting_admin)
    await call.answer()
    await call.message.edit_text(
        "⏳ <b>To‘lovingiz adminga yuborildi.</b>\n"
        "Admin tasdiqlagach, sizga xabar keladi. Iltimos, kuting."
    )
 
 
@router.callback_query(Slide.waiting_admin)
async def waiting_admin_any(call: CallbackQuery):
    await call.answer("⏳ To‘lovingiz tekshirilmoqda, iltimos kuting.", show_alert=True)
 
 
@router.callback_query(F.data.startswith("adm_"), F.from_user.id == ADMIN_ID)
async def admin_decision(call: CallbackQuery, bot: Bot):
    action, oid = call.data.split(":")
    order = orders.get(int(oid))
    if not order or order.status != "pending":
        await call.answer("Bu to‘lov allaqachon ko‘rib chiqilgan.", show_alert=True)
        return
 
    user_ctx = FSMContext(
        storage=storage,
        key=StorageKey(bot_id=bot.id, chat_id=order.user_id, user_id=order.user_id),
    )
 
    if action == "adm_ok":
        order.status = "approved"
        verdict = "✅ <b>Tushdi deb tasdiqlandi</b>"
        await user_ctx.set_state(Slide.design)
        await user_ctx.update_data(topic=order.topic, pages=order.pages, price=order.price)
        try:
            await bot.send_message(
                order.user_id,
                "✅ <b>To‘lovingiz tasdiqlandi!</b> Slayd yaratish imkoniyati faollashtirildi.",
            )
            await bot.send_message(order.user_id, designs_text(), reply_markup=designs_kb())
        except TelegramAPIError as e:
            logging.error("Foydalanuvchiga xabar yuborilmadi: %s", e)
    else:
        order.status = "rejected"
        verdict = "❌ <b>Tushmadi deb belgilandi</b>"
        await user_ctx.set_state(Slide.payment)
        await user_ctx.update_data(topic=order.topic, pages=order.pages, price=order.price)
        try:
            await bot.send_message(
                order.user_id,
                "❌ <b>To‘lovingiz tushmagan.</b>\n"
                "Agar to‘lov qilgan bo‘lsangiz, ma’lumotlarni tekshirib, qaytadan «✅ To‘lov qildim» tugmasini bosing.\n\n"
                + payment_text(order.topic, order.pages, order.price),
                reply_markup=payment_kb(),
            )
        except TelegramAPIError as e:
            logging.error("Foydalanuvchiga xabar yuborilmadi: %s", e)
 
    await call.answer("Bajarildi")
    try:
        await call.message.edit_text(call.message.html_text + f"\n\n{verdict}", reply_markup=None)
    except TelegramAPIError:
        pass
 
 
# ============================== 5. DIZAYN VA REJA ==============================
 
 
@router.callback_query(Slide.design, F.data.startswith("design:"))
async def choose_design(call: CallbackQuery, state: FSMContext, bot: Bot):
    design_num = int(call.data.split(":")[1])
    if design_num not in DESIGNS:
        await call.answer("Noto‘g‘ri tanlov", show_alert=True)
        return
 
    data = await state.get_data()
    topic, pages = data["topic"], data["pages"]
    await state.clear()  # takroriy bosishdan himoya
    await call.answer()
 
    name = DESIGNS[design_num][0]
    try:
        await call.message.edit_text(
            f"🎨 Siz <b>{design_num}. {name}</b> dizaynini tanladingiz.\n"
            "⏳ Reja tayyorlanmoqda, bir necha daqiqa kuting..."
        )
    except TelegramAPIError:
        pass
 
    try:
        plan = await asyncio.wait_for(build_plan(topic, pages, design_num), timeout=PLAN_TIMEOUT)
    except asyncio.TimeoutError:
        logging.error("Reja vaqtida tayyor bo‘lmadi — shablon ishlatiladi")
        plan = (
            f"🎨 <b>Dizayn: {design_num}. {name}</b>\n\n"
            f"📌 <b>Mavzu: {html.escape(topic)}</b>\n\n" + template_plan(topic, pages)
        )
 
    chunks = split_text(plan)
    for chunk in chunks:
        await bot.send_message(call.from_user.id, chunk)
    await bot.send_message(
        call.from_user.id,
        "✅ Slayd rejangiz tayyor! Yana buyurtma berish uchun menyudan foydalaning.",
        reply_markup=main_menu_kb(),
    )
 
 
# ============================== ISHGA TUSHIRISH ==============================
 
 
async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=storage)
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
 
 
if __name__ == "__main__":
    asyncio.run(main())
