from references import link_urls
import html,json,pathlib,math
from pdf_vectors import convert
ROOT=pathlib.Path(__file__).parent
OUT=ROOT/'dist/assets/figures';OUT.mkdir(exist_ok=True)
# Figure number, PDF page, plot bounds in original PDF points, caption.
FIGURES=[
(1,12,(56,630,484,155),'Diagram of the scene in Ferguson shortly following the initial altercation (New York Times, 2014).'),
(2,15,(72,430,224,300),'Examples of templates used on Wikipedia to denote issues with articles: unreferenced, copy edit, disputed, current, and peacock.'),
(3,20,(312,420,242,122),'Ford’s sources work process for breaking news (Ford, 2012a).'),
(4,20,(312,140,242,208),'A simulated example of a reference using the cite web template, and its result.'),
(5,25,(290,395,250,190),'The Zipf curve identified by Almeida et al. (2007), plotted on a log-log graph.'),
(6,26,(260,452,280,195),'The number of contributors remaining active each month has consistently fallen since 2008 (Keyes, 2013).'),
(7,31,(284,372,270,61),'A Wikipedia reference annotated to show its composition.'),
(8,35,(56,80,484,630),'Edits per day (black) plotted against daily pageviews (red). Includes the original incident key and peak annotations.'),
(9,36,(56,326,484,454),'Editors’ first contributions to the article, plotted against account ages. Peaks 1 and 2 highlighted red and blue. Letters refer to the incident key in Figure 8.'),
(10,37,(263,553,277,177),'Editing rates per peak 1 sample, in edits per hour.'),
(11,37,(267,236,273,179),'Editing rates per peak 2 sample, in edits per hour.'),
(12,38,(56,302,484,252),'Content added to each peak per sample, expressed as a percentage of the final figure for each peak.'),
(13,39,(56,519,484,173),'Reference densities, in references per kilobyte, per sample. Left: peak 1. Right: peak 2.'),
(14,40,(299,590,242,184),'Source types used in each peak.'),
(15,41,(70,459,470,317),'Locations of sources across both peaks as a percentage of total citations.'),
(16,45,(56,485,484,270),'Average content added per edit over each experience category.'),
(17,46,(56,507,484,279),'Average edits (bars) and content created (line) added to the article per user, by year of account creation.'),
(18,46,(301,200,240,211),'Users’ edits to the article against their edit ranking, log-log, fit to the Zipf curve (dotted).'),
(19,47,(56,443,484,342),'Edits made by the top ten contributors, including all other editors combined.'),
(20,47,(56,90,484,339),'Content added by the top ten contributors by edit count, including all other editors combined.')]
RASTER={1,2,5,6};HTML={3,4,7};DATA={16,19,20}
# Extended regions remove graphic labels/captions from prose during reflow.
REGIONS={}
for f,p,(x,y,w,h),c in FIGURES:
 pad=65 if f in {2,5,7} else 35
 REGIONS.setdefault(p,[]).append((x-4,y-pad,w+8,h+pad+3))
# Figure 16's displayed position, and whole-page graphics.
REGIONS[45]=[(56,465,484,290)]
REGIONS[35]=[(50,70,500,645)];REGIONS[36]=[(50,290,500,495)];REGIONS[47]=[(50,60,500,730)]
def in_graphic(page,line):
 x=line['x']+line['w']/2;y=line['y']+line['h']/2
 return any(a<=x<=a+w and b<=y<=b+h for a,b,w,h in REGIONS.get(page,[]))

def bar_svg(number,labels,values,unit,max_value):
 width=760;height=70+len(labels)*37;left=158;plot=510;rows=[]
 for i,(name,v) in enumerate(zip(labels,values)):
  y=30+i*37
  rows.append(f'<text x="{left-12}" y="{y+17}" text-anchor="end">{html.escape(name)}</text><rect x="{left}" y="{y}" width="{v/max_value*plot:.3f}" height="24" rx="2" fill="{"#7b857e" if name=="Others" else "#32634e"}"><title>{html.escape(name)}: {v:.2f} {unit}</title></rect><text x="{left+v/max_value*plot+8:.3f}" y="{y+17}">{v:.2f}</text>')
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title"><title id="title">Figure {number}: {unit} by contributor group</title><rect width="100%" height="100%" fill="white"/><g font-family="Arial,sans-serif" font-size="13" fill="#24372d">'+''.join(rows)+f'<text x="{left}" y="{height-8}">{html.escape(unit)}</text></g></svg>'
 (OUT/f'figure-{number}.svg').write_text(svg)
 return '<details class="figure-data"><summary>View chart data</summary><table><thead><tr><th scope="col">Contributor / group</th><th scope="col">'+html.escape(unit)+'</th></tr></thead><tbody>'+''.join(f'<tr><th scope="row">{html.escape(n)}</th><td>{v:.2f}</td></tr>' for n,v in zip(labels,values))+'</tbody></table></details>'
