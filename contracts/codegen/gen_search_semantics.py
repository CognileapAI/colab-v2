"""Generate identical typed semantic vocabulary for core and ontology service."""
import hashlib
import json
from pathlib import Path
import sys

source = Path(__file__).resolve().parents[1] / 'search/semantics.json'
value = json.loads(source.read_text())
digest = hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
Path(sys.argv[1]).write_text('"""Generated from contracts/search/semantics.json; do not edit."""\n'
                           + f'SEMANTICS = {value!r}\nSEMANTIC_VERSION = {digest!r}\n')
