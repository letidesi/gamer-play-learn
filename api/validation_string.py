import re

import re

def validation_name(name):
    # Retira espaços antes e depois
    name = name.strip()
    if not name:
        return False  # vazio ou só espaços é inválido

    pattern = r"^[A-Za-zÀ-ÖØ-öø-ÿ \-]+$"
    return re.match(pattern, name) is not None
