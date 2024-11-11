from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    waiting_for_sber_id = State()
    waiting_for_school21_nickname = State()
    waiting_for_team_name = State()
    waiting_for_role_level = State()
    waiting_for_activity_description = State()
    waiting_for_skip_description = State()
    waiting_for_final_confirmation = State()


class Search(StatesGroup):
    waiting_for_role = State()
    waiting_for_level = State()
    users_list = State()


class FixtureImportState(StatesGroup):
    waiting_for_file = State()


class Admin_state(StatesGroup):
    waiting_for_commands = State()


class Start_state(StatesGroup):
    wait_for_action = State()
