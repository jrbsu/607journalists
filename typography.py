"""Apply prose typography without changing HTML attributes or source data."""
import re
from html.parser import HTMLParser


def italicise_et_al(document):
 class Formatter(HTMLParser):
  def __init__(self):
   super().__init__(convert_charrefs=False)
   self.parts=[]
   self.stack=[]
  def handle_starttag(self,tag,attrs):
   self.parts.append(self.get_starttag_text())
   if tag not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}:
    self.stack.append(tag)
  def handle_endtag(self,tag):
   self.parts.append('</'+tag+'>')
   if tag in self.stack:
    self.stack=self.stack[:len(self.stack)-1-self.stack[::-1].index(tag)]
  def handle_data(self,data):
   if not any(t in self.stack for t in ('i','em','script','style')):
    data=re.sub(r'\bet\s+al\.',lambda m:'<i>'+m[0]+'</i>',data,flags=re.I)
   self.parts.append(data)
  def handle_entityref(self,name):self.parts.append('&'+name+';')
  def handle_charref(self,name):self.parts.append('&#'+name+';')
  def handle_comment(self,data):self.parts.append('<!--'+data+'-->')
  def handle_decl(self,data):self.parts.append('<!'+data+'>')
 formatter=Formatter()
 formatter.feed(document)
 return ''.join(formatter.parts)
