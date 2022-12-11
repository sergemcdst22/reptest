from datetime import date, timedelta
import locale
from typing import List

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text
from fastapi import FastAPI, Request

from models import Order, OrderType, Igloo, User
from services import get_bc_intervals, \
    register_new_order, register_user_if_not_registered, get_all_igloos, get_all_order_types, \
        save_igloo, save_order_type, save_order, get_current_order_and_its_type, \
            text_data, save_num_guests, save_day, save_bot_last_message_id, get_bot_last_message_id, \
                get_cur_datetime, build_intervals_starts, build_intervals, save_interval, save_interval_start, save_interval_end, \
                    calc_order_price, build_intervals_ends
        

share_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
share_button = types.KeyboardButton(text="Share", request_contact=True)
share_keyboard.add(share_button)


greeting_txt = '''
Привет! Этот бот поможет забронировать иглу в Ташкенте. (... приветственный текст...)
Запишите наш телефон для уточнения любых вопросов (звонить с 11 до 19)
8 999 123 4567

Для удобства и так как после каждого гостя мы тщательно убираем иглу, часы аренды поделены на интервалы с промежутками между интервалами в 30 минут.
Цена указана за один интервал, поэтому чем больше вы заказываете интервалов, тем выгоднее
Сейчас мы предлагаем следующие интервалы:

12:00 - 13:00
13:30 - 14:30
15:00 - 15:30
16:00 - 17:00
17:30 - 18:30
19:00 - 20:00
21:00 - 22:00
22:30 - 23:30
24:00 - 01:00

Цена зависит от количества гостей, а также действут скидка на часы до 18:30 (цена до 18:30 для 1-2 гостей 200 000 сум за интервал, для 3-6 -- 250 000, после 18:30 для 1-2 гостей 300 000 за интервал, для 3-6 -- 400 000 сум)
Кроме почасовой аренды, доступны планы с фиксированным количеством интервалов и включенными в стоимость дополнительными услугами (еда, напитки, фотосессия). Чтобы узнать подробности о доступных планах, нажмите кнопку Планы.

Для заказа нажмите кнопку ✨ Новый заказ, после выбора вариантов и даты заказ будет предварительно оформлен и бот направит вам номер карты для его оплаты, при поступлении оплаты наш оператор в рабочее время (с 11 до 19) подтвердит заказ. Если оплата не поступит через час после оформления заказа (или до 12 часов следующего рабочего дня, если заказ сделан после 18), заказ будет удален.
До нажатия кнопки "подтвердить заказ" вы можете изменить все варианты, для этого предусмотрены кнопки "Сменить ..."'''

bot = Bot(token="5942557669:AAG-isUqC27f0dyi-caOA1cZlKWEli9uqRs")
dp = Dispatcher(bot)
admin_id = 5159856006
locale.setlocale(locale.LC_MONETARY, "uz_UZ.UTF-8")

def rows(buttons, row_size):
    """
    Build rows for the keyboard. Divides list of buttons to list of lists of buttons.

    """
    return [buttons[i:i + row_size] for i in range(0, max(len(buttons) - row_size, 0) + 1, row_size)]


def build_calendar(user_id):
    cur_datetime = get_cur_datetime()
    today = date(cur_datetime.year, cur_datetime.month, cur_datetime.day)
    weekday = today.weekday()

    if weekday == 0:
        days = [(today + timedelta(days=i), True, get_bc_intervals(user_id, today + timedelta(days=i))) for i in range(14)]
    else:
        monday = today - timedelta(days=weekday)
        days = [(monday + timedelta(days=i), weekday <= i < 14 + weekday, 
            get_bc_intervals(user_id, monday + timedelta(days=i)) if weekday <= i <= 14 + weekday else None) for i in range(21)]
    
    days_buttons = [
        types.InlineKeyboardButton(text=f'✔{d[0].day}' if d[1] and d[2] else '--', callback_data=f"day_{d[0].day}.{d[0].month}_{str(d[2])}" if d[1] and d[2] else '_')
        for d in days
    ]

    keyboard = types.InlineKeyboardMarkup(row_width=7)
    keyboard.add(*days_buttons)
    keyboard.add(types.InlineKeyboardButton(text="Выбрать этот день", callback_data="day_choose"))
    return keyboard



