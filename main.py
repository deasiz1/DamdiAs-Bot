import random
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, ContentType
import logging

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("TELEGRAM_ADMIN_ID", "0"))

if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
if not ADMIN_ID:
    raise ValueError("TELEGRAM_ADMIN_ID environment variable is required")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()


class OrderStates(StatesGroup):
    waiting_for_language = State()
    viewing_menu = State()
    waiting_for_day = State()
    waiting_for_quantity = State()
    waiting_for_contact = State()
    waiting_for_delivery = State()
    waiting_for_address = State()
    waiting_for_time = State()
    waiting_for_payment = State()


MENU = {
    "Понедельник":
    "Макароны с мясом, салат, компот, хлеб, приборы",
    "Вторник":
    "Манты, салат, компот, хлеб, приборы",
    "Среда":
    "Рассольник, котлеты с пюре,  винегрет, компот, хлеб, приборы",
    "Четверг":
    "Суп лапша куриный, манты, салат свекольный, компот, хлеб, приборы",
    "Пятница":
    "Борщ, плов, ачичук, компот, хлеб, приборы",
    "Суббота":
    "Чечевичный суп, жаркое из курицы, салат витаминный, компот, хлеб, приборы"
}

MENU_KZ = {
    "Дүйсенбі":
    "Макарон етпен, салат, компот, нан, ас құралдары",
    "Сейсенбі":
    "Манты, салат, компот, нан, ас құралдары",
    "Сәрсенбі":
    "Рассольник, картоп пюресі мен котлет, винегрет салаты, компот, нан, ас құралдары",
    "Бейсенбі":
    "Тауық кеспе сорпасы, манты, қызылша салаты, компот, нан,ас құралдары ",
    "Жұма":
    "Борщ, палау, ачичук салаты, компот, нан, ас құралдары",
    "Сенбі":
    "Жасымық сорпасы, тауық қуырдағы, дәруменді салат, компот, нан, ас құралдары"
}

PRICE_MEAL = 2500
DELIVERY_COST = 800


@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(keyboard=[[
        KeyboardButton(text="Русский 🇷🇺"),
        KeyboardButton(text="Қазақ 🇰🇿")
    ]],
                                   resize_keyboard=True)
    await message.answer("Выберите язык / Тілді таңдаңыз:",
                         reply_markup=keyboard)
    await state.set_state(OrderStates.waiting_for_language)


@dp.message(StateFilter(OrderStates.waiting_for_language))
async def choose_language(message: types.Message, state: FSMContext):
    if message.text == "Русский 🇷🇺":
        lang = "Русский 🇷🇺"
        menu = MENU
        view_menu_text = "Посмотреть меню"
        choose_day_text = "Выберите день:"
        choose_quantity_text = "Выберите количество порций:"
        contact_text = "Пожалуйста, отправьте свой номер телефона:"
        delivery_text = "Выберите способ получения:"
        pickup_text = "Введите время самовывоза (например, 12:30):"
        address_text = "Введите адрес доставки:"
        payment_text = "Обязательно, Пожалуйста отправьте скриншот оплаты или PDF-файл (Kaspi/перевод)"
        greeting = ("Здравствуйте! 👋\n"
                    "Добро пожаловать в бот для заказа обеда! 🍲\n"
                    "Выберите блюда из меню и оформите заказ 😋\n"
                    "🚚 Доставка осуществляется с 13:00.")
    else:
        lang = "Қазақ 🇰🇿"
        menu = MENU_KZ
        view_menu_text = "Мәзірді қарау"
        choose_day_text = "Күнді таңдаңыз:"
        choose_quantity_text = "Порция санын таңдаңыз:"
        contact_text = "Телефон нөміріңізді жіберіңіз:"
        delivery_text = "Жеткізу әдісін таңдаңыз:"
        pickup_text = "Тауарды алу уақытын енгізіңіз (мысалы, 12:30):"
        address_text = "Жеткізу мекенжайын енгізіңіз:"
        payment_text = "Міндетті, төлемнің скриншотын немесе PDF файлын жіберіңіз (Kaspi/перевод)"
        greeting = ("Сәлеметсіз бе! 👋\n"
                    "Түскі асқа тапсырыс беру ботына қош келдіңіз! 🍲\n"
                    "Дәмді мәзірімізді қарап, тапсырысыңызды беріңіз 😋\n"
                    "🚚 Жеткізу 13:00-ден бастап жүзеге асырылады.")

    await state.update_data(language=lang,
                            menu=menu,
                            view_menu_text=view_menu_text,
                            choose_day_text=choose_day_text,
                            choose_quantity_text=choose_quantity_text,
                            contact_text=contact_text,
                            delivery_text=delivery_text,
                            pickup_text=pickup_text,
                            address_text=address_text,
                            payment_text=payment_text)

    await message.answer(greeting)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=view_menu_text, callback_data="view_menu")
    ]])
    await message.answer(f"{view_menu_text}:", reply_markup=keyboard)
    await state.set_state(OrderStates.viewing_menu)


