"""Use the dissertation's contents as the canonical heading catalogue."""
import re,html

def sentence_case(text):
 if text.isupper():
  text=text.lower()
  for name in ['Wikipedia','Michael Brown','Darren Wilson','Zipf']:
   text=re.sub(re.escape(name),name,text,flags=re.I)
 text=re.sub(r'Zipf’s Law','Zipf’s law',text)
 text=text.replace(': Speed',': speed').replace(': Accuracy',': accuracy')
 return text[:1].upper()+text[1:]

def join_heading_lines(lines):
 result=[]
 for l in lines:
  if result and re.fullmatch(r'\d+(?:\.\d+)*\s*',result[-1]['text']) and abs(l['y']-result[-1]['y'])<1 and l['text'].isupper():
   result[-1]={**result[-1],'text':result[-1]['text'].strip()+' '+l['text']}
  else:result.append(dict(l))
 return result

def catalogue(pages):
 entries={}
 for page in pages[3:5]:
  rows={}
  for l in page['lines']:
   if 60<l['y']<790:rows.setdefault(round(l['y'],1),[]).append(l)
  for row in rows.values():
   text=' '.join(l['text'].strip() for l in sorted(row,key=lambda l:l['x']))
   m=re.match(r'^(\d+(?:\.\d+)*)\s+(.+?)\s+\d+$',text)
   if m:entries[m[1]]=sentence_case(m[2])
 return entries

def render_heading(number,title):
 level=min(4,2+number.count('.'))
 return f'<h{level} id="section-{number}" class="section-heading"><span class="section-number">{number}</span> {html.escape(title)}</h{level}>'

def render_contents(entries):
 items=['<li><a href="#page-2">Abstract</a></li>','<li><a href="#page-3">Acknowledgements</a></li>','<li><a href="#page-6">List of figures</a></li>']
 for number,title in entries.items():items.append(f'<li class="toc-depth-{number.count(".")}"><a href="#section-{number}"><span>{number}</span> {html.escape(title)}</a></li>')
 return '<h2>Table of contents</h2><nav class="document-toc" aria-label="Table of contents"><ol>'+''.join(items)+'</ol></nav>'
