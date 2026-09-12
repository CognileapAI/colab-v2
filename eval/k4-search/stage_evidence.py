"""Prepare reviewed reference annotations; stage API defaults to a read-only preflight."""
import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler


def facts_for_file(key, filename, condition, role):
    if filename.lower().endswith('.docx'): return {'roles':['documentation']}
    if filename.lower().endswith('.ipynb'): return {'roles':['analysis_code']}
    facts={}
    for source,target in [('region','region'),('cadence','cadence'),
                          ('direct_observation','directObservation'),('interpolated','interpolated')]:
        if condition.get(source) is not None: facts[target]=condition[source]
    if role:
        facts['roles']=[role['role']]
        if role.get('variable'): facts['variable']=role['variable']
        if role['role'] in ('model_input','auxiliary_input','validation','prediction'):
            facts['model']='U-Net'
    if key=='LD-VEG-LV2' and filename.startswith('Prediction_'):
        facts.update(roles=['prediction'],model='U-Net')
    if key=='LD-VEG-LV1': facts['nativeResolutionM']=2000
    date=re.search(r'(?<!\d)(20\d{6})(?!\d)|(?<!\d)(20\d{6})\d{4}',filename)
    if date:
        value=dt.datetime.strptime(date[1] or date[2],'%Y%m%d').date().isoformat()
        facts['period']={'start':value,'end':value}
    elif condition.get('coverage') and key in ('LD-VEG-LV1','LD-DRGH-LV1'):
        facts['period']=dict(zip(('start','end'),condition['coverage']))
    elif key=='LD-VEG-LV1-MODELIN' and filename.startswith('HLS_'):
        facts.update(period={'start':'2023-05-01','end':'2023-05-31'},cadence='monthly')
    return facts


def build_packet(root, reference_root):
    here=Path(__file__).resolve().parent
    reports=root/'dev-package/reports/stage3-ai-search-plan'
    snapshot=json.loads((reports/'dev-data-snapshot.json').read_text())
    provenance=json.loads((reports/'source-provenance-01.json').read_text())
    from reference_evidence import verify_sources
    if verify_sources(reference_root,provenance): raise ValueError('source document changed; review collection again')
    conditions=json.loads((here/'condition-evidence.json').read_text())['datasets']
    roles=json.loads((here/'file-role-evidence.json').read_text())['evidence']
    sources={Path(s['path']).name:s for s in provenance['sources']}
    result=[]
    for dataset in snapshot['datasets']:
        key=dataset['manifest_key']
        for file in dataset['files']:
            if file['kind']!='본체': continue
            role=next((r for r in roles if r['dataset_key']==key and r['file']==file['file_name']),None)
            facts=facts_for_file(key,file['file_name'],conditions.get(key,{}),role)
            if not facts: continue
            name=(file['file_name'] if file['file_name'] in sources else role['source_document'] if role else
                  '#processing_description_NDVI.docx' if 'VEG' in key else '#processing_description_Precipitation.docx')
            source=sources[name]
            if file['file_name'].endswith('.ipynb'):
                matches=[p for p in Path(reference_root).rglob('*.ipynb') if p.name==file['file_name']]
                if len(matches)!=1: raise ValueError('missing/ambiguous notebook source')
                raw=matches[0].read_bytes(); notebook=json.loads(raw)
                name=file['file_name']
                source={'sha256':hashlib.sha256(raw).hexdigest(),'paragraphs':[
                    {'text':''.join(cell.get('source',[]))} for cell in notebook['cells'] if cell['cell_type']=='code']}
            text='\n'.join(p['text'] for p in source['paragraphs'])
            if len(text)>20000: raise ValueError(f'source exceeds API text limit: {name}')
            result.append(dict(dataset_key=key,dataset_name=dataset['name'],file_name=file['file_name'],
                facts=facts,source={'label':name,'locator':'처리 단계·자료 설명 본문 (수집 문단 전체)','text':text},
                source_document_sha256=source['sha256']))
    if not result: raise ValueError('no evidence inputs')
    inputs=[here/'condition-evidence.json',here/'file-role-evidence.json',reports/'source-provenance-01.json',reports/'dev-data-snapshot.json',Path(__file__)]
    return dict(kind='reference evidence preparation; no target IDs or automatic review',items=result,
                hashes={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs})


