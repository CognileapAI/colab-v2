"""온톨로지 회차 5단계 — Ted 판정 페이지 생성기.

에이전트가 쓴 decisions.json 을 읽어, 결정마다 상황·선택지·권고와 「결정 문장 만들기」가 있는
한 파일짜리 HTML 을 만든다. 외부 글꼴·CDN·스크립트 없음(로컬 파일로 열어도 되고 아티팩트로 올려도 된다).

  python3 page.py <decisions.json> --out <decision-page.html>

decisions.json 형식(colab-ontology-round-decisions/1):
  {"schema": "...", "title": "온톨로지 3회차 판정", "subtitle": "…", "scoreboard": "답 가능 8 · 부분 3 …",
   "intro": "문단(평문)", "decisions": [
     {"id": "d1", "title": "…", "context": ["문단", …], "table": [["머리", …], ["값", …]],
      "options": [{"key": "가", "label": "…", "detail": "…", "recommended": true}],
      "input": {"label": "…", "placeholder": "…"}}]}
문자열은 평문이다(HTML 을 넣지 않는다). 종료코드 0 · 1(형식 불일치).
"""
from __future__ import annotations

import argparse
import html
import json
import pathlib
import sys

TEMPLATE = """<title>__TITLE__</title>
<style>
:root{--paper:#f4f6f5;--ink:#1c2429;--ink2:#46525b;--mute:#7a858d;--rule:#d6dcda;--card:#fff;
--acc:#1d5f8a;--accbg:#e3eef6;--code:#eaeeed}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){color-scheme:dark;--paper:#131a1e;--ink:#e4e9ec;
--ink2:#b3bec5;--mute:#8a969e;--rule:#29343a;--card:#1b2429;--acc:#7fb7de;--accbg:#16303f;--code:#232d33}}
:root[data-theme="dark"]{color-scheme:dark;--paper:#131a1e;--ink:#e4e9ec;--ink2:#b3bec5;--mute:#8a969e;--rule:#29343a;
--card:#1b2429;--acc:#7fb7de;--accbg:#16303f;--code:#232d33}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:Pretendard,'Noto Sans KR',-apple-system,'Segoe UI',sans-serif;
font-size:15.5px;line-height:1.7;padding-inline:16px;padding-block:28px 72px}
.wrap{max-width:960px;margin:0 auto;display:flex;flex-direction:column;gap:18px}
h1,h2{text-wrap:balance;margin:0}h1{font-size:1.65rem;line-height:1.25}h2{font-size:1.08rem}
.sub{color:var(--mute);font-size:.86rem}.lede{color:var(--ink2);max-width:66ch;margin:6px 0 0}
.board{background:var(--accbg);border-radius:10px;padding:10px 16px;font-variant-numeric:tabular-nums}
section{background:var(--card);border:1px solid var(--rule);border-radius:10px;padding:16px 18px}
p{margin:6px 0}.tbl{overflow-x:auto;margin:8px 0}
table{border-collapse:collapse;width:100%;min-width:480px;font-size:.88rem}
th,td{border:1px solid var(--rule);padding:6px 9px;text-align:left;vertical-align:top}th{background:var(--code)}
.opts{display:flex;flex-direction:column;gap:8px;margin-top:10px}
.opt{display:grid;grid-template-columns:20px 1fr;gap:10px;border:1px solid var(--rule);border-radius:8px;padding:9px 12px;cursor:pointer}
.opt:has(input:checked){border-color:var(--acc);background:var(--accbg)}.opt input{margin-top:5px;accent-color:var(--acc)}
.opt b{display:block}.opt small{color:var(--ink2)}.rec{font-size:.72rem;color:var(--acc);font-weight:700;margin-left:6px}
input[type=text],textarea{font:inherit;font-size:.92rem;color:var(--ink);background:var(--code);border:1px solid var(--rule);
border-radius:8px;padding:8px 10px;width:100%}textarea{min-height:200px;resize:vertical}
label.f{display:block;margin-top:10px;font-size:.88rem;color:var(--ink2)}
.row{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-top:10px}
button{font:inherit;font-weight:600;background:var(--acc);color:#fff;border:0;border-radius:8px;padding:8px 14px;cursor:pointer}
button.ghost{background:transparent;color:var(--acc);border:1px solid var(--acc)}
button:focus-visible,input:focus-visible,textarea:focus-visible{outline:2px solid var(--acc);outline-offset:2px}
.msg{color:var(--ink2);font-size:.88rem}
</style>
<div class="wrap" id="app"></div>
<script type="application/json" id="data">__DATA__</script>
<script>
(function(){
var D=JSON.parse(document.getElementById('data').textContent),app=document.getElementById('app');
var MARK=['㈎','㈏','㈐','㈑','㈒','㈓'];
function el(t,a,c){var e=document.createElement(t);if(a)for(var k in a){if(k==='text')e.textContent=a[k];else e.setAttribute(k,a[k]);}
 (c||[]).forEach(function(x){if(x)e.appendChild(typeof x==='string'?document.createTextNode(x):x);});return e;}
var head=el('header',null,[el('h1',{text:D.title}),D.subtitle?el('p',{class:'sub',text:D.subtitle}):null,D.intro?el('p',{class:'lede',text:D.intro}):null]);
app.appendChild(head);
if(D.scoreboard)app.appendChild(el('div',{class:'board',text:D.scoreboard}));
var inputs={};
D.decisions.forEach(function(d,i){
 var s=el('section',{id:d.id},[el('h2',{text:(i+1)+'. '+d.title})]);
 (d.context||[]).forEach(function(p){s.appendChild(el('p',{text:p}));});
 if(d.table&&d.table.length){var t=el('table');d.table.forEach(function(r,ri){var tr=el('tr');r.forEach(function(c){tr.appendChild(el(ri?'td':'th',{text:String(c)}));});t.appendChild(tr);});
  s.appendChild(el('div',{class:'tbl'},[t]));}
 var box=el('div',{class:'opts'});
 d.options.forEach(function(o,oi){var inp=el('input',{type:'radio',name:d.id,value:String(oi),id:d.id+'-'+oi});if(o.recommended)inp.checked=true;
  var b=el('b',null,[MARK[oi]+' '+o.label,o.recommended?el('span',{class:'rec',text:'권고'}):null]);
  box.appendChild(el('label',{class:'opt',for:d.id+'-'+oi},[inp,el('span',null,[b,o.detail?el('small',{text:o.detail}):null])]));});
 if(!d.options.some(function(o){return o.recommended;})&&d.options.length)box.querySelector('input').checked=true;
 s.appendChild(box);
 if(d.input){var id=d.id+'-text';s.appendChild(el('label',{class:'f',for:id,text:d.input.label}));
  var ti=el('input',{type:'text',id:id,placeholder:d.input.placeholder||''});s.appendChild(ti);inputs[d.id]=ti;}
 app.appendChild(s);});
var out=el('textarea',{id:'out','aria-label':'결정 문장',readonly:'readonly'}),msg=el('span',{class:'msg'});
var copy=el('button',{type:'button',text:'복사'}),reset=el('button',{type:'button',class:'ghost',text:'권고로 되돌리기'});
app.appendChild(el('section',null,[el('h2',{text:'결정 문장'}),el('p',{class:'msg',text:'고른 대로 문장이 만들어집니다. 복사해 대화창에 붙여 주세요.'}),out,el('div',{class:'row'},[copy,reset,msg])]));
function render(){var all=true,lines=D.decisions.map(function(d,i){var c=document.querySelector('input[name="'+d.id+'"]:checked'),oi=c?+c.value:0,o=d.options[oi];
 if(!o.recommended)all=false;var t=(i+1)+'. '+MARK[oi]+' '+o.label;var x=inputs[d.id];if(x&&x.value.trim())t+=' — '+x.value.trim();return t;});
 out.value=(all?'다 권고대로\\n\\n':'')+D.title+':\\n'+lines.join('\\n');}
app.addEventListener('change',render);app.addEventListener('input',render);
reset.addEventListener('click',function(){D.decisions.forEach(function(d){var r=d.options.findIndex(function(o){return o.recommended;});
 var e=document.getElementById(d.id+'-'+(r<0?0:r));if(e)e.checked=true;});render();msg.textContent='권고값으로 되돌렸습니다.';});
copy.addEventListener('click',function(){if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(out.value).then(function(){msg.textContent='복사했습니다.';},function(){out.select();msg.textContent='선택했습니다. Ctrl+C로 복사하세요.';});}else{out.select();msg.textContent='선택했습니다. Ctrl+C로 복사하세요.';}});
render();})();
</script>
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("decisions", type=pathlib.Path)
    ap.add_argument("--out", type=pathlib.Path, required=True)
    a = ap.parse_args(argv)
    d = json.loads(a.decisions.read_text(encoding="utf-8"))
    if d.get("schema") != "colab-ontology-round-decisions/1" or not d.get("decisions"):
        print("판정 실패: decisions.json 형식이 아니다(schema·decisions)", file=sys.stderr)
        return 1
    for x in d["decisions"]:
        if not x.get("id") or not x.get("title") or not x.get("options"):
            print(f"판정 실패: 결정 {x.get('id')} 에 id·title·options 가 필요하다", file=sys.stderr)
            return 1
    data = json.dumps(d, ensure_ascii=False).replace("</", "<\\/")
    a.out.write_text(TEMPLATE.replace("__TITLE__", html.escape(d.get("title", "온톨로지 회차 판정")))
                     .replace("__DATA__", data), encoding="utf-8")
    print(json.dumps({"out": str(a.out), "decisions": len(d["decisions"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
