import json
import logging

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
)

from config import config
from database import repository as db
from utils.keyboards import plans_kb, main_menu_kb

logger = logging.getLogger(__name__)
router = Router()

# Prices in Telegram Stars (XTR). Logic: bigger volume = cheaper per gen.
# Pack 50:   75 ⭐ = 1.50 ⭐/gen
# Pack 200: 249 ⭐ = 1.25 ⭐/gen
# Starter:  199 ⭐ = 0.66 ⭐/gen  (300/mo)
# Pro:      599 ⭐ = 0.40 ⭐/gen  (1500/mo)
# Ultra:    999 ⭐ fair-use
PLANS = {
    "starter":  {"title": "Starter — 300 ген/мес",  "credits": 300,   "stars": 199,  "plan": "starter"},
    "pro":      {"title": "Pro — 1500 ген/мес",      "credits": 1500,  "stars": 599,  "plan": "pro"},
    "ultra":    {"title": "Ultra — безлимит",        "credits": 10000, "stars": 999,  "plan": "ultra"},
    "pack50":   {"title": "Пакет 50 генераций",      "credits": 50,    "stars": 75,   "plan": None},
    "pack200":  {"title": "Пакет 200 генераций",     "credits": 200,   "stars": 249,  "plan": None},
}


@router.message(Command("plans"))
@router.callback_query(F.data == "show_plans")
async def show_plans(event):
    text = (
        "⚡ <b>Пакеты и подписки</b>\n\n"
        "🆓 <b>Free:</b> 3 мема в день\n\n"
        "<b>Подписки (мес):</b>\n"
        "🔹 <b>Starter</b> — 300 ген · 199 ⭐\n"
        "🔷 <b>Pro</b> — 1500 ген + HD · 599 ⭐\n"
        "💎 <b>Ultra</b> — безлимит + HD · 999 ⭐\n\n"
        "<b>Разовые пакеты:</b>\n"
        "📦 50 генераций · 75 ⭐\n"
        "📦 200 генераций · 249 ⭐\n\n"
        "<i>Оплата через Telegram Stars ⭐</i>"
    )
    if isinstance(event, Message):
        await event.answer(text, parse_mode="HTML", reply_markup=plans_kb())
    else:
        await event.message.edit_text(text, parse_mode="HTML", reply_markup=plans_kb())
        await event.answer()


@router.callback_query(F.data.startswith("buy:"))
async def handle_buy(call: CallbackQuery, bot: Bot):
    plan_key = call.data.split(":")[1]
    plan = PLANS.get(plan_key)
    if not plan:
        await call.answer("Неизвестный план.", show_alert=True)
        return

    payload = json.dumps({"plan_key": plan_key, "user_id": call.from_user.id})
    await bot.send_invoice(
        chat_id=call.message.chat.id,
        title=plan["title"],
        description=f"Зачисление {plan['credits']} генераций на ваш аккаунт.",
        payload=payload,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=plan["title"], amount=plan["stars"])],
        start_parameter=f"buy_{plan_key}",
    )
    await call.answer()


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message):
    payment = message.successful_payment
    try:
        payload = json.loads(payment.invoice_payload)
    except Exception:
        logger.error("Bad payment payload: %s", payment.invoice_payload)
        return

    plan_key = payload.get("plan_key", "")
    user_id = message.from_user.id
    plan_info = PLANS.get(plan_key)
    if not plan_info:
        return

    payment_id = await db.create_payment(
        user_id=user_id,
        provider="telegram",
        amount=payment.total_amount,
        currency=payment.currency,
        payload=payload,
    )
    await db.confirm_payment(payment_id)

    if plan_info["plan"]:
        await db.set_plan(user_id, plan_info["plan"], plan_info["credits"])
    else:
        await db.add_credits(user_id, plan_info["credits"])

    await db.log_event(user_id, "payment_success", {
        "plan_key": plan_key,
        "credits": plan_info["credits"],
        "amount": payment.total_amount,
    })

    await message.answer(
        f"✅ Оплата прошла! Начислено <b>{plan_info['credits']}</b> генераций.\n"
        "Приятного мемотворчества! 🎉",
        parse_mode="HTML",
        reply_markup=main_menu_kb(),
    )
