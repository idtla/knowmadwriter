import pytest
from telegram_bot.modules.content import handlers as content_handlers
from telegram_bot.core.states import state_manager, State


@pytest.mark.asyncio
async def test_newpost_command(text_update, dummy_context):
    await content_handlers.newpost_command(text_update, dummy_context)
    assert state_manager.get_state(123) == State.CREATING_CONTENT
    assert dummy_context.bot.sent_messages
