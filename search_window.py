#-*- coding:utf-8 -*-

import wx
import wx.lib.buttons as buttons
import wx.html

import cPickle, re, os.path, sys, codecs, zipfile

from whoosh.spelling import SpellChecker
from whoosh.filedb.filestore import FileStorage
from whoosh.index import open_dir

from mythread import SearchThread, DisplayThread, dataModel
from mydialog import *
from read_window import ReadingToolFrame, FIVE_BOOKS_TITLES
from utils import arabic2thai,thai2arabic

import manifest

class ResultWindow(wx.html.HtmlWindow):
    """Window Class that overrides HTMLWindow Class"""
    
    def __init__(self, lang, *kw):
        wx.html.HtmlWindow.__init__(self, *kw)
        self.lang = lang
        self.bookFrames = {}
        self.keywords = ''
        self.frameId = {}
        self.clicked_pages = []
        
    def SetLanguage(self, lang):
        self.lang = lang
    
    def SetKeyWords(self, keywords):
        self.keywords = keywords

    def CreateReadingFrame(self, volume, page, lang=None, isCompare=False,hide=False, item=None):
        if lang is None:
            lang = self.lang
        keywords = u''
        if not isCompare:
            keywords = self.keywords
            
        if lang not in self.bookFrames:
            self.frameId[lang] = wx.NewId()
            size,pos = None,None
            if isCompare:
                w,h = wx.GetDisplaySize()
                x = 0
                if 'wxGTK' in wx.PlatformInfo:
                    x = 5 
                size = (w/2)-x,h-30
                if lang == 'thai' or lang == 'thaimm' or lang == 'thaiwn' or lang == 'thaimc' or lang == 'thaibt':
                    pos = (0,0)
                elif isCompare and lang == 'pali':
                    pos = (w/2)+x,0
            self.bookFrames[lang] = ReadingToolFrame(self,self.frameId[lang],
                                                          volume,page,lang=lang, 
                                                          keywords=keywords,size=size,pos=pos)
            self.bookFrames[lang].Show()
            self.bookFrames[lang].Bind(wx.EVT_CLOSE, self.OnFrameClose) 
        else:
            self.bookFrames[lang].SetKeyWords(keywords)
            self.bookFrames[lang].Raise()
            self.bookFrames[lang].Iconize(False)

        # scroll to item position
        scroll_position = 0
        if isCompare and item != None:
            for result in self.bookFrames[lang].GetContent(volume, page):
                content = result['content']
                scroll_position = content.find(u'[%s]'%(arabic2thai(unicode(item))))
                break;

        if lang != 'thaibt' and page == 0:
            self.bookFrames[lang].GenStartPage()
        elif lang != 'thaibt' and page != 0:
            self.bookFrames[lang].GenStartPage()
            self.bookFrames[lang].SetVolumePage(volume,page)
            self.bookFrames[lang].LoadContent(scroll=scroll_position)
        else:
            self.bookFrames[lang].LoadFiveBookContent(volume, page)
            
        if hide:
            self.bookFrames[lang].HideBooks()
        
    def VerticalAlignWindows(self, lang1, lang2):
        if len(self.bookFrames) < 2:
            return
        langs = self.bookFrames.keys()
        w,h = wx.GetDisplaySize()
        x,y = 0,0
        if 'wxGTK' in wx.PlatformInfo:
            x = 5 
        elif 'wxMac' in wx.PlatformInfo:
            y = 30

        if self.bookFrames[lang1].side == None:
            self.bookFrames[lang1].side = 'L'
        elif self.bookFrames[lang1].side == 'L':
            self.bookFrames[lang2].side = 'R'
        elif self.bookFrames[lang1].side == 'R':
            self.bookFrames[lang2].side = 'L'
        
        if self.bookFrames[lang2].side == None:
            self.bookFrames[lang2].side = 'R'

        self.bookFrames[lang1].HideBooks()
        self.bookFrames[lang2].HideBooks()
        self.bookFrames[lang1].SetSize(((w/2)-x,h-30))
        self.bookFrames[lang2].SetSize(((w/2)-x,h-30))

        if self.bookFrames[lang1].side == 'R':
            self.bookFrames[lang1].Move(((w/2)+x,y))
            self.bookFrames[lang2].Move((0,y))
        elif self.bookFrames[lang1].side == 'L':
            self.bookFrames[lang1].Move((0,y))
            self.bookFrames[lang2].Move(((w/2)+x,y))

    def CloseBookFrames(self):
        langs = self.bookFrames.keys()
        for lang in langs:
            self.bookFrames[lang].Close()
        
    def OnFrameClose(self,event):
        found = False
        for lang in self.bookFrames:
            if self.bookFrames[lang].GetId() == event.GetId():
                found = True
                break
        if found:
            self.bookFrames[lang].SaveBookmarks()
            del self.bookFrames[lang]
        event.Skip()
        
    def OnLinkClicked(self,link):
        scrollPos = self.GetScrollPos(wx.VERTICAL)
        href = link.GetHref()
        cmd,body = href.split(':')
        if cmd == 'p':
            volume,page,lang,now,per,total,i = body.split(u'_')
            self.GetParent().AddRead(int(i))
            self.GetParent().UpdateResults(int(now),int(per),int(total))
            self.keywords = self.GetParent().text.GetValue()
            self.CreateReadingFrame(int(volume),int(page),hide=True,lang=lang)
        elif cmd == 's':
            self.GetParent().text.AppendSearch(body)
            self.GetParent().DoFind(body)
        elif cmd == 'n':
            now,per,total = body.split(u'_')
            self.GetParent().now = int(now)
            if int(now) not in self.clicked_pages:
                self.clicked_pages.append(int(now))
            self.GetParent().ProcessPage(int(now),int(per),int(total))
            
        self.ScrollLines(scrollPos)

            
