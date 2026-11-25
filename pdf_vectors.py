"""Convert the supplied PDF's vector chart artwork to SVG, preserving plotted geometry.
This intentionally handles this document's PDF operators, not arbitrary PDFs.
"""
import re,zlib,copy,html,pathlib
ROOT=pathlib.Path(__file__).parent
source=ROOT.parent/'607journalists.pdf'
if not source.exists():source=ROOT/'dist/607journalists.pdf'
raw=source.read_bytes()
objects={int(m[1]):m[2] for m in re.finditer(rb'(\d+) 0 obj\s*(.*?)\s*endobj',raw,re.S)}
def walk(n):
 v=objects[n]
 if re.search(rb'/Type\s*/Page\b',v):return [n]
 return sum((walk(int(x)) for x in re.findall(rb'(\d+) 0 R',re.search(rb'/Kids\s*\[(.*?)\]',v,re.S)[1])),[])
PAGES=walk(744)
def stream(n):
 v=objects[n];m=re.search(rb'stream\r?\n',v)
 lm=re.search(rb'/Length\s+(\d+)(\s+0 R)?',v[:m.start()]);length=int(objects[int(lm[1])].strip()) if lm[2] else int(lm[1])
 data=v[m.end():m.end()+length]
 return zlib.decompress(data) if b'/FlateDecode' in v[:m.start()] else data
def resources(v):
 m=re.search(rb'/Resources\s+(\d+) 0 R',v)
 return objects[int(m[1])] if m else v

def mul(a,b):
 A,B,C,D,E,F=a;g,h,i,j,k,l=b
 return (A*g+C*h,B*g+D*h,A*i+C*j,B*i+D*j,A*k+C*l+E,B*k+D*l+F)
def fmt(x):return f'{x:.5g}'
def matrix(m):return 'matrix('+ ' '.join(map(fmt,m))+')'
def tokens(s):
 # Strings are atomic: never interpret operator-like words inside them.
 r=rb'\((?:\\[\s\S]|[^\\()])*\)|<[^<>]*>|\[(?:\((?:\\[\s\S]|[^\\()])*\)|[^\]])*\]|/[^\s\[\]()<>]+|[-+]?(?:\d*\.\d+|\d+)|[^\s]+'
 return re.findall(r,s)
def unstring(s):
 if s.startswith(b'<'):
  try:return bytes.fromhex(s[1:-1].decode())
  except:return b''
 s=s[1:-1]
 s=re.sub(rb'\\([0-7]{1,3})',lambda m:bytes([int(m[1],8)]),s)
 return re.sub(rb'\\(.)',lambda m:{b'n':b'\n',b'r':b'\r',b't':b'\t'}.get(m[1],m[1]),s)
