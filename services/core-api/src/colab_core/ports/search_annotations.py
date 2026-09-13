"""Grounded concept proposals; model text is never accepted as a new fact."""
from __future__ import annotations


def _strings(value):
    if isinstance(value,str):yield value
    elif isinstance(value,list):
        for child in value:yield from _strings(child)
    elif isinstance(value,dict):
        for child in value.values():yield from _strings(child)


def validate_selections(source, proofs, proposal):
    if not isinstance(proposal,dict) or set(proposal)!={'selections'}:
        raise ValueError('invalid proposal shape')
    selected=proposal['selections']
    if not isinstance(selected,list) or len(selected)>6:
        raise ValueError('invalid proposal bound')
    candidates={p['node']['concept_id']:p for p in proofs}
    facts={f['predicate']:f for f in source['facts']}
    result=[];seen=set()
    for choice in selected:
        if not isinstance(choice,dict) or set(choice)!={'concept_id','predicate','quote'}:
            raise ValueError('invalid concept selection')
        if any(not isinstance(v,str) or not v.strip() for v in choice.values()) or len(choice['quote'])>500:
            raise ValueError('invalid selection text')
        cid=choice['concept_id'];predicate=choice['predicate'];quote=choice['quote']
        if cid not in candidates or predicate not in facts or cid in seen:
            raise ValueError('selection was not read or is duplicated')
        seen.add(cid);proof=candidates[cid];fact=facts[predicate]
        aliases={proof['node']['label']}
        same={e['dst'] if e['src']==cid else e['src'] for e in proof['edges']
              if e['relation']=='같은 말이다' and cid in (e['src'],e['dst'])}
        aliases.update(n['label'] for n in proof['neighbors'] if n['concept_id'] in same)
        if not any(quote in v for v in _strings(fact['value'])) or not any(a.casefold() in quote.casefold() for a in aliases):
            raise ValueError('selection has no literal source grounding')
        result.append({'concept_id':cid,'label':proof['node']['label'],'quote':quote,
                       'source_locator':fact['source_locator'],'terms':sorted(a.casefold() for a in aliases)})
    return result
