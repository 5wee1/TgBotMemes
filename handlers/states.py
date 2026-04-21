from aiogram.fsm.state import State, StatesGroup


class MemeGen(StatesGroup):
    waiting_style = State()
    waiting_new_idea = State()
    waiting_broadcast = State()
