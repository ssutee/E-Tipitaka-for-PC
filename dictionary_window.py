#-*- coding:utf-8 -*-

import wx
import sys, os.path, cPickle, sqlite3

class DictWindow(wx.Frame):
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)

        # set icon
        icon = wx.IconBundle()
        icon.AddIconFromFile(os.path.join(sys.path[0],'resources','dict.ico'), wx.BITMAP_TYPE_ANY)
        self.SetIcons(icon)


        self.SetWindowStyle( self.GetWindowStyle() | wx.STAY_ON_TOP ) 
        
        self.SetSize((600,400))
        self.Center()
        
        font = wx.Font(18, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        font.SetFaceName('TF Chiangsaen')
        #self.SetFont(font)

        mainSizer = wx.BoxSizer(wx.VERTICAL)

        self.hboxToolbar = wx.BoxSizer(wx.HORIZONTAL)

        labelWord = wx.StaticText(self, -1, u'ค้นหา: ')
        self.input = wx.TextCtrl(self, -1, pos=(0,0), size=(-1,-1), style=wx.TE_PROCESS_ENTER)
        self.input.SetFont(font)
        self.input.Bind(wx.EVT_TEXT_ENTER, self.OnTextEntered)
        self.input.Bind(wx.EVT_TEXT, self.OnTextEntered)

        self.hboxToolbar.Add(labelWord, 0, wx.ALL | wx.CENTER | wx.ALIGN_RIGHT, 5)
        self.hboxToolbar.Add(self.input, 1, wx.ALL | wx.CENTER, 1)
        
        mainSizer.Add(self.hboxToolbar,0,wx.EXPAND | wx.ALL)

        self.sp = wx.SplitterWindow(self,-1)
        mainSizer.Add(self.sp,1,wx.EXPAND)
        
        self.rightPanel = wx.Panel(self.sp,-1)
        self.text = wx.TextCtrl(self.rightPanel, -1, style=wx.TE_READONLY|wx.TE_RICH2|wx.TE_MULTILINE)
        self.text.SetFont(font)

        rightSizer = wx.StaticBoxSizer(wx.StaticBox(self.rightPanel, -1, u'คำแปล'), wx.VERTICAL)
        rightSizer.Add(self.text,1,wx.ALL | wx.EXPAND,0)
        self.rightPanel.SetSizer(rightSizer)
        self.rightPanel.SetAutoLayout(True)
        rightSizer.Fit(self.rightPanel)
        
        lpID = wx.NewId()
        #self.leftPanel = wx.Panel(self.sp,lpID)

        #self.wordList = wx.ListBox(self.leftPanel,-1,choices=[],style=wx.LB_SINGLE)
        #self.wordList.Bind(wx.EVT_LISTBOX, self.OnSelectWord)
        #self.wordList.Bind(wx.EVT_LISTBOX_DCLICK, self.OnDoubleClick)
        tID = wx.NewId()
        self.wordList = wx.ListCtrl(self.sp,tID,style=wx.LC_REPORT | wx.BORDER_NONE | wx.LC_SINGLE_SEL)
        self.wordList.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelectWord)
        self.wordList.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
        self.wordList.SetFont(font)
        self.wordList.InsertColumn(0,u"คำศัพท์")
        self.wordList.SetColumnWidth(0, 250)

        #leftSizer = wx.StaticBoxSizer(wx.StaticBox(self.leftPanel, -1, u'คำศัพท์'), wx.VERTICAL)
        #leftSizer.Add(self.wordList,1,wx.ALL | wx.EXPAND,0)
        #self.leftPanel.SetSizer(leftSizer)
        #self.leftPanel.SetAutoLayout(True)
        #leftSizer.Fit(self.leftPanel)
        
        self.sp.SplitVertically(self.wordList,self.rightPanel,200)
        self.sp.SetSashSize(5)
        
        self.SetSizer(mainSizer)

        searchWindow = self.GetParent().resultWindow.GetParent()

        self.conn = sqlite3.connect(os.path.join(sys.path[0],'resources','p2t_dict.db'))
        cursor = self.conn.cursor()

        cursor.execute('SELECT * FROM p2t')
        self.all_items = cursor.fetchall()

        #self.dbDict = searchWindow.dbDict
        #self.all_items = searchWindow.all_items

        self.input.SetValue('')

    def SetContent(self,content):
        self.text.SetValue(content)

    def SetInput(self,text):
        self.input.SetValue(text)
        
    def OnClose(self, event):
        self.Hide()
        event.Skip()

    def OnTextEntered(self, event):
        text = self.input.GetValue().strip()

        text1 = text.replace(u'\u0e0d',u'\uf70f').replace(u'\u0e4d',u'\uf711').replace(u'ฐ',u'\uf700')
        text1 = text1.encode('utf8')

        text2 = text.replace(u'\u0e0d',u'\uf70f').replace(u'\u0e4d',u'\uf711')
        text2 = text2.encode('utf8')

        self.wordList.DeleteAllItems()

        if text != '':
            items = self.LookupDictSQLite(text1,text2,prefix=True)
            if len(items) > 0:
                for i,item in enumerate(items):
                    self.wordList.InsertStringItem(i,item[0])
            else:
                self.text.SetValue(text + u'\n\n'+u'ไม่พบคำนี้ในพจนานุกรม')
        else:
            self.text.SetValue(text + u'\n'+u'กรุณาป้อนคำที่ต้องการค้นหา')
            
        #if len(items) > 0:
        #    self.wordList.InsertStringItem(0,items[0][0])

        """
        if len(items) > 0:
            self.wordList.SetItems(map(lambda x:x[0].decode('utf8'), items))        
            word = self.wordList.GetString(0)
            item = self.LookupDict(word)
            if item != None:
                tran = self.dbDict['index'][item[1]].decode('utf8')
                self.text.SetValue(word+u'\n\n'+tran)
            self.wordList.Select(0)
        else:
            self.wordList.Clear()
            self.text.SetValue(text.decode('utf8') + u'\n\n'+u'ไม่พบคำนี้ในพจนานุกรม')
        """

        event.Skip()

    def LookupDictSQLite(self, word1, word2=None, prefix=False):
        cursor = self.conn.cursor()
        if prefix:
            if word2:                
                cursor.execute("SELECT * FROM p2t WHERE headword LIKE '%s%%' OR headword LIKE '%s%%' "%(word1,word2))
            else:
                cursor.execute("SELECT * FROM p2t WHERE headword LIKE '%s%%' "%(word1))
                
            return cursor.fetchmany(size=50)
        else:
            if word2:
                cursor.execute("SELECT * FROM p2t WHERE headword = '%s' OR headword = '%s'"%(word1,word2))
            else:
                cursor.execute("SELECT * FROM p2t WHERE headword = '%s' "%(word1))
                
            return cursor.fetchone()            

    def LookupDict(self, word):
        items = self.dbDict['dict'].items(word.encode('utf8'))
        if len(items) > 0:
            return items[0]
        return None

    def OnSelectWord(self, event):
        self.currentItem =  event.m_itemIndex
        word = self.wordList.GetItemText(self.currentItem)
        item = self.LookupDictSQLite(word)
        if item != None:
            tran = item[1]
            self.text.SetValue(word+u'\n\n'+tran)
        event.Skip()

    def OnDoubleClick(self, event):
        word = self.wordList.GetItemText(self.currentItem)
        self.input.SetValue(word)
        event.Skip()
