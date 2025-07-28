import pytest
from telegram_bot.utils import html_processor as hp


def test_validate_html():
    valid, _ = hp.validate_html('<html><body><p>ok</p></body></html>')
    assert valid
    valid2, _ = hp.validate_html('<html><body>')
    assert isinstance(valid2, bool)


def test_extract_images_from_html():
    html = '<html><body><img src="images/pic.jpg" alt="x"><img src="http://test/remote.png"></body></html>'
    images = hp.extract_images_from_html(html)
    assert images == [{'src': 'images/pic.jpg', 'filename': 'pic.jpg', 'alt': 'x'}]


def test_replace_placeholders():
    result = hp.replace_placeholders('Hello {{NAME}}', {'NAME': 'World'})
    assert result == 'Hello World'


def test_find_placeholders_in_template():
    template = '{{TITLE}} {{UNKNOWN}}'
    info = hp.find_placeholders_in_template(template)
    assert '{{TITLE}}' in info['required']
    assert '{{UNKNOWN}}' in info['unknown']


def test_estimate_reading_time():
    html = '<p>' + ('word ' * 400) + '</p>'
    minutes = hp.estimate_reading_time(html)
    assert minutes >= 2


def test_validate_placeholder_value():
    assert hp.validate_placeholder_value('numero', '10')
    assert not hp.validate_placeholder_value('numero', 'x')
    assert hp.validate_placeholder_value('url', 'http://test')
    assert not hp.validate_placeholder_value('url', 'ftp://x')
    assert hp.validate_placeholder_value('desplegable', 'op1', 'op1,op2')
    assert not hp.validate_placeholder_value('desplegable', 'op3', 'op1,op2')
