#-*- coding:utf-8 -*-

import wx
from wx.html import HtmlEasyPrinting

import sqlite3, cPickle, re, os.path, sys, codecs, json
from xml.etree.ElementTree import Element, ElementTree

from utils import arabic2thai,thai2arabic
from mydialog import *
from dictionary_window import DictWindow        

class ReferenceWindow(wx.html.HtmlWindow):    
            
    def OnLinkClicked(self, link):
        href = link.GetHref()
        dlg = wx.SingleChoiceDialog(self.Parent, 'เลือกภาษา', 'พระไตรปิฎกฉบับหลวง', [u'ไทย', u'บาลี'], wx.CHOICEDLG_STYLE)
        dlg.Center()
        if dlg.ShowModal() == wx.ID_OK:
            tokens = href.split('/')
            volume = thai2arabic(tokens[0])
            item = thai2arabic(re.split(r'[\-,\w]', tokens[2])[0])
            if hasattr(self, 'Delegate') and hasattr(self.Delegate, 'OnLinkToReference'):
                self.Delegate.OnLinkToReference(
                    u'thai' if dlg.GetStringSelection() == u'ไทย' else u'pali', 
                    int(volume), int(item))
        dlg.Destroy()

class Printer(HtmlEasyPrinting):
    def __init__(self):
        HtmlEasyPrinting.__init__(self)
    
    def GetHtmlText(self, text):
        return text
        
    def Print(self, text, doc_name):
        self.SetHeader(doc_name)
        self.PrintText(self.GetHtmlText(text), doc_name)
        
    def PreviewText(self, text, doc_name):
        self.SetHeader(doc_name)
        HtmlEasyPrinting.PreviewText(self, self.GetHtmlText(text))
        

FIVE_BOOKS_PAGES = {
    1:466,
    2:817,
    3:1572,
    4:813,
    5:614,
}

FIVE_BOOKS_TITLES = [
    u'ขุมทรัพย์จากพระโอษฐ์', 
    u'อริยสัจจากพระโอษฐ์ ๑', 
    u'อริยสัจจากพระโอษฐ์ ๒', 
    u'ปฏิจจสมุปบาทจากพระโอษฐ์', 
    u'พุทธประวัติจากพระโอษฐ์',]
        
FIVE_BOOKS_SECTIONS = {
    1:[
        u'',
        u'หมวดที่ ๑ ว่าด้วย การทุศีล',
        u'หมวดที่ ๒ ว่าด้วย การไม่สังวร',
        u'หมวดที่ ๓ ว่าด้วย เกียรติและลาภสักการะ',
        u'หมวดที่ ๔ ว่าด้วย การทำไปตามอำนาจกิเลส',
        u'หมวดที่ ๕ ว่าด้วย การเป็นทาสตัณหา',
        u'หมวดที่ ๖ ว่าด้วย การหละหลวมในธรรม',
        u'หมวดที่ ๗ ว่าด้วย การลืมคำปฏิญาณ',
        u'หมวดที่ ๘ ว่าด้วย พิษสงทางใจ',
        u'หมวดที่ ๙ ว่าด้วย การเสียความเป็นผู้หลักผู้ใหญ่',
        u'หมวดที่ ๑๐ ว่าด้วย การมีศีล',
        u'หมวดที่ ๑๑ ว่าด้วย การมีสังวร',
        u'หมวดที่ ๑๒ ว่าด้วย การเป็นอยู่ชอบ',
        u'หมวดที่ ๑๓ ว่าด้วย การไม่ทำไปตามอำนาจกิเลส',
        u'หมวดที่ ๑๔ ว่าด้วย การไม่เป็นทาสตัณหา',
        u'หมวดที่ ๑๕ ว่าด้วย การไม่หละหลวมในธรรม',
        u'หมวดที่ ๑๖ ว่าด้วย การไม่ลืมคำปฏิญาณ',
        u'หมวดที่ ๑๗ ว่าด้วย การหมดพิษสงทางใจ',
        u'หมวดที่ ๑๘ ว่าด้วย การไม่เสียความเป็นผู้หลักผู้ใหญ่',
        u'หมวดที่ ๑๙ ว่าด้วย เนื้อนาบุญของโลก',                                                            
    ], 
    2:[
        u'ภาคนำ ว่าด้วย ข้อความที่ควรทราบก่อนเกี่ยวกับจตุราริยสัจ',
        u'ภาค ๑ ว่าด้วย ทุกขอริยสัจ ความจริงอันประเสริฐคือทุกข์',
        u'ภาค ๒ ว่าด้วย สมุทยอริยสัจ ความจริงอันประเสริฐคือเหตุให้เกิดทุกข์',
        u'ภาค ๓ ว่าด้วย นิโรธอริยสัจ ความจริงอันประเสริฐคือความดับไม่เหลือของทุกข์',
    ], 
    3:[
        u'',
        u'',
        u'',
        u'',
        u'ภาค ๔ ว่าด้วย มัคคอริยสัจ ความจริงอันประเสริฐคือมรรค',
        u'ภาคผนวก ว่าด้วย เรื่องนำมาผนวก เพื่อความสะดวกแก่การอ้างอิงสำหรับเรื่องที่ตรัสซ้ำ ๆ บ่อย ๆ',
    ], 
    4:[
        u'บทนำ ว่าด้วย เรื่องที่ควรทราบก่อนเกี่ยวกับปฏิจจสมุปบาท',
        u'หมวด ๑ ว่าด้วย ลักษณะ – ความสำคัญ – วัตถุประสงค์ของเรื่องปฏิจจสมุปบาท',
        u'หมวด ๒ ว่าด้วย ปฏิจจสมุปบาทคืออริยสัจสมบูรณ์แบบ',
        u'หมวด ๓ ว่าด้วย บาลีแสดงว่าปฏิจจสมุปบาทไม่ใช่เรื่องข้ามภพข้ามชาติ',
        u'หมวด ๔ ว่าด้วย ปฏิจจสมุปบาทเกิดได้เสมอในชีวิตประจำวันของคนเรา',
        u'หมวด ๕ ว่าด้วย ปฏิจจสมุปบาทซึ่งแสดงการเกิดดับแห่งกิเลสและความทุกข์',
        u'หมวด ๖ ว่าด้วย ปฏิจจสมุปบาทที่ตรัสในรูปของการปฏิบัติ',
        u'หมวด ๗ ว่าด้วย โทษของการไม่รู้และอานิสงส์ของการรู้ปฏิจจสมุปบาท',
        u'หมวด ๘ ว่าด้วย ปฏิจจสมุปบาทเกี่ยวกับความเป็นพระพุทธเจ้า',
        u'หมวด ๙ ว่าด้วย ปฏิจจสมุปบาทกับอริยสาวก',
        u'หมวด ๑๐ ว่าด้วย ปฏิจจสมุปบาทนานาแบบ',
        u'หมวด ๑๑ ว่าด้วย ลัทธิหรือทิฏฐิที่ขัดกับปฏิจจสมุปบาท',
        u'หมวด ๑๒ ว่าด้วย ปฏิจจสมุปบาทที่ส่อไปในทางภาษาคน - เพื่อศีลธรรม',
        u'บทสรุป ว่าด้วย คุณค่าพิเศษของปฏิจจสมุปบาท',
    ], 
    5:[
        u'ภาคนำ ข้อความให้เกิดความสนใจในพุทธประวัติ',
        u'ภาค ๑ เริ่มแต่การเกิดแห่งวงศ์สากยะ, เรื่องก่อนประสูติ, จนถึงออกผนวช',
        u'ภาค ๒ เริ่มแต่ออกผนวชแล้วเที่ยวเสาะแสวงหาความรู้ ทรมานพระองค์ จนได้ตรัสรู้',
        u'ภาค ๓ เริ่มแต่ตรัสรู้แล้วทรงประกอบด้วยพระคุณธรรมต่าง ๆ จนเสด็จไปโปรดปัญจวัคคีย์บรรลุผล',
        u'ภาค ๔ เรื่องเบ็ดเตล็ดใหญ่น้อยต่าง ๆ ตั้งแต่โปรดปัญจวัคคีย์แล้ว  ไปจนถึงจวนจะปรินิพพาน',
        u'ภาค ๕ การปรินิพพาน',
        u'ภาค ๖ เรื่องการบำเพ็ญบารมีในอดีตชาติ ซึ่งเต็มไปด้วยทิฏฐานุคติอันสาวกในภายหลังพึงดำเนินตาม',
    ]}        
        
