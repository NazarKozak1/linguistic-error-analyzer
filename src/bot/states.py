from aiogram.fsm.state import State, StatesGroup

class OnboardingSteps(StatesGroup):
    """fsm states for user onboarding."""
    choose_language = State()