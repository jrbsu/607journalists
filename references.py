"""Bibliography anchors and conservative author/year citation matching."""
import re,html,unicodedata,collections


def clean_source_urls(text):
 # Bibliography URLs end at the access note or the end of the entry.
 return re.sub(r'https?://.*?(?=\s*\[Accessed|$)',
               lambda m: re.sub(r'\s+', '', m[0]), text)

def link_urls(text):
 """Escape plain text and link web addresses without swallowing punctuation."""
 parts=[];end=0
 for m in re.finditer(r'https?://[^\s<>|]+',text):
  url=m[0].rstrip('.,;')
  while url.endswith(')') and url.count(')')>url.count('('):url=url[:-1]
  parts.extend([html.escape(text[end:m.start()]),
                '<a href="'+html.escape(url,quote=True)+'">'+html.escape(url)+'</a>'])
  end=m.start()+len(url)
 parts.append(html.escape(text[end:]))
 return ''.join(parts)

def correct_citations(text):
 # Explicit editorial corrections; retain the extracted PDF source unchanged.
 return re.sub(r'\bKittur et al\.\s*\(2007\)', 'Kittur et al. (2007a)', text)

def key(s):return ''.join(c for c in unicodedata.normalize('NFKD',s.casefold()) if not unicodedata.combining(c))
def slug(s):return re.sub(r'[^a-z0-9]+','-',key(s)).strip('-')
class References:
 def __init__(self,lines):
  self.entries=[];self.matches=[];self.aliases=collections.defaultdict(list);self.by_page=collections.defaultdict(list)
  for page in lines[57:69]:
   buf=[];last=None
   def flush():
    if not buf:return
    text=clean_source_urls(' '.join(buf));buf.clear()
    if text.startswith('SINGH, P.V., TAN, Y. and MOOKERJEE, V., 2011.'):
     text=text.replace('2011.', '2008.', 1)
    m=re.search(r'\b(1[89]\d{2}|20\d{2})([a-z]?)\.',text)
    if not m:raise ValueError('Missing bibliography year: '+text)
    year=m[1]+m[2];authors=text[:m.start()].strip(' .,');first=authors.split(',')[0]
    names=re.findall(r'(?:^|,\s+|\band\s+)([A-ZÀ-ÖØ-ÞĀ-Ž][A-ZÀ-ÖØ-ÞĀ-Ž .’\'-]*),\s*[A-Z]',authors)
    if not names:names=[first]
    ident='ref-'+slug(first)+'-'+year
    if any(e['id']==ident for e in self.entries):ident+='-'+str(len(self.entries))
    entry={'id':ident,'text':text,'page':page['page'],'year':year,'authors':names};self.entries.append(entry);self.by_page[page['page']].append(entry)
    aliases=[first.title()]
    if len(names)==2:aliases +=[names[0].title()+' and '+names[1].title()]
    if len(names)>2:aliases +=[names[0].title()+' et al.']
    for alias in aliases:self.aliases[(key(alias),year)].append(entry)
   for l in page['lines']:
    t=l['text'].strip()
    if l['y']<60 or l['y']>790 or t=='7 BIBLIOGRAPHY':continue
    if last is not None and last-l['y']>19:flush()
    buf.append(t);last=l['y']
   flush()
  # Build longest-first aliases, including typography variants, without fuzzy year matching.
  names=sorted({a for a,y in self.aliases},key=len,reverse=True)
  self.pattern=re.compile(r'(?<![\w])('+ '|'.join(re.escape(n) for n in names)+r')(,\s*|\s*\(\s*)(\d{4}[a-z]?)(?![\da-z])',re.I)
  self.count=0;self.unresolved=[];self.used=collections.defaultdict(list)
 def link_text(self,text):
  text=correct_citations(text)
  # Match against a diacritic-normalized shadow of text, keeping original display wording.
  shadow=''.join(''.join(c for c in unicodedata.normalize('NFD',v) if not unicodedata.combining(c)) for v in text)
  parts=[];end=0
  for m in self.pattern.finditer(shadow):
   candidates=self.aliases.get((key(m[1]),m[3]),[])
   if len(candidates)!=1:
    self.unresolved.append(text[m.start():m.end()]);continue
   e=candidates[0];self.count+=1;cid='cite-'+str(self.count);self.used[e['id']].append(cid)
   parts.append(link_urls(text[end:m.start()]));parts.append(f'<a class="citation" id="{cid}" href="#{e["id"]}" title="{html.escape(e["text"],quote=True)}">'+html.escape(text[m.start():m.end()])+'</a>');end=m.end()
  parts.append(link_urls(text[end:]));result=''.join(parts)
  # Figure references are exact, retaining figure letters such as 2a / 2d.
  result=re.sub(r'\bFigure\s+(\d{1,2})([a-e]?)(?!\d)',lambda m:f'<a class="figure-ref" href="#figure-{m[1]}">{m[0]}</a>' if 1<=int(m[1])<=20 else m[0],result)
  return result
 def render_page(self,page):
  out=[]
  for e in self.by_page[page]:
   text=link_urls(e['text']);back=''
   cites=self.used[e['id']]
   if cites:back='<div class="reference-backlinks">Cited in text: '+ ' '.join(f'<a href="#{c}" aria-label="Return to citation {i+1}">{i+1} ↩</a>' for i,c in enumerate(cites))+'</div>'
   out.append(f'<div class="reference" id="{e["id"]}" tabindex="-1"><p>{text}</p>{back}</div>')
  return ('<h2>7 Bibliography</h2><details class=reference-note><summary>Citation notes for this web edition</summary><p>This web edition corrects the Singh, Tan and Mookerjee bibliography year from 2011 to 2008 to match the in-text citation. In section 2.5, “Kittur et al. (2007)” is clarified as “Kittur et al. (2007a)”: the discussion of newcomers taking on more of the workload identifies <i>Power of the Few vs. Wisdom of the Crowd</i>, rather than the 2007b paper on conflict and coordination. Both citations now link to their bibliography entries. The original wording remains in the downloadable PDF. Context-dependent “ibid.” references remain plain text.</p></details>' if page==58 else '')+'\n'.join(out)
