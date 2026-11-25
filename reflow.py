"""Join clear prose continuations across PDF pages, preserving deep links."""
import html
import re


def plain_text(markup):
 return html.unescape(re.sub(r'<[^>]+>', '', markup))


def join_page_paragraphs(segments, last_lines):
 joined=[]
 for index in range(1,len(segments)):
  previous,current=segments[index-1],segments[index]
  opening=re.match(r'<div class="reading-text" id="page-(\d+)"><p>(.*?)</p>',current,re.S)
  if not opening:continue
  page=int(opening[1])
  if not 8<=page<=57:continue
  # A full justified last line without a sentence ending is a continuation.
  line=last_lines.get(page-1)
  if not line or line['w']<470:continue
  figure_at=previous.find('<figure ')
  prose=previous[:figure_at] if figure_at>=0 else previous[:-6]
  paragraphs=list(re.finditer(r'<p>(.*?)</p>',prose,re.S))
  if not paragraphs:continue
  final=paragraphs[-1]
  if prose[final.end():].strip():continue # Preserve intervening headings/lists.
  left=plain_text(final[1]).rstrip()
  right=plain_text(opening[2]).lstrip()
  if not left or not right or re.search(r'[.!?:;][”’\")\]]*$',left):continue
  # The source occasionally ends a full line with a compound-word hyphen.
  separator='' if left.endswith('-') else ' '
  marker=f'<span id="page-{page}" class="page-continuation"></span>'
  replacement='<p>'+final[1]+separator+marker+opening[2]+'</p>'
  segments[index-1]=previous[:final.start()]+replacement+previous[final.end():]
  segments[index]='<div class="reading-text">'+current[opening.end():]
  joined.append((page-1,page,left[-70:],right[:70]))
 return joined
