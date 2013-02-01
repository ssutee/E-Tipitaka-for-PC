#-*- coding:utf8 -*-

import sys, re
import cgi

def thai2arabic(number):
    assert isinstance(number, unicode), "%r is not unicode" % (number)
    d_tha = u'๐๑๒๓๔๕๖๗๘๙'
    d_arb = u'0123456789'
    result = ''
    for c in number:
        if c in d_tha:
            result += d_arb[d_tha.find(c)]
        else:
            result += c
    return result

def arabic2thai(number):
    assert isinstance(number, unicode), "%r is not unicode" % (number)
    d_tha = u'๐๑๒๓๔๕๖๗๘๙'
    d_arb = u'0123456789'
    result = ''
    for c in number:
        if c in d_arb:
            result += d_tha[d_arb.find(c)]
        else:
            result += c
    return result
    

def parse(data):
    title = re.findall('<FONT class=head1>(.+?)</font>',data,re.S)[0]

    p = data.find('<TABLE width=90')
    x = re.findall('<DIV class=e>(.+?)</DIV>',data[p:],re.S)

    
    ret = re.findall('<pre>(.+?)</center><br>',x[0],re.S)
    if len(ret) != 1:
        content = ''
    else:
        content = ret[0]
        content = re.sub('</?[a|center|u].*?>','',content).strip()

    meta = re.findall('<u>(.+?)</u>',x[0],re.S)[0]

    title = title.strip().split('\r\n')
    x = title[0].split()

    volumn,book_name,sub_volumn = thai2arabic(x[2]),x[3],thai2arabic(x[5])
    scroll_name = title[1]
    lines = thai2arabic(re.findall('บรรทัดที่ (.+?)\.',meta.strip(),re.S)[0].strip())
    pages = thai2arabic(re.findall('หน้าที่ (.+?)\.',meta.strip(),re.S)[0].strip())

    return dict(content=content.decode('utf8','ignore'),volumn=volumn,
                book_name=book_name.decode('utf8','ignore'),sub_volumn=sub_volumn,
                scroll_name=scroll_name.decode('utf8','ignore'),lines=lines,pages=pages)

re_string = re.compile(r'(?P<htmlchars>[<&>])|(?P<space>^[ \t]+)|(?P<lineend>\r\n|\r|\n)|(?P<protocal>(^|\s)((http|ftp)://.*?))(\s|$)', re.S|re.M|re.I)
def plaintext2html(text, tabstop=4):
    def do_sub(m):
        c = m.groupdict()
        if c['htmlchars']:
            return cgi.escape(c['htmlchars'])
        if c['lineend']:
            return '<br>'
        elif c['space']:
            t = m.group().replace('\t', '&nbsp;'*tabstop)
            t = t.replace(' ', '&nbsp;')
            return t
        elif c['space'] == '\t':
            return ' '*tabstop;
        else:
            url = m.group('protocal')
            if url.startswith(' '):
                prefix = ' '
                url = url[1:]
            else:
                prefix = ''
            last = m.groups()[-1]
            if last in ['\n', '\r', '\r\n']:
                last = '<br>'
            return '%s<a href="%s">%s</a>%s' % (prefix, url, url, last)
    return re.sub(re_string, do_sub, text)
