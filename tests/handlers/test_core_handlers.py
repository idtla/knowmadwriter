import pytest
from telegram_bot.core import handlers
from telegram_bot.core.states import state_manager, State


@pytest.mark.asyncio
async def test_start_command_unregistered(text_update, dummy_context):
    await handlers.start_command(text_update, dummy_context)
    assert dummy_context.bot.sent_photo or dummy_context.bot.sent_messages


@pytest.mark.asyncio
async def test_help_command(text_update, dummy_context):
    await handlers.help_command(text_update, dummy_context)
    assert dummy_context.bot.sent_messages
