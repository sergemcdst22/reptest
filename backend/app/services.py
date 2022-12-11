from datetime import datetime, date, timedelta
import pytz
from typing import List, Tuple, Optional
import locale

from sqlmodel import Session, select, create_engine

from models import Igloo, User, Order, OrderType, Info


locale.setlocale(locale.LC_MONETARY, "uz_UZ.UTF-8")

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

all_intervals = [[f"{h}:00-{h}:15", f"{h}:15-{h}:30", f"{h}:30-{h}:45", f"{h}:45-{h+1 if h+1 < 24 else 0}:00"] for h in list(range(12, 24)) + list(range(2))]
all_intervals = [i for a in all_intervals for i in a]


def intervaldiff(end: str, start: str):
    time1 = datetime(2022, 12, 9)
    hour, minute = map(int, start.split(':'))
    time1 = time1.replace(hour=hour, minute=minute)
    time2 = datetime(2022, 12, 9)
    hour, minute = map(int, end.split(':'))
    time2 = time2.replace(hour=hour, minute=minute)
    if time2.hour != 2:
        time1 = time1 + timedelta(minutes=15)
    if time1.hour > 5 and time2.hour <= 5:
        time2 = time2.replace(day=10)

    return (time2 - time1).seconds / 3600


def addhours(interval: str, hours: int):
    hour, minute = map(int, interval.split(":"))
    hour = (hour + hours) % 24
    return f"{hour}:{minute if minute != 0 else '00'}"


def build_intervals_starts(intervals: List[str], min_hours_count: int):

    result = []

    for interval in intervals:
        start_interval, end_interval = interval.split("-")
        cur_interval = start_interval
        while intervaldiff(end_interval, cur_interval) >= min_hours_count:
            result.append(cur_interval)
            cur_interval = add15(cur_interval)

    return result


def interval_in(interval: str, intervals: str) -> bool: 
    start, end = intervals.split("-")
    start_hour, start_minute = map(int, start.split(":"))
    end_hour, end_minute = map(int, end.split(":"))
    hour, minute = map(int, interval.split(":"))

    if end_hour < 5:
        end_hour += 24
    if hour < 5:
        hour += 24
 

    return start_hour < hour < end_hour or \
        hour > start_hour and hour == end_hour and (minute <= end_minute if end_hour==26 else minute < end_minute) or \
            hour == start_hour and minute >= start_minute and hour < end_hour or \
                hour == start_hour == end_hour and (start_minute <= minute <= end_minute if end_hour==26 else start_minute <= minute < end_minute)


def build_intervals_ends(intervals: List[str], start_interval: str, min_hours_count: int):

    result = []

    index = 0

    while index < len(intervals) and not interval_in(start_interval, intervals[index]):
        index += 1
    
    result = []
    cur_interval = addhours(start_interval, min_hours_count)
    while interval_in(cur_interval, intervals[index]):
        result.append(cur_interval)
        cur_interval = add15(cur_interval)      

    return result


def build_intervals(intervals: List[str], total_hours_count: int):

    result = []

    for interval in intervals:
        start_interval, end_interval = interval.split("-")
        cur_interval = start_interval
        while intervaldiff(end_interval, cur_interval) >= total_hours_count:
            result.append(f"{cur_interval}-{addhours(cur_interval, total_hours_count)}")
            cur_interval = add15(cur_interval)

    return result


def get_cur_datetime():
    tz = pytz.timezone('Asia/Tashkent')
    return datetime.now(tz)


def get_free_intervals(date: date, igloo_id):

    intervals = all_intervals[:]
    results = []
    date_str = str(date)

    with Session(engine) as session:
        statement = select(Order).where(Order.date == date_str).where(Order.igloo_id == igloo_id).where(Order.all_steps_gone == True)
        results = session.exec(statement).all()

    for order in results:         
        i = 0
        start = intervals[i].split("-")[0]
        while start != order.start_time:
            i += 1
            start = intervals[i].split("-")[0]

        for j in range(i, len(intervals)):                
            if intervals[j].split("-")[0] == order.end_time:
                break
            intervals[j] = "..."

    cur_datetime = get_cur_datetime()
    if date.day == cur_datetime.day:
        intervals = [interval for interval in intervals if int(interval.split("-")[0].split(":")[0]) > cur_datetime.hour or int(interval.split("-")[0].split(":")[0]) < 5]

    return intervals