def validate_base(url):
    parsed=urlsplit(url)
    if parsed.scheme!='http' or parsed.hostname not in ('127.0.0.1','localhost','::1') or parsed.username or parsed.password or parsed.path not in ('','/') or parsed.query or parsed.fragment:
        raise ValueError('only an explicit WSL loopback HTTP origin is accepted')
    return url.rstrip('/')


def resolve_targets(items, datasets, get_files):
    resolved=[]; cache={}
    for item in items:
        matches=[d for d in datasets if d['name']==item['dataset_name']]
        if len(matches)!=1: raise ValueError(f'missing/ambiguous dataset: {item["dataset_name"]}')
        dataset=matches[0]['datasetId']
        if dataset not in cache: cache[dataset]=get_files(dataset)
        files=[f for f in cache[dataset] if f['fileName']==item['file_name']]
        if len(files)!=1: raise ValueError(f'missing/ambiguous file: {item["file_name"]}')
        file=files[0]
        resolved.append(dict(dataset_id=dataset,file_id=file['fileId'],payload=dict(
            expectedRevision=(file['evidence'] or {}).get('revision',0),
            expectedFileRevision=file['fileRevision'],facts=item['facts'],source=item['source'],status='draft')))
    return resolved


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        return None


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',action='store_true')
    parser.add_argument('--reference-root',type=Path)
    parser.add_argument('--packet',type=Path)
    parser.add_argument('--base-url')
    parser.add_argument('--token-file',type=Path)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--reviewed',action='store_true',help='explicitly confirm the packet claims; otherwise save drafts')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists(): parser.error('output already exists')
    if args.build:
        if args.apply or args.reviewed: parser.error('build does not write to a service')
        if not args.reference_root: parser.error('build requires reference-root for current source verification')
        output=build_packet(Path(__file__).resolve().parents[2],args.reference_root)
    else:
        if not (args.packet and args.base_url and args.token_file): parser.error('packet, base-url and token-file are required')
        if args.reviewed and not args.apply: parser.error('reviewed requires explicit apply')
        base=validate_base(args.base_url); token=args.token_file.read_text().strip()
        if not token or '\n' in token or '\r' in token: parser.error('invalid token file')
        opener=build_opener(NoRedirect())
        def call(path,payload=None):
            request=Request(base+'/api/v1'+path,method='GET' if payload is None else 'PUT',
                headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'},
                data=None if payload is None else json.dumps(payload).encode())
            with opener.open(request,timeout=30) as response: return json.load(response)
        datasets=[]; cursor=None; seen=set()
        from urllib.parse import urlencode
        while True:
            page=call('/datasets?'+urlencode({'limit':100,**({'cursor':cursor} if cursor else {})}))
            datasets.extend(page['items']); cursor=page.get('nextCursor')
            if not cursor: break
            if cursor in seen: raise ValueError('repeating dataset cursor')
            seen.add(cursor)
        packet=json.loads(args.packet.read_text())
        resolved=resolve_targets(packet['items'],datasets,lambda id:call(f'/datasets/{id}/search-evidence')['items'])
        output={'mode':'apply' if args.apply else 'preflight','targets':len(resolved),'written':0,'status':'prepared'}
        if args.apply:
            try:
                for target in resolved:
                    if args.reviewed: target['payload']['status']='reviewed'
                    call(f'/datasets/{target["dataset_id"]}/files/{target["file_id"]}/search-evidence',target['payload'])
                    output['written']+=1
                output['status']='completed'
            except Exception:
                output['status']='failed; earlier writes retained; do not blindly retry'
                args.output.write_text(json.dumps(output,ensure_ascii=False,indent=2))
                raise
    with args.output.open('x') as stream: json.dump(output,stream,ensure_ascii=False,indent=2)
    print(json.dumps({k:v for k,v in output.items() if k not in ('items','hashes')},ensure_ascii=False))
    return 0


if __name__=='__main__': raise SystemExit(main())
