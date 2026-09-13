"""Generate shared ontology wire constants from the frozen core-ai seam."""
import sys
from pathlib import Path
import yaml

root=Path(__file__).resolve().parents[2]
seam=yaml.safe_load((root/'contracts/seams/core-ai.yaml').read_text())
schema=seam['components']['schemas']['OntologyManifest']['properties']
def operation_path(method, operation_id):
    return next(path for path,ops in seam['paths'].items()
                if ops.get(method,{}).get('operationId') == operation_id)

values={'LOOKUP_PATH':operation_path('post', 'lookupOntologyConcepts'),
        'PROPOSAL_PATH':operation_path('post', 'proposeSearchConcepts'),
        'MAX_CONCEPTS':seam['components']['schemas']['OntologyLookup']['properties']['concepts']['maxItems'],
        'MANIFEST_PATH':operation_path('get', 'getOntologyManifest'),'PROTOCOL':schema['protocol']['const'],
        'MAX_ENTRIES':schema['entries']['maxProperties'],
        'MAX_KEY_LENGTH':schema['entries']['propertyNames']['maxLength'],
        'KEY_PATTERN':schema['entries']['propertyNames']['pattern'],
        'DIGEST_PATTERN':schema['version']['pattern']}
Path(sys.argv[1]).write_text('"""Auto-generated from contracts/seams/core-ai.yaml; do not edit."""\n'+
    ''.join(f'{key} = {value!r}\n' for key,value in values.items()))