def get_big_intervals(intervals):

    if intervals == all_intervals:
        start = all_intervals[0].split("-")[0]
        end = all_intervals[-1].split("-")[1]
        return [f"{start}-{end}"]

    answer = []
    i = 0
    n = len(intervals)
    
    while i < n:
        
        while i < n and intervals[i] == "...":
            i += 1
            
        if i == n:
            return answer

        subinterval = intervals[i]
 
        j = i + 1

        if j == n or intervals[j] == "...":
            answer.append(subinterval)
        else:
            while j < n and intervals[j] != "...":
                j += 1

            answer.append(f"{subinterval.split('-')[0]}-{intervals[j-1].split('-')[1]}")

            if j == n:
                return answer
        
        i = j + 1

    return answer


def interval_fits_min_hours(interval: str, min_hours: int):
    first, second = interval.split('-')
    time1 = datetime(2022, 12, 9)
    hour, minute = map(int, first.split(':'))
    time1 = time1.replace(hour=hour, minute=minute)
    time2 = datetime(2022, 12, 9)
    hour, minute = map(int, second.split(':'))
    time2 = time2.replace(hour=hour, minute=minute)
    if time1.hour > 5 and time2.hour <= 5:
        time2 = time2.replace(day=10)
    return (time2-time1).seconds >= (min_hours + 0.25) * 3600


def save_bot_last_message_id(tg_id, msg_id):
    with Session(engine) as session:
        statement = select(User).where(User.id == tg_id)
        result = session.exec(statement).first()

        result.last_bot_message_id = msg_id

        session.commit()


def get_bot_last_message_id(tg_id):
    with Session(engine) as session:
        statement = select(User).where(User.id == tg_id)
        result = session.exec(statement).first()

        return result.last_bot_message_id


def get_big_clear_intervals(date, igloo_id, min_hours=1):
    intervals = get_free_intervals(date, igloo_id)
    intervals = get_big_intervals(intervals)
    return [interval for interval in intervals if interval_fits_min_hours(interval, min_hours)]


def get_bc_intervals(user_id, date):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.id == user_id)).first()
        order = session.exec(select(Order).where(Order.id == user.current_order_id)).first()
        order_type = session.exec(select(OrderType).where(OrderType.id == order.order_type_id)).first()

    return get_big_clear_intervals(date, order.igloo_id, 
        order_type.total_hours_count if order_type.total_hours_count else order_type.min_hours_count)


def register_new_order(user_id) -> Order:

    with Session(engine) as session:
        statement = select(Order).where(Order.user_id == user_id).where(Order.all_steps_gone == False)
        results = session.exec(statement).all()

        for result in results:
            session.delete(result)

        session.commit()
    
    cur_datetime = get_cur_datetime()

    if cur_datetime.hour > 2:
        cur_date = date(cur_datetime.year, cur_datetime.month, cur_datetime.day)
    else:
        day_before_datetime = cur_datetime - timedelta(days=1)
        cur_date = date(day_before_datetime.year, day_before_datetime.month, day_before_datetime.day)

    if 12 <= cur_datetime.hour <= 15:
        removing_datetime = cur_datetime + timedelta(hours=3)
    else:
        days = 1 if cur_datetime.hour > 15 else 0
        removing_datetime = cur_datetime + timedelta(days=days)
        removing_datetime = removing_datetime.replace(hour = 14).replace(minute=0).replace(second=0).replace(microsecond=0)
 

    order = Order(date=str(cur_date), user_id=user_id, registered_at=str(cur_datetime), removing_at=str(removing_datetime))

    with Session(engine) as session:
        session.add(order)

        user = session.exec(select(User).where(User.id == user_id)).first()

        user.current_order_id = order.id

        session.commit()

    return order


