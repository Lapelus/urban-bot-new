from typing import List
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from bot.config import settings
from bot.dao.models import Category


def main_user_kb(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Купить билеты", callback_data="catalog")
    kb.button(text="ℹ️ О мероприятии", callback_data="about")
    if user_id in settings.ADMIN_IDS:
        kb.button(text="⚙️ Админ панель", callback_data="admin_panel")
    kb.adjust(1)
    return kb.as_markup()


def catalog_kb(catalog_data: List[Category]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for category in catalog_data:
        kb.button(text=category.category_name, callback_data=f"category_{category.id}")
    kb.button(text="секретик", callback_data="home")
    kb.button(text="🏠 На главную", callback_data="home")
    kb.adjust(2)
    return kb.as_markup()


def purchases_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🗑 Смотреть билеты", callback_data="purchases")
    kb.button(text="🏠 На главную", callback_data="home")
    kb.adjust(1)
    return kb.as_markup()


def product_kb(product_id, price) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="💸 Купить", callback_data=f"name_buy_{product_id}_{price}")
    kb.button(text="🛍 Назад", callback_data="catalog")
    kb.button(text="🏠 На главную", callback_data="home")
    kb.adjust(2)
    return kb.as_markup()


def get_product_buy_kb(product_id, user_tg_id) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=f'Оплатить', callback_data=f"pay_{product_id}_{user_tg_id}")
    kb.button(text="🏠 На главную", callback_data="home")
    kb.adjust(1)
    return kb.as_markup()

def confirm_age_kb(product_id, price) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Подтверждаю', callback_data=f"buy_{product_id}_{price}")
    kb.button(text='Сори, мелюзга', callback_data='home')
    kb.adjust(1)
    return kb.as_markup()

def get_ticket_kb(payment_id) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Получить', callback_data=f"get_{payment_id}")
    kb.adjust(1)
    return kb.as_markup()

