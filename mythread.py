#-*- coding:utf-8 -*-

import wx
import threading, sqlite3, os.path, sys
from cgi import escape as htmlescape

from whoosh.highlight import highlight, HtmlFormatter, SimpleFragmenter
from whoosh.analysis import NgramTokenizer

dataModel = {} # data model for displaying query results

class SearchThread(threading.Thread):
    """
    SearchThread Class
    """
    def __init__(self, lang, field, keywords,checkedItems,window,mode='all'):
        threading.Thread.__init__(self)
        self.window = window
        self.keywords = keywords
        self.field = field
        self.checkedItems = checkedItems
        self.lang = lang
        
    def term2prefix(self, qobj):
        return Prefix(fieldname=qobj.fieldname,text=qobj.text,boost=qobj.boost)

    def change_phrase(self, qobj):
        x = Wildcard(qobj.fieldname,u'*%s'%(qobj.words[0]))
        y = Prefix(qobj.fieldname,qobj.words[-1])
        if len(qobj.words) > 2:
            u = Phrase(qobj.fieldname,qobj.words[1:-1])
            return Or([And([x,u,y]),qobj])
        return Or([And([x,y]),qobj])
        
    def run(self):
        conn = sqlite3.connect(os.path.join(sys.path[0],'resources','%s.db'%(self.lang)))
        searcher = conn.cursor()
        terms = map(lambda term: term.replace('+',' '),self.keywords.split())
        
        args = ()
        if self.lang != 'thaibt':            
            query = 'SELECT * FROM %s WHERE '%(self.lang)
            query += "content LIKE '%%%s%%' "%(terms[0]) 
            for term in terms[1:]:
                query += "AND content LIKE '%%%s%%' "%(term) 

            if len(self.checkedItems) > 0:
                query += 'AND ('
                query += "volumn = '%02d' "%(self.checkedItems[0]+1)
                for p in self.checkedItems[1:]:
                    query += "OR volumn = '%02d' "%(p+1)
                query += ')'
        else:
            query = 'SELECT * FROM speech WHERE content LIKE ?'
            args = ('%'+terms[0]+'%',)
            for term in terms[1:]:
                if term.find('v:') == 0:
                    try:
                        query += ' AND ('
                        for vol in term[2:].split(','):
                            if '-' in vol and len(vol.split('-')) == 2:
                                start, end = map(int, vol.split('-'))
                                for i in xrange(start, end+1, 1):
                                    query += 'book = ? OR '
                                    args += (i,)
                            else:
                                query += 'book = ? OR '
                                args += (int(vol),)
                        query = query.rstrip(' OR ') + ')'
                    except ValueError, e:
                        pass                    
                else:
                    query += ' AND content LIKE ?'
                    args += ('%'+term+'%',)

        wx.CallAfter(self.window.QueryStarted)
        
        new_results = []
        for result in searcher.execute(query, args):
            r = {}
            if self.lang == 'thai' or self.lang == 'pali':
                r['volume'] = result[0]
                r['page'] = result[1]
                r['items'] = result[2]
                r['content'] = result[3]
            elif self.lang == 'thaimc':
                r['volume'] = result[0]
                r['page'] = result[1]
                r['items'] = result[2]
                r['header'] = result[3]
                r['footer'] = result[4]
                r['display'] = result[5]
                r['content'] = result[6]
            elif self.lang == 'thaimm':
                r['volume'] = result[0]
                r['volume_orig'] = result[1]
                r['page'] = result[2]
                r['items'] = result[3]
                r['content'] = result[4]
            elif self.lang == 'thaibt':
                r['volume'] = result[0]
                r['page'] = result[1]
                r['content'] = result[3]
            new_results.append(r)

        wx.CallAfter(self.window.QueryFinished, new_results)
        
class DisplayThread(threading.Thread):
    """
    Display Class thats reformats results to HTML and insert output into dataModel
    """
    def __init__(self, results, lang, keywords, window, p=(0,0)):
        threading.Thread.__init__(self)
        self.results = results
        self.keywords = keywords
        self.lang = lang
        self.p = p
        self.window = window
        
    def run(self):
        termset = []
        keywords = self.keywords.replace('+',' ')
        keywords = ' '.join(filter(lambda x:x.find('v:') != 0, keywords.split()))

        for t in keywords.split():
            termset.append(t)                

        items = []
        wx.CallAfter(self.window.DisplayStarted)
        key = '%d:%d'%self.p
        if key not in dataModel:
            for i,r in enumerate(self.results[self.p[0]:self.p[1]]):
                nMin = min([len(t) for t in termset])
                nMax = max([len(t) for t in termset])
                excerpts = highlight(r['content'],
                                     termset,NgramTokenizer(nMin,nMax),
                                     SimpleFragmenter(size=70),
                                     MyHtmlFormatter(tagname='font',attrs='size="4" color="purple"'))
                
                if self.lang == 'pali' and 'wxMac' not in wx.PlatformInfo:
                    excerpts = excerpts.replace(u'ฐ',u'\uf700').replace(u'ญ',u'\uf70f').replace(u'\u0e4d',u'\uf711')
                
                if self.lang != 'thaibt':
                    items.append((self.p[0]+i+1,r['volume'].lstrip(u'0'),r['page'].lstrip(u'0'),r['items'],excerpts))
                else:
                    items.append((self.p[0]+i+1, unicode(r['volume']), unicode(r['page']), u'0', excerpts))
                    
                wx.CallAfter(self.window.UpdateProgress, (i+1)*10)
            dataModel[key] = items
        wx.CallAfter(self.window.DisplayFinished)

class MyHtmlFormatter(object):
    def __init__(self, tagname="strong", attrs="", between="...", classname="match", termclass="term"):
        self.between = between
        self.tagname = tagname
        self.classname = classname
        self.termclass = termclass
        self.attrs = attrs
        
    def _format_fragment(self, text, fragment, seen):
        tagname = self.tagname
        attrs = self.attrs
        htmlclass = " ".join((self.classname, self.termclass))
        
        output = []
        index = fragment.startchar
        
        for t in fragment.matches:
            if t.startchar > index:
                output.append(text[index:t.startchar])
            
            ttxt = htmlescape(text[t.startchar:t.endchar])
            if t.matched:
                if t.text in seen:
                    termnum = seen[t.text]
                else:
                    termnum = len(seen)
                    seen[t.text] = termnum
                ttxt = '<%s %s class="%s%s">%s</%s>' % (tagname, attrs, htmlclass, termnum, ttxt, tagname)
            
            output.append(ttxt)
            index = t.endchar
        
        return "".join(output)
    
    def __call__(self, text, fragments):
        seen = {}
        return self.between.join(self._format_fragment(text, fragment, seen)
                                 for fragment in fragments)