def remove_non_payed_orders():

    cur_datetime = get_cur_datetime()

    with Session(engine) as session:
        statement = select(Order).where(Order.is_payed == False)
        results = session.exec(statement).all()

    removing_orders = []

    for result in results:
        exp_datetime = datetime.fromisoformat(result.removing_at)
        if exp_datetime >= cur_datetime:
            removing_orders.append(result)

    with Session(engine) as session:
        for o in removing_orders:
            session.delete(o)
        session.commit()


def register_user_if_not_registered(tg_id, name, fullname):

    with Session(engine) as session:

        statement = select(User).where(User.id == tg_id)
        results = session.exec(statement).all()

        if not results:
            session.add(User(id=tg_id, name=name, fullname=fullname))

        session.commit()


def save_igloo(tg_id: int, igloo_id: int):

    with Session(engine) as session:
        statement = select(User).where(User.id == tg_id)
        result = session.exec(statement).first()

        statement = select(Order).where(Order.id == result.current_order_id)
        result = session.exec(statement).first()

        result.igloo_id = igloo_id

        session.commit()


def save_order_type(tg_id: int, order_type_id: int):

    with Session(engine) as session:
        statement = select(User).where(User.id == tg_id)
        result = session.exec(statement).first()

        statement = select(Order).where(Order.id == result.current_order_id)
        result = session.exec(statement).first()

        result.order_type_id = order_type_id

        session.commit()


def get_full_date(day: str):
    day, month = map(int, day.split("."))
    cur_datetime = get_cur_datetime()
    if cur_datetime.month == 12 and month == 1:
        return str(date(cur_datetime.year + 1, month, day))
    else:
        return str(date(cur_datetime.year, month, day))


def save_day(tg_id: int, day: str):

    with Session(engine) as session:
        statement = select(User).where(User.id == tg_id)
        result = session.exec(statement).first()

        statement = select(Order).where(Order.id == result.current_order_id)
        result = session.exec(statement).first()

        result.date = get_full_date(day)

        session.commit()


def save_num_guests(tg_id: int, guests_count: int):

    with Session(engine) as session:
        statement = select(User).where(User.id == tg_id)
        result = session.exec(statement).first()

        statement = select(Order).where(Order.id == result.current_order_id)
        result = session.exec(statement).first()

        result.guests_count = guests_count

        session.commit()



def calc_order_price(interval: str, order_type: OrderType, guests_count: int):

    if order_type.total_sum:
        return order_type.total_sum

    first, second = interval.split('-')
    time1 = datetime(2022, 12, 9)
    hour, minute = map(int, first.split(':'))
    time1 = time1.replace(hour=hour, minute=minute)
    time2 = datetime(2022, 12, 9)
    hour, minute = map(int, second.split(':'))
    time2 = time2.replace(hour=hour, minute=minute)
    if time1.hour > 5 and time2.hour <= 5:
        time2 = time2.replace(day=10)

    if time1.hour >= 18 or time1.hour <= 5:
        return int(((time2-time1).seconds /3600) * (order_type.sum_per_hour_12 if guests_count < 3 else order_type.sum_per_hour_36))

    elif time2.hour < 18 and time2.hour > 5 or (time2.hour == 18 and time2.minute == 0):
        return int(((time2-time1).seconds /3600) * (order_type.sum_per_hour_12_happy if guests_count < 3 else order_type.sum_per_hour_36_happy))

    else:
        happy_price = ((datetime(2022, 12, 9, 18, 0, 0)-time1).seconds /3600) * (order_type.sum_per_hour_12_happy if guests_count < 3 else order_type.sum_per_hour_36_happy)
        evening_price = ((time2-datetime(2022, 12, 9, 18, 0, 0)).seconds /3600) * (order_type.sum_per_hour_12 if guests_count < 3 else order_type.sum_per_hour_36)
        return int(happy_price + evening_price)


