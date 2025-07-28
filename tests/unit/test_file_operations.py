import os
from telegram_bot.utils.file_operations import write_json_file, read_json_file, ensure_dir_exists, file_exists, backup_file


def test_json_read_write(tmp_path):
    data = {'a': 1}
    file = tmp_path / 'test.json'
    write_json_file(file, data)
    assert file_exists(file)
    loaded = read_json_file(file)
    assert loaded == data


def test_ensure_dir_exists(tmp_path):
    new_dir = tmp_path / 'newdir'
    ensure_dir_exists(new_dir)
    assert os.path.isdir(new_dir)


def test_backup_file(tmp_path):
    f = tmp_path / 'a.txt'
    f.write_text('x')
    backup = backup_file(f, tmp_path)
    assert backup.exists()
