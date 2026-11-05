import argparse, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_STORE=Path('data/documents/processed/structured_legal_document_store_v3.json')
DEFAULT_KG=Path('visualization/global_legal_kg_svg_extracted.json')
BASE='vn_law_2013_45_2013_qh13'

def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--store',type=Path,default=DEFAULT_STORE);ap.add_argument('--kg',type=Path,default=DEFAULT_KG);ap.add_argument('--out',type=Path,default=Path('data/kg/legal_kg_matched.json'));args=ap.parse_args()
 if not args.store.exists(): raise SystemExit(f'Khong tim thay store: {args.store}')
 store=read(args.store); articles=store.get('articles',[])
 if not isinstance(articles,list): raise SystemExit('Store phai co articles list')
 original=read(args.kg) if args.kg.exists() else {'nodes':[],'edges':[]}
 nodes={str(n['id']):dict(n) for n in original.get('nodes',[]) if isinstance(n,dict) and n.get('id')}
 edges=list(original.get('edges',[])); seen={(e.get('source'),e.get('target'),e.get('relation')) for e in edges}
 def edge(s,t,r):
  k=(s,t,r)
  if k not in seen: edges.append({'source':s,'target':t,'relation':r,'provenance':'structured_store'});seen.add(k)
 report={'articles':len(articles),'clauses':0,'points':0,'matched_articles':0,'matched_clauses':0,'new_articles':0,'new_clauses':0,'new_points':0,'article_numbers':[],'warnings':[],'kg_source':str(args.kg) if args.kg.exists() else None}
 law=BASE
 if law not in nodes: nodes[law]={'id':law,'name':'Luật Đất đai 2013','type':'LegalDocument','provenance':'structured_store'}
 for a in articles:
  try: num=int(a['article_number'])
  except (ValueError,KeyError,TypeError): report['warnings'].append('Article number khong hop le');continue
  aid=f'{BASE}_article_{num}'; existed=aid in nodes
  report['matched_articles' if existed else 'new_articles']+=1
  node=nodes.setdefault(aid,{'id':aid,'name':f'Điều {num}'})
  node.update({'type':'LegalArticle','article_number':num,'text_raw':a.get('text_raw',''),'body_raw':a.get('body_raw',''),'body_corrected':a.get('body_corrected') or a.get('body_raw',''),'heading':a.get('heading_raw') or a.get('heading_text_ocr') or '', 'source_pdf':(a.get('source') or {}).get('file'),'source_location':a.get('source',{}),'verification_status':a.get('verification_status','unknown'),'provenance_text':'structured_store'})
  edge(law,aid,'HAS_ARTICLE')
  report['article_numbers'].append(num)
  for c in a.get('clauses',[]):
   n=str(c.get('number','')).strip()
   if not n.isdigit(): report['warnings'].append(f'Dieu {num}: clause {n} khong hop le');continue
   cid=f'{aid}_clause_{n}'; existed=cid in nodes
   report['matched_clauses' if existed else 'new_clauses']+=1;report['clauses']+=1
   cn=nodes.setdefault(cid,{'id':cid,'name':f'Khoản {n}'})
   cn.update({'type':'LegalClause','article_number':num,'clause_number':int(n),'text':c.get('text',''),'start_line':c.get('start_line'),'verification_status':a.get('verification_status','unknown'),'provenance_text':'structured_store'})
   edge(aid,cid,'HAS_CLAUSE')
   for p in c.get('points',[]):
    letter=str(p.get('letter','')).strip().lower()
    if not re.fullmatch(r'[a-zđ]',letter): report['warnings'].append(f'Dieu {num} khoan {n}: point {letter}');continue
    pid=f'{cid}_point_{letter}'
    if pid not in nodes: report['new_points']+=1
    pn=nodes.setdefault(pid,{'id':pid,'name':f'Điểm {letter}'})
    pn.update({'type':'LegalPoint','article_number':num,'clause_number':int(n),'point_letter':letter,'text':p.get('text',''),'start_line':p.get('start_line'),'verification_status':a.get('verification_status','unknown'),'provenance_text':'structured_store'})
    edge(cid,pid,'HAS_POINT');report['points']+=1
 # Preserve SVG-derived UNKNOWN edges as UNKNOWN; do not invent semantics.
 output={'metadata':{'name':'Matched legal KG - demo','document':'Luật Đất đai 2013 (historical)','warning':'OCR and parser issues remain; SVG UNKNOWN relations are unverified','source_store':str(args.store),'source_kg':str(args.kg) if args.kg.exists() else None},'nodes':list(nodes.values()),'edges':edges,'matching_report':report}
 write(args.out,output);write(args.out.with_name('kg_matching_report.json'),report)
 print('MATCHING COMPLETE');print(json.dumps({k:v for k,v in report.items() if k not in ('article_numbers','warnings')},ensure_ascii=False,indent=2));print('Output:',args.out)
if __name__=='__main__': main()