def convert(page,bounds,title):
 obj=objects[PAGES[page-1]];elements=[];defs=[]
 def render(data,res,state,depth=0):
  if depth>12:raise ValueError('Recursive form')
  stack=[];args=[];path=[];ctm_path=None
  def emit(element):
   if not state.get('empty_clip'):elements.append(element)
  fonts={}; fm=re.search(rb'/Font\s*<<(.*?)>>',res,re.S)
  if fm:
   for name,ref in re.findall(rb'/(\w+)\s+(\d+) 0 R',fm[1]):fonts[name]=objects[int(ref)]
  xobjs={};xm=re.search(rb'/XObject\s*<<(.*?)>>',res,re.S)
  if xm:xobjs={name:int(ref) for name,ref in re.findall(rb'/(\w+)\s+(\d+) 0 R',xm[1])}
  states={};em=re.search(rb'/ExtGState\s*<<(.*?)>>',res,re.S)
  if em:
   for name,ref in re.findall(rb'/(\w+)\s+(\d+) 0 R',em[1]):states[name]=objects[int(ref)]
  for t in tokens(data):
   if t[:1] in [b'/',b'(',b'[',b'<'] or re.fullmatch(rb'[-+]?(?:\d*\.\d+|\d+)',t):args.append(t);continue
   op=t.decode('latin1'); nums=lambda:[float(x) for x in args]
   if op=='q':stack.append(copy.deepcopy(state))
   elif op=='Q':state=stack.pop()
   elif op=='cm':state['m']=mul(state['m'],nums())
   elif op in ['sc','scn','rg','SC','SCN','RG','g','G']:
    ns=nums();ns=ns*3 if len(ns)==1 else ns
    if len(ns)>=3:state['stroke' if op[0].isupper() else 'fill']='rgb('+','.join(str(round(v*255)) for v in ns[:3])+')'
   elif op=='gs':
    es=states.get(args[0][1:],b'')
    for key,prop in [(b'ca','fill_alpha'),(b'CA','stroke_alpha')]:
     am=re.search(rb'/'+key+rb'\s+([\d.]+)',es)
     if am:state[prop]=float(am[1])
   elif op=='w':state['width']=float(args[0])
   elif op=='d':state['dash']=' '.join(re.findall(r'[\d.]+',args[0].decode()))
   elif op in ['m','l','c','v','y','re','h']:
    ns=nums();ctm_path=state['m']
    if op=='re':
     x,y,w,h=ns;path += [f'M {x} {y} h {w} v {h} h {-w} Z']
    elif op=='h':path.append('Z')
    elif op in ['m','l','c']:path.append({'m':'M','l':'L','c':'C'}[op]+' '+' '.join(map(fmt,ns)))
    elif op=='v':path.append('S '+' '.join(map(fmt,ns)))
    elif op=='y':path.append('C '+' '.join(map(fmt,ns+ns[-2:])))
   elif op in ['W','W*']:
    # The document uses zero-area cross clips and tiny polygon clips for markers.
    # Preserve those marks directly; the outer SVG viewport clips each figure.
    if len(path)==5 and [v[0] for v in path]==['M','L','M','L','Z']:state['empty_clip']=True
    elif path and all(v=='Z' or re.fullmatch(r'[ML] [-+0-9.e]+ [-+0-9.e]+',v) for v in path):
     pts=[list(map(float,v[1:].split())) for v in path if v[0] in 'ML']
     if pts and max(p[0] for p in pts)-min(p[0] for p in pts)<20 and max(p[1] for p in pts)-min(p[1] for p in pts)<20:state['shape_clip']=(list(path),ctm_path)
   elif op in ['f','f*','F','S','s','B','B*','b','b*','n']:
    if path and op!='n':
     if op in ['f','f*','F'] and state.get('shape_clip'):path,ctm_path=state['shape_clip']
     if op in ['s','b','b*']:path.append('Z')
     fill=state['fill'] if op not in ['S','s'] else 'none';stroke=state['stroke'] if op in ['S','s','B','B*','b','b*'] else 'none'
     emit(f'<path d="{" ".join(path)}" transform="{matrix(ctm_path)}" fill="{fill}" fill-opacity="{state["fill_alpha"]}" stroke-opacity="{state["stroke_alpha"]}" stroke="{stroke}" stroke-width="{state["width"]}" stroke-dasharray="{state["dash"]}" fill-rule="{"evenodd" if "*" in op else "nonzero"}"/>')
    path=[]
   elif op=='BT':state['tm']=(1,0,0,1,0,0)
   elif op=='Tm':state['tm']=nums()
   elif op=='Tf':state['font']=args[0][1:];state['fs']=float(args[1])
   elif op in ['Tj','TJ']:
    ss=re.findall(rb'\((?:\\[\s\S]|[^\\()])*\)|<[^<>]*>',args[0]) if op=='TJ' else args
    bs=b''.join(unstring(s) for s in ss); font=fonts.get(state['font'],b'')
    text=bs.decode('mac_roman' if b'MacRoman' in font else 'cp1252',errors='replace')
    text=''.join(c for c in text if ord(c)>=32)
    if text.strip():
     m=mul(state['m'],state['tm']);a,b,c,d,e,f=m;m=(a,b,-c,-d,e,f)
     bold='bold' if b'Bold' in font else 'normal';italic='italic' if b'Italic' in font or b'Oblique' in font else 'normal'
     emit(f'<text transform="{matrix(m)}" font-family="Arial, sans-serif" font-size="{state["fs"]}" font-weight="{bold}" font-style="{italic}" fill="{state["fill"]}">{html.escape(text)}</text>')
   elif op=='Do':
    ref=xobjs.get(args[0][1:]);v=objects.get(ref,b'')
    if re.search(rb'/Subtype\s*/Form',v):
     st=copy.deepcopy(state);mm=re.search(rb'/Matrix\s*\[([^]]+)\]',v)
     if mm:st['m']=mul(st['m'],[float(x) for x in mm[1].split()])
     render(stream(ref),resources(v),st,depth+1)
    elif ref:raise ValueError(f'Raster image in chart page {page}')
   args=[]
 st={'m':(1,0,0,1,0,0),'tm':(1,0,0,1,0,0),'fill':'black','stroke':'black','width':1,'dash':'none','font':b'TT1','fs':1,'fill_alpha':1,'stroke_alpha':1,'clips':[]}
 cid=int(re.search(rb'/Contents\s+(\d+)',obj)[1]);render(stream(cid),resources(obj),st)
 x,y,w,h=bounds
 return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="{x} {-y-h} {w} {h}" role="img" aria-labelledby="title"><title id="title">{html.escape(title)}</title><defs>'+''.join(defs)+'</defs><g transform="scale(1,-1)">'+''.join(elements)+'</g></svg>'