@dp.callback_query(F.data == "view_menu",
                   StateFilter(OrderStates.viewing_menu))
async def show_menu(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    menu_text = "\n".join(
        [f"{day}: {dish}" for day, dish in data['menu'].items()])
    await callback.message.answer(f"Меню на неделю / Апта мәзірі:\n{menu_text}"
                                  )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=day, callback_data=f"day_{day}")
    ] for day in data['menu'].keys()])
    await callback.message.answer(data['choose_day_text'],
                                  reply_markup=keyboard)
    await state.set_state(OrderStates.waiting_for_day)


@dp.callback_query(F.data.startswith("day_"),
                   StateFilter(OrderStates.waiting_for_day))
async def choose_day(callback: types.CallbackQuery, state: FSMContext):
    day = callback.data.split("_", 1)[1]
    await state.update_data(day=day)
    data = await state.get_data()

    buttons = [[InlineKeyboardButton(text=str(i), callback_data=f"qty_{i}")]
               for i in range(1, 21)]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.answer(data['choose_quantity_text'],
                                  reply_markup=keyboard)
    await state.set_state(OrderStates.waiting_for_quantity)


@dp.callback_query(F.data.startswith("qty_"),
                   StateFilter(OrderStates.waiting_for_quantity))
async def quantity(callback: types.CallbackQuery, state: FSMContext):
    qty = int(callback.data.split("_", 1)[1])
    await state.update_data(quantity=qty)
    data = await state.get_data()
    await callback.message.answer(data['contact_text'])
    await state.set_state(OrderStates.waiting_for_contact)


@dp.message(StateFilter(OrderStates.waiting_for_contact))
async def contact(message: types.Message, state: FSMContext):
    await state.update_data(contact=message.text)
    data = await state.get_data()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Доставка(Yandex)" if data['language'] ==
                             "Русский 🇷🇺" else "Жеткізу(Yandex)",
                             callback_data="delivery"),
        InlineKeyboardButton(text="Самовывоз" if data['language'] ==
                             "Русский 🇷🇺" else "Өз-өзіңіз алып кету",
                             callback_data="pickup")
    ]])
    await message.answer(data['delivery_text'], reply_markup=keyboard)
    await state.set_state(OrderStates.waiting_for_delivery)


@dp.callback_query(F.data.in_(["delivery", "pickup"]),
                   StateFilter(OrderStates.waiting_for_delivery))
async def choose_delivery(callback: types.CallbackQuery, state: FSMContext):
    mode = callback.data
    await state.update_data(mode=mode)
    data = await state.get_data()

    if mode == "pickup":
        await callback.message.answer(data['pickup_text'])
        await state.set_state(OrderStates.waiting_for_time)
    else:
        await callback.message.answer(data['address_text'])
        await state.set_state(OrderStates.waiting_for_address)


@dp.message(StateFilter(OrderStates.waiting_for_address))
async def address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    data = await state.get_data()
    order_id = random.randint(1000, 9999)
    await state.update_data(order_id=order_id)

    total = PRICE_MEAL * data['quantity'] + DELIVERY_COST
    text = (f"Ваш заказ / Сіздің тапсырыс:\n"
            f"День / Күн: {data['day']}\n"
            f"Порций / Порция саны: {data['quantity']}\n"
            f"Контакт / Байланыс: {data['contact']}\n"
            f"Адрес / Мекенжай: {data['address']}\n"
            f"Сумма / Бағасы: {total}₸\n"
            f"Номер заказа / Тапсырыс нөмірі: {order_id}")
    await message.answer(text)

    requisites_text = (
        "💳 Реквизиты для оплаты:\n"
        "Halyk перевод: +7 701 599 15 02 (Гюльхан А.)\n"
        "Kaspi перевод: +7 701 599 15 02 (Гюльхан А.)\n\n"
        "После оплаты отправьте скриншот или PDF подтверждения сюда 👇")
    await message.answer(requisites_text)
    await message.answer(data['payment_text'])
    await state.set_state(OrderStates.waiting_for_payment)