def build_calendar2(order: Order, order_type: OrderType):
    cur_datetime = get_cur_datetime()
    today = date(cur_datetime.year, cur_datetime.month, cur_datetime.day)
    weekday = today.weekday()

    if order_type.sum_per_hour_12:
        ...
    else:
        ...





def build_start_times_for_date(intervals: List[str]):

    intervals_buttons = [
        types.InlineKeyboardButton(text=f'{interval}', callback_data=f"start_interval_{interval}")
        for interval in intervals
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    keyboard.add(*intervals_buttons)    
    keyboard.add(types.InlineKeyboardButton(text="Выбрать это начало интервала", callback_data="start_interval_choose"))
    return keyboard


def build_end_times_for_date(intervals: List[str]):

    intervals_buttons = [
        types.InlineKeyboardButton(text=f'{interval}', callback_data=f"end_interval_{interval}")
        for interval in intervals
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    keyboard.add(*intervals_buttons)    
    keyboard.add(types.InlineKeyboardButton(text="Выбрать это окончание интервала", callback_data="end_interval_choose"))
    return keyboard


def build_both_times_for_date(intervals: List[str]):
    intervals_buttons = [
        types.InlineKeyboardButton(text=f'{interval}', callback_data=f"interval_{interval}")
        for interval in intervals
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    keyboard.add(*intervals_buttons)    
    keyboard.add(types.InlineKeyboardButton(text="Выбрать этот интервал", callback_data="interval_choose"))
    return keyboard


def build_plan_buttons_for_choose(show_details_btn=True, plans=None):
    plans = plans or get_all_order_types()
    plan_buttons = [types.InlineKeyboardButton(text=plan.name, callback_data=f"plan_{plan.id}_{plan.name}") for plan in plans]

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(*plan_buttons)
    if show_details_btn:
        keyboard.add(types.InlineKeyboardButton(text="Показать подробное описание планов", callback_data="plans_show"))
    return keyboard


def build_igloo_buttons_for_choose(show_details_btn=True, igloos=None):
    igloos = igloos or get_all_igloos()
    igloo_buttons = [types.InlineKeyboardButton(text=igloo.name, callback_data=f"igloo_{igloo.id}_{igloo.name}") for igloo in igloos]

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(*igloo_buttons)
    if show_details_btn:
        keyboard.add(types.InlineKeyboardButton(text="Показать фото иглу по адресам", callback_data="igloos_show"))
    return keyboard


def build_num_guests_buttons_for_choose(): 
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton(text="1-2", callback_data="numguests_2_1-2"))
    keyboard.add(types.InlineKeyboardButton(text="3-6", callback_data="numguests_6_3-6"))
    return keyboard


def build_approve_button(): 
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton(text="подтвердить", callback_data="approve"))
    return keyboard



async def ask_igloo(message: types.Message, user_id: int):
    msg = await message.answer("Выберите адрес", reply_markup=build_igloo_buttons_for_choose())
    save_bot_last_message_id(user_id, msg.message_id)


async def ask_order_type(message: types.Message, user_id: int):
    msg = await message.answer("Выберите план", reply_markup=build_plan_buttons_for_choose())
    save_bot_last_message_id(user_id, msg.message_id)


async def ask_guests_count(message: types.Message, user_id: int):
    msg = await message.answer("Выберите число гостей", reply_markup=build_num_guests_buttons_for_choose())
    save_bot_last_message_id(user_id, msg.message_id)


async def ask_order_date(message: types.Message, user_id: int):
    order, order_type = get_current_order_and_its_type(user_id)
    dat = date.fromisoformat(order.date)
    spl = f"{dat.day}.{dat.month}", str(get_bc_intervals(user_id, dat))
    save_day(user_id, spl[0])
    msg = await message.answer(f'Выберите дату. Сейчас выбрана: {". Доступные интервалы: ".join(spl)}', reply_markup=build_calendar(user_id))
    save_bot_last_message_id(user_id, msg.message_id)


async def ask_order_user_approve(message: types.Message, user_id: int, order: Order):
    msg = await message.answer(f"Все данные введены, нажмите кнопку, чтобы подтвердить заказ. {text_data(order)}. После нажатия кнопки 'подтвердить' изменить заказ с помощью бота будет невозможно, если нужно что-то поменять, сделайте это сейчас с помощью одной из команд 'change...'", reply_markup=build_approve_button())
    save_bot_last_message_id(user_id, msg.message_id)



@dp.message_handler(Text(startswith="✨ Новый заказ"))
async def start(message: types.Message):
    register_user_if_not_registered(message.from_id, message.from_user.first_name, message.from_user.full_name)
    register_new_order(message.from_id)
    
    try:
        last_msg_id = get_bot_last_message_id(message.from_id)
        await bot.delete_message(message.from_id, last_msg_id)
    except:
        ...


    await ask_igloo(message, message.from_id)



@dp.message_handler(Text(startswith="📜 Сменить план"))
async def change_plan(message: types.Message):
    tg_id = message.from_id

    order, order_type = get_current_order_and_its_type(tg_id)
    if not order:
        await message.answer("Нет текущего заказа. Для старта оформления введите команду /new")
        return

    try:
        last_msg_id = get_bot_last_message_id(tg_id)
        await bot.delete_message(tg_id, last_msg_id)
    except:
        ...

    await ask_order_type(message, tg_id)


@dp.message_handler(Text(startswith="🧭 Сменить адрес"))
async def change_igloo(message: types.Message):
    tg_id = message.from_id

    order, order_type = get_current_order_and_its_type(tg_id)
    if not order:
        await message.answer("Нет текущего заказа. Для старта оформления введите команду /new")
        return

    try:
        last_msg_id = get_bot_last_message_id(tg_id)
        await bot.delete_message(tg_id, last_msg_id)
    except:
        ...
    await ask_igloo(message, tg_id)


@dp.message_handler(Text(startswith="📅 Сменить время и дату"))
async def change_datetime(message: types.Message):
    tg_id = message.from_id    

    order, order_type = get_current_order_and_its_type(tg_id)
    if not order:
        await message.answer("Нет текущего заказа. Для старта оформления введите команду /new")
        return
    if not order.igloo_id:
        await message.answer("Адрес не выбран")
        return
    if not order_type:
        await message.answer("План не выбран")
        return 
        
    try:
        last_msg_id = get_bot_last_message_id(tg_id)
        print(last_msg_id)
        await bot.delete_message(tg_id, last_msg_id)
    except:
        ...

    await ask_order_date(message, tg_id)


@dp.message_handler(Text(startswith="👨‍👧‍👧 Сменить число гостей"))
async def change_guests_cnt(message: types.Message):
    tg_id = message.from_id
    order, order_type = get_current_order_and_its_type(tg_id)
    if not order:
        await message.answer("Нет текущего заказа. Для старта оформления введите команду /new")
        return
    if not order_type:
        await message.answer("План не выбран")
        return
    if not order_type.sum_per_hour_12:
        await message.answer("Для пакетных планов число гостей не указывается")
        return        

    try:
        last_msg_id = get_bot_last_message_id(tg_id)
        await bot.delete_message(tg_id, last_msg_id)
    except:
        ...
    await ask_guests_count(message, tg_id)


@dp.message_handler(commands="start")
async def cmd_start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.row("✨ Новый заказ")
    buttons = ["📜 Сменить план", "🧭 Сменить адрес", "📅 Сменить время и дату", "👨‍👧‍👧 Сменить число гостей"] 
    keyboard.add(*buttons)
    await message.answer(greeting_txt, reply_markup=keyboard)
 

@dp.callback_query_handler(Text(startswith="igloos_show"))
async def show_igloos(query: types.CallbackQuery): 

    message = query.message
    user_id = query.from_user.id   

    igloos = get_all_igloos()

    await query.answer()
    await message.delete()

    for igloo in igloos:
        with open(igloo.photo_local_path, 'rb') as f:
            img = f.read()
        await message.answer_photo(img, f"{igloo.name} ({igloo.address})")

    keyboard = build_igloo_buttons_for_choose(False, igloos)

    msg = await message.answer("Выберите адрес", reply_markup=keyboard) 
    save_bot_last_message_id(user_id, msg.message_id)


@dp.callback_query_handler(Text(startswith="igloo_"))
async def save_igloo_id(query: types.CallbackQuery):
    
    spl = query.data.split("_")[1:]
    igloo_id = int(spl[0])
    tg_id = query.from_user.id

    save_igloo(tg_id, igloo_id)
    
    await query.answer()
    await query.message.edit_text(f"Выбран адрес: {spl[1]}")

    save_bot_last_message_id(tg_id, -1)

    order, order_type = get_current_order_and_its_type(query.from_user.id)


    if not order_type:
        await ask_order_type(query.message, tg_id)
    elif order_type.sum_per_hour_12 and not order.guests_count:
        await ask_guests_count(query.message, tg_id)
    elif not order.date or not order.start_time:
        await ask_order_date(query.message, tg_id)
    else:
        await ask_order_user_approve(query.message, tg_id, order)


@dp.callback_query_handler(Text(startswith="plans_show"))
async def show_plans(query: types.CallbackQuery):
    message = query.message    
    user_id = query.from_user.id

    plans = get_all_order_types()

    await query.answer()
    await message.delete() 

    for plan in plans:
        with open(plan.photo_local_path, 'rb') as f:
            img = f.read()
        await message.answer_photo(img, f"{plan.name}")

    keyboard = build_plan_buttons_for_choose(False, plans)

    msg = await message.answer("Выберите план", reply_markup=keyboard)
    save_bot_last_message_id(user_id, msg.message_id)
    

@dp.callback_query_handler(Text(startswith="plan_"))
async def save_plan_id(query: types.CallbackQuery):

    spl = query.data.split("_")[1:]
    plan_id = int(spl[0])
    tg_id = query.from_user.id

    save_order_type(tg_id, plan_id)

    await query.answer()
    await query.message.edit_text(f"Выбран план: {spl[1]}")
    save_bot_last_message_id(tg_id, -1)

    order, order_type = get_current_order_and_its_type(query.from_user.id)

    if not order.igloo_id:
        await ask_igloo(query.message, tg_id)
    elif order_type.sum_per_hour_12 and not order.guests_count:
        await ask_guests_count(query.message, tg_id)
    elif not order.date or not order.start_time:
        await ask_order_date(query.message, tg_id)
    else:
        await ask_order_user_approve(query.message, tg_id, order)


@dp.callback_query_handler(Text(startswith="numguests_"))
async def save_numguests(query: types.CallbackQuery):

    spl = query.data.split("_")[1:]
    num_guests = int(spl[0])
    tg_id = query.from_user.id

    save_num_guests(tg_id, num_guests)

    await query.answer()
    await query.message.edit_text(f"Выбрано число гостей: {spl[1]}")
    save_bot_last_message_id(tg_id, -1)

    order, order_type = get_current_order_and_its_type(query.from_user.id)

    if not order.igloo_id:
        await ask_igloo(query.message, tg_id) 
    elif not order.date or not order.start_time:
        await ask_order_date(query.message, tg_id)
    else:
        await ask_order_user_approve(query.message, tg_id, order)


@dp.callback_query_handler(Text(startswith="approve"))
async def approve_order(query: types.CallbackQuery):

    txt_order, price, order_id, removing_at, (card_number, card_bank, card_name) = save_order(query.from_user.id)
    
    await query.answer()
    await query.message.edit_text(f"Спасибо, заказ ({txt_order}) сохранен. Переведите его цену: {locale.currency(price, grouping=True)} на карту {card_number}, в комментарии укажите номер заказа: {str(order_id)[-4:]}. Если перевод не будет доставлен до {str(removing_at)[:-6]}, заказ будет удален")
    await bot.send_message(admin_id, f"Заказ от пользователя {query.from_user.full_name} (tg id: {query.from_user.id}) номер {str(order_id)[-4:]} на сумму {price}. Подробно о заказе: {txt_order}")
 

@dp.callback_query_handler(Text(startswith="day_choose"))
async def choose_day(query: types.CallbackQuery):
    
    tg_id = query.from_user.id
    order, order_type = get_current_order_and_its_type(tg_id)
    
    intervals = None
    if order_type.min_hours_count:
        try:
            intervals = get_bc_intervals(tg_id, date.fromisoformat(order.date))
            intervals = build_intervals_starts(intervals, order_type.min_hours_count)
            save_interval_start(tg_id, intervals[0])
        except:
            ...
        if not intervals:
            await query.message.answer("В эту дату нет доступных интервалов, кто-то забронировал раньше Вас. Выберите другую дату (/changedatetime)")
            await query.message.delete()
            return
        await query.message.edit_text(f"Выбрана дата: {order.date}. Выберите начало интервала бронирования. Сейчас выбрано: {intervals[0]}", reply_markup=build_start_times_for_date(intervals))
    else:
        try:
            intervals = get_bc_intervals(tg_id, date.fromisoformat(order.date))
            intervals = build_intervals(intervals, order_type.total_hours_count)
            save_interval(tg_id, intervals[0], order_type.total_sum)
        except:
            ...
        if not intervals:
            await query.message.answer("В эту дату нет доступных интервалов, кто-то забронировал раньше Вас. Выберите другую дату (/changedatetime)")
            await query.message.delete()
            return
        await query.message.edit_text(f"Выбрана дата: {order.date}. Выберите интервал бронирования. Сейчас выбран: {intervals[0]}. Цена заказа: {locale.currency(order_type.total_sum, grouping=True)}", reply_markup=build_both_times_for_date(intervals))
    
    await query.answer()


@dp.callback_query_handler(Text(startswith="day_"))
async def prechoose_day(query: types.CallbackQuery):
       
    spl = query.data.split("_")[1:]
    await query.message.edit_text(f'Выберите дату. Сейчас выбрана: {". Доступные интервалы: ".join(spl)}', reply_markup=build_calendar(query.from_user.id))
    save_day(query.from_user.id, spl[0])
    await query.answer()


@dp.callback_query_handler(Text(startswith="start_interval_choose"))
async def choose_interval_start(query: types.CallbackQuery):
       
    tg_id = query.from_user.id
    order, order_type = get_current_order_and_its_type(tg_id)
    
    intervals = None
    end_intervals = None
    try:
        intervals = get_bc_intervals(tg_id, date.fromisoformat(order.date)) 
        end_intervals = build_intervals_ends(intervals, order.start_time, order_type.min_hours_count)
    except Exception as e:
        print(e)

    if not intervals or not end_intervals:
        await query.message.answer("В эту дату нет доступных интервалов, кто-то забронировал раньше Вас. Выберите другую дату (/changedatetime)")
        await query.message.delete()
        return

    price = calc_order_price(f"{order.start_time}-{end_intervals[0]}", order_type, order.guests_count)
    save_interval_end(tg_id, end_intervals[0], price)   

    await query.message.edit_text(f"Выбрана дата: {order.date} и начало интервала бронирования {order.start_time}. Выберите окончание интервала бронирования. Сейчас выбрано: {end_intervals[0]}. Сумма заказа: {price}", reply_markup=build_end_times_for_date(end_intervals))
    
    await query.answer()


@dp.callback_query_handler(Text(startswith="end_interval_choose"))
async def choose_interval_end(query: types.CallbackQuery):
       
    await query.answer()
    await query.message.delete()
    save_bot_last_message_id(query.from_user.id, -1)

    order, order_type = get_current_order_and_its_type(query.from_user.id)

    await ask_order_user_approve(query.message, query.from_user.id, order) 


@dp.callback_query_handler(Text(startswith="interval_choose"))
async def choose_interval(query: types.CallbackQuery):
       
    await query.answer()
    await query.message.delete()
    save_bot_last_message_id(query.from_user.id, -1)

    order, order_type = get_current_order_and_its_type(query.from_user.id)

    await ask_order_user_approve(query.message, query.from_user.id, order) 


@dp.callback_query_handler(Text(startswith="start_interval_"))
async def prechoose_interval_start(query: types.CallbackQuery):
       
    tg_id = query.from_user.id
    order, order_type = get_current_order_and_its_type(tg_id)
    start_interval = query.data.split("_")[-1]

    save_interval_start(tg_id, start_interval)    

    intervals = get_bc_intervals(tg_id, date.fromisoformat(order.date))
    intervals = build_intervals_starts(intervals, order_type.min_hours_count)    
    
    await query.message.edit_text(f"Выбрана дата: {order.date}. Выберите начало интервала бронирования. Сейчас выбрано: {start_interval}", reply_markup=build_start_times_for_date(intervals))

    await query.answer()


@dp.callback_query_handler(Text(startswith="end_interval_"))
async def prechoose_interval_end(query: types.CallbackQuery):

    tg_id = query.from_user.id
    order, order_type = get_current_order_and_its_type(tg_id)
    
    intervals = None
    end_intervals = None
    try:
        intervals = get_bc_intervals(tg_id, date.fromisoformat(order.date)) 
        end_intervals = build_intervals_ends(intervals, order.start_time, order_type.min_hours_count)
    except Exception as e:
        print(e)

    if not intervals or not end_intervals:
        await query.message.answer("В эту дату нет доступных интервалов, кто-то забронировал раньше Вас. Выберите другую дату (/changedatetime)")
        await query.message.delete()
        return

    end_interval = query.data.split("_")[-1]
    price = calc_order_price(f"{order.start_time}-{end_interval}", order_type, order.guests_count)
    save_interval_end(tg_id, end_intervals[0], price)   

    await query.message.edit_text(f"Выбрана дата: {order.date} и начало интервала бронирования {order.start_time}. Выберите окончание интервала бронирования. Сейчас выбрано: {end_interval}. Сумма заказа: {price}", reply_markup=build_end_times_for_date(end_intervals))
    
    await query.answer()
    

@dp.callback_query_handler(Text(startswith="interval_"))
async def prechoose_interval(query: types.CallbackQuery):
       
    tg_id = query.from_user.id
    order, order_type = get_current_order_and_its_type(tg_id)
    interval = query.data.split("_")[-1]

    save_interval(tg_id, interval, order_type.total_sum)    

    intervals = get_bc_intervals(tg_id, date.fromisoformat(order.date))
    intervals = build_intervals(intervals, order_type.total_hours_count)    
    
    
    
    await query.message.edit_text(f"Выбрана дата: {order.date}. Выберите интервал бронирования. Сейчас выбран: {interval}. Цена заказа: {locale.currency( order_type.total_sum, grouping=True )}", reply_markup=build_both_times_for_date(intervals))

    await query.answer()
  

#executor.start_polling(dp, skip_updates=True)
# my changes
app = FastAPI()


@app.get("/")
async def root():
    return "ok"


@app.post("/")
async def process_update(request: Request):
    update = await request.json()
    update = types.Update(**update)
    print("incoming", update)
    await dp.process_update(update)


 