def add15(interval: str):
    hour, minute = map(int, interval.split(":"))
    minute += 15
    if minute > 45:
        div, mod = divmod(minute, 60)
        minute = mod
        hour = (hour + div) % 24
    return f"{hour}:{minute if minute != 0 else '00'}"


def save_interval_start(tg_id: int, interval_start: str):
    with Session(engine) as session:
        statement = select(User).where(User.id == tg_id)
        user = session.exec(statement).first()

        statement = select(Order).where(Order.id == user.current_order_id)
        order = session.exec(statement).first()
 
        order.start_time = interval_start

        session.commit()


def save_interval_end(tg_id: int, interval_end: str, price: int):
    with Session(engine) as session:
        statement = select(User).where(User.id == tg_id)
        user = session.exec(statement).first()

        statement = select(Order).where(Order.id == user.current_order_id)
        order = session.exec(statement).first()
  
        order.end_time = add15(interval_end)
        order.price = price

        session.commit()


def save_interval(tg_id: int, interval: str, price: int):

    with Session(engine) as session:
        statement = select(User).where(User.id == tg_id)
        user = session.exec(statement).first()

        statement = select(Order).where(Order.id == user.current_order_id)
        order = session.exec(statement).first()

        start, end = interval.split('-')
        order.start_time = start
        order.end_time = add15(end)
        order.price = price

        session.commit()


def save_order(tg_id: int) -> Tuple[str, int, str, Tuple[str, str, str]]:

    with Session(engine) as session:
        statement = select(User).where(User.id == tg_id)
        user = session.exec(statement).first()

        statement = select(Order).where(Order.id == user.current_order_id)
        order = session.exec(statement).first()

        order.all_steps_gone = True
        user.current_order_id = None

        info = session.exec(select(Info)).first()

        card_info = (info.card_number, info.card_bank, info.card_name)



        session.commit()

        return text_data(order), order.price, order.id, order.removing_at, card_info


def approve_order(order_id: int):
    with Session(engine) as session:
        statement = select(Order).where(Order.id == order_id)
        result = session.exec(statement).first()

        result.is_payed = True

        session.commit()


def get_all_igloos() -> List[Igloo]:
    with Session(engine) as session:
        return session.exec(select(Igloo)).all()


def get_current_order_and_its_type(tg_id: int) -> Tuple[Optional[Order], Optional[OrderType]]:
    with Session(engine) as session:
        user = session.exec(select(User).where(User.id == tg_id)).first()

        order = None
        order_type = None

        try:
            order = session.exec(select(Order).where(Order.id == user.current_order_id)).first()
        except:
            ...
        try:
            order_type = session.exec(select(OrderType).where(OrderType.id == order.order_type_id)).first()
        except:
            ...

        return order, order_type 


def get_order_date(user_id: int) -> str:
    with Session(engine) as session:
        user = session.exec(select(User).where(User.id == user_id)).first()
        order = session.exec(select(Order).where(Order.id == user.current_order_id)).first()

        return order.date


def text_data(order: int) -> str:
    with Session(engine) as session: 
        igloo = session.exec(select(Igloo).where(Igloo.id == order.igloo_id)).first()

        plan = session.exec(select(OrderType).where(OrderType.id == order.order_type_id)).first()

        guests_count = "" if not order.guests_count else f", кол-во гостей: до {order.guests_count}"

        return f"Иглу: {igloo.name}, план: {plan.name}, дата: {order.date}{guests_count}, часы: {order.start_time}-{order.end_time}, общая сумма: {locale.currency(order.price, grouping=True)}"


def get_all_order_types() -> List[OrderType]:
    with Session(engine) as session:
        return session.exec(select(OrderType)).all()


def make_odred_need_phone(order_id: int, phone: str=None):
    with Session(engine) as session:
        statement = select(Order).where(Order.id == order_id)
        order = session.exec(statement).first()

        order.needs_call = True

        if phone:
            statement = select(User).where(User.id == order.user_id)
            user = session.exec(statement).first()
            
            user.phone = phone

        session.commit()