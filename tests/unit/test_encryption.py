from telegram_bot.utils.encryption import encrypt_data, decrypt_data


def test_encrypt_decrypt():
    text = 'secret'
    enc = encrypt_data(text)
    assert enc != text
    dec = decrypt_data(enc)
    assert dec == text
