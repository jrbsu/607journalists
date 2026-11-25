"""Reconstruct the dissertation's five tables from positioned PDF text."""
import html

# Bounds include captions and notes so they are not also emitted as prose.
SPECS = {
 17: (1, 355, 160, 790, 'The “criteria for speedy deletion” (Wikipedia, 2015a).'),
 33: (2, 330, 285, 530, 'The broad categories used to sort editors for analysis.'),
 42: (3, 55, 105, 610, 'Locations of sources in both peaks, ranked by average number of citations in each sample.'),
 43: (4, 55, 275, 550, 'Users sorted into experience categories.'),
 44: (5, 55, 445, 720, 'Users’ edits to the article and total content added by experience category.'),
}

def in_table(page, line):
 if page not in SPECS:return False
 _, left, bottom, top, _ = SPECS[page]
 return line['x'] >= left and bottom <= line['y'] <= top

def rows_at(lines, top, bottom, columns):
 """Group by baseline before splitting merged extraction fragments into cells."""
 groups=[]
 for line in sorted((l for l in lines if bottom <= l['y'] <= top),key=lambda l:(-l['y'],l['x'])):
  if not groups or abs(groups[-1][0]-line['y'])>2:groups.append((line['y'],[]))
  groups[-1][1].append(line)
 rows=[]
 for _,group in groups:
  cells=['']*len(columns)
  for l in sorted(group,key=lambda l:l['x']):
   col=min(range(len(columns)),key=lambda i:abs(columns[i]-l['x']))
   cells[col]=(cells[col]+' '+l['text'].strip()).strip()
  # PDFKit sometimes merges adjacent numeric cells into one fragment.
  for i in range(len(cells)-1):
   if cells[i] and not cells[i+1] and len(cells[i].split())==2:
    a,b=cells[i].split()
    if b.endswith('%'):cells[i],cells[i+1]=a,b
  rows.append(cells)
 return rows

def render_table(number, caption, headers, rows, row_header=0, total=False):
 head='<thead><tr>'+''.join('<th scope="col">'+html.escape(h)+'</th>' for h in headers)+'</tr></thead>'
 def row(cells):
  return '<tr>'+''.join(('<th scope="row">' if i==row_header else '<td>')+html.escape(c)+('</th>' if i==row_header else '</td>') for i,c in enumerate(cells))+'</tr>'
 body='<tbody>'+''.join(row(r) for r in (rows[:-1] if total else rows))+'</tbody>'
 foot='<tfoot>'+row(rows[-1])+'</tfoot>' if total else ''
 return f'<div class="table-scroll" role="region" aria-labelledby="table-{number}-caption" tabindex="0"><table class="research-table" id="table-{number}"><caption id="table-{number}-caption"><b>Table {number}.</b> {html.escape(caption)}</caption>'+head+body+foot+'</table></div>'

def build_tables(pages, link_text):
 result={}
 for page,(number,left,bottom,top,caption) in SPECS.items():
  lines=[l for l in pages[page-1]['lines'] if in_table(page,l)]
  if number==1:
   rows=[];group=''
   for l in sorted((l for l in lines if l['y']>195),key=lambda l:-l['y']):
    t=l['text'].strip()
    if t in ('General','Articles-specific'):group=t;continue
    import re
    m=re.match(r'([GA]\d+)\. (.*)',t)
    if m:rows.append([m[1],group,m[2]])
    else:rows[-1][2]+=' '+t
   headers=['Criterion','Applies to','Description'];row_header=0;total=False
  elif number==2:
   rows=rows_at(lines,495,320,[339,416]);headers=['Edits/day','Category'];row_header=1;total=False
  elif number==3:
   raw=rows_at(lines,540,125,[63,199,240,290,314,453,494])
   rows=[]
   for rank,cells in enumerate(raw,1):
    # The first nine right-hand ranks share a fragment with the publisher.
    if not cells[4]:cells[3],cells[4]=cells[3].split(' ',1)
    rows.append([str(rank),*cells[:3],*cells[4:]])
   headers=['Rank','Peak 1: publisher','Average uses','Per cent','Peak 2: publisher','Average uses','Per cent'];row_header=0;total=False
  elif number==4:
   rows=rows_at(lines,510,310,[63,147,295,343,411,466]);rows[-1][1]='Total/average';rows[-1][0]=''
   headers=['Edits/day','Category','Count','% Count','Of which status*','% Status'];row_header=1;total=True
  else:
   rows=rows_at(lines,665,465,[63,204,249,314,385,470]);headers=['Category','Count','Total edits','Edits (mean)','Total added (bytes)','Added (mean)'];row_header=0;total=True
  expected={1:21,2:8,3:20,4:9,5:9}[number]
  assert len(rows)==expected,(number,len(rows))
  assert all(len(r)==len(headers) for r in rows)
  markup=render_table(number,caption,headers,rows,row_header,total)
  if number==4:markup+='<p class="table-note">'+link_text('* “Status” refers to users with “rollback” or administrative privileges (Arazy et al., 2015).')+'</p>'
  result[page]=markup
 return result
