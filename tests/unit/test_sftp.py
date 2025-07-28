import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram_bot.modules.sftp import handlers as sftp_handlers
from telegram_bot.models.user import User
from telegram_bot.models.site import Site


@pytest.mark.asyncio
async def test_upload_file_to_sftp(monkeypatch):
    user = await User.create({'telegram_id': 'u3', 'name': 'Sftp', 'email': 's@e.com', 'status': 'active'})
    site = await Site.create({'user_id': user.id, 'name': 'S', 'domain': 'd.com', 'sftp_config': {'host':'h','port':22,'username':'u','password':'p','remote_dir':'/'}})
    # patch paramiko
    ssh = MagicMock()
    sftp = MagicMock()
    ssh.open_sftp.return_value = sftp
    monkeypatch.setattr(sftp_handlers.paramiko, 'SSHClient', MagicMock(return_value=ssh))
    result = await sftp_handlers.upload_file_to_sftp('u3', None, '/file.txt', content='data')
    assert result
    ssh.connect.assert_called()
    sftp.putfo.assert_called()