DATASETS={16:(["Power","Highly active","Very active","Active","Casual","Infrequent","Very infrequent","Anonymous"],[21629/319,269977/2816,59411/780,76538/1110,53848/562,12930/138,978/19,6263/253],'Bytes added per edit',110),19:(["Mandruss","Cwobeel","ChrisGualtieri","MrX","Bob K31416","Gaijin42","Michael-Ridgway","Dyrnych","Isaidnoway","Sy9045","Others"],[21.16,15.25,4.41,3.87,2.70,2.32,1.98,2.06,2.40,1.80,42.05],'Share of edits (%)',46),20:(["Mandruss","Cwobeel","ChrisGualtieri","MrX","Bob K31416","Gaijin42","Michael-Ridgway","Dyrnych","Isaidnoway","Sy9045","Others"],[18.80,25.92,3.71,4.36,.99,3.19,3.56,1.53,4.05,1.62,32.28],'Share of content added (%)',36)}
CODE='''<ref>{{cite web |url=http://www.theguardian.com/world/2014/jul/20/three-pro-russia-rebel-leaders-suspects-over-downed-mh17
|title=Three pro-Russia rebel leaders at the centre of suspicions over downed MH17
|first=Alec |last=Luhn |work=[[The Guardian]]
|date=20 July 2014 |accessdate=8 September 2014}}</ref>'''
CITATION='Luhn, Alec (20 July 2014). “Three pro-Russia rebel leaders at the centre of suspicions over downed MH17”. The Guardian. Retrieved 8 September 2014.'
CUSTOM={3:'''<div class="workflow"><div class="flow-step">Breaking news item</div><div class="flow-arrow" aria-hidden="true">↓</div><div class="flow-step">Is it relevant?</div><div class="flow-branches"><div><b>Yes</b> — provide rationale<br>↓<div class="flow-step">Is it accurate?</div><div class="flow-branches"><div><b>Yes</b> — provide categories<br>↓<div class="flow-step">Provide in-depth sources that corroborate</div><div class="flow-step">Summarise and insert into article</div></div><div><b>No</b> — provide rationale<br>↓<div class="flow-step">Discard</div></div></div></div><div><b>No</b> — provide rationale<br>↓<div class="flow-step">Discard</div></div></div></div>''',4:'<pre><code>'+link_urls(CODE)+'</code></pre><div class="citation-example"><b>Rendered reference</b><br>1. '+html.escape(CITATION)+'</div>',7:'''<div class="annotated-citation"><span><small>Citation number</small>1.</span><span><small>Author</small>Luhn, Alec</span><span><small>Publication date</small>20 July 2014</span><span><small>Title and hyperlink</small>Three pro-Russia rebel leaders at the centre of suspicions over downed MH17</span><span><small>Publication</small>The Guardian</span><span><small>Access date</small>8 September 2014</span></div>'''}
def image_dimensions(path):
 """Read intrinsic dimensions so lazy loading cannot move anchor targets."""
 if path.suffix=='.svg':
  import xml.etree.ElementTree as ET
  attrs=ET.parse(path).getroot().attrib
  return float(attrs['width']),float(attrs['height'])
 import struct
 with path.open('rb') as image:
  assert image.read(2)==b'\xff\xd8'
  while True:
   assert image.read(1)==b'\xff'
   marker=image.read(1)
   while marker==b'\xff':marker=image.read(1)
   length=struct.unpack('>H',image.read(2))[0]
   if marker in (b'\xc0',b'\xc1',b'\xc2'):
    _,height,width=struct.unpack('>BHH',image.read(5))
    return width,height
   image.seek(length-2,1)

def build_figures(link_text=html.escape):
 result={}
 for f,p,box,caption in FIGURES:
  extra=''
  if f in HTML:
   content=CUSTOM[f];note='Recreated as accessible HTML from the original figure.'
  else:
   ext='jpg' if f in RASTER else 'svg'
   if f in DATA:
    extra=bar_svg(f,*DATASETS[f]);note='Recreated from Table 5 (total bytes ÷ edits).' if f==16 else 'Recreated from the printed percentages; horizontal bars replace the original pie chart. Percentages retain the original rounding.'
   elif f not in RASTER:
    (OUT/f'figure-{f}.svg').write_text(convert(p,box,caption));note='Vector reconstruction of the PDF’s plotted geometry; original scales and marks are preserved. Underlying sample values are not inferred.'
   else:note='Original source graphic, extracted from the PDF. The underlying data are not included in the dissertation.' if f in {5,6} else 'Original source illustration extracted from the PDF.'
   width,height=image_dimensions(OUT/f'figure-{f}.{ext}')
   content=f'<a class="figure-image" href="assets/figures/figure-{f}.{ext}" target="_blank" aria-label="Enlarge Figure {f}"><img src="assets/figures/figure-{f}.{ext}" alt="{html.escape(caption,quote=True)}" loading="lazy" width="{width:g}" height="{height:g}"></a>'
  result.setdefault(p,[]).append(f'<figure id="figure-{f}" class="research-figure">{content}<figcaption><b>Figure {f}.</b> {link_text(caption)}<small>{note}</small><a href="607journalists.pdf#page={p}">Compare with the original PDF ↗</a></figcaption>{extra}</figure>')
 (OUT/'chart-data.json').write_text(json.dumps({str(k):{'labels':v[0],'values':v[1],'unit':v[2]} for k,v in DATASETS.items()},indent=2))
 return {p:'\n'.join(fs) for p,fs in result.items()}
