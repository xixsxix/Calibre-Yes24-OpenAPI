from pathlib import Path

path = Path('yes24.py')
text = path.read_text(encoding='utf-8')

def one(old, new, label):
    global text
    n = text.count(old)
    if n != 1:
        raise SystemExit(f'{label}: expected 1 anchor, found {n}')
    text = text.replace(old, new, 1)

one('    version = (0, 5, 0)\n', '    version = (0, 5, 3)\n', 'version')
one('        "identifier:isbn",\n', '        "identifier:isbn",\n        "identifier:yes24",\n', 'identifier')
one(
    '        isbn = cls._clean_isbn13(item.get("isbn13"))\n        if isbn:\n            mi.set_identifier("isbn", isbn)\n\n        publisher = cls._clean_text(item.get("publisher"))\n',
    '        isbn = cls._clean_isbn13(item.get("isbn13"))\n        if isbn:\n            mi.set_identifier("isbn", isbn)\n\n        # Preserve the exact YES24 product identity so the separate\n        # Library Status plugin can match the user-selected edition.\n        item_id = str(item.get("itemId") or "").strip()\n        if item_id.isdigit():\n            mi.set_identifier("yes24", item_id)\n\n        publisher = cls._clean_text(item.get("publisher"))\n',
    'itemId bridge',
)
one(
    '        add(cls._core_title(title))\n        if not queries and authors:\n            add(authors[0])\n\n        return queries\n',
    '        add(cls._core_title(title))\n        if not queries and authors:\n            add(authors[0])\n\n        # Broaden discovery for ASCII letter/number spacing variants only.\n        for query in list(queries):\n            compact = query\n            previous = None\n            while compact != previous:\n                previous = compact\n                compact = re.sub(r"(?<=[A-Za-z])\\s+(?=\\d)", "", compact)\n                compact = re.sub(r"(?<=\\d)\\s+(?=[A-Za-z])", "", compact)\n            add(compact)\n\n        return queries\n',
    '0.5.2 search fallback',
)
one(
    '    def _title_sequence_conflict(cls, query_title, item):\n        query_number = cls._title_sequence_number(query_title)\n        if query_number is None:\n            return False\n\n        candidate_number = cls._title_sequence_number(item.get("title"))\n        return candidate_number != query_number\n',
    '    def _title_sequence_conflict(cls, query_title, item):\n        candidate_title = cls._clean_text((item or {}).get("title"))\n        query_key = cls._normalize_match_text(query_title)\n        candidate_key = cls._normalize_match_text(candidate_title)\n        if query_key and candidate_key and query_key == candidate_key:\n            return False\n\n        query_number = cls._title_sequence_number(query_title)\n        if query_number is None:\n            return False\n\n        candidate_number = cls._title_sequence_number(candidate_title)\n        return candidate_number != query_number\n',
    '0.5.3 sequence guard',
)
compile(text, 'yes24.py', 'exec')
path.write_text(text, encoding='utf-8')
print('0.5.3 source consolidation OK')
