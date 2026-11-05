import json, math, re
from collections import Counter
from pathlib import Path

STOP={'và','của','là','có','cho','các','được','trong','về','theo','tại','này','những','một','khi','đối','với','đất','luật','quyền','sử','dụng'}
def tokens(s): return [w for w in re.findall(r'[^\W_]+',str(s).lower(),re.UNICODE) if w not in STOP and len(w)>1]
def load(path):
 data=json.loads(Path(path).read_text(encoding='utf-8'));nodes=data['nodes'];byid={n['id']:n for n in nodes};docs=[]
 for n in nodes:
  if n.get('type') not in ('LegalArticle','LegalClause','LegalPoint'):continue
  txt=n.get('text') or n.get('body_corrected') or n.get('body_raw') or ''
  if txt.strip():docs.append({'node':n,'text':txt,'tf':Counter(tokens(txt))})
 df=Counter();[df.update(d['tf'].keys()) for d in docs]
 return docs,df,len(docs),byid

def search(q,index,k=6):
 docs,df,N,byid=index;ts=tokens(q);counts=Counter(ts)
 article=re.search(r'điều\s*(\d{1,3})',q,re.I);clause=re.search(r'khoản\s*(\d+)',q,re.I);point=re.search(r'điểm\s*([a-zđ])\b',q,re.I)
 out=[]
 for d in docs:
  n=d['node'];score=0.0;size=sum(d['tf'].values())
  for t,c in counts.items():
   f=d['tf'][t]
   if f:score+=math.log(1+(N-df[t]+.5)/(df[t]+.5))*f*2.2/(f+1.2*(.25+.75*size/120))*min(c,2)
  if article:
   if n.get('article_number')!=int(article.group(1)):continue
   score+=15
  if clause:
   if n.get('type')=='LegalArticle' or n.get('clause_number')!=int(clause.group(1)):continue
   score+=10
  if point:
   if n.get('type')!='LegalPoint' or n.get('point_letter')!=point.group(1).lower():continue
   score+=8
  if score>0:out.append((score,d))
 out.sort(key=lambda x:x[0],reverse=True)
 # Avoid presenting entire articles when a relevant clause/point is available.
 if not article and not clause and not point:
  out.sort(key=lambda x:(x[0]+(2 if x[1]['node']['type']!='LegalArticle' else 0)),reverse=True)
 return [{'score':round(s,3),'node':d['node'],'text':d['text']} for s,d in out[:k]]

def citation(n):
 s=f"Điều {n['article_number']}"
 if n.get('clause_number'):s+=f", Khoản {n['clause_number']}"
 if n.get('point_letter'):s+=f", Điểm {n['point_letter']}"
 return s+' — Luật Đất đai 2013'
