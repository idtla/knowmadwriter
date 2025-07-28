import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "telegram_bot")))
import asyncio
from types import SimpleNamespace
import pytest
from telegram_bot.database import connection as db


class DummyBot:
    def __init__(self):
        self.sent_messages = []
        self.sent_photos = []

    async def send_message(self, chat_id, text, **kwargs):
        self.sent_messages.append((chat_id, text))

    async def send_photo(self, chat_id, photo=None, **kwargs):
        self.sent_photos.append((chat_id, photo))

    async def edit_message_text(self, chat_id, message_id=None, text=None, **kwargs):
        self.sent_messages.append((chat_id, text))


@pytest.fixture
def dummy_user():
    return SimpleNamespace(id=123, first_name="Tester", mention_html=lambda: "Tester")


@pytest.fixture
def dummy_chat():
    return SimpleNamespace(id=456)



@pytest.fixture
def dummy_context():
    return SimpleNamespace(bot=DummyBot(), user_data={}, chat_data={})


@pytest.fixture
def text_update(dummy_user, dummy_chat):
    async def _no_op(*a, **k):
        pass
    message = SimpleNamespace(message_id=1, chat=dummy_chat, text="hola", reply_html=_no_op, reply_text=_no_op, from_user=dummy_user)
    return SimpleNamespace(update_id=1, message=message, effective_user=dummy_user, effective_chat=dummy_chat)


@pytest.fixture
def callback_update(dummy_user, dummy_chat):
    async def _no_op(*a, **k):
        pass
    callback = SimpleNamespace(id='1', data='test', message=SimpleNamespace(message_id=1, chat=dummy_chat), answer=_no_op, edit_message_text=_no_op)
    return SimpleNamespace(update_id=2, callback_query=callback, effective_user=dummy_user, effective_chat=dummy_chat)


@pytest.fixture(autouse=True)
def temp_db(monkeypatch, tmp_path):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    db.connection = None
    db.cursor = None
    db.setup_database()
    yield
    db.close_connection()
