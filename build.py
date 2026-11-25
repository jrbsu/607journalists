import json,re,html,shutil,pathlib
from user_roles import extract_roles,render_user,render_key
root=pathlib.Path(__file__).parent; out=root/'dist'; pages=json.load(open(root/'pages.json')); lines=json.load(open(root/'lines.json'))
chapters={2:'Abstract',3:'Acknowledgements',4:'Contents',6:'List of figures',7:'1 · Introduction',10:'2 · Literature review',28:'3 · Methodology',35:'4 · Results',49:'5 · Analysis and discussion',56:'6 · Conclusion',58:'7 · Bibliography',70:'8 · Appendices'}
from figures import build_figures,in_graphic,FIGURES
from tables import build_tables,in_table
from references import References,correct_citations
from headings import catalogue,join_heading_lines,render_heading,render_contents,sentence_case
heading_titles=catalogue(lines)
user_roles=extract_roles(lines)
minor_headings={37:{"Peak 1 — Initial Ferguson riots","Peak 2 — Wilson indictment decision"},38:{"Text added"},40:{"Source types","Source geography"},41:{"Publishers of sources"},45:{"Account age"},70:{"Peak 1","Peak 2"},71:{"Peak 1","Peak 2"}}
references=References(lines)
figures=build_figures(references.link_text)
tables=build_tables(lines,references.link_text)
chapter_targets={p:('section-'+t.split(' · ')[0] if ' · ' in t else 'page-'+str(p)) for p,t in chapters.items()}
nav=''.join(f'<a href="#{chapter_targets[p]}">{html.escape(t)}</a>' for p,t in chapters.items())
body=[]; index=[]; last_prose_lines={}
for page,data in zip(pages[1:],lines[1:]):
 n=page['page']; label=re.search(r'!([0-9ivx]+)\s*$',page['text']); label=label.group(1) if label else str(n)
 ls=[l for l in data['lines'] if l['y']>60 and l['y']<790 and l['text'].strip() and '607 Journalists J.R.B.' not in l['text']]
 illustrated=bool(re.search(r'Figure \d+:|Table \d+:',page['text'])) or n in [17,33,35,36,40,41,42,43,44,45,46,47,72,73,74]
 chunks=[]; buf=[]; prev=None; table_inserted=False
 def flush():
  if buf:
   text=' '.join(buf);chunks.append('<p>'+(html.escape(text) if 58<=n<=69 or n==6 else references.link_text(text))+'</p>');buf.clear()
   if n in (70,71):chunks[-1]=re.sub(r'\b\d{9}\b',lambda m:'<a href="https://en.wikipedia.org/w/index.php?oldid='+m[0]+'">'+m[0]+'</a>',chunks[-1])
 for l in join_heading_lines(ls):
  t=l['text'].strip()
  if in_table(n,l):
   if not table_inserted:
    flush();chunks.append(tables[n]);table_inserted=True;prev=None
   continue
  if in_graphic(n,l):continue
  if illustrated and n<58 and (l['h']<13 or re.fullmatch(r'[\d,.% /—–-]+|Peak [12]|Edits/hr',t)):continue
  numbered=re.match(r'^(\d+(?:\.\d+)*)\s+(.+)$',t)
  if n>=7 and numbered and numbered[1] in heading_titles and sentence_case(numbered[2]).casefold()==heading_titles[numbered[1]].casefold():
   flush();chunks.append(render_heading(numbered[1],heading_titles[numbered[1]]));prev=None;continue
  if t in ['ABSTRACT','ACKNOWLEDGEMENTS','TABLE OF CONTENTS','LIST OF FIGURES']:
   flush();chunks.append('<h2>'+html.escape(sentence_case(t))+'</h2>');prev=None;continue
  if t in minor_headings.get(n,set()):
   flush();chunks.append('<h4 class="minor-heading">'+html.escape(t.replace('— Initial','— initial'))+'</h4>');prev=None;continue
  if prev and (prev['y']-l['y']>30 or l['y']>prev['y']+5 or (n>=58 and prev['y']-l['y']>19)):
   # Graphics can interrupt a sentence without introducing a paragraph.
   continuation=n<58 and t[:1].islower() and not re.search(r'[.!?:;][”’\")\]]*$',prev['text'])
   if not continuation:flush()
  if n>=72:flush()
  buf.append(t);prev=l;last_prose_lines[n]=l
 flush()
 text='\n'.join(chunks)
 if 58<=n<=69:text=f'<!--bibliography-{n}-->'
 if n==4:text=render_contents(heading_titles)
 if n==5:text=''
 if n==6:
  text='<h2>List of figures</h2><ol class=figure-index>'+''.join(f'<li><a href="#figure-{f}">{html.escape(c)}</a></li>' for f,p,b,c in FIGURES)+'</ol>'
 if n>=72:
  # PDF extraction interleaves three columns; read each column top to bottom.
  users=sorted((l for l in ls if not l['text'].startswith('8.2 ') and not (n==74 and l['x']>390 and l['y']<115)),key=lambda l:(round(l['x']/169),-l['y']))
  text=(render_heading('8.2',heading_titles['8.2'])+'<p>Usernames link to their Wikipedia user pages. The symbols below preserve the role markings in the original dissertation.</p>'+render_key() if n==72 else '')
  text+='<ul class="registered-users">'+''.join(render_user(l['text'].strip(),user_roles[l['text'].strip()]) for l in users)+'</ul>'
 text+=figures.get(n,'')
 body.append(f'<div class="reading-text" id="page-{n}">{text}</div>')
 chapter=next(title for start,title in reversed(list(chapters.items())) if start<=n)
 index.append({'id':f'page-{n}','label':chapter,'text':re.sub(r'\s+',' ',correct_citations(page['text']).replace('607 Journalists J.R.B. Sutherland',''))})
