from aiogram import Router, F
from aiogram.enums import ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery, FSInputFile, BufferedInputFile
from loguru import logger
from pyexpat.errors import messages
from sqlalchemy.ext.asyncio import AsyncSession
from bot.user.img_gen import ticket_gen
from bot.admin.utils import process_dell_text_msg
from bot.config import bot, settings
from bot.dao.dao import UserDAO, CategoryDao, ProductDao, PurchaseDao, TicketDao
from bot.dao.models import Ticket
from bot.user.kbs import main_user_kb, catalog_kb, product_kb, get_product_buy_kb, confirm_age_kb
from bot.user.schemas import TelegramIDModel, ProductCategoryIDModel, PaymentData, TicketData
from bot.admin.kbs import admin_confirm_buy, cancel_kb_inline, home_kb_inline

catalog_router = Router()


class BuyTicket(StatesGroup):
    product_id = State()
    namesurname = State()
    year = State()
    tel_number = State()
    payment_id = State()


@catalog_router.callback_query(F.data == "catalog")
async def page_catalog(call: CallbackQuery, session_without_commit: AsyncSession):
    await call.answer("Загрузка каталога...")
    catalog_data = await CategoryDao.find_all(session=session_without_commit)

    await call.message.edit_text(
        text="Выберите категорию:",
        reply_markup=catalog_kb(catalog_data)
    )


@catalog_router.callback_query(F.data.startswith("category_"))
async def page_catalog_products(call: CallbackQuery, session_without_commit: AsyncSession):
    category_id = int(call.data.split("_")[-1])
    products_category = await ProductDao.find_all(session=session_without_commit,
                                                  filters=ProductCategoryIDModel(category_id=category_id))
    count_products = len(products_category)
    if count_products:
        await call.answer(f"В данной категории {count_products} товаров.")
        for product in products_category:
            product_text = (
                f"🎫 <b>{product.name}</b>\n\n"
                f"💰 <b>Цена:</b> {product.price} руб.\n\n"
                f"📝 <b>Описание:</b>\n<i>{product.description}</i>\n\n"
                f"━━━━━━━━━━━━━━━━━━"
            )
            await call.message.answer(
                product_text,
                reply_markup=product_kb(product.id, product.price)
            )
    else:
        await call.answer("В данной категории нет товаров.")


#@catalog_router.callback_query(F.data.startswith('buy_'))
#async def process_about(call: CallbackQuery, session_without_commit: AsyncSession):
#    user_info = await UserDAO.find_one_or_none(
#        session=session_without_commit,
#        filters=TelegramIDModel(telegram_id=call.from_user.id)
#    )
#    _, product_id, price = call.data.split('_')
#    await bot.send_invoice(
#        chat_id=call.from_user.id,
#        title=f'Оплата 👉 {price}₽',
#        description=f'Пожалуйста, завершите оплату в размере {price}₽, чтобы открыть доступ к выбранному товару.',
#        payload=f"{user_info.id}_{product_id}",
#        provider_token=settings.PROVIDER_TOKEN,
#        currency='rub',
#        prices=[LabeledPrice(
#            label=f'Оплата {price}',
#            amount=int(price) * 100
#        )],
#        reply_markup=get_product_buy_kb(price)
#    )
#    await call.message.delete()

@catalog_router.callback_query(F.data.startswith('name_buy_'))
async def user_process_buy_ticket(call: CallbackQuery, state: FSMContext):
    _, a, product_id, price = call.data.split('_')
    await call.answer('Введите необходимые данные')
    await call.message.delete()
    msg = await call.message.answer(text="✍️ Введите своё имя и фамилию", reply_markup=cancel_kb_inline())
    await state.update_data(last_msg_id=msg.message_id, product_id=product_id)
    await state.set_state(BuyTicket.namesurname)


@catalog_router.message(F.text, BuyTicket.namesurname)
async def user_insert_name(message: Message, state: FSMContext):
    await state.update_data(namesurname=message.text)
    await process_dell_text_msg(message, state)
    msg = await message.answer(text="🤓 Теперь введите свой курс", reply_markup=cancel_kb_inline())
    await state.update_data(last_msg_id=msg.message_id)
    await state.set_state(BuyTicket.year)


@catalog_router.message(F.text, BuyTicket.year)
async def user_insert_year(message: Message, state: FSMContext):
    await state.update_data(year=message.text)
    await process_dell_text_msg(message, state)
    msg = await message.answer(text="📱 Введите номер телефона(с которого будет совершен перевод)",
                               reply_markup=cancel_kb_inline())
    await state.update_data(last_msg_id=msg.message_id)
    await state.set_state(BuyTicket.tel_number)


@catalog_router.message(F.text, BuyTicket.tel_number)
async def user_insert_tel_number(message: Message, state: FSMContext, session_without_commit: AsyncSession):
    await state.update_data(tel_number=message.text)
    await process_dell_text_msg(message, state)
    product_id = await state.get_value(key='product_id')
    product_data = await ProductDao.find_one_or_none_by_id(data_id=int(product_id), session=session_without_commit)
    price = product_data.price
    msg = await message.answer(text="🔞 Подтвердите, что на момент проведения мероприятия Вам будет больше 18 лет",
                               reply_markup=confirm_age_kb(product_id, price))
    await state.update_data(last_msg_id=msg.message_id)
    await state.set_state(BuyTicket.payment_id)


