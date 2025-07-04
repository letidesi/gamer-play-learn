import unicodedata
import requests

def validate_word(word: str) -> bool | None:
    try:
        url = f"https://api.conceptnet.io/c/pt/{word.lower()}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return bool(data)
        elif response.status_code == 404:
            return False
        else:
            return None
    except Exception:
        return None
