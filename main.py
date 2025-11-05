import os
import asyncio
import random
import logging
from aiohttp import web
import nest_asyncio

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, ContentType

# ====== Настройка asyncio для совместимости с Render ======
nest_asyncio.apply()

# ====== Переменные окружения ======
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("TELEGRAM_ADMIN_ID", "0"))

if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
if not ADMIN_ID:
    raise ValueError("TELEGRAM_ADMIN_ID environment variable is required")

# ====== Логирование ======
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ====== Состояния ======
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

# ====== Меню и цены ======
MENU = {
    "Понедельник": "Макароны с мясом, салат, компот, хлеб, приборы",
    "Вторник": "Манты, салат, компот, хлеб, приборы",
    "Среда": "Рассольник, котлеты с пюре, винегрет, компот, хлеб, приборы",
    "Четверг": "Суп лапша куриный, манты, салат свекольный, компот, хлеб, приборы",
    "Пятница": "Борщ, плов, ачичук, компот, хлеб, приборы",
    "Суббота": "Чечевичный суп, жаркое из курицы, салат витаминный, компот, хлеб, приборы"
}
MENU_KZ = {
    "Дүйсенбі": "Макарон етпен, салат, компот, нан, ас құралдары",
    "Сейсенбі": "Манты, салат, компот, нан, ас құралдары",
    "Сәрсенбі": "Рассольник, картоп пюресі мен котлет, винегрет салаты, компот, нан, ас құралдары",
    "Бейсенбі": "Тауық кеспе сорпасы, манты, қызылша салаты, компот, нан,ас құралдары ",
    "Жұма": "Борщ, палау, ачичук салаты, компот, нан, ас құралдары",
    "Сенбі": "Жасымық сорпасы, тауық қуырдағы, дәруменді салат, компот, нан, ас құралдары"
}
PRICE_MEAL = 2500
DELIVERY_COST = 800

# ====== Хендлеры ======
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Русский 🇷🇺"), KeyboardButton(text="Қазақ 🇰🇿")]], resize_keyboard=True)
    await message.answer("Выберите язык / Тілді таңдаңыз:", reply_markup=keyboard)
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
        greeting = ("Здравствуйте! 👋\nДобро пожаловать в бот для заказа обеда! 🍲\nВыберите блюда из меню и оформите заказ 😋\n🚚 Доставка осуществляется с 13:00.")
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
        greeting = ("Сәлеметсіз бе! 👋\nТүскі асқа тапсырыс беру ботына қош келдіңіз! 🍲\nДәмді мәзірімізді қарап, тапсырысыңызды беріңіз 😋\n🚚 Жеткізу 13:00-ден бастап жүзеге асырылады.")
    
    await state.update_data(language=lang, menu=menu, view_menu_text=view_menu_text,
                            choose_day_text=choose_day_text, choose_quantity_text=choose_quantity_text,
                            contact_text=contact_text, delivery_text=delivery_text,
                            pickup_text=pickup_text, address_text=address_text, payment_text=payment_text)
    await message.answer(greeting)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=view_menu_text, callback_data="view_menu")]])
    await message.answer(f"{view_menu_text}:", reply_markup=keyboard)
    await state.set_state(OrderStates.viewing_menu)

@dp.callback_query(F.data == "view_menu", StateFilter(OrderStates.viewing_menu))
async def show_menu(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    menu_text = "\n".join([f"{day}: {dish}" for day, dish in data['menu'].items()])
    await callback.message.answer(f"Меню на неделю / Апта мәзірі:\n{menu_text}")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=day, callback_data=f"day_{day}")] for day in data['menu'].keys()])
    await callback.message.answer(data['choose_day_text'], reply_markup=keyboard)
    await state.set_state(OrderStates.waiting_for_day)

@dp.callback_query(F.data.startswith("day_"), StateFilter(OrderStates.waiting_for_day))
async def choose_day(callback: types.CallbackQuery, state: FSMContext):
    day = callback.data.split("_", 1)[1]
    await state.update_data(day=day)
    data = await state.get_data()
    buttons = [[InlineKeyboardButton(text=str(i), callback_data=f"qty_{i}")] for i in range(1, 21)]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(data['choose_quantity_text'], reply_markup=keyboard)
    await state.set_state(OrderStates.waiting_for_quantity)

@dp.callback_query(F.data.startswith("qty_"), StateFilter(OrderStates.waiting_for_quantity))
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
        InlineKeyboardButton(text="Доставка(Yandex)" if data['language']=="Русский 🇷🇺" else "Жеткізу(Yandex)", callback_data="delivery"),
        InlineKeyboardButton(text="Самовывоз" if data['language']=="Русский 🇷🇺" else "Өз-өзіңіз алып кету", callback_data="pickup")
    ]])
    await message.answer(data['delivery_text'], reply_markup=keyboard)
    await state.set_state(OrderStates.waiting_for_delivery)

@dp.callback_query(F.data.in_(["delivery","pickup"]), StateFilter(OrderStates.waiting_for_delivery))
async def choose_delivery(callback: types.CallbackQuery, state: FSMContext):
    mode = callback.data
    await state.update_data(mode=mode)
    data = await state.get_data()
    if mode=="pickup":
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
    total =