@dp.message(StateFilter(OrderStates.waiting_for_time))
async def pickup_time(message: types.Message, state: FSMContext):
    await state.update_data(time=message.text)
    data = await state.get_data()
    order_id = random.randint(1000, 9999)
    await state.update_data(order_id=order_id)

    total = PRICE_MEAL * data['quantity']
    text = (f"Ваш заказ / Сіздің тапсырыс:\n"
            f"День / Күн: {data['day']}\n"
            f"Порций / Порция саны: {data['quantity']}\n"
            f"Контакт / Байланыс: {data['contact']}\n"
            f"Время самовывоза / Алу уақыты: {data['time']}\n"
            f"Сумма / Бағасы: {total}₸\n"
            f"Номер заказа / Тапсырыс нөмірі: {order_id}")

    await message.answer(text)

    requisites_text = (
        "💳 Реквизиты для оплаты:\n"
        "Halyk перевод: +7 701 599 15 02 (Гюльхан А.)\n"
        "Kaspi перевод: +7 701 599 15 02 (Гюльхан А.)\n\n"
        "После оплаты отправьте скриншот или PDF подтверждения сюда 👇")
    await message.answer(requisites_text)
    await message.answer(data['payment_text'])
    await state.set_state(OrderStates.waiting_for_payment)


@dp.message(
    StateFilter(OrderStates.waiting_for_payment),
    F.content_type.in_(
        [ContentType.TEXT, ContentType.DOCUMENT, ContentType.PHOTO]))
async def payment(message: types.Message, state: FSMContext):
    data = await state.get_data()

    if message.document:
        if not message.document.file_name.lower().endswith(".pdf"):
            await message.answer(
                "Пожалуйста, отправьте PDF-файл или ссылку на оплату.")
            return
        payment_info = f"PDF-файл: {message.document.file_name}"
        await bot.send_document(ADMIN_ID,
                                message.document.file_id,
                                caption=f"Заказ №{data['order_id']}")
    elif message.photo:
        payment_info = "Скриншот оплаты"
        await bot.send_photo(ADMIN_ID,
                             message.photo[-1].file_id,
                             caption=f"Заказ №{data['order_id']}")
    else:
        payment_info = message.text

    order_summary = (
        f"Новый заказ!\n"
        f"Заказ №{data['order_id']}\n"
        f"День: {data['day']}\n"
        f"Порций: {data['quantity']}\n"
        f"Контакт: {data['contact']}\n"
        f"{'Адрес: ' + data.get('address','') if data.get('address') else ''}\n"
        f"{'Время самовывоза: ' + data.get('time','') if data.get('time') else ''}\n"
        f"Оплата: {payment_info}")
    await bot.send_message(ADMIN_ID, order_summary)
    await message.answer("Спасибо! Ваш заказ принят ✅")

    await state.clear()

    keyboard = ReplyKeyboardMarkup(keyboard=[[
        KeyboardButton(text="Русский 🇷🇺"),
        KeyboardButton(text="Қазақ 🇰🇿")
    ]],
                                   resize_keyboard=True)
    await message.answer("Выберите язык / Тілді таңдаңыз:",
                         reply_markup=keyboard)
    await state.set_state(OrderStates.waiting_for_language)


if __name__ == "__main__":
    print("Бот запускается...")
    asyncio.run(dp.start_polling(bot))
from aiohttp import web
import nest_asyncio

nest_asyncio.apply()  # чтобы asyncio мог работать в Replit


async def handle(request):
    return web.Response(text="Bot is alive!")


app = web.Application()
app.router.add_get("/", handle)


async def start_web():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()


# Запускаем веб-сервер и бота одновременно
async def main():
    await start_web()
    await dp.start_polling(bot)


import asyncio

asyncio.run(main())
