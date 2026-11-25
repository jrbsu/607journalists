"""Validate navigation, reference integrity, and data behind recreated charts."""
from html.parser import HTMLParser
from pathlib import Path
from collections import Counter
import json,xml.etree.ElementTree as ET
class Audit(HTMLParser):
 def __init__(self):super().__init__();self.ids=[];self.refs=[];self.anchors=0
 def handle_starttag(self,t,a):
  a=dict(a)
  if 'id' in a:self.ids.append(a['id'])
  if t=='a':
   assert self.anchors==0,'Nested anchor';self.anchors+=1
  for k in ['href','src']:
   if k in a:self.refs.append(a[k])
 def handle_endtag(self,t):
  if t=='a':self.anchors-=1
p=Path(__file__).parent/'dist';a=Audit();a.feed((p/'index.html').read_text());counts=Counter(a.ids)
assert not [k for k,v in counts.items() if v>1], 'Duplicate IDs'
for r in a.refs:
 if r.startswith('#'):assert r[1:] in counts,r
 elif not r.startswith(('http:','https:','mailto:')):assert (p/r.split('#')[0]).is_file(),r
assert sum(i.startswith('ref-') for i in a.ids)==165
assert sum(i.startswith('figure-') for i in a.ids)==20
assert sum(i.startswith('page-') for i in a.ids)==73
for svg in (p/'assets/figures').glob('*.svg'):ET.parse(svg)
data=json.loads((p/'assets/figures/chart-data.json').read_text())
assert abs(sum(data['19']['values'])-100)<.02
assert abs(sum(data['20']['values'])-100)<.02
assert abs(data['16']['values'][1]-95.87)<.01
assert abs(data['16']['values'][-1]-24.75)<.01
print(f'Validated 20 figures, 165 references, {sum(i.startswith("cite-") for i in a.ids)} citations, all internal links, local assets, SVG syntax, and chart data.')

# Source URLs must remain intact and clickable after PDF line reconstruction.
from references import References
import re
from urllib.parse import urlsplit
source_refs=References(json.loads((p.parent/'lines.json').read_text()))
class LinkAudit(HTMLParser):
 def __init__(self):super().__init__();self.depth=0;self.links=[];self.bare=[]
 def handle_starttag(self,tag,attrs):
  if tag=='a':
   self.depth+=1;self.links.append(dict(attrs).get('href',''))
 def handle_endtag(self,tag):
  if tag=='a':self.depth-=1
 def handle_data(self,text):
  if not self.depth and re.search(r'https?://',text):self.bare.append(text)
links=LinkAudit();links.feed((p/'index.html').read_text())
assert not links.bare,links.bare
for url in links.links:
 if url.startswith(('http://','https://')):
  assert not re.search(r'\s',url),url
  assert urlsplit(url).netloc,url
for entry in source_refs.entries:
 for url in re.findall(r'https?://[^\s]+',entry['text']):
  assert url.rstrip('.,;') in links.links,url
source_lines=json.loads((p.parent/'lines.json').read_text())
expected_users=[l['text'].strip() for page in source_lines[71:] for l in page['lines'] if 60<l['y']<790 and not l['text'].startswith(('607 Journalists','8.2 ')) and not (page['page']==74 and l['x']>390 and l['y']<115)]
from urllib.parse import unquote
actual_users=[unquote(url.split('/wiki/User:',1)[1]).replace('_',' ') for url in links.links if '/wiki/User:' in url]
assert actual_users and Counter(actual_users)==Counter(expected_users)
assert actual_users[:3]==['220 of Borg','331dot','4154aiden']
assert all(name not in actual_users for name in ['Key:','Administrators','Users with rollback','Subsequently-blocked users'])
print(f'Validated clickable source URLs, whitespace-free external links, and all {len(actual_users)} registered users.')

