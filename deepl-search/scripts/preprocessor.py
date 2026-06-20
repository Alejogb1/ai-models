import re
import string
from typing import List, Optional


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r'\d+', '0', text)
    text = text.translate(str.maketrans('', '', string.punctuation))
    text = re.sub(r'\s+', ' ', text).strip()
    return text


SESSION_SEP = ' [SEP] '


def build_session(queries: List[str], sep: str = SESSION_SEP) -> str:
    cleaned = [normalize(q) for q in queries]
    return sep.join(cleaned)


try:
    from symspellpy import SymSpell, Verbosity

    _symspell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
    _dictionary_loaded = False

    def _ensure_dictionary():
        global _dictionary_loaded
        if not _dictionary_loaded:
            import os
            import pkg_resources
            dict_path = pkg_resources.resource_filename(
                'symspellpy', 'frequency_dictionary_en_82_765.txt'
            )
            if os.path.exists(dict_path):
                _symspell.load_dictionary(dict_path, term_index=0, count_index=1)
                _dictionary_loaded = True

    def spell_correct(text: str, max_edit_distance: int = 2) -> str:
        _ensure_dictionary()
        if not _dictionary_loaded:
            return text
        words = text.split()
        corrected = []
        for word in words:
            suggestions = _symspell.lookup(word, Verbosity.CLOSEST, max_edit_distance)
            corrected.append(suggestions[0].term if suggestions else word)
        return ' '.join(corrected)

except ImportError:
    def spell_correct(text: str, max_edit_distance: int = 2) -> str:
        return text


def preprocess(raw_queries: List[str]) -> str:
    normalized = [normalize(q) for q in raw_queries]
    corrected = [spell_correct(q) for q in normalized]
    return build_session(corrected)
