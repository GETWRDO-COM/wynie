import hashlib
import json
from typing import Dict, List
from datetime import datetime


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def hash_row(row: Dict) -> str:
    # stable json with sorted keys, without volatile fields
    clean = {k: row[k] for k in sorted(row.keys())}
    return sha256_text(json.dumps(clean, separators=(',', ':'), ensure_ascii=False))


def artifact_hash_from_files(file_hashes: List[str]) -> str:
    concat = '|'.join(sorted(file_hashes))
    return sha256_text(concat)


def parse_date_str(val: str) -> str:
    # normalizes YYYY-MM-DD
    try:
        return datetime.strptime(val, '%Y-%m-%d').date().isoformat()
    except Exception:
        try:
            return datetime.fromisoformat(val).date().isoformat()
        except Exception:
            return val