# Role symbols preserve the PDF's historical bold, underline, and italic key.
from user_roles import extract_roles,ROLES
roles=extract_roles(source_lines)
assert roles['Nihiltres']==['administrator']
assert roles['Niceguyedc']==['rollback']
assert roles['TranquilHope']==['rollback']
assert roles['Truthtellerfurgesonreality']==['blocked']
assert roles['Nerwen']==[]
class RoleAudit(HTMLParser):
 def __init__(self):super().__init__();self.user=None;self.markers={}
 def handle_starttag(self,tag,attrs):
  attrs=dict(attrs)
  if tag=='li':self.user=None
  if tag=='a' and '/wiki/User:' in attrs.get('href',''):
   self.user=unquote(attrs['href'].split('/wiki/User:')[1]).replace('_',' ');self.markers[self.user]=[]
  if tag=='sup' and attrs.get('class')=='user-role':
   assert self.user
   assert attrs['role']=='img' and attrs['aria-label']==attrs['title']
   self.markers[self.user].append(attrs['aria-label'])
role_audit=RoleAudit();role_audit.feed((p/'index.html').read_text())
labels={key:label for key,symbol,label in ROLES}
assert role_audit.markers=={name:[labels[key] for key in assigned] for name,assigned in roles.items()}
role_counts=Counter(role for assigned in roles.values() for role in assigned)
assert role_counts=={'administrator':30,'rollback':76,'blocked':7},role_counts
print('Validated all historical role markers: 30 administrators, 76 rollback users, 7 subsequently blocked users.')

class ParagraphAudit(HTMLParser):
 def __init__(self):super().__init__();self.current=None;self.paragraphs=[]
 def handle_starttag(self,tag,attrs):
  if tag=='p':self.current=''
 def handle_data(self,text):
  if self.current is not None:self.current+=text
 def handle_endtag(self,tag):
  if tag=='p' and self.current is not None:
   self.paragraphs.append(self.current);self.current=None
paragraphs=ParagraphAudit();paragraphs.feed((p/'index.html').read_text())
assert any('accurately reflects the content of these citations and there is no method' in text for text in paragraphs.paragraphs)
assert any('simply for consistency among articles' in text for text in paragraphs.paragraphs)
print('Validated continuous paragraphs across PDF page breaks and interrupted figure layouts.')

# Tables must preserve the PDF's cells rather than dropping numeric fragments.
class TableAudit(HTMLParser):
 def __init__(self):super().__init__();self.tables={};self.current=None;self.row=None;self.cell=None
 def handle_starttag(self,tag,attrs):
  attrs=dict(attrs)
  if tag=='table' and attrs.get('id','').startswith('table-'):
   self.current=[];self.tables[attrs['id']]=self.current
  if self.current is not None:
   if tag=='tr':self.row=[];self.current.append(self.row)
   if tag in ('th','td'):self.cell=''
 def handle_data(self,text):
  if self.cell is not None:self.cell+=text
 def handle_endtag(self,tag):
  if tag in ('th','td') and self.cell is not None:
   self.row.append(self.cell);self.cell=None
  if tag=='table':self.current=None
rendered_tables=TableAudit();rendered_tables.feed((p/'index.html').read_text())
assert {k:len(v)-1 for k,v in rendered_tables.tables.items()}=={'table-1':21,'table-2':8,'table-3':20,'table-4':9,'table-5':9}
for number,width in [(1,3),(2,2),(3,7),(4,6),(5,6)]:
 assert all(len(row)==width for row in rendered_tables.tables[f'table-{number}'])
counts=rendered_tables.tables['table-4'][1:-1]
contributions=rendered_tables.tables['table-5'][1:-1]
assert sum(int(row[2]) for row in counts)==601
assert sum(int(row[4]) for row in counts)==107
assert [sum(int(row[i].replace(',','')) for row in contributions) for i in (1,2,4)]==[601,5997,501574]
assert rendered_tables.tables['table-5'][-1]==['Total/average','601','5,997','9.98','501,574','834.6']
assert rendered_tables.tables['table-3'][10]==['10','KSDK','6.6','3.3%','CBS News','7.2','2.1%']
print('Validated all five tables, cell counts, merged PDF cells, and contributor totals.')
