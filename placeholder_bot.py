import re

PLACEHOLDER_PATTERN = re.compile(r"\{\{(.*?)\}\}")

def detect_placeholders(template: str) -> list:
    """Devuelve una lista de placeholders encontrados en la plantilla."""
    return PLACEHOLDER_PATTERN.findall(template)

def fill_template(template: str, data: dict) -> str:
    """Rellena la plantilla usando los datos proporcionados.

    Lanzará un ValueError si falta algún placeholder en los datos.
    """
    placeholders = detect_placeholders(template)
    missing = [ph for ph in placeholders if ph not in data]
    if missing:
        raise ValueError(f"Faltan datos para: {', '.join(missing)}")

    def replacer(match):
        key = match.group(1)
        return str(data[key])

    return PLACEHOLDER_PATTERN.sub(replacer, template)