class ReadingToolFrame(wx.Frame):
    """Frame Class for reading the books"""
    
    def __init__(self, resultWindow, id, volume, page, lang='thai', keywords='', size=None, pos=None):
        self.side = None
        self.dictOpen = False
        self.useInter = False
        
        title = u''
        if lang == 'thai':
            title = u'อ่านพระไตรปิฎก (ภาษาไทย ฉบับบาลีสยามรัฐ)'
        elif lang == 'pali':
            title = u'อ่านพระไตรปิฎก (ภาษาบาลี ฉบับบาลีสยามรัฐ)'
        elif lang == 'thaimm':
            title = u'อ่านพระไตรปิฎก (ภาษาไทย ฉบับมหามกุฏฯ)'
        elif lang == 'thaiwn':
            title = u'อ่านพระไตรปิฎก (ภาษาไทย ฉบับวัดนาป่าพง)'
        elif lang == 'thaimc':
            title = u'อ่านพระไตรปิฎก (ภาษาไทย ฉบับมหาจุฬาฯ)'

        w,h = wx.GetDisplaySize()
        self.margin = 150
        if size == None:
            size = (w-self.margin,h-self.margin-30)
        if pos == None:
            pos = (self.margin/2,self.margin/2)

        wx.Frame.__init__(self, parent=None, id=id, title=title,size=size,pos=pos)
        
        # set icon
        icon = wx.IconBundle()
        icon.AddIconFromFile(os.path.join(sys.path[0],'resources','e-tri_64_icon.ico'), wx.BITMAP_TYPE_ANY)
        self.SetIcons(icon)
        
        # load pickle files      
        f = open(os.path.join(sys.path[0],'resources','book_page.pkl'),'rb')
        self.dbPage = cPickle.load(f)
        f.close()
        
        f = open(os.path.join(sys.path[0],'resources','book_name.pkl'),'rb')
        self.dbName = cPickle.load(f)
        f.close()
        
        f = open(os.path.join(sys.path[0],'resources','book_item.pkl'),'rb')
        self.dbItem = cPickle.load(f)
        f.close()

        f = open(os.path.join(sys.path[0],'resources','maps.pkl'),'rb')
        self.dbMap = cPickle.load(f)
        f.close()

        f = open(os.path.join(sys.path[0],'resources','mc_map.pkl'),'rb')
        self.dbMcmap = cPickle.load(f)
        f.close()
        
        self.bt_tree = json.loads(open(os.path.join(sys.path[0],'resources','bt_toc.json')).read())

        # set parameters
        self.page = page
        self.volume = volume
        self.lang = lang
        self.dirname = '.'
        self.resultWindow = resultWindow
        self.content = u''
        self.display = None
        self.keywords = keywords
        self.entering = ''
        self.config_file = os.path.join(sys.path[0],'config','style.txt')
        self.find_position = 0
        self.fdlg = False
        
        # books (hide/show)    
        self.isHide = False
        
        if self.lang == 'thai':
            conn = sqlite3.connect(os.path.join(sys.path[0],'resources','thai.db'))
            self.searcher1 = conn.cursor()
        elif self.lang == 'pali':
            conn = sqlite3.connect(os.path.join(sys.path[0],'resources','pali.db'))
            self.searcher1 = conn.cursor()
        elif self.lang == 'thaimm':
            conn = sqlite3.connect(os.path.join(sys.path[0],'resources','thaimm.db'))
            self.searcher1 = conn.cursor()
        elif self.lang == 'thaiwn':
            conn = sqlite3.connect(os.path.join(sys.path[0],'resources','thaiwn.db'))
            self.searcher1 = conn.cursor()
        elif self.lang == 'thaimc':
            conn = sqlite3.connect(os.path.join(sys.path[0],'resources','thaimc.db'))
            self.searcher1 = conn.cursor()
        elif self.lang == 'thaibt':
            conn = sqlite3.connect(os.path.join(sys.path[0],'resources','thaibt.db'))
            self.searcher1 = conn.cursor()


        self.statusBar = self.CreateStatusBar()
        self.statusBar.SetFieldsCount(2)
        self.statusBar.SetStatusWidths([-1,-1])
        font = wx.Font(13, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        font.SetFaceName('TF Chiangsaen')
        self.statusBar.SetFont(font)
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.sp = wx.SplitterWindow(self,style=wx.SP_3DSASH)
        mainSizer.Add(self.sp,1,wx.EXPAND)
        self.SetSizer(mainSizer)

        self.CreateLeftPanel()
        self.CreateRightPanel()

        self.sp.SplitVertically(self.leftPanel,self.rightPanel,350)
        self.sp.SetMinimumPaneSize(5)
        
        # printing
        self.printer = Printer()
        page_setup_data = self.printer.GetPageSetupData()
        page_setup_data.SetDefaultMinMargins(False)
        page_setup_data.SetMarginTopLeft((10,10))
        page_setup_data.SetMarginBottomRight((10,10))
        
        if self.lang == 'thaibt' and len(self.keywords) == 0:
            self.bookLists.SelectItem(self.FirstVolume, True)
                
    def CreateHeader(self):
        self.titlePanel1 = wx.Panel(self.rightPanel,-1)
        
        if 'gtk2' in wx.PlatformInfo:
            style = wx.TE_READONLY|wx.TE_MULTILINE|wx.NO_BORDER|wx.TE_RICH2
        else:
            style = wx.TE_READONLY|wx.NO_BORDER|wx.TE_RICH2
            
        self.title1 = wx.TextCtrl(self.titlePanel1,-1,u'หัวเรื่อง',size=(-1,40),style=style|wx.TE_CENTER)
        self.title1.SetFont(wx.Font(18, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
        self.titleSizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.titleSizer1.Add(self.title1,1,flag=wx.EXPAND)
        self.titlePanel1.SetBackgroundColour('white')
        self.titlePanel1.SetSizer(self.titleSizer1)

        self.titlePanel2 = wx.Panel(self.rightPanel,-1)
        self.title2 = wx.TextCtrl(self.titlePanel2,-1,u'หัวเรื่อง',size=(-1,40),style=style|wx.TE_CENTER)
        self.title2.SetFont(wx.Font(18, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
        self.titleSizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.titleSizer2.Add(self.title2,1,flag=wx.EXPAND)
        self.titlePanel2.SetBackgroundColour('white')
        self.titlePanel2.SetSizer(self.titleSizer2)

        self.pageNumPanel = wx.Panel(self.rightPanel,-1)
        self.pageNum = wx.TextCtrl(self.pageNumPanel,-1,u'เลขหน้า',size=(300,40),style=style|wx.TE_LEFT)
        self.itemNum = wx.TextCtrl(self.pageNumPanel,-1,u'เลขข้อ',size=(300,40),style=style|wx.TE_RIGHT)
        self.pageNum.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
        self.itemNum.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
        self.pageNumSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.pageNumSizer.Add(self.pageNum,flag=wx.LEFT,border=15)
        self.pageNumSizer.Add((20,20),1,flag=wx.EXPAND)
        self.pageNumSizer.Add(self.itemNum,flag=wx.RIGHT,border=15)
        self.pageNum.SetBackgroundColour('white')
        self.itemNum.SetBackgroundColour('white')
        self.pageNumPanel.SetBackgroundColour('white')
        self.pageNumPanel.SetSizer(self.pageNumSizer)
    
    def CreateMainWindow(self):
        self.mainWindowPanel = wx.Panel(self.rightPanel, -1)
        self.mainWindowPanel.SetBackgroundColour('white')
        self.mainWindow = wx.TextCtrl(self.mainWindowPanel, -1, style=wx.TE_READONLY|wx.NO_BORDER|wx.TE_MULTILINE|wx.TE_RICH2)#|wx.TE_DONTWRAP)wx.TE_RICH2|

        self.mainWindow.Bind(wx.EVT_CHAR, self.OnChar)
        self.mainWindow.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_FIND, self.OnFind)
        self.Bind(wx.EVT_FIND_NEXT, self.OnFind)
        self.Bind(wx.EVT_FIND_CLOSE, self.OnFindClose)

        self.font = self.LoadFont()
        
        if self.font != None and self.font.IsOk():
            self.mainWindow.SetFont(self.font)
        else:
            self.font = self.mainWindow.GetFont()
            self.font.SetPointSize(14)
            self.mainWindow.SetFont(self.font)
        
        if 'wxMac' in wx.PlatformInfo:
            self.mainWindow.Bind(wx.EVT_MOTION,self.OnSelectText)
        else:
            self.mainWindow.Bind(wx.EVT_LEFT_UP,self.OnSelectText)

        sizer = wx.BoxSizer(wx.VERTICAL)
                
        sizer.Add(self.mainWindow, 10, flag=wx.EXPAND|wx.LEFT,border=15)
        
        if self.lang == 'thaibt':
            self.refsWindow = ReferenceWindow(self.mainWindowPanel)
            self.refsWindow.Delegate = self
            self.refsWindow.SetStandardFonts(self.font.GetPointSize(),self.font.GetFaceName())              
            sizer.Add(self.refsWindow, 1, flag=wx.EXPAND|wx.ALL, border=5)
        else:
            self.refsWindow = None
        
        self.mainWindowPanel.SetSizer(sizer)
        

    def CreateTools(self):
        self.topSizer = wx.BoxSizer(wx.HORIZONTAL)

        # page view
        viewPanel = wx.Panel(self.rightPanel,-1)
        viewSizer = wx.StaticBoxSizer(wx.StaticBox(viewPanel, -1, u'อ่านทีละหน้า'), orient=wx.HORIZONTAL)

        leftIcon = wx.Image(os.path.join(sys.path[0],'resources','left.png'),wx.BITMAP_TYPE_PNG).Scale(32,32)
        self.btnPrev = wx.BitmapButton(viewPanel, -1, wx.BitmapFromImage(leftIcon)) 
        rightIcon = wx.Image(os.path.join(sys.path[0],'resources','right.png'),wx.BITMAP_TYPE_PNG).Scale(32,32)
        self.btnNext = wx.BitmapButton(viewPanel, -1, wx.BitmapFromImage(rightIcon)) 

        viewSizer.Add(self.btnPrev)
        viewSizer.Add(self.btnNext)
        viewPanel.SetSizer(viewSizer)

        # compare to the another
        comparePanel = wx.Panel(self.rightPanel,-1)
        compareSizer = wx.StaticBoxSizer(wx.StaticBox(comparePanel, -1, u'เทียบเคียงกับ'), orient=wx.HORIZONTAL)

        if self.lang == 'thai':
            self.comboCompare = wx.ComboBox(comparePanel, -1, choices=[u'บาลี  (บาลีสยามรัฐ)',u'ไทย (มหามกุฏฯ)',u'ไทย (มหาจุฬาฯ)'], style=wx.CB_DROPDOWN|wx.CB_READONLY)
        elif self.lang == 'pali':
            self.comboCompare = wx.ComboBox(comparePanel, -1, choices=[u'ไทย  (บาลีสยามรัฐ)',u'ไทย (มหามกุฏฯ)',u'ไทย (มหาจุฬาฯ)'], style=wx.CB_DROPDOWN|wx.CB_READONLY)
        elif self.lang == 'thaimm':
            self.comboCompare = wx.ComboBox(comparePanel, -1, choices=[u'ไทย (บาลีสยามรัฐ)',u'บาลี  (บาลีสยามรัฐ)',u'ไทย (มหาจุฬาฯ)'], style=wx.CB_DROPDOWN|wx.CB_READONLY)
        elif self.lang == 'thaimc':
            self.comboCompare = wx.ComboBox(comparePanel, -1, choices=[u'ไทย (บาลีสยามรัฐ)',u'บาลี (บาลีสยามรัฐ)',u'ไทย (มหามกุฏฯ)'], style=wx.CB_DROPDOWN|wx.CB_READONLY)
        elif self.lang == 'thaibt':
            self.comboCompare = wx.ComboBox(comparePanel, -1, choices=[], style=wx.CB_DROPDOWN|wx.CB_READONLY)            
            
        self.comboCompare.Disable()
        self.comboCompare.Bind(wx.EVT_COMBOBOX,self.OnSelectCompare)

        compareSizer.Add(self.comboCompare, flag=wx.ALIGN_CENTER)
        comparePanel.SetSizer(compareSizer)
     
        # tools
        self.toolsPanel = wx.Panel(self.rightPanel,-1)       
        toolsSizer = wx.StaticBoxSizer(wx.StaticBox(self.toolsPanel, -1, u'เครื่องมือ'), orient=wx.HORIZONTAL)
        
        # lexicon
        self.lexiconPanel = wx.Panel(self.rightPanel, -1, size=(-1,-1))
        lexiconSizer = wx.StaticBoxSizer(wx.StaticBox(self.lexiconPanel, -1, u'พจนานุกรม'), orient=wx.HORIZONTAL)
               
        layoutIcon = wx.Image(os.path.join(sys.path[0],'resources','layout.gif'),wx.BITMAP_TYPE_GIF).Scale(32,32)
        self.btnLayout = wx.BitmapButton(self.toolsPanel, -1, wx.BitmapFromImage(layoutIcon))
        self.btnLayout.SetToolTip(wx.ToolTip(u'แสดง/ซ่อน หน้าต่างเลือกหนังสือ'))
        
        searchIcon = wx.Image(os.path.join(sys.path[0],'resources','search.png'),wx.BITMAP_TYPE_PNG)
        self.btnSelFind = wx.BitmapButton(self.toolsPanel, -1, wx.BitmapFromImage(searchIcon)) 
        self.btnSelFind.SetToolTip(wx.ToolTip(u'ค้นหาจากข้อความที่ถูกเลือก'))

        starIcon = wx.Image(os.path.join(sys.path[0],'resources','star.png'),wx.BITMAP_TYPE_PNG)
        self.btnStar = wx.BitmapButton(self.toolsPanel, -1, wx.BitmapFromImage(starIcon)) 
        self.btnStar.SetToolTip(wx.ToolTip(u'ที่คั่นหน้า'))

        if self.lang == 'pali': 
            dictIcon = wx.Image(os.path.join(sys.path[0],'resources','dict.png'),wx.BITMAP_TYPE_PNG)
            self.btnDict = wx.BitmapButton(self.lexiconPanel, -1, wx.BitmapFromImage(dictIcon)) 
            self.btnDict.SetToolTip(wx.ToolTip(u'พจนานุกรมบาลี-ไทย'))
        
        self.menu_items = self.LoadMenuItems()        
        self.popupmenu = None
        
        size = self.btnSelFind.GetSize()
        fontsIcon = wx.Image(os.path.join(sys.path[0],'resources','fonts.png'),wx.BITMAP_TYPE_PNG)
        self.btnFonts = wx.BitmapButton(self.toolsPanel, -1, wx.BitmapFromImage(fontsIcon),size=size)
        self.btnFonts.SetToolTip(wx.ToolTip(u'เปลี่ยนรูปแบบตัวหนังสือ'))
        incIcon = wx.Image(os.path.join(sys.path[0],'resources','fontSizeUp.gif'),wx.BITMAP_TYPE_GIF)
        self.btnUp = wx.BitmapButton(self.toolsPanel, -1, wx.BitmapFromImage(incIcon),size=size)
        self.btnUp.SetToolTip(wx.ToolTip(u'เพิ่มขนาดตัวหนังสือ'))
        decIcon = wx.Image(os.path.join(sys.path[0],'resources','fontSizeDown.gif'),wx.BITMAP_TYPE_GIF)
        self.btnDown = wx.BitmapButton(self.toolsPanel, -1, wx.BitmapFromImage(decIcon),size=size)
        self.btnDown.SetToolTip(wx.ToolTip(u'ลดขนาดตัวหนังสือ'))        

        saveIcon = wx.Image(os.path.join(sys.path[0],'resources','save.png'),wx.BITMAP_TYPE_PNG).Scale(32,32)
        self.btnSave = wx.BitmapButton(self.toolsPanel, -1, wx.BitmapFromImage(saveIcon))
        self.btnSave.SetToolTip(wx.ToolTip(u'บันทึกข้อมูลลงไฟล์'))

        printIcon = wx.Image(os.path.join(sys.path[0],'resources','print.png'),wx.BITMAP_TYPE_PNG)
        self.btnPrint = wx.BitmapButton(self.toolsPanel, -1, wx.BitmapFromImage(printIcon))
        self.btnPrint.SetToolTip(wx.ToolTip(u'พิมพ์หน้าที่ต้องการ'))
        
        toolsSizer.Add(self.btnSelFind)
        toolsSizer.Add((5,-1))
        toolsSizer.Add(self.btnStar)        
        toolsSizer.Add((5,-1))

        if self.lang == 'pali':
            lexiconSizer.Add(self.btnDict)        
            lexiconSizer.Add((30,-1))
        else:
            self.lexiconPanel.Hide()

        toolsSizer.Add(self.btnLayout)
        toolsSizer.Add((5,-1))
        toolsSizer.Add(self.btnFonts)
        toolsSizer.Add(self.btnUp)
        toolsSizer.Add(self.btnDown)
        toolsSizer.Add((5,-1))
        toolsSizer.Add(self.btnSave)
        toolsSizer.Add(self.btnPrint)
        
        self.toolsPanel.SetSizer(toolsSizer)
        self.lexiconPanel.SetSizer(lexiconSizer)

        # top sizer
        self.topSizer.Add(viewPanel,flag=wx.EXPAND)
        self.topSizer.Add(comparePanel,flag=wx.EXPAND)
        self.topSizer.Add(self.toolsPanel,flag=wx.EXPAND)
        self.topSizer.Add(self.lexiconPanel,flag=wx.EXPAND)

        self.btnPrev.Bind(wx.EVT_BUTTON, self.OnClickPrev)
        self.btnNext.Bind(wx.EVT_BUTTON, self.OnClickNext)
        self.btnUp.Bind(wx.EVT_BUTTON, self.OnClickUp)
        self.btnDown.Bind(wx.EVT_BUTTON, self.OnClickDown)
        self.btnSelFind.Bind(wx.EVT_BUTTON, self.OnClickSelFind)
        self.btnLayout.Bind(wx.EVT_BUTTON, self.OnClickHide)
        self.btnSave.Bind(wx.EVT_BUTTON, self.OnClickSave)
        self.btnPrint.Bind(wx.EVT_BUTTON, self.OnClickPrint)
        self.btnStar.Bind(wx.EVT_BUTTON, self.OnShowPopup)
        self.btnFonts.Bind(wx.EVT_BUTTON, self.OnFonts)
        if self.lang == 'pali':
            self.btnDict.Bind(wx.EVT_BUTTON, self.OnClickDict)

    def CreatePaintPanel(self):
        # paint
        self.paintPanel = wx.Panel(self.rightPanel,-1)
        
        paintIcon = wx.Image(os.path.join(sys.path[0],'resources','yellow.png'),wx.BITMAP_TYPE_PNG).Scale(16,16)
        self.btnPaint = wx.BitmapButton(self.paintPanel, -1, wx.BitmapFromImage(paintIcon))
        self.btnPaint.SetToolTip(wx.ToolTip(u'ระบายสีข้อความที่ถูกเลือก'))
        
        unPaintIcon = wx.Image(os.path.join(sys.path[0],'resources','white.png'),wx.BITMAP_TYPE_PNG).Scale(16,16)
        self.btnUnPaint = wx.BitmapButton(self.paintPanel, -1, wx.BitmapFromImage(unPaintIcon))
        self.btnUnPaint.SetToolTip(wx.ToolTip(u'ระบายสีข้อความที่ถูกเลือก'))
        
        self.paintPanel.SetBackgroundColour('white')
        paintSizer = wx.BoxSizer(wx.HORIZONTAL)
        paintSizer.Add(self.btnPaint)
        paintSizer.Add(self.btnUnPaint)
        self.paintPanel.SetSizer(paintSizer)      

        self.btnPaint.Bind(wx.EVT_BUTTON, self.OnClickPaint)
        self.btnUnPaint.Bind(wx.EVT_BUTTON, self.OnClickUnPaint)

        if 'wxMac' in wx.PlatformInfo:
            self.paintPanel.Hide()
    
    def CreateRightPanel(self):
        self.rightPanel = wx.Panel(self.sp,-1)

        self.CreateHeader()
        self.CreateMainWindow()
        self.CreateTools()
        self.CreatePaintPanel()

        # right panel main sizer
        rightSizer = wx.BoxSizer(wx.VERTICAL)
        rightSizer.Add(self.topSizer,flag=wx.EXPAND)
        rightSizer.Add(self.titlePanel1,flag=wx.EXPAND)
        rightSizer.Add(self.titlePanel2,flag=wx.EXPAND)
        rightSizer.Add(self.pageNumPanel,flag=wx.EXPAND)
        rightSizer.Add(wx.StaticLine(self.rightPanel),flag=wx.EXPAND)
        rightSizer.Add(self.paintPanel,flag=wx.EXPAND)
        rightSizer.Add(self.mainWindowPanel,1,flag=wx.EXPAND)
        self.rightPanel.SetSizer(rightSizer)

    def CreateLeftPanel(self):
        self.leftPanel = wx.Panel(self.sp,-1)
        naviPanel = wx.Panel(self.leftPanel,-1)
        naviSizer = wx.StaticBoxSizer(wx.StaticBox(naviPanel, -1, u'เลือกอ่านที่'), orient=wx.HORIZONTAL)

        self.labelPage = wx.StaticText(naviPanel,-1,u'หน้า: ')
        self.labelItem = wx.StaticText(naviPanel,-1,u'ข้อ: ')
        self.labelCheck = wx.StaticText(naviPanel,-1,u'=สยามรัฐฯ')
        
        self.textPage = wx.TextCtrl(naviPanel, -1, size=(50,-1),style=wx.TE_PROCESS_ENTER)
        self.textPage.Bind(wx.EVT_TEXT_ENTER, self.OnPressEnterPage)
        self.textPage.Bind(wx.EVT_TEXT, self.OnPressEnterPage)
		
        self.textItem = wx.TextCtrl(naviPanel, -1, size=(50,-1),style=wx.TE_PROCESS_ENTER)
        self.textItem.Bind(wx.EVT_TEXT_ENTER, self.OnPressEnterItem)
        self.textItem.Bind(wx.EVT_TEXT, self.OnPressEnterItem)
        if self.lang == 'thaibt':
            self.textItem.Enable(False)
        
        self.checkBox = wx.CheckBox(naviPanel,-1)
        self.checkBox.Bind(wx.EVT_CHECKBOX, self.OnCheckInter)
		
        naviSizer.Add(self.labelPage,flag=wx.ALIGN_CENTER_VERTICAL)
        naviSizer.Add(self.textPage,flag=wx.ALIGN_CENTER_VERTICAL)
        naviSizer.Add(wx.StaticText(naviPanel,-1,u'  หรือ  '),flag=wx.ALIGN_CENTER_VERTICAL)
        naviSizer.Add(self.labelItem,flag=wx.ALIGN_CENTER_VERTICAL)
        naviSizer.Add(self.textItem,flag=wx.ALIGN_CENTER_VERTICAL)
        naviSizer.Add((5,-1))
        naviSizer.Add(self.checkBox,flag=wx.ALIGN_CENTER_VERTICAL)
        naviSizer.Add(self.labelCheck,flag=wx.ALIGN_CENTER_VERTICAL)
        
        naviPanel.SetSizer(naviSizer)
        if self.lang == 'thai' or self.lang == 'pali' or self.lang == 'thaiwn' or self.lang == 'thaimc':
            books = [u'%s. %s'%(arabic2thai(unicode(x)),self.dbName['%s_%d'%(self.lang,x)].decode('utf8','ignore')) for x in range(1,46)]
        elif self.lang == 'thaimm':
            books = [u'%s. %s'%(arabic2thai(unicode(x)),self.dbName['%s_%d'%(self.lang,x)].decode('utf8','ignore')) for x in range(1,92)]

        if self.lang == 'thaimc':
            self.checkBox.Show()
            self.labelCheck.Show()
        else:
            self.checkBox.Hide()
            self.labelCheck.Hide()
            
        
        if self.lang != 'thaibt':
            self.bookLists = wx.ListBox(self.leftPanel,-1,choices=books,style=wx.LB_SINGLE|wx.NO_BORDER)
            self.bookLists.SetSelection(0)
            self.bookLists.Bind(wx.EVT_LISTBOX, self.OnSelectBook)
        else:
            self.bookLists = wx.TreeCtrl(self.leftPanel, -1, wx.DefaultPosition, wx.DefaultSize, style=wx.TR_HIDE_ROOT|wx.TR_HAS_BUTTONS)
            self.bookLists.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged)
            self.CreateTree(None, self.bookLists)            

        leftSizer = wx.BoxSizer(wx.VERTICAL)
        leftSizer.Add(naviPanel)
        leftSizer.Add(self.bookLists,1,flag=wx.EXPAND)
        self.leftPanel.SetSizer(leftSizer)

    def CreateTree(self, data, tree):
        root = tree.AddRoot('root')
        keys = self.bt_tree.keys()
        keys.sort()
        for key in keys:
            volume = tree.AppendItem(root, FIVE_BOOKS_TITLES[int(key)-1])
            tree.SetPyData(volume, tuple(self.bt_tree[key][0]) + (None,) )
            if int(key) == 1:
                self.FirstVolume = volume
            secs = map(int, self.bt_tree[key][1].keys())
            secs.sort()            
            for sec in secs:
                section = tree.AppendItem(volume, FIVE_BOOKS_SECTIONS[int(key)][int(sec)])
                tree.SetPyData(section, tuple(self.bt_tree[key][1][str(sec)]) + (int(sec),))
        child, cookie = tree.GetFirstChild(root)
        tree.Expand(child)

    def OnSelChanged(self, event):
        info = self.bookLists.GetItemPyData(event.GetItem())
        self.LoadFiveBookContent(info[0], info[1], info[2])        
        
    def LoadFiveBookContent(self, volume, page, section=None):        
        self.searcher1.execute('SELECT * FROM speech WHERE book=? AND page=?', (volume, page))
        result = self.searcher1.fetchone()
        if result:
            self.page = page
            self.volume = volume
            if section:
                self.section = section
            elif len(result[2].split()[1].split('.')) > 1:
                self.section = int(result[2].split()[1].split('.')[1])
            else:
                self.section = 0            
            self.GenStartPage()
            self.LoadContent(content=result[3])
            refs = re.findall(ur'[๐๑๒๓๔๕๖๗๘๙\w\-,]+/[๐๑๒๓๔๕๖๗๘๙\w\-,]+/[๐๑๒๓๔๕๖๗๘๙\w\-,]+', result[3], re.U)
            if len(refs) > 0:
                html = u'<b>อ้างอิง: </b> '
                for ref in refs:
                    ref = ref.strip().strip(u')').strip(u'(').strip(u',').strip()
                    html += u'<a href="%s">%s</a>  '%(ref, ref)
                self.refsWindow.SetPage(html)
            else:
                self.refsWindow.SetPage(u'')

    def LoadMenuItems(self):
        menu_items = []
        fav_file = os.path.join(sys.path[0],'config','%s.fav'%(self.lang))
        if os.path.exists(fav_file):
            tmp = []
            for text in codecs.open(fav_file,'r','utf8').readlines():
                if text.strip() == '': continue
                tokens = thai2arabic(text.strip()).split()
                v = int(tokens[1])
                p = int(tokens[3])
                tmp.append((v,p,text.strip()))
            tmp.sort()
            for v,p,text in tmp:
                menu_items.append(text)
        return menu_items        
    
    def LoadBookmarks(self, menu):
        for text in self.menu_items:
            item = menu.Append(-1,text)
            self.Bind(wx.EVT_MENU, self.OnGotoBookmark, item)
                
    def SaveBookmarks(self):
        out = codecs.open(os.path.join(sys.path[0],'config','%s.fav'%(self.lang)),'w','utf8')
        for text in self.menu_items:
            out.write(text+'\n')
        out.close()
        
    def SetKeyWords(self, keywords):
        self.keywords = keywords
        
    def OnDeleteBookmarkSelected(self, event):
        dialog = wx.MultiChoiceDialog(self, 
            u'โปรดเลือกคั่นหน้าที่ต้องการลบ',u'ตัวเลือกคั่นหน้า', self.menu_items)            
        if dialog.ShowModal() == wx.ID_OK:
            items = []
            for sel in dialog.GetSelections():
                items.append(self.menu_items[sel])
            for item in items:
                self.menu_items.remove(item)                
        dialog.Destroy()
        
    def OnBookmarkSelected(self, event):
        if self.page != 0:
            x,y = self.btnStar.GetScreenPosition()
            w,h = self.btnStar.GetSize()   
            dialog = BookMarkDialog(self,pos=(x,y+h))
            if dialog.ShowModal() == wx.ID_OK:
                note = dialog.GetName()
                name = u'%s : %s' %(arabic2thai(u'เล่มที่ %d หน้าที่ %d'%(self.volume, self.page)),note)
                self.menu_items.append(name)
            dialog.Destroy()
        else:
            wx.MessageBox(u'หน้ายังไม่ได้ถูกเลือก',u'พบข้อผิดพลาด')
        
    def OnGotoBookmark(self, event):
        item = self.popupmenu.FindItemById(event.GetId())
        text = thai2arabic(item.GetText())
        tokens = text.split(' ')
        self.volume = int(tokens[1])
        self.page = int(tokens[3])
        if self.lang != 'thaibt':
            self.bookLists.SetSelection(self.volume-1)
            self.LoadContent()
        else:
            root = self.bookLists.GetRootItem()
            child, cookie = self.bookLists.GetFirstChild(root)
            for i in xrange(self.volume):
                child = self.bookLists.GetNextSibling(child)
            self.bookLists.SelectItem(child, True)
            self.page = int(tokens[3])
            self.LoadFiveBookContent(self.volume, self.page)
    
    def ZoomIn(self):
        font = self.mainWindow.GetFont()
        size = font.GetPointSize()
        font.SetPointSize(size+1)
        self.mainWindow.SetFont(font)
        if self.refsWindow:
            self.refsWindow.SetStandardFonts(font.GetPointSize(), font.GetFaceName())
        self.processTags()
        self.SetHighLight()
        self.SaveFont(font)
        
    def ZoomOut(self):
        font = self.mainWindow.GetFont()
        size = font.GetPointSize()
        font.SetPointSize(size-1)
        self.mainWindow.SetFont(font)
        if self.refsWindow:
            self.refsWindow.SetStandardFonts(font.GetPointSize(), font.GetFaceName())
        self.processTags()
        self.SetHighLight()
        self.SaveFont(font)
        
        
    def OnClickUp(self, event):
        self.ZoomIn()
        event.Skip()
        
    def OnClickDown(self, event):
        self.ZoomOut()
        event.Skip()       
        
    def OnClickNext(self, event):
        self.DoNext()
        event.Skip
        
    def OnClickPrev(self, event):
        self.DoPrev()
        event.Skip()

    def ShowProgress(self, percentage):
        self.pageNum.SetValue(u'%d%%'%(percentage*100))
	
    def GotoPage(self, page):
        if self.lang != 'thaibt':
            try:
                page = int(page)
                found = False
                for r in self.GetContent(self.volume, page):
                    found = True
                if found:
                    self.page = int(page)
                    self.LoadContent()
                else:
                    self.GenStartPage(u'ผลการค้นหา : ไม่พบหน้าที่ต้องการ')                
            except ValueError,e:
                self.GenStartPage(u'ผลการค้นหา : ไม่พบหน้าที่ต้องการ')
        else:
            try:
                self.LoadFiveBookContent(self.volume, int(page))
            except ValueError,e:
                pass
    
    def GotoItem(self, item):
        if self.lang == 'thaibt':
            return

        if item == u'':
            self.GenStartPage()
        else:
            try:
                lang = self.lang.encode('utf8','ignore')
                volume = self.volume
                sub_vol = 0
                
                if len(item.split(u'.')) == 2:
                    item, sub_vol = map(int,item.split(u'.'))
                elif len(item.split(u'.')) == 1:
                    item = int(item)
                    sub_vol = 1
                
                if self.useInter:
                    self.page = int(self.dbMcmap['v%d-%d-i%d'%(volume,sub_vol,item)])
                    self.LoadContent()
                elif not self.useInter and sub_vol in self.dbItem[lang][volume] and item in self.dbItem[lang][volume][sub_vol]:
                    self.page = self.dbItem[lang][volume][sub_vol][item][0]
                    self.LoadContent()
                else:
                    self.GenStartPage(u'ผลการค้นหา : ไม่พบข้อที่ต้องการ')
            except ValueError,e:
                self.GenStartPage(u'ผลการค้นหา : ไม่พบข้อที่ต้องการ')
    
    
    def OnPressEnterPage(self, event):
        page = self.textPage.GetValue().strip()
        self.GotoPage(page)
        event.Skip()
        
    def OnPressEnterItem(self, event):
        item = self.textItem.GetValue().strip()
        self.GotoItem(item)
        event.Skip()
    
    def OnSelectCompare(self, event):
        lang = self.lang

        if self.comboCompare.GetSelection() == 0:
            if lang == 'thai':
                comp_lang = 'pali'
            elif lang == 'pali':
                comp_lang = 'thai'
            elif lang == 'thaimm':
                comp_lang = 'thai'
            elif lang == 'thaimc':
                comp_lang = 'thai'
            elif lang == 'thaiwn':
                comp_lang = 'thai'
        elif self.comboCompare.GetSelection() == 1:
            if lang == 'thai':
                comp_lang = 'thaimm'
            elif lang == 'pali':
                comp_lang = 'thaimm'
            elif lang == 'thaimm':
                comp_lang = 'pali'
            elif lang == 'thaimc':
                comp_lang = 'pali'
            elif lang == 'thaiwn':
                comp_lang = 'pali'
        elif self.comboCompare.GetSelection() == 2:
            if lang == 'thai':
                comp_lang = 'thaimc'
            elif lang == 'pali':
                comp_lang = 'thaimc'
            elif lang == 'thaimm':
                comp_lang = 'thaimc'
            elif lang == 'thaimc':
                comp_lang = 'thaimm'
            elif lang == 'thaiwn':
                comp_lang = 'thaimc'
        elif self.comboCompare.GetSelection() == 3:
            if lang == 'thai':
                comp_lang = 'thaiwn'
            elif lang == 'pali':
                comp_lang = 'thaiwn'
            elif lang == 'thaimm':
                comp_lang = 'thaiwn'
            elif lang == 'thaimc':
                comp_lang = 'thaiwn'
            elif lang == 'thaiwn':
                comp_lang = 'thaimm'

        volume = self.volume
        page = self.page

        # find all items in the page
        for d in self.GetContent(volume,page):
            items = map(int,d['items'].split())
            if lang == 'thaimm':
                vol_origs = map(int,d['volume_orig'].split())
                volume = vol_origs[0]
                lang = 'thaimm_orig'     
        
        found = False
        # find item and sub volumn
        if lang == 'thaimc':
            item,sub = map(int,self.dbMcmap['v%d-p%d'%(volume,page)])
            found = True
        else:
            # get the first item
            item = items[0]
            for sub in self.dbItem[lang][volume]:
                if item in self.dbItem[lang][volume][sub]:
                    pages = self.dbItem[lang][volume][sub][item]
                    if page in pages:
                        found = True
                        break

        if comp_lang == 'thaimm':
            comp_lang = 'thaimm_orig'

        # find the matched page of comp_lang

        if item in self.dbItem[comp_lang][volume][sub]:
            page = self.dbItem[comp_lang][volume][sub][item][0]
        else:
            page = 0

        if comp_lang == 'thaimc':
            page = int(self.dbMcmap['v%d-%d-i%d'%(volume,sub,item)])

        if lang == 'thaimm_orig':
            lang = 'thaimm'

        if comp_lang == 'thaimm_orig':
            comp_lang = 'thaimm'
            if '%d-%d-%d'%(volume,sub,item) not in self.dbMap['thaimm']:
                item = 1
            volume = int(self.dbMap['thaimm']['%d-%d-%d'%(volume,sub,item)])
        
        self.resultWindow.CreateReadingFrame(volume,page, lang=comp_lang,item=item,isCompare=True)
        self.resultWindow.VerticalAlignWindows(lang, comp_lang)

        event.Skip()

    def OnClickSelFind(self, event):
        s,t = self.mainWindow.GetSelection()
        selected = self.mainWindow.GetRange(s,t).strip()
        if selected != '':
            topWindow= self.resultWindow.GetParent()
            topWindow.Raise()
            topWindow.Iconize(False)
            topWindow.Maximize()
            if self.lang == 'thai':
                topWindow.comboLang.SetSelection(0)
                topWindow.radio4.Disable()
            elif self.lang == 'pali':
                topWindow.comboLang.SetSelection(1)
                topWindow.radio4.Enable()
            elif self.lang == 'thaimm':
                topWindow.comboLang.SetSelection(2)
                topWindow.radio4.Disable()
            elif self.lang == 'thaiwn':
                topWindow.comboLang.SetSelection(3)
                topWindow.radio4.Disable()
            elif self.lang == 'thaimc':
                topWindow.comboLang.SetSelection(4)
                topWindow.radio4.Disable()

            topWindow.text.AppendSearch(selected)
            topWindow.DoFind(selected)
        else:
            wx.MessageBox(u'ข้อความยังไม่ได้ถูกเลือก',u'พบข้อผิดพลาด  ')
        event.Skip()
        
    def OnClickHide(self, event):
        if self.isHide:
            self.ShowBooks()
        else:
            self.HideBooks()
        event.Skip()

    def HideBooks(self):
        if not self.isHide:
            self.sp.Unsplit(self.leftPanel)
            self.isHide = not self.isHide
            self.Refresh()
        
    def ShowBooks(self):
        margin = self.margin
        w,h = wx.GetDisplaySize()
        self.SetSize((w-margin,h-margin-30))
        self.Move((margin/2,margin/2))
        if self.isHide:
            self.sp.SplitVertically(self.leftPanel,self.rightPanel,350)
            self.isHide = not self.isHide
            self.Refresh()
        
    def OnClickPaint(self, event):
        s,t = self.mainWindow.GetSelection()
        font = self.mainWindow.GetFont()
        self.mainWindow.SetStyle(s,t, wx.TextAttr(wx.NullColour,'yellow',font))    
        event.Skip()

    def OnClickUnPaint(self, event):
        s,t = self.mainWindow.GetSelection()
        font = self.mainWindow.GetFont()
        self.mainWindow.SetStyle(s,t, wx.TextAttr(wx.NullColour,'white',font))    
        event.Skip()
        
    def OnClickPrint(self, event):
        # choose page range dialog
        page = self.page
        volume = self.volume
        lang = self.lang
        
        if self.lang != 'thaibt':
            tmp = self.dbName['%s_%d'%(lang,volume)].decode('utf8','ignore').split()
            msg1 = u' '.join(tmp[:3])
            msg2 = u' '.join(tmp[3:])
            num = int(self.dbPage['%s_%d'%(lang,volume)])
        else:
            msg1 = FIVE_BOOKS_TITLES[self.volume]
            msg2 = u''
            num = FIVE_BOOKS_PAGES[self.volume]
        
        cur = 1
        if page != 0:
            cur = page
            
        data = {'from':cur-1, 'to':cur-1}
        pageDlg = ChoosePagesDialog(self,u'โปรดเลือกหน้าที่ต้องการพิมพ์', msg1, msg2, num, data)       
        pageDlg.Center()         
        ret = pageDlg.ShowModal()

        if data['from'] <= data['to']:
            pages = range(data['from'],data['to']+1)
        else:
            pages = range(data['from'],data['to']-1,-1)        
        
        if ret == wx.ID_OK:
            cur_font = self.LoadFont()
            text = u'<font face="TF Chiangsaen" size=+2>' if cur_font == None else u'<font face="%s" size=+2>'%(cur_font.GetFaceName())
            text += u"<div align=center><b>%s</b><br><b>%s</b><br><b>%s</b><br>หน้าที่ %s ถึง %s</div><hr>"%(self.GetFullTitle(lang,volume),msg1,msg2,arabic2thai(str(data['from']+1).decode('utf8','ignore')),arabic2thai(str(data['to']+1).decode('utf8','ignore')))
            for page in pages:
                for d in self.GetContent(volume,page+1):
                    if lang == 'pali':
                        content = d['content'].replace(u'ฐ',u'\uf700').replace(u'ญ',u'\uf70f').replace(u'\u0e4d',u'\uf711')
                    else:
                        content = d['content']
                    content = content.replace(u'\t',u'&nbsp;'*7).replace(u'\x0a',u'<br>').replace(u'\x0b',u'<br>').replace(u'\x0c',u'<br>').replace(u'\x0d',u'<br>')
                    text += u'<div align=right>หน้าที่ %s</div><p>'%(arabic2thai(str(page+1).decode('utf8','ignore')))
                    text += u'%s<p><p><p>'%(content)
            text += u'</font>'
            self.printer.Print(text,"")
        
        pageDlg.Destroy()

        event.Skip()
        
        
    def OnClickSave(self, event):
        # choose page range dialog
        page = self.page
        volume = self.volume
        lang = self.lang
        
        if self.lang != 'thaibt':
            tmp = self.dbName['%s_%d'%(lang,volume)].decode('utf8','ignore').split()
            msg1 = u' '.join(tmp[:3])
            msg2 = u' '.join(tmp[3:])
            num = int(self.dbPage['%s_%d'%(lang,volume)])
        else:
            msg1 = FIVE_BOOKS_TITLES[self.volume]
            msg2 = u''
            num = FIVE_BOOKS_PAGES[self.volume]

        cur = 1
        if page != 0:
            cur = page
            
        data = {'from':cur-1, 'to':cur-1}
        pageDlg = ChoosePagesDialog(self,u'โปรดเลือกหน้าที่ต้องการบันทึก',msg1,msg2,num,data)
        pageDlg.Center()        
        ret = pageDlg.ShowModal()

        if data['from'] <= data['to']:
            pages = range(data['from'],data['to']+1)
        else:
            pages = range(data['from'],data['to']-1,-1)        
        
        if ret == wx.ID_OK:
            # call searcher volumn, page
            text = u'%s\n%s\n\n'%(msg1,msg2)
            for page in pages:
                for d in self.GetContent(volume,page+1):
                    if lang == 'pali':
                        content = d['content'].replace(u'ฐ',u'\uf700').replace(u'ญ',u'\uf70f').replace(u'\u0e4d',u'\uf711')
                    else:
                        content = d['content']                
                    text += u' '*60 + u'หน้าที่ %s\n\n'%(arabic2thai(str(page+1).decode('utf8','ignore')))
                    text += u'%s\n\n\n'%(content)
            saveFile = '%s_volumn-%02d_page-%04d-%04d'%(lang,volume,data['from']+1,data['to']+1)
            wildcard = u'Plain Text (*.txt)|*.txt'
            saveDlg = wx.FileDialog(self, u'โปรดเลือกไฟล์', self.dirname, saveFile, wildcard, \
                    wx.SAVE | wx.OVERWRITE_PROMPT)
            if saveDlg.ShowModal() == wx.ID_OK:
                filename=saveDlg.GetFilename()
                self.dirname=saveDlg.GetDirectory()
                filehandle=codecs.open(os.path.join(self.dirname, filename),'w','utf-8')
                filehandle.write(text)
                filehandle.close()
            saveDlg.Destroy()
        
        pageDlg.Destroy()

        event.Skip()

    def OnClickDict(self, event):
        if not self.dictOpen:
            self.dictWindow = DictWindow(self)
            self.dictWindow.Bind(wx.EVT_CLOSE, self.OnDictClose)
            self.dictWindow.SetTitle(u'พจนานุกรม บาลี-ไทย')
            self.dictWindow.Show()
            self.dictOpen = True

            s,t = self.mainWindow.GetSelection()
            if s < t:
                text = self.mainWindow.GetRange(s,t)
                text = text.strip().split('\n')[0]
                self.dictWindow.SetInput(text)

        event.Skip()

    def OnDictClose(self, event):
        self.dictOpen = False
        event.Skip()
        
    def OnFonts(self, event):
        curFont = self.LoadFont()
        fontData = wx.FontData()
        fontData.EnableEffects(False)
        fontData.SetInitialFont(curFont)
        dialog = wx.FontDialog(self, fontData)
        if dialog.ShowModal() == wx.ID_OK:
            data = dialog.GetFontData()
            font = data.GetChosenFont()
            if font.IsOk():
                self.SaveFont(font)
                self.font = font
                self.mainWindow.SetFont(font)
                if self.refsWindow:
                    self.refsWindow.SetStandardFonts(font.GetPointSize(), font.GetFaceName())
                font = wx.Font(self.font.GetPointSize()+2, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
                font.SetFaceName(self.font.GetFaceName())
                self.title1.SetStyle(0,len(self.title1.GetValue()), wx.TextAttr('blue',wx.NullColour,font))                
                self.title2.SetStyle(0,len(self.title2.GetValue()), wx.TextAttr('blue',wx.NullColour,font))
                font.SetPointSize(self.font.GetPointSize()-4)                
                self.pageNum.SetStyle(0,len(self.pageNum.GetValue()), wx.TextAttr('#378000',wx.NullColour,font))
                self.itemNum.SetStyle(0,len(self.itemNum.GetValue()), wx.TextAttr('#378000',wx.NullColour,font))
                self.processTags()
                self.SetHighLight()
        dialog.Destroy()
        event.Skip()
        
    def SaveFont(self,font):
        t = u'%s,%d,%d,%d,%d'%(font.GetFaceName(),font.GetFamily(),font.GetStyle(),font.GetWeight(),font.GetPointSize())
        codecs.open(os.path.join(sys.path[0],'config','font_read.log'),'w','utf8').write(t)        
        
    def LoadFont(self):
        font = None
        if os.path.exists(os.path.join(sys.path[0],'config','font_read.log')):
            tokens = codecs.open(os.path.join(sys.path[0],'config','font_read.log'),'r','utf8').read().split(',')
            if len(tokens) == 5:
                font = wx.Font(int(tokens[4]),int(tokens[1]),int(tokens[2]),int(tokens[3]))
                font.SetFaceName(tokens[0])
                return font
        return font
                
    def OnSelectBook(self, event):
        volume = self.bookLists.GetSelection() + 1
        if volume > 0:
            self.volume = volume
            self.GenStartPage()
        event.Skip()

    def GetFullTitle(self, lang, volume):
        if lang == 'thai':
            dlang = u'ไทย'
            title1 = u'พระไตรปิฎก ฉบับบาลีสยามรัฐ (ภาษา%s) เล่มที่ %s'%(dlang,arabic2thai(unicode(volume)))
        elif lang == 'pali':
            dlang = u'บาลี'
            title1 = u'พระไตรปิฎก ฉบับบาลีสยามรัฐ (ภาษา%s) เล่มที่ %s'%(dlang,arabic2thai(unicode(volume)))
        elif lang == 'thaimm':
            title1 = u'พระไตรปิฎก ฉบับมหามกุฏฯ (ภาษาไทย) เล่มที่ %s'%(arabic2thai(unicode(volume)))
        elif lang == 'thaiwn':
            title1 = u'พระไตรปิฎก ฉบับวัดนาป่าพง (ภาษาไทย) เล่มที่ %s'%(arabic2thai(unicode(volume)))        
        elif lang == 'thaimc':
            title1 = u'พระไตรปิฎก ฉบับมหาจุฬาฯ (ภาษาไทย) เล่มที่ %s'%(arabic2thai(unicode(volume)))
        else:
            title1 = u''
            
        return title1
        
    def GenStartPage(self, info=u''):
        if self.lang != 'thaibt':            
            self.page = 0
            
        self.comboCompare.Disable()

        # add header

        if self.lang != 'thaibt':
            title1 = self.GetFullTitle(self.lang, self.volume)            
        else:
            title1 = FIVE_BOOKS_TITLES[int(self.volume)-1]
            
        self.title1.SetValue(title1)        
        font = wx.Font(18, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        font.SetFaceName(self.font.GetFaceName())
        font.SetPointSize(self.font.GetPointSize()+2)
        self.title1.SetStyle(0, len(title1), wx.TextAttr('blue',wx.NullColour,font))
        
        if self.lang != 'thaibt':
            tokens = self.dbName['%s_%d'%(self.lang,self.volume)].split()                        
            title2 = u'%s %s'%(' '.join(tokens[:3]).decode('utf8','ignore'),' '.join(tokens[3:]).decode('utf8','ignore'))
        elif self.section != None:
            title2 = FIVE_BOOKS_SECTIONS[self.volume][self.section]
        else:
            title2 = u''
            
        self.title2.SetValue(title2)             
        self.title2.SetStyle(0,len(title2), wx.TextAttr('blue',wx.NullColour,font))
        
        if self.lang != 'thaibt':
            self.pageNum.SetValue(u'')
        else:
            font.SetPointSize(self.font.GetPointSize()-4)
            pageNum = arabic2thai(u'หน้าที่ %s/%s'%(unicode(self.page), FIVE_BOOKS_PAGES[self.volume]))
            self.pageNum.SetStyle(0,len(pageNum), wx.TextAttr('#378000', wx.NullColour, font))
            self.pageNum.SetValue(pageNum)
        
        self.itemNum.SetValue(u'')
        
        self.statusBar.SetStatusText(u'', 0)        
        
        if self.lang != 'thaibt':
            pages = map(lambda x:u'%s'%(x),range(1,int(self.dbPage['%s_%d'%(self.lang,self.volume)])+1))
            text1 = u'\nพระไตรปิฎกเล่มที่ %d มี\n\tตั้งแต่หน้าที่ %d - %d'%(self.volume, int(pages[0]), int(pages[-1]))
            text2 = u''
            lang = self.lang.encode('utf8','ignore')
            sub = self.dbItem[lang][self.volume].keys()

            if len(sub) == 1:
                items = self.dbItem[lang][self.volume][1].keys()
                text2 = u'\n\tตั้งแต่ข้อที่ %s - %s'%(items[0],items[-1])
            else:
                text2 = u'\n\tแบ่งเป็น %d เล่มย่อย มีข้อดังนี้'%(len(sub))
                for s in sub:
                    items = self.dbItem[lang][self.volume][s].keys()
                    text2 = text2 + '\n\t\t %d) %s.%d - %s.%d'%(s,items[0],s,items[-1],s)
            self.mainWindow.SetValue(arabic2thai(text1 + text2 + u'\n\n' + info))

        if 'wxMac' in wx.PlatformInfo:
            font = self.mainWindow.GetFont()
            self.mainWindow.SetFont(font)
            if self.refsWindow:
                self.refsWindow.SetStandardFonts(font.GetPointSize(), font.GetFaceName())
        
    def OnSelectText(self, event):
        s,t = self.mainWindow.GetSelection()
        if s < t:
            text = self.mainWindow.GetRange(s,t)
            text = text.split('\n')[0]
            self.statusBar.SetStatusText(u'คำที่เลือกคือ "%s"'%text,0)
            if self.dictOpen:
                self.dictWindow.SetInput(text)
        else:
            self.statusBar.SetStatusText(u'',0)
        event.Skip()
        
    def OnShowPopup(self, event):
        x,y = self.btnStar.GetPosition()
        w,h = self.btnStar.GetSize()     
        if (self.popupmenu != None):
            self.popupmenu.Destroy()
        self.popupmenu = wx.Menu()
        bookmark = self.popupmenu.Append(-1, u'คั่นหน้านี้')
        self.Bind(wx.EVT_MENU, self.OnBookmarkSelected, bookmark)
        delete = self.popupmenu.Append(-1, u'ลบคั่นหน้า')
        self.Bind(wx.EVT_MENU, self.OnDeleteBookmarkSelected, delete)
        self.popupmenu.AppendSeparator()        
        self.LoadBookmarks(self.popupmenu)
        self.toolsPanel.PopupMenu(self.popupmenu,(x,y+h))

    def readConfig(self):
        line = open(self.config_file).readline()
        tokens = line.split()
        if len(tokens) == 2:
            ccode, diff_size = tokens
            if re.match('[abcdefABCDEF0123456789]{6}',ccode) and re.match('\d+',diff_size):
                return '#%s'%(ccode), int(diff_size)
        return '#3CBF3F', 4

    def processTags(self):
        if self.display:
            if 'wxMac' in wx.PlatformInfo:
                window_font = self.mainWindow.GetFont()
                fsize = window_font.GetPointSize()
                font = self.mainWindow.GetFont()
                self.mainWindow.SetFont(font)
                if self.refsWindow:
                    self.refsWindow.SetStandardFonts(font.GetPointSize(), font.GetFaceName())
            else:
                font = self.mainWindow.GetFont()
                fsize = font.GetPointSize()
                

            for token in self.display.split():
                tag,x,y = token.split('|')
                if tag == 's3' or tag == 'p3':
                    ccode, diff_size = self.readConfig()
                    font.SetPointSize(fsize-diff_size)
                    if 'wxMac' not in wx.PlatformInfo:
                        self.mainWindow.SetStyle(int(x), int(y), wx.TextAttr(ccode,wx.NullColour,font))
                    else:
                        self.mainWindow.SetStyle(int(x)-1, int(y)-1, wx.TextAttr(ccode,wx.NullColour,font))
                elif tag == 'h1' or tag == 'h2' or tag == 'h3':
                    font.SetPointSize(fsize)
                    if 'wxMac' not in wx.PlatformInfo:
                        self.mainWindow.SetStyle(int(x), int(y), wx.TextAttr('blue',wx.NullColour,font))
                    else:
                        self.mainWindow.SetStyle(int(x)-1, int(y)-1, wx.TextAttr('blue',wx.NullColour,font))


    def SetHighLight(self):
        if self.lang == 'thai' or self.lang == 'thaimm' or self.lang == 'thaiwn' or self.lang == 'thaimc' or self.lang == 'thaibt':
            keywords = self.keywords
        elif self.lang == 'pali':
            if 'wxMac' not in wx.PlatformInfo:
                keywords = self.keywords.replace(u'ฐ',u'\uf700').replace(u'ญ',u'\uf70f').replace(u'\u0e4d',u'\uf711')
            else:
                keywords = self.keywords
                
        print 'hight light', keywords        
        if self.content != u'' and keywords != u'':
            font = self.mainWindow.GetFont()
            for term in keywords.replace('+',' ').split():
                n = self.content.find(term)
                while n != -1:
                    print n, n+len(term)
                    self.mainWindow.SetStyle(n,n+len(term), wx.TextAttr('purple',wx.NullColour,font))
                    n = self.content.find(term,n+1)

    def SetContent(self,content,keywords=None,display=None,header=None,footer=None,scroll=0):
        self.keywords = keywords
        
        if self.lang == 'pali':
            self.content = content.replace(u'ฐ',u'\uf700').replace(u'ญ',u'\uf70f').replace(u'\u0e4d',u'\uf711')                
        elif self.lang == 'thai' or self.lang == 'thaimm' or self.lang == 'thaiwn' or self.lang == 'thaibt':
            self.content = content
        elif self.lang == 'thaimc':
            self.content = content
            display = '' if display == None else display
            if header != None:
                self.content = header + self.content
                display += u' h1|0|%d'%(len(header))
            if footer != None:
                self.content = self.content + footer
                display += u' s3|%d|%d'%(len(self.content)-len(footer), len(self.content))
            
        self.display = display

        self.mainWindow.SetValue(self.content)
        
        self.processTags()
        
        if keywords != None and len(keywords.strip()) > 0:
            self.SetHighLight()
            self.statusBar.SetStatusText(u'คำค้นหาคือ "%s"'%(keywords),1)
        else:
            self.statusBar.SetStatusText(u'',1)

        if scroll > 0:
            self.mainWindow.Freeze()
            x,y = self.mainWindow.PositionToXY(scroll)
            self.mainWindow.ScrollLines(y)
            self.mainWindow.Thaw()

    def SetVolumePage(self, volume, page):
        self.volume = volume
        self.page = page

    def LoadContent(self, id=None, display=None, content=None, scroll=0):
        if self.lang != 'thaibt':
            self.LoadContentNormal(scroll=scroll)
        else:
            self.SetContent(unicode(content), unicode(self.keywords), None, scroll=scroll)

    def GetContent(self, volume, page):
        if self.lang != 'thaibt':            
            select = 'SELECT * FROM %s WHERE volumn = ? AND page = ?'%(self.lang)
            args = ('%02d'%(volume), '%04d'%(page))
        else:
            select = 'SELECT * FROM speech WHERE book=? AND page=?'
            args = (volume, page)
            
        results = self.searcher1.execute(select, args)
        for result in results:
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
                r['content'] = result[3]
            yield r

    def LoadContentNormal(self, scroll=0):
        totalPage = self.dbPage['%s_%d'%(self.lang,self.volume)]
        for r in self.GetContent(self.volume, self.page):
            text = r['content']

            #add header
            tokens = self.dbName['%s_%d'%(self.lang,self.volume)].split()
            
            title1 = self.GetFullTitle(self.lang, self.volume)
            self.title1.SetValue(title1)
            font = wx.Font(self.font.GetPointSize()+2, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
            font.SetFaceName(self.font.GetFaceName())            
            self.title1.SetStyle(0,len(title1), wx.TextAttr('blue',wx.NullColour,font))
            title2 = u'%s %s'%(' '.join(tokens[:3]).decode('utf8','ignore'),' '.join(tokens[3:]).decode('utf8','ignore'))
            self.title2.SetValue(title2)
            self.title2.SetStyle(0,len(title2), wx.TextAttr('blue',wx.NullColour,font))
            pageNum = arabic2thai(u'หน้าที่ %s/%s'%(unicode(self.page),totalPage))
            self.pageNum.SetValue(pageNum)
            items = r['items'].split()
            if len(items) == 1:
                itemNum = u'ข้อที่ %s'%(items[0])
            else:
                itemNum = u'ข้อที่ %s - %s'%(items[0],items[-1])
            self.itemNum.SetValue(arabic2thai(itemNum))
            font.SetPointSize(self.font.GetPointSize()-4)
            self.pageNum.SetStyle(0,len(pageNum), wx.TextAttr('#378000',wx.NullColour,font))
            self.itemNum.SetStyle(0,len(itemNum), wx.TextAttr('#378000',wx.NullColour,font))
            self.statusBar.SetStatusText(u'',0)
            self.comboCompare.Enable()
            if self.lang == 'thaiwn':
                self.SetContent(unicode(text),unicode(self.keywords),display=r['display'],scroll=scroll)
            elif self.lang == 'thaimc':
                self.SetContent(unicode(text),unicode(self.keywords),display=r['display'],header=r['header'],footer=r['footer'],scroll=scroll)
            else:
                self.SetContent(unicode(text),unicode(self.keywords),scroll=scroll)

        self.bookLists.SetSelection(self.volume-1)

    def DoNext(self):
        if self.lang != 'thaibt':            
            if self.page < int(self.dbPage['%s_%d'%(self.lang,self.volume)]):
                self.page += 1
            self.LoadContent()
        else:
            self.LoadFiveBookContent(self.volume, self.page+1)

    def DoPrev(self):
        if self.lang != 'thaibt':
            if self.page > 1:
                self.page -= 1            
            self.LoadContent()
        else:
            self.LoadFiveBookContent(self.volume, self.page-1)                

    def OnFindClose(self, event):
        event.GetDialog().Destroy()
        self.fdlg = False

    def OnFind(self, event):
        find_string = event.GetFindString()
        text = self.mainWindow.GetValue()
        et = event.GetEventType()
        if event.GetFlags() == wx.FR_DOWN:
            p = text.find(find_string, self.mainWindow.GetInsertionPoint()+1)
        else:
            p = text.rfind(find_string, 0, self.mainWindow.GetInsertionPoint()-1)
        if p >= 0:
            self.mainWindow.SetInsertionPoint(p+len(find_string))
            self.mainWindow.SetFocus()
            self.mainWindow.SetSelection(p,p+len(find_string))
        else:
            dlg = wx.MessageDialog(self, u'ไม่พบคำว่า "%s"'%(find_string), u'E-Tipitaka', wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()

    def OnKeyDown(self, event):
        key = event.GetKeyCode()
        controlDown = event.ControlDown()
        cmdDown = event.CmdDown()
        if (controlDown or cmdDown) and key in (ord('F'), ord('f')) and not self.fdlg:
            self.fdlg = True
            data = wx.FindReplaceData(wx.FR_DOWN)
            find_dialog = wx.FindReplaceDialog(self.mainWindow, 
                data, u'ค้นหาคำในหน้านี้', style=wx.FR_NOMATCHCASE | wx.FR_NOWHOLEWORD)
            find_dialog.data = data
            find_dialog.Show(True)
        event.Skip()
        
    def OnChar(self,event):
        trans  = {3653:49,   47:50,   45:51, 3616:52, 3606:53,
                  3640:54, 3638:55, 3588:56, 3605:57, 3592:48, 3651:46}
        code = event.GetKeyCode()
        code = trans.get(code,code)
        if code == wx.WXK_LEFT:
            self.DoPrev()
            self.entering = ''
        elif code == wx.WXK_RIGHT:
            self.DoNext()
            self.entering = ''
        if (code >= 48 and code <= 57) or code == 46: # 46 = '.'
            self.entering += chr(code)
        elif code == 105 or code == 112 or code == 3618 or code == 3619: # 105 = 'i', 112 = 'p'
            try:
                if code == 3619 or code == 105:
                    self.GotoItem(self.entering)
                elif code == 3618 or code == 112:
                    self.GotoPage(self.entering)
                self.entering = ''
            except ValueError,e:
                self.entering = ''
        elif code == 43: # 43 = '+'
            self.ZoomIn()
            self.entering = ''
        elif code == 45: # 45 = '-'
            self.ZoomOut()
            self.entering = ''
        else:
            self.entering = ''
        event.Skip()
        
    def OnCheckInter(self, event):
        if self.checkBox.IsChecked():
            self.useInter = True
        else:
            self.useInter = False
            
        item = self.textItem.GetValue().strip()
        if item != u'':
            self.GotoItem(item)            
            
        event.Skip()

    def OnLinkToReference(self, lang, volume, item): 
        if item in self.dbItem[lang][volume][1]:
            page = self.dbItem[lang][volume][1][item][0]
        else:
            page = 0

        print volume, page, item

        self.resultWindow.CreateReadingFrame(volume, page, lang=lang, item=item, isCompare=True)
        self.resultWindow.VerticalAlignWindows('thaibt', lang)
