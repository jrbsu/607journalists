"""Recover appendix role markings from this dissertation's PDF drawing commands."""
import re
import html
from urllib.parse import quote
import pdf_vectors as pdf

ROLES = [('administrator', '†', 'Administrator'),
         ('rollback', '‡', 'User with rollback'),
         ('blocked', '§', 'Subsequently blocked user')]

def extract_roles(lines):
 result={}
 number=rb'([-\d.]+)'
 for page in lines[71:]:
  obj=pdf.objects[pdf.PAGES[page['page']-1]]
  content=pdf.stream(int(re.search(rb'/Contents\s+(\d+) 0 R',obj)[1]))
  content=re.sub(rb'\s+',b' ',content)
  fonts={name:pdf.objects[int(ref)] for name,ref in re.findall(rb'/(TT\d+)\s+(\d+) 0 R',pdf.resources(obj))}
  # Underlines use a flipped coordinate system with an explicit horizontal stroke.
  underlines=[]
  pattern=rb'q\s+1 0 0 -1 '+number+rb' '+number+rb' cm\s+'+number+rb' '+number+rb' m\s+'+number+rb' '+number+rb' l S Q'
  for m in re.finditer(pattern,content):
   x,origin,offset,y,width,y2=map(float,m.groups())
   assert y==y2
   underlines.append((x+offset,origin-y,width-offset))
  runs=[]
  for m in re.finditer(rb'q\s+1 0 0 1 '+number+rb' '+number+rb' cm\s+BT(.*?)ET\s+Q',content,re.S):
   font=re.search(rb'/(TT\d+)\s+1 Tf',m[3])
   if font:runs.append((float(m[1]),float(m[2]),fonts[font[1]]))
  for line in page['lines']:
   name=line['text'].strip()
   if not 60<line['y']<790 or name.startswith(('607 Journalists','8.2 ')) or (page['page']==74 and line['x']>390 and line['y']<115):continue
   matching=[font for x,y,font in runs if abs(x-line['x'])<1 and abs(y-line['y']-2.1)<1]
   assert matching,(page['page'],name)
   roles=[]
   if any(b'Verdana-Bold' in font for font in matching):roles.append('administrator')
   if any(abs(x-line['x'])<1 and abs(y-line['y'])<2 for x,y,width in underlines):roles.append('rollback')
   if any(b'Verdana-Italic' in font for font in matching):roles.append('blocked')
   result[name]=roles
 return result

def render_user(name,roles):
 markers=''.join('<sup class="user-role" role="img" aria-label="'+label+'" title="'+label+'">'+symbol+'</sup>' for key,symbol,label in ROLES if key in roles)
 return '<li><a href="https://en.wikipedia.org/wiki/User:'+quote(name.replace(' ','_'),safe='')+'">'+html.escape(name)+'</a>'+markers+'</li>'

def render_key():
 return '<p class="user-role-key">'+ ' · '.join('<span>'+symbol+' '+label+'</span>' for key,symbol,label in ROLES)+'. Markings reflect the original dissertation.</p>'