class TipiSearchCtrl(wx.SearchCtrl):
    """
    Text Control for entering user queries that can save search history
    """
    maxSearches = 20 # maximum of search history
    def __init__(self, parent, id=-1, value="",
                 pos=wx.DefaultPosition, size=wx.DefaultSize, style=0,
                 doSearch=None,lang='thai'):
        style |= wx.TE_PROCESS_ENTER
        wx.SearchCtrl.__init__(self, parent, id, value, pos, size, style)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnTextEntered)
        self.Bind(wx.EVT_MENU_RANGE, self.OnMenuItem, id=1, id2=self.maxSearches)
        self.doSearch = doSearch
        self.lang = lang
        self.searches = []

        logFile = os.path.join(sys.path[0],'config','history.log')
        if os.path.exists(logFile):
            for text in codecs.open(logFile,'r','utf-8').readlines():
                if text.strip() == '': continue 
                self.searches.append(text.strip())
                if len(self.searches) > self.maxSearches:
                    del self.searches[0]
            menu = self.MakeMenu()
            self.SetMenu(menu)

    def OnTextEntered(self, evt):
        text = self.GetValue().strip()
        if self.doSearch(text):
            self.AppendSearch(text)

    def AppendSearch(self, text):
        if text.strip() != u'':
            if text not in self.searches:
                self.searches.append(text)
            if len(self.searches) > self.maxSearches:
                del self.searches[0]
            self.SetMenu(self.MakeMenu())

    def OnMenuItem(self, evt):
        text = self.searches[evt.GetId()-1]
        self.SetValue(text)
        self.doSearch(text)
        
    def MakeMenu(self):
        font = wx.Font(13, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        font.SetFaceName('TF Chiangsaen')
        menu = wx.Menu()
        
        #append header
        item = wx.MenuItem(menu,-1,u'คำค้นหาล่าสุด')
        item.SetFont(font)
        item.Enable(False)
        menu.AppendItem(item)

        for idx, txt in enumerate(self.searches):
            item = wx.MenuItem(menu,1+idx,txt)
            item.SetFont(font)
            menu.AppendItem(item)
        return menu
        
    def SaveSearches(self):
        out = codecs.open(os.path.join(sys.path[0],'config','history.log'),'w','utf-8')
        for search in self.searches:
            if self.lang == 'pali':
                search = search.replace(u'ฐ',u'\uf700').replace(u'ญ',u'\uf70f').replace(u'\u0e4d',u'\uf711')
            out.write(u'%s\n'%(search))
        out.close()
        
    def SetLanguage(self,lang):
        self.lang = lang
        
    def GetLanguage(self):
        return self.lang
        

class SearchToolFrame(wx.Frame):
    """Frame Class that displays results"""
    
    def __init__(self):
        wx.Frame.__init__(self, parent=None, id=-1, 
            title=u'โปรแกรมตรวจหาและเทียบเคียงพุทธวจนจากพระไตรปิฎก (E-Tipitaka %s)'%(manifest.__version__),size=(1000,700))

        icon = wx.IconBundle()
        icon.AddIconFromFile(os.path.join(sys.path[0],'resources','e-tri_64_icon.ico'), wx.BITMAP_TYPE_ANY)
        self.SetIcons(icon)

        self.now = 0
        self.total = 0
        self.pages = 0
        self.per = 10
        self.lang = 'thai'
        self.mode = 'all'
        self.speller = {}
        self.checkedItems = range(45)
        self.read = []
        self.wildcard = u'E-Tipitaka Backup File (*.etz)|*.etz'

        for lang in ['thai','pali']:
            st = FileStorage(os.path.join(sys.path[0],'spell_%s'%(lang)))
            self.speller[lang] = SpellChecker(st)

        f = open(os.path.join(sys.path[0],'resources','book_name.pkl'),'rb')
        self.bookNames = cPickle.load(f)
        f.close()
 
        self.resultWindow = ResultWindow(self.lang,self)

        self.font = self.LoadFont()
        if self.font != None and self.font.IsOk():
            self.resultWindow.SetStandardFonts(self.font.GetPointSize(),self.font.GetFaceName())                    

        self.statusBar = self.CreateMyStatusBar()
        self.topSizer = self.CreateSearchBar()

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.topSizer,flag=wx.EXPAND)
        self.sizer.Add(self.resultWindow,1,flag=wx.EXPAND)
        self.SetSizer(self.sizer)
    
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        
    def CreateMyStatusBar(self):
        statusBar = self.CreateStatusBar()
        statusBar.SetFieldsCount(4)
        statusBar.SetStatusWidths([-1,170,170,100])
        self.progress = wx.Gauge(statusBar, -1, 100,size=(100,-1))
        self.progress.SetBezelFace(3)
        self.progress.SetShadowWidth(3)
        statusBar.Bind(wx.EVT_SIZE, self.OnSize)  
        return statusBar      
        
    def CreateSearchBar(self):
        panel = wx.Panel(self,-1)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        
        self.text = TipiSearchCtrl(panel, -1,size=(-1,-1),doSearch=self.DoFind)
        if 'wxMac' not in wx.PlatformInfo and self.font != None and self.font.IsOk():
            font = self.font
            font.SetPointSize(16)
            self.text.SetFont(font)
        else:
            font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL, False, u'')   
            self.text.SetFont(font)
    
        #langs = [u'ไทย (บาลีสยามรัฐ)',u'บาลี (บาลีสยามรัฐ)',u'ไทย (มหามกุฏฯ)',u'ไทย (วัดนาป่าพง)',u'ไทย (มหาจุฬาฯ)']
        #langs = [u'ไทย (บาลีสยามรัฐ)',u'บาลี (บาลีสยามรัฐ)',u'ไทย (มหามกุฏฯ)',u'ไทย (มหาจุฬาฯ)']
        
        langs = [u'ไทย (ฉบับหลวง)',u'บาลี (สยามรัฐ)',u'ไทย (มหามกุฏฯ)',u'ไทย (มหาจุฬาฯ)',u'ไทย (จากพระโอษฐ์ ๕ เล่ม)']
        
        langPanel = wx.Panel(panel,-1)
        langSizer = wx.StaticBoxSizer(wx.StaticBox(langPanel, -1, u'ภาษา'), orient=wx.HORIZONTAL)
        self.comboLang = wx.ComboBox(langPanel,-1,choices=langs,style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.comboLang.SetStringSelection(langs[0])
        langSizer.Add(self.comboLang)
        langPanel.SetSizer(langSizer)

        self.comboLang.Bind(wx.EVT_COMBOBOX,self.OnSelectLanguage)

        books = [u'ทั้งหมด',u'กำหนดเอง']
        self.radio2 = wx.RadioBox(panel,-1,u'เล่มที่ต้องการค้นหา',choices=books, majorDimension=2)
        self.radio2.Bind(wx.EVT_RADIOBOX,self.OnSelectBook)
        
        sorting = [u'คะแนน',u'เลขหน้า']
        self.radio3 = wx.RadioBox(panel,-1,u'เรียงลำดับคำตอบ',choices=sorting, majorDimension=2)
        self.radio3.Bind(wx.EVT_RADIOBOX,self.OnSelectSorting)
        self.radio3.Hide()
        
        matching = [u'ทั้งหมด',u'ส่วนหน้า',u'บางส่วน']
        self.radio4 = wx.RadioBox(panel,-1,u'ความเหมือนในการจับคู่คำ',choices=matching, majorDimension=3)
        self.radio4.Bind(wx.EVT_RADIOBOX,self.OnSelectMatching)
        self.radio4.Disable()
        self.radio4.Hide()

        searchIcon = wx.Image(os.path.join(sys.path[0],'resources','search.png'),wx.BITMAP_TYPE_PNG).Scale(16,16)
        self.btnFind = buttons.GenBitmapTextButton(panel,-1,wx.BitmapFromImage(searchIcon),u'ค้นหา',size=(65,35))
        self.btnFind.Bind(wx.EVT_BUTTON, self.OnClickFind)
                
        symbolPanel = wx.Panel(panel,-1)       
        symbolSizer = wx.StaticBoxSizer(wx.StaticBox(symbolPanel, -1, u'อักษรพิเศษ'), orient=wx.HORIZONTAL)
        nikhahitIcon = wx.Image(os.path.join(sys.path[0],'resources','nikhahit.gif'),wx.BITMAP_TYPE_GIF).Scale(16,16)
        self.btnNikhahit = wx.BitmapButton(symbolPanel, -1, wx.BitmapFromImage(nikhahitIcon))         

        thothanIcon = wx.Image(os.path.join(sys.path[0],'resources','thothan.gif'),wx.BITMAP_TYPE_GIF).Scale(16,16)
        self.btnThoThan = wx.BitmapButton(symbolPanel, -1, wx.BitmapFromImage(thothanIcon))                 
        
        yoyingIcon = wx.Image(os.path.join(sys.path[0],'resources','yoying.gif'),wx.BITMAP_TYPE_GIF).Scale(16,16)
        self.btnYoYing = wx.BitmapButton(symbolPanel, -1, wx.BitmapFromImage(yoyingIcon))         

        symbolSizer.Add(self.btnNikhahit)
        symbolSizer.Add(self.btnThoThan)
        symbolSizer.Add(self.btnYoYing)
        symbolPanel.SetSizer(symbolSizer)

        fontsIcon = wx.Image(os.path.join(sys.path[0],'resources','fonts.png'),wx.BITMAP_TYPE_PNG)
        self.btnFonts = wx.BitmapButton(panel, -1, wx.BitmapFromImage(fontsIcon),size=(-1,40))
        self.btnFonts.SetToolTip(wx.ToolTip(u'เปลี่ยนรูปแบบตัวหนังสือ'))

        self.btnFonts.Bind(wx.EVT_BUTTON, self.OnClickFonts)
        self.btnNikhahit.Bind(wx.EVT_BUTTON, self.OnClickNikhahit)
        self.btnThoThan.Bind(wx.EVT_BUTTON, self.OnClickThoThan)
        self.btnYoYing.Bind(wx.EVT_BUTTON, self.OnClickYoYing)

        leftIcon = wx.Image(os.path.join(sys.path[0],'resources','left.png'),wx.BITMAP_TYPE_PNG).Scale(32,32)
        self.btnPrev = wx.BitmapButton(panel, -1, wx.BitmapFromImage(leftIcon)) 
        rightIcon = wx.Image(os.path.join(sys.path[0],'resources','right.png'),wx.BITMAP_TYPE_PNG).Scale(32,32)
        self.btnNext = wx.BitmapButton(panel, -1, wx.BitmapFromImage(rightIcon))
        
        importIcon = wx.Image(os.path.join(sys.path[0],'resources','import.png'),wx.BITMAP_TYPE_PNG).Scale(32,32)
        self.btnImport = wx.BitmapButton(panel, -1, wx.BitmapFromImage(importIcon)) 
        self.btnImport.SetToolTip(wx.ToolTip(u'นำข้อมูลส่วนตัวเข้า'))
        exportIcon = wx.Image(os.path.join(sys.path[0],'resources','export.png'),wx.BITMAP_TYPE_PNG).Scale(32,32)
        self.btnExport = wx.BitmapButton(panel, -1, wx.BitmapFromImage(exportIcon))         
        self.btnExport.SetToolTip(wx.ToolTip(u'นำข้อมูลส่วนตัวออก'))
        
        self.btnImport.Bind(wx.EVT_BUTTON, self.OnClickImport)
        self.btnExport.Bind(wx.EVT_BUTTON, self.OnClickExport)        
        
        bookIcon = wx.Image(os.path.join(sys.path[0],'resources','books.png'),wx.BITMAP_TYPE_PNG).Scale(32,32)
        self.btnRead = buttons.GenBitmapTextButton(panel,-1,wx.BitmapFromImage(bookIcon),u'อ่านพระไตรปิฎก',size=(-1,40))
        
        self.btnNext.Bind(wx.EVT_BUTTON, self.OnClickNext)
        self.btnPrev.Bind(wx.EVT_BUTTON, self.OnClickPrev)
        self.btnRead.Bind(wx.EVT_BUTTON, self.OnClickRead)
        self.btnNext.Disable()
        self.btnPrev.Disable()
        
        self.btnAbout = wx.Button(panel, -1, u'เกี่ยวกับโปรแกรม',size=(-1, -1))        
        self.btnAbout.SetToolTip(wx.ToolTip(u'เกี่ยวกับโปรแกรม E-Tipitaka'))        
        self.btnAbout.Bind(wx.EVT_BUTTON, self.OnClickAbout)
        
        sizer1.Add(symbolPanel,flag=wx.ALIGN_CENTER)
        sizer1.Add(self.btnFonts,flag=wx.ALIGN_CENTER)
        sizer1.Add((5,5))
        sizer1.Add(self.text,1,wx.ALIGN_CENTER|wx.RIGHT, 3)
        sizer1.Add(self.btnFind,flag=wx.ALIGN_CENTER)
        sizer1.Add((5,5))
        sizer1.Add(self.btnAbout, 0, flag=wx.ALIGN_CENTER)
        
        sizer2.Add(self.btnRead,flag=wx.ALIGN_BOTTOM)
        sizer2.Add((5,5))
        sizer2.Add(langPanel,flag=wx.ALIGN_BOTTOM | wx.EXPAND)
        sizer2.Add(self.radio4,flag=wx.ALIGN_BOTTOM | wx.EXPAND)
        sizer2.Add(self.radio2,flag=wx.ALIGN_BOTTOM | wx.EXPAND)
        sizer2.Add(self.radio3,flag=wx.ALIGN_BOTTOM | wx.EXPAND)
        sizer2.Add((5,5))
        
        sizer2.Add(self.btnPrev,flag=wx.ALIGN_BOTTOM | wx.SHAPED)    
        sizer2.Add(self.btnNext,flag=wx.ALIGN_BOTTOM | wx.SHAPED)

        sizer2.Add((20,-1), 0)
        
        sizer2.Add(self.btnExport,flag=wx.ALIGN_BOTTOM | wx.SHAPED)
        sizer2.Add(self.btnImport,flag=wx.ALIGN_BOTTOM | wx.SHAPED)    
        
        mainSizer.Add(sizer1,1,flag=wx.EXPAND)
        mainSizer.Add(sizer2,1,flag=wx.EXPAND)
        
        panel.SetSizer(mainSizer)

        if 'wxMac' in wx.PlatformInfo:
            symbolPanel.Hide()
        
        return panel
        
    def OnClickNikhahit(self, event):
        text = self.text.GetValue()
        ins = self.text.GetInsertionPoint()
        text = text[:ins] + u'\uf711' + text[ins:]
        self.text.SetValue(text)
        self.text.SetFocus()
        self.text.SetInsertionPoint(ins+1)
        event.Skip()
        
    def OnClickThoThan(self, event):
        text = self.text.GetValue()
        ins = self.text.GetInsertionPoint()
        text = text[:ins] + u'\uf700' + text[ins:]
        self.text.SetValue(text)
        self.text.SetFocus()
        self.text.SetInsertionPoint(ins+1)
        event.Skip()
        
    def OnClickYoYing(self, event):
        text = self.text.GetValue()
        ins = self.text.GetInsertionPoint()
        text = text[:ins] + u'\uf70f' + text[ins:]
        self.text.SetValue(text)
        self.text.SetFocus()
        self.text.SetInsertionPoint(ins+1)
        event.Skip()
        
    def OnClickFonts(self, event):
        curFont = self.LoadFont()
        fontData = wx.FontData()
        fontData.EnableEffects(False)
        fontData.SetInitialFont(curFont)
        dialog = wx.FontDialog(self,fontData)
        if dialog.ShowModal() == wx.ID_OK:
            data = dialog.GetFontData()
            font = data.GetChosenFont()
            if font.IsOk():
                self.SaveFont(font)
                self.font = font
                if 'wxMac' not in wx.PlatformInfo:
                    size = font.GetPointSize()
                    font.SetPointSize(16)
                    self.text.SetFont(font)
                    font.SetPointSize(size)
                self.resultWindow.SetStandardFonts(font.GetPointSize(),font.GetFaceName())
        dialog.Destroy()
        event.Skip()

    def SaveFont(self,font):
        t = u'%s,%d,%d,%d,%d'%(font.GetFaceName(),font.GetFamily(),font.GetStyle(),font.GetWeight(),font.GetPointSize())
        codecs.open(os.path.join(sys.path[0],'config','font_search.log'),'w','utf8').write(t)        
        
    def LoadFont(self):
        font = None
        if os.path.exists(os.path.join(sys.path[0],'config','font_search.log')):
            tokens = codecs.open(os.path.join(sys.path[0],'config','font_search.log'),'r','utf8').read().split(',')
            if len(tokens) == 5:
                font = wx.Font(int(tokens[4]),int(tokens[1]),int(tokens[2]),int(tokens[3]))
                font.SetFaceName(tokens[0])
                return font
        return font

        
    def UpdateResults(self,now,per,total):
        text = u''
        label1 = u'พระไตรปิฎก เล่มที่'
        label2 = u'หน้าที่'
        
        p2 = now * per
        p1 = p2 - per
        
        pages = total/per
        if total % 10:
            pages += 1
        
        if p2 > total:
            p2 = total

        if p1 >= 0:            
            key = '%d:%d'%(p1,p2)
            for i,vol,page,items,excerpts in dataModel[key]:
                labelItems = items.split()
                if len(items.split()) == 1:
                    labelItems = labelItems[0]
                else:
                    labelItems = u'%s - %s'%(labelItems[0],labelItems[-1])
                read = u''
                if i in self.read:
                    read = u'(อ่านแล้ว)'

                if int(vol) <= 8:
                    ccode ="#1e90ff"
                elif int(vol) <= 33:
                    ccode ="#ff4500"
                else:
                    ccode ="#a020f0"

                if self.lang != 'thaibt':
                    bookname = self.bookNames['%s_%s'%(self.lang,vol.encode('utf8','ignore'))].decode('utf8','ignore')
                    html_item = u'<font size="4" color="%s">%s ข้อที่ %s</font>'%(ccode, bookname, arabic2thai(labelItems))
                else:
                    bookname, html_item = u'', u''
                
                html_excerpts = u'<font size="4">%s</font><br>'%(excerpts) 
                if self.lang != 'thaibt':
                    entry = u'%s. %s %s %s %s' % (arabic2thai(unicode(i)),label1,arabic2thai(vol),label2,arabic2thai(page))
                else:
                    entry = u'%s. %s %s %s' % (arabic2thai(unicode(i)), FIVE_BOOKS_TITLES[int(vol)-1], label2, arabic2thai(page))
                    
                html_entry = u'''
                    <font size="4">
                        <a href="p:%s_%s_%s_%d_%d_%d_%d">%s</a>
                        <font color="red">%s</font><br>
                    </font>
                '''%(vol,page,self.lang,now,per,total,i,entry,read)
                text += u'<div>' + html_entry + html_excerpts + html_item + u'</div><br>'
                 
            keywords = self.keywords
            if self.lang == 'pali':
                keywords = self.keywords.replace(u'ฐ',u'\uf700').replace(u'ญ',u'\uf70f').replace(u'\u0e4d',u'\uf711')
            keywords = ' '.join(filter(lambda x:x.find('v:') != 0, keywords.split()))
                
            # Add more info about hit pages
            v_pages = self.group_results[0]
            s_pages = self.group_results[1]
            a_pages = self.group_results[2]
            
            if self.lang != 'thaibt':
                info = u'''
                    <div align="center">
                        <table cellpadding="0">
                            <tr>
                                <th align="center"><b><font color="#1e90ff">พระวินัยฯ</font></b></th>
                                <th>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th>
                                <th align="center"><b><font color="#ff4500">พระสุตตันตฯ</font></b></th>
                                <th>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th>
                                <th align="center"><b><font color="#a020f0">พระอภิธรรมฯ</font></b></th>                                                        
                            </tr>
                            <tr>
                                <td align="center">%s หน้า</td>
                                <td>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</td>                            
                                <td align="center">%s หน้า</td>
                                <td>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</td>                            
                                <td align="center">%s หน้า</td>                                                                                
                            </tr>
                        </table>
                    </div><br/><p/>
                ''' % (arabic2thai(unicode(v_pages)),arabic2thai(unicode(s_pages)),arabic2thai(unicode(a_pages)))
            else:
                info = u''
                
            header = u'''
                <div align="center">
                    <font size="3" color="brown">ผลการค้นหา %d - %d จากทั้งหมด %d หน้า สำหรับคำว่า "%s"</font>
                </div>''' % (p1+1,p2,self.total,keywords)
                
            suggests = self.DoSuggest(self.keywords)
            hint = u''
            if suggests != []:
                hint = u'<br><br><div align="right"><font size="3" color="red">หรือคุณหมายถึง: %s</font></div><br>'%(self.MakeUpSuggests(suggests))
            select_pages = self.MakeUpSelectPages(self.pages,now,per,total)
            self.resultWindow.SetPage(info + arabic2thai(header) + hint + text + '<br>' + select_pages)
            self.statusBar.SetStatusText(u'ผลการค้นหา %d - %d'%(p1+1,p2), 2)
            
        if now == 1:
            self.btnPrev.Disable()          
        if now == pages:
            self.btnNext.Disable()
        if now > 1:
            self.btnPrev.Enable()
        if now < pages:
            self.btnNext.Enable()
            
    def UpdateProgress(self, count):
        self.progress.SetValue(count)
        
    def QueryStarted(self):
        dataModel.clear()
        self.btnFind.Disable()
        self.btnFind.Refresh()
        self.btnNext.Disable()
        self.btnNext.Refresh()
        self.btnPrev.Disable()
        self.btnPrev.Refresh()
        label = u'โปรแกรมกำลังค้นหาข้อมูล'
        self.resultWindow.SetPage(u'โปรแกรมกำลังค้นหาข้อมูล กรุณารอซักครู่...')
        self.statusBar.SetStatusText(u'%s'%(label),0)
        self.statusBar.SetStatusText(u'',1)
        self.statusBar.SetStatusText(u'',2)
        
    def QueryFinished(self, results):
        self.results = results
        self.group_results = [0,0,0]
        for result in self.results:
            volume = int(result['volume'])
            if volume <= 8:
                self.group_results[0] += 1
            elif volume <= 33:
                self.group_results[1] += 1
            else:
                self.group_results[2] += 1
        
        self.total = len(self.results)        
        self.pages = self.total/self.per
        if self.total%10:
            self.pages += 1
        self.now = 1
        if self.total == 0:
            self.btnFind.Enable()
            self.now = 0
                    
        #Update status bar
        self.statusBar.SetStatusText(u'',0)
        label1 = u'ค้นเจอทั้งหมด'
        label2 = u'หน้า'
        self.statusBar.SetStatusText('%s %d %s'%(label1,self.total,label2), 1)
        p1,p2 = 0,self.per
        if self.total < self.per:
            p2 = self.total
        #Start the first display
        if self.total > 0:
            thread = DisplayThread(self.results,self.lang,self.keywords,self,(p1,p2))
            thread.start()
        else:
            text1 = ''
            if self.lang == 'thai':
                tmp = u'ไทย'
                text1 = u'<div align="center"><h2>ไม่พบคำว่า "%s" ในพระไตรปิฎก (ภาษา%s ฉบับหลวง)</h2></div>'%(self.text.GetValue(),tmp)
            elif self.lang == 'pali':
                tmp = u'บาลี'
                text1 = u'<div align="center"><h2>ไม่พบคำว่า "%s" ในพระไตรปิฎก (ภาษา%s ฉบับสยามรัฐ)</h2></div>'%(self.text.GetValue(),tmp)
            elif self.lang == 'thaimm':
                text1 = u'<div align="center"><h2>ไม่พบคำว่า "%s" ในพระไตรปิฎก (ภาษาไทย ฉบับมหามกุฏฯ)</h2></div>'%(self.text.GetValue())
            elif self.lang == 'thaiwn':
                text1 = u'<div align="center"><h2>ไม่พบคำว่า "%s" ในพระไตรปิฎก (ภาษาไทย ฉบับวัดนาป่าพง)</h2></div>'%(self.text.GetValue())
            elif self.lang == 'thaimc':
                text1 = u'<div align="center"><h2>ไม่พบคำว่า "%s" ในพระไตรปิฎก (ภาษาไทย ฉบับมหาจุฬาฯ)</h2></div>'%(self.text.GetValue())
            elif self.lang == 'thaibt':
                text1 = u'<div align="center"><h2>ไม่พบคำว่า "%s" ใน ๕ เล่มจากพระโอษฐ์ (ภาษาไทย ฉบับท่านพุทธทาส)</h2></div>'%(self.text.GetValue())


            suggests = self.DoSuggest(self.keywords)
            text2 = u''
            if suggests != []:
                text2 = u'<div align="left">หรือคุณหมายถึง: %s</div>'%(self.MakeUpSuggests(suggests))
            keywords = self.text.GetValue().strip()
            if keywords != u'':
                
                self.resultWindow.SetPage(text1+text2)
            else:
                self.resultWindow.SetPage(u'<div align="center"><h2>คุณยังไม่ได้ใส่คำค้นหา</h2></div>')

    def MakeUpSuggests(self, suggests):
        text = u''
        for suggest in suggests:
            if self.lang == 'pali':
                suggest = suggest.replace(u'ฐ',u'\uf700').replace(u'ญ',u'\uf70f').replace(u'\u0e4d',u'\uf711')
            text += u'<a href="s:%s">%s</a> '%(suggest,suggest)
        return text
                
    def DoSuggest(self, keywords):
        keywords = keywords.replace('+',' ')
        if len(keywords.split()) > 1:
            return []
        if self.lang == u'thaimm' or self.lang == u'thaiwn' or self.lang == u'thaimc' or self.lang == u'thaibt':
            return self.speller['thai'].suggest(keywords,number=5)
        return self.speller[self.lang].suggest(keywords,number=5)
    
    def MakeUpSelectPages(self, pages, now, per, total):
        text = u'ผลการค้นหาทั้งหมด<br>'
        for i in range(1,pages+1):
            thai_num = arabic2thai(unicode(i))
            if i != now:
                if i in self.resultWindow.clicked_pages:
                    text += u'<b><i><a href="n:%d_%d_%d">%s</a></i></b> '%(i,per,total,thai_num)
                else:
                    text += u'<a href="n:%d_%d_%d">%s</a> '%(i,per,total,thai_num)
            else:
                text += u'<b>%s</b> '%(thai_num)

        return '<div align="center">' + text + '</div>'
    
    def DisplayStarted(self):
        label = u'โปรแกรมกำลังจัดแสดงข้อมูล'
        self.resultWindow.SetPage(u'')
        self.statusBar.SetStatusText(u'%s'%(label),0)
        self.btnFind.Disable()
        self.btnFind.Refresh()
        self.btnNext.Disable()
        self.btnNext.Refresh()
        self.btnPrev.Disable()
        self.btnPrev.Refresh()

    
    def DisplayFinished(self):
        self.btnFind.Enable()
        self.btnFind.Refresh()
        self.btnNext.Enable()
        self.btnNext.Refresh()
        self.btnPrev.Enable()
        self.btnPrev.Refresh()
        self.UpdateResults(self.now,self.per,self.total)
        self.progress.SetValue(0)
        self.statusBar.SetStatusText(u'',0)
        self.text.SetInsertionPointEnd()

    def DoFind(self, keywords):
        if keywords.replace('+',' ').strip() == '':
            return True

        self.resultWindow.clicked_pages = [1]
        self.read = []
        self.text.SetValue(keywords)
        
        if self.comboLang.GetSelection() == 0:
            self.lang = 'thai'
            self.keywords = keywords
        elif self.comboLang.GetSelection() == 1:
            self.lang = 'pali'
            if 'wxMac' not in wx.PlatformInfo:
                self.keywords = keywords.replace(u'\uf700',u'ฐ').replace(u'\uf70f',u'ญ').replace(u'\uf711',u'\u0e4d')
            else:
                self.keywords = keywords
        elif self.comboLang.GetSelection() == 2:
            self.lang = 'thaimm'
            self.keywords = keywords
        elif self.comboLang.GetSelection() == 3:
            self.lang = 'thaimc'
            self.keywords = keywords
        elif self.comboLang.GetSelection() == 4:
            self.lang = 'thaibt'
            self.keywords = keywords
        elif self.comboLang.GetSelection() == 5:
            self.lang = 'thaiwn'
            self.keywords = keywords
        
        self.resultWindow.SetLanguage(self.lang)
        self.resultWindow.SetKeyWords(self.keywords)

        thread = SearchThread(self.lang,'content',self.keywords,self.checkedItems,self)
        thread.start()

        return True
        
    def AddRead(self,i):
        self.read.append(i)
                
    def OnSize(self,event):
        rect = self.statusBar.GetFieldRect(3)
        self.progress.SetRect(rect)
    
    def ProcessPage(self,now,per,total):
        p2 = now * per
        p1 = p2 - per
        if p2 > total:
            p2 = total
        key = '%d:%d'%(p1,p2)
        if key not in dataModel:
            thread = DisplayThread(self.results,self.lang,self.keywords,self,(p1,p2))
            thread.start()
        else:
            self.UpdateResults(now,per,total)         
    
    def OnClickNext(self, event):
        if self.pages > 0:
            if self.now < self.pages:
                self.now += 1   
            self.ProcessPage(self.now, self.per, self.total)
            
    def OnClickPrev(self, event):
        if self.pages > 0:
            if self.now > 1:
                self.now -= 1
            self.ProcessPage(self.now, self.per, self.total)
    
    def OnClickFind(self, event):
        keywords = self.text.GetValue().strip()
        self.text.AppendSearch(keywords)
        self.DoFind(keywords)

    def OnClickRead(self, event):
        if self.comboLang.GetSelection() == 0:
            self.lang = 'thai'
        elif self.comboLang.GetSelection() == 1:
            self.lang = 'pali'
        elif self.comboLang.GetSelection() == 2:
            self.lang = 'thaimm'
        elif self.comboLang.GetSelection() == 3:
            self.lang = 'thaimc'
        elif self.comboLang.GetSelection() == 4:
            self.lang = 'thaibt'

        self.resultWindow.SetLanguage(self.lang)
        self.resultWindow.SetKeyWords('')

        if self.lang == 'thaibt':
            self.resultWindow.CreateReadingFrame(1,1)
        else:
            self.resultWindow.CreateReadingFrame(1,0)
            
        event.Skip()

    def OnClickAbout(self, event):
        x,y = self.GetScreenPosition()
        dialog = AboutDialog(self,pos=(x+5,y+67))
        dialog.ShowModal()
        dialog.Destroy()
        
    def OnSelectBook(self, event):
        if self.radio2.GetSelection() == 0:
            self.mode = 'all'
            if self.lang == 'thaimm':
                self.checkedItems = range(91)
            else:
                self.checkedItems = range(45)
        else:
            self.mode = 'partial'
            dialog = SelectBooksDialog(self.checkedItems, self.lang)
            result = dialog.ShowModal()
            if result == wx.ID_OK:
                self.checkedItems = dialog.GetCheckedItems()
            else:
                self.radio2.SetSelection(0)
                self.mode = 'all'
            dialog.Destroy()
        event.Skip()

    def OnSelectLanguage(self, event):
        if self.comboLang.GetSelection() == 1:
            self.text.SetLanguage('pali')
            self.lang = 'pali'
            self.checkedItems = range(45)
            self.radio2.SetSelection(0)
            self.radio2.Enable()
            self.radio4.Enable()
        elif self.comboLang.GetSelection() == 0:
            self.text.SetLanguage('thai')
            self.lang = 'thai'
            self.checkedItems = range(45)
            self.radio2.SetSelection(0)
            self.radio2.Enable()
            self.radio4.Disable()
        elif self.comboLang.GetSelection() == 2:    
            self.text.SetLanguage('thaimm')
            self.lang = 'thaimm'
            self.checkedItems = range(91)
            self.radio2.SetSelection(0)
            self.radio2.Enable()
            self.radio4.Disable()
        elif self.comboLang.GetSelection() == 3:    
            self.text.SetLanguage('thaimc')
            self.lang = 'thaimc'
            self.checkedItems = range(45)
            self.radio2.SetSelection(0)
            self.radio2.Enable()
            self.radio4.Disable()
        elif self.comboLang.GetSelection() == 4:    
            self.text.SetLanguage('thaibt')
            self.lang = 'thaibt'
            self.checkedItems = range(45)
            self.radio2.SetSelection(0)
            self.radio2.Disable()
            self.radio4.Disable()
        elif self.comboLang.GetSelection() == 5:    
            self.text.SetLanguage('thaiwn')
            self.lang = 'thaiwn'
            self.checkedItems = range(5)
            self.radio2.SetSelection(0)
            self.radio2.Enable()
            self.radio4.Disable()

        event.Skip()

    def OnSelectSorting(self, event):
        event.Skip()
        
    def OnSelectMatching(self, event):
        if self.radio4.GetSelection() == 2:
            dialog = WarningDialog(self,u'การค้นหาแบบนี้จะใช้เวลาในการค้นนานกว่าปกติ',
                                   u'คุณต้องการจะเลือกการค้นหาแบบนี้หรือไม่?',
                                   u'เลือก',u'ไม่เลือก',size=(300,110))
            result = dialog.ShowModal()
            if result != wx.ID_OK:
                self.radio4.SetSelection(0)
            dialog.Destroy()
        event.Skip()
        
    def OnClickImport(self, event):
        dialog = wx.FileDialog(self, u'เลือกไฟล์ข้อมูลส่วนตัว', os.path.expanduser("~"),
            '', self.wildcard, wx.OPEN|wx.CHANGE_DIR)
        if dialog.ShowModal() == wx.ID_OK:
            self.resultWindow.CloseBookFrames()
            with zipfile.ZipFile(os.path.join(dialog.GetDirectory(), dialog.GetFilename()), 'r') as fz:
                fz.extractall(os.path.join(sys.path[0],'config'))
            wx.MessageBox(u'นำข้อมูลส่วนตัวเข้าสำเร็จ', u'E-Tipitaka')
        dialog.Destroy()

    def OnClickExport(self, event):
        from datetime import datetime
        
        zip_file = 'backup-%s.etz' % (datetime.now().strftime('%Y-%m-%d'))
        dialog = wx.FileDialog(self, u'บันทึกข้อมูลส่วนตัว', os.path.expanduser("~"), 
            zip_file, self.wildcard, wx.SAVE | wx.OVERWRITE_PROMPT)        
        if dialog.ShowModal() == wx.ID_OK:
            config_dir = os.path.join(sys.path[0],'config')
            with zipfile.ZipFile(os.path.join(dialog.GetDirectory(), dialog.GetFilename()), 'w') as fz:
                for config_file in map(lambda x: os.path.join(config_dir, x), os.listdir(config_dir)):
                    fz.write(config_file, os.path.split(config_file)[-1])
            wx.MessageBox(u'นำข้อมูลส่วนตัวออกสำเร็จ', u'E-Tipitaka')
        dialog.Destroy()
        
    def OnClose(self, event):
        self.text.SaveSearches()
        self.resultWindow.CloseBookFrames()
        event.Skip()
        
