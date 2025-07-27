import pytest
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from placeholder_bot import detect_placeholders, fill_template


def test_detect_placeholders_simple():
    template = "Hola {{nombre}}, bienvenido a {{sitio}}"
    assert detect_placeholders(template) == ["nombre", "sitio"]


def test_fill_template_complete():
    template = "Hola {{nombre}}"
    data = {"nombre": "Carlos"}
    assert fill_template(template, data) == "Hola Carlos"


def test_fill_template_missing():
    template = "Hola {{nombre}} en {{sitio}}"
    data = {"nombre": "Ana"}
    with pytest.raises(ValueError):
        fill_template(template, data)
