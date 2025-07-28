import pytest
import asyncio
from telegram_bot.models.user import User
import types
from telegram_bot.modules.auth import handlers as auth_handlers
from telegram_bot.core.states import state_manager, State


@pytest.mark.asyncio
async def test_full_registration_flow(text_update, dummy_context):
    # start register
    await auth_handlers.register_command(text_update, dummy_context)
    assert state_manager.get_state(123) == State.REGISTERING
    # send auth code
    text_update.message.text = '12345678'
    await auth_handlers.process_auth_code(text_update, dummy_context)
    # send name
    text_update.message.text = 'Tester'
    await auth_handlers.process_name(text_update, dummy_context)
    # send email
    text_update.message.text = 'tester@example.com'
    await auth_handlers.process_email(text_update, dummy_context)
    # simulate callback confirm
    cb_update = types.SimpleNamespace(callback_query=types.SimpleNamespace(data='register:confirm', answer=asyncio.coroutine(lambda: None), message=types.SimpleNamespace(message_id=1, chat=text_update.effective_chat), edit_message_text=asyncio.coroutine(lambda *a, **k: None)), effective_user=text_update.effective_user, effective_chat=text_update.effective_chat)
    await auth_handlers.register_callback(cb_update, dummy_context)
    user = User.get_by_telegram_id("123")
    assert state_manager.get_state(123) == State.IDLE