from reflow import join_page_paragraphs
joined_paragraphs=join_page_paragraphs(body,last_prose_lines)
print(f'Joined {len(joined_paragraphs)} paragraphs split across PDF pages.')
head='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>607 Journalists — Joseph R. B. Sutherland</title><meta name="description" content="The complete 2015 dissertation on Wikipedia’s response to breaking news. Read, search, and explore the original research."><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&amp;family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;0,6..72,700;1,6..72,400&amp;display=swap" rel="stylesheet"><link rel="icon" type="image/svg+xml" href="favicon.svg"><link rel="stylesheet" href="style.css"></head><body><a class="skip" href="#main">Skip to dissertation</a><header><a class="brand" href="#top">607 Journalists<span> A dissertation · 2015</span></a><a href="607journalists.pdf" download>Download PDF ↓</a></header><div class="layout"><aside><label for="search">Search the dissertation</label><div class="search"><input id="search" type="search" placeholder="Try ‘editor experience’"><kbd>/</kbd></div><div id="search-status" role="status"></div><div id="search-results"></div><details class="contents" open><summary>Contents</summary><nav aria-label="Chapters">'''
hero='''</nav></details><p class="aside-note">Joseph R. B. Sutherland<br>Robert Gordon University<br>April 2015</p></aside><main id="main"><div id="top" class="hero"><p class="eyebrow">BA (Hons.) Journalism · Robert Gordon University</p><h1>607 Journalists</h1><p class="subtitle">An evaluation of Wikipedia’s response to and coverage of breaking news and current events</p><p class="byline">Joseph R. B. Sutherland <span>April 2015</span></p><div class="edition">The complete dissertation, adapted for reading on the web. The research and references reflect April 2015. Read continuously by chapter, with figures and linked references throughout. The original formatting is available in the downloadable PDF.</div><details class="original"><summary>Original title page</summary><img src="assets/page-1.jpg" loading="lazy" width="1100" height="1500" alt="Original dissertation title page"></details><div class="jump"><a href="#section-1">Start reading →</a><a href="#section-4">Explore the results</a></div></div>'''
document=head+nav+hero+''.join(body)+'<footer>607 Journalists · Joseph R. B. Sutherland · April 2015<br><a href="#top">Back to top ↑</a></footer></main></div><script src="search-index.js"></script><script src="app.js"></script></body></html>'
for n in range(58,70):document=document.replace(f'<!--bibliography-{n}-->',references.render_page(n).replace('<h2>7 Bibliography</h2>',render_heading('7',heading_titles['7'])))
# Format visible prose only, leaving URLs and citation title attributes intact.
from typography import italicise_et_al
document=italicise_et_al(document)
(out/'index.html').write_text(document)
(out/'search-index.js').write_text('const searchIndex='+json.dumps(index)+';')
if (root.parent/'607journalists.pdf').exists():shutil.copy(root.parent/'607journalists.pdf',out/'607journalists.pdf')
print(f'Built {len(body)} continuous text segments with {len(pages)} original page images.')

(root/'citation-audit.json').write_text(json.dumps({'references':len(references.entries),'linked_citations':references.count,'unresolved_author_year_matches':sorted(set(references.unresolved))},indent=2))
print(f'{len(references.entries)} bibliography entries; {references.count} linked citations. Unresolved: {sorted(set(references.unresolved))}')