@catalog_router.callback_query(F.data.startswith('buy_'), BuyTicket.payment_id)
async def process_about(call: CallbackQuery):
    _, product_id, price = call.data.split('_')
    text = (
        f"💸 Сумма оплаты: <b>{price}руб</b>\n"
        "Переведите указанную сумму на следующий номер телефона: <b>89660998213 Мария П. !!Т-банк!!</b>\n"
        "После совершения перевода <b>нажмите на кнопку</b> для проверки администратором\n\n"
        "🕒 <i>Время ожидания может достигать 1 часа, если спустя это время ничего не произошло, то напишите Толику: @toliktarakanov</i>"
    )
    return await call.message.answer(text=text, reply_markup=get_product_buy_kb(product_id, call.from_user.id))


@catalog_router.callback_query(F.data.startswith('pay_'), BuyTicket.payment_id)
async def process_about(call: CallbackQuery, session_with_commit: AsyncSession, state: FSMContext):
    _, product_id, user_tg_id = call.data.split('_')
    product_data = await ProductDao.find_one_or_none_by_id(session=session_with_commit, data_id=int(product_id))
    payment_data = {
        'user_id': int(call.from_user.id),
        'price': int(product_data.price),
        'product_id': int(product_id),
        'paid': False
    }
    payment_data_up = await PurchaseDao.find_one_or_none(session=session_with_commit,
                                                         filters=PaymentData(**payment_data))
    if payment_data_up:
        pass
    else:
        await PurchaseDao.add(session=session_with_commit, values=PaymentData(**payment_data))
    payment_data_up = await PurchaseDao.find_one_or_none(session=session_with_commit,
                                                         filters=PaymentData(**payment_data))
    ticket_data = await state.get_data()
    for admin_id in settings.ADMIN_IDS:
        try:
            username = call.from_user.username
            user_info = f"@{username} ({call.from_user.id})" if username else f"c ID {call.from_user.id}"

            await bot.send_message(
                chat_id=admin_id,
                text=(
                    f"💲 Пользователь {user_info} сделал запрос на оплату <b>{product_data.name}</b> (ID: {product_id}) "
                    f"за <b>{product_data.price} ₽</b>.\n"
                    f"Данные перевода: {ticket_data["namesurname"]} номер: {ticket_data["tel_number"]}\n"
                    "Проверьте свой электронный кошелек и подтвердите оплату"
                ),
                reply_markup=admin_confirm_buy(payment_data_up.id)
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления администраторам: {e}")
    await state.update_data(payment_id=str(payment_data_up.id))


@catalog_router.callback_query(F.data.startswith("get_"))
async def process_about(call: CallbackQuery, state: FSMContext, session_with_commit: AsyncSession):
    user_ticket_data = await state.get_data()
    product_data = await ProductDao.find_one_or_none_by_id(data_id=int(user_ticket_data["product_id"]),
                                                           session=session_with_commit)
    del user_ticket_data["last_msg_id"]
    del user_ticket_data["product_id"]
    await TicketDao.add(session_with_commit, values=TicketData(**user_ticket_data))
    await call.message.answer_photo(photo=BufferedInputFile(await ticket_gen(user_ticket_data["payment_id"], product_data.price), filename="ticket.jpeg"))
    await call.message.answer(text='Вернуться на главную', reply_markup=home_kb_inline())
#@catalog_router.pre_checkout_query(lambda query: True)
#async def pre_checkout_query(pre_checkout_q: PreCheckoutQuery):
#    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)


#@catalog_router.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
#async def successful_payment(message: Message, session_with_commit: AsyncSession):
#    payment_info = message.successful_payment
#    user_id, product_id = payment_info.invoice_payload.split('_')
#    payment_data = {
#        'user_id': int(user_id),
#        'price': payment_info.total_amount / 100,
#        'product_id': int(product_id)
#    }
#    # Добавляем информацию о покупке в базу данных
#    await PurchaseDao.add(session=session_with_commit, values=PaymentData(**payment_data))
#    product_data = await ProductDao.find_one_or_none_by_id(session=session_with_commit, data_id=int(product_id))
#
#    # Формируем уведомление администраторам
#    for admin_id in settings.ADMIN_IDS:
#        try:
#            username = message.from_user.username
#            user_info = f"@{username} ({message.from_user.id})" if username else f"c ID {message.from_user.id}"
#
#            await bot.send_message(
#                chat_id=admin_id,
#                text=(
#                    f"💲 Пользователь {user_info} купил товар <b>{product_data.name}</b> (ID: {product_id}) "
#                    f"за <b>{product_data.price} ₽</b>."
#                )
#            )
#        except Exception as e:
#            logger.error(f"Ошибка при отправке уведомления администраторам: {e}")
#
#    # Подготавливаем текст для пользователя
#    file_text = "📦 <b>Товар включает файл:</b>" if product_data.file_id else "📄 <b>Товар не включает файлы:</b>"
#    product_text = (
#        f"🎉 <b>Спасибо за покупку!</b>\n\n"
#        f"🛒 <b>Информация о вашем товаре:</b>\n"
#        f"━━━━━━━━━━━━━━━━━━\n"
#        f"🔹 <b>Название:</b> <b>{product_data.name}</b>\n"
#        f"🔹 <b>Описание:</b>\n<i>{product_data.description}</i>\n"
#        f"🔹 <b>Цена:</b> <b>{product_data.price} ₽</b>\n"
#        f"🔹 <b>Закрытое описание:</b>\n<i>{product_data.hidden_content}</i>\n"
#        f"━━━━━━━━━━━━━━━━━━\n"
#        f"{file_text}\n\n"
#        f"ℹ️ <b>Информацию о всех ваших покупках вы можете найти в личном профиле.</b>"
#    )
#
#    # Отправляем информацию о товаре пользователю
#    if product_data.file_id:
#        await message.answer_document(
#            document=product_data.file_id,
#            caption=product_text,
#            reply_markup=main_user_kb(message.from_user.id)
#        )
#    else:
#        await message.answer(
#            text=product_text,
#            reply_markup=main_user_kb(message.from_user.id)
#        )
