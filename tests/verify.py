import importlib.util,json
from pathlib import Path
R=Path(__file__).parent
s=importlib.util.spec_from_file_location('entry',R.parent/'scripts/wechat_public_article_extract.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
cases=json.loads((R/'fixtures.json').read_text())
results=[]
def fake(p):
 d=json.loads(p.split('DATA:\n',1)[1]);return json.dumps({'node_ids':[d['candidates'][0]['id']] if d['candidates'] else [],'diagnosis':'fixture','next_action':'read_media'})
for c in cases:
 r=m.extract_page(c['html'],c['status'],runner=fake)
 norm=lambda v:''.join(v.split())
 if c['kind']=='blocked':good=not r['ok'] and r['content_status']=='blocked'
 elif c['kind'] in ('image','voice','video'):good=not r['ok'] and r['content_status'] in ('media_pending','unknown_structure')
 elif c['expected']:good=norm(c['expected']) in norm(r['text']) and 'NOT_BODY_' not in r['text']
 else:good=r.get('field')!='dom' or '真实文章正文' in r['text']
 results.append({'name':c['name'],'pass':good,'status':r['content_status'],'model':r['model_fallback']})
# Failure must remain visible, not erase extracted text or fabricate media.
def fail(p):raise TimeoutError()
r=m.extract_page('<div id="js_content">说明<video src="https://example.invalid/a.mp4"></video></div>',runner=fail)
assert r['text_ok'] and not r['ok'] and r['model_fallback']['status']=='failed'
# Blocked pages must never invoke a model.
r=m.extract_page('<h1>该文章为付费内容</h1>',runner=lambda p:(_ for _ in ()).throw(AssertionError()))
assert r['content_status']=='blocked' and not r['model_fallback']['triggered']

print(json.dumps([{'name':r['name'],'pass':r['pass'],'status':r['status']} for r in results],ensure_ascii=False,indent=2))
print('passed',sum(r['pass'] for r in results),'of',len(results))
assert all(r['pass'] for r in results)
