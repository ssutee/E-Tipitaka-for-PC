#-*- coding:utf-8 -*-

import wx
import wx.lib.buttons as buttons
import wx.html

import cPickle, re, os.path, sys, codecs
from utils import arabic2thai,thai2arabic
import manifest

class AboutDialog(wx.Dialog):
    def __init__(self,parent,pos):
        wx.Dialog.__init__(self,parent,-1, u'เกี่ยวกับโปรแกรม E-Tipitaka',size=(530,180),pos=pos)
        label1 = wx.StaticText(self,-1,u'E-Tipitaka %s - พัฒนาโดย นายสุธี สุดประเสริฐ สงวนลิขสิทธิ์ (C) 2010\nเขียนด้วย Python 2.5.4 และ wxPython 2.8 (unicode)' % (manifest.__version__))
        label2 = wx.StaticText(self,-1,u'โปรแกรมนี้เป็นซอฟแวร์เสรีและสามารถแจกจ่ายได้ตามสนธิสัญญา GNU General Public License')
        label3 = wx.StaticText(self,-1,u'หากมีคำแนะนำ หรือ พบข้อผิดพลาดของโปรแกรม \nกรุณาแจ้งที่ <e.tipitaka@gmail.com>')
        btnOk = wx.Button(self,wx.ID_OK,u'ตกลง')
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(label1,0, wx.EXPAND|wx.ALL, 10)
        mainSizer.Add(label2,0, wx.EXPAND|wx.ALL, 10)
        bottomSizer = wx.BoxSizer(wx.HORIZONTAL)
        bottomSizer.Add(label3,flag=wx.ALIGN_CENTER_VERTICAL)
        bottomSizer.Add((20,20),1,wx.EXPAND)
        bottomSizer.Add(btnOk)
        mainSizer.Add(bottomSizer,0,wx.EXPAND|wx.ALL, 10)
        self.SetSizer(mainSizer)
                                 
class BookMarkDialog(wx.Dialog):
    def __init__(self,parent,pos):
        wx.Dialog.__init__(self,parent,-1, u'โปรดใส่ข้อมูลของคั่นหน้า',size=(200,100),pos=pos)
        
        nameLbl = wx.StaticText(self,-1, u'หมายเหตุ :')
        self.name = wx.TextCtrl(self,-1, u'',validator=NotEmptyValidator())
        self.name.SetFocus()
        mainSizer = wx.BoxSizer(wx.VERTICAL)       
        s1 = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
        s1.AddGrowableCol(1)
        s1.Add(nameLbl,0,wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        s1.Add(self.name, 0, wx.EXPAND)
        mainSizer.Add(s1,0,wx.EXPAND|wx.ALL,10)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btnOk = wx.Button(self, wx.ID_OK, u'ตกลง',size=(-1,-1))
        self.btnCancel = wx.Button(self, wx.ID_CANCEL, u'ยกเลิก',size=(-1,-1))
        self.btnOk.SetDefault()
        btnSizer.Add((20,20),1)
        btnSizer.Add(self.btnOk)
        btnSizer.Add((10,20))
        btnSizer.Add(self.btnCancel)
        btnSizer.Add((20,20),1)
        mainSizer.Add(btnSizer,0,wx.EXPAND|wx.BOTTOM,10)
        self.SetSizer(mainSizer)
              
    def GetName(self):
        return self.name.GetValue()

class WarningDialog(wx.Dialog):
    def __init__(self,parent,msg1,msg2,lb1,lb2,size=(400,135)):
        wx.Dialog.__init__(self, parent, -1, u'คำเตือน', size=size)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add((-1,10),flag=wx.EXPAND)
        s1 = wx.BoxSizer(wx.HORIZONTAL)
        s1.Add((20,-1),1,flag=wx.EXPAND)
        s1.Add(wx.StaticText(self,-1,u'%s'%(msg1),style=wx.ALIGN_CENTER))
        s1.Add((20,-1),1,flag=wx.EXPAND)
        
        s2 = wx.BoxSizer(wx.HORIZONTAL)
        s2.Add((20,-1),1,flag=wx.EXPAND)
        s2.Add(wx.StaticText(self,-1,u'%s'%(msg2),style=wx.ALIGN_CENTER))
        s2.Add((20,-1),1,flag=wx.EXPAND)
        
        mainSizer.Add(s1,flag=wx.EXPAND)
        mainSizer.Add(s2,flag=wx.EXPAND)
        mainSizer.Add((-1,10),flag=wx.EXPAND)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btnOk = wx.Button(self, wx.ID_OK, u'%s'%(lb1),size=(-1,-1))
        self.btnCancel = wx.Button(self, wx.ID_CANCEL, u'%s'%(lb2),size=(-1,-1))
        self.btnOk.SetDefault()
        btnSizer.Add((20,-1),1,flag=wx.EXPAND)
        btnSizer.Add(self.btnOk,flag=wx.EXPAND)
        btnSizer.Add((10,-1))
        btnSizer.Add(self.btnCancel,flag=wx.EXPAND)
        btnSizer.Add((20,-1),1,flag=wx.EXPAND)
        mainSizer.Add(btnSizer,flag=wx.EXPAND)
        self.SetSizer(mainSizer)

class ChoosePagesDialog(wx.Dialog):
    def __init__(self,parent,msg1,msg2,num,data):
        wx.Dialog.__init__(self, parent, -1, u'โปรดเลือกหน้าที่ต้องการบันทึก', size=(350,170))
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        s1 = wx.BoxSizer(wx.HORIZONTAL)
        s1.Add((20,-1),1,flag=wx.EXPAND)
        s1.Add(wx.StaticText(self,-1,u'%s'%(msg1),style=wx.ALIGN_CENTER))
        s1.Add((20,-1),1,flag=wx.EXPAND)
        
        s2 = wx.BoxSizer(wx.HORIZONTAL)
        s2.Add((20,-1),1,flag=wx.EXPAND)
        s2.Add(wx.StaticText(self,-1,u'%s'%(msg2),style=wx.ALIGN_CENTER))
        s2.Add((20,-1),1,flag=wx.EXPAND)

        s3 = wx.BoxSizer(wx.HORIZONTAL)
        s3.Add((20,-1),1,flag=wx.EXPAND)
        s3.Add(wx.StaticText(self,-1,u'หน้า',style=wx.ALIGN_CENTER))
        s3.Add((20,-1),1,flag=wx.EXPAND)
        
        rangeSizer = wx.BoxSizer(wx.HORIZONTAL)

        fromChoice = wx.ComboBox(self,-1,size=(70,-1),
                                 choices=[u'%d'%(x) for x in range(1,num+1)],validator=DataXferPagesValidator(data,'from'))
        toChoice = wx.ComboBox(self,-1,size=(70,-1),
                               choices=[u'%d'%(x) for x in range(1,num+1)],validator=DataXferPagesValidator(data,'to'))
        
        rangeSizer.Add((20,-1),1,flag=wx.EXPAND)
        rangeSizer.Add(fromChoice)
        rangeSizer.Add(wx.StaticText(self,-1,u' ถึง ',style=wx.ALIGN_CENTER),flag=wx.ALIGN_CENTER_VERTICAL)
        rangeSizer.Add(toChoice)
        rangeSizer.Add((20,-1),1,flag=wx.EXPAND)
        
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnOk = wx.Button(self, wx.ID_OK, u'ตกลง',size=(-1,-1))
        btnCancel = wx.Button(self, wx.ID_CANCEL, u'ยกเลิก',size=(-1,-1))
        btnOk.SetDefault()
        btnSizer.Add((20,-1),1,flag=wx.EXPAND)
        btnSizer.Add(btnOk,flag=wx.EXPAND)
        btnSizer.Add((10,-1))
        btnSizer.Add(btnCancel,flag=wx.EXPAND)
        btnSizer.Add((20,-1),1,flag=wx.EXPAND)

        mainSizer.Add((-1,10),flag=wx.EXPAND)
        mainSizer.Add(s1,flag=wx.EXPAND)
        mainSizer.Add((-1,5),flag=wx.EXPAND)
        mainSizer.Add(s2,flag=wx.EXPAND)
        mainSizer.Add((-1,10),flag=wx.EXPAND)
        mainSizer.Add(s3,flag=wx.EXPAND)
        mainSizer.Add((-1,5),flag=wx.EXPAND)
        mainSizer.Add(rangeSizer,flag=wx.EXPAND)
        mainSizer.Add((-1,15),flag=wx.EXPAND)
        mainSizer.Add(btnSizer,flag=wx.EXPAND)
        self.SetSizer(mainSizer)
        
class SelectBooksDialog(wx.Dialog):
    def __init__(self, checkedItems=(), lang='thai'):
        self.lang = lang
        w,h = wx.GetDisplaySize()
        self.margin = 150
        wx.Dialog.__init__(self, None, -1, u'โปรดเลือกเล่มที่ต้องการค้นหา',size=(w-self.margin,h-self.margin-30),pos=(self.margin/2,self.margin/2))
        f = open(os.path.join(sys.path[0],'resources','book_name.pkl'),'rb')
        db = cPickle.load(f)
        f.close()
        if lang == 'thai' or lang == 'pali' or lang == 'thaiwn':
            self.checklist = wx.CheckListBox(self, -1, 
                choices=[arabic2thai(u'พระไตรปิฎกเล่มที่ %d %s'%(x,db['thai_'+str(x)].decode('utf8'))) for x in range(1,46)])
        elif lang == 'thaimm':
            self.checklist = wx.CheckListBox(self, -1, 
                choices=[arabic2thai(u'พระไตรปิฎกเล่มที่ %d %s'%(x,db['thaimm_'+str(x)].decode('utf8'))) for x in range(1,92)])

        for i in checkedItems:
            self.checklist.Check(i,True)

        self.checklist.Bind(wx.EVT_CHECKLISTBOX, self.OnCheckListBox)
            
        leftSizer = wx.BoxSizer(wx.VERTICAL)
        self.btnFirst = wx.Button(self, -1, u'พระวินัยปิฎก')
        self.btnSecond = wx.Button(self, -1, u'พระสุตตันตปิฎก')
        self.btnThird = wx.Button(self, -1, u'พระอภิธรรมปิฎก')
        self.btnSelAll = wx.Button(self, -1, u'เลือกทั้งหมด')
        self.btnDelAll = wx.Button(self, -1, u'ลบทั้งหมด')

        self.btnFirst.Bind(wx.EVT_BUTTON,self.OnClickFirst)
        self.btnSecond.Bind(wx.EVT_BUTTON,self.OnClickSecond)
        self.btnThird.Bind(wx.EVT_BUTTON,self.OnClickThird)
        self.btnSelAll.Bind(wx.EVT_BUTTON,self.OnClickSelAll)
        self.btnDelAll.Bind(wx.EVT_BUTTON,self.OnClickDelAll)

        self.btnOk = wx.Button(self, wx.ID_OK, u'ตกลง')
        self.btnOk.SetDefault()
        self.btnCancel = wx.Button(self, wx.ID_CANCEL, u'ยกเลิก')

        if len(checkedItems) == 0:
            self.btnOk.Disable()
        
        leftSizer.Add(self.btnFirst,flag=wx.EXPAND)
        leftSizer.Add(self.btnSecond,flag=wx.EXPAND)
        leftSizer.Add(self.btnThird,flag=wx.EXPAND)
        leftSizer.Add((-1,30),flag=wx.EXPAND)
        leftSizer.Add(self.btnSelAll,flag=wx.EXPAND)
        leftSizer.Add(self.btnDelAll,flag=wx.EXPAND)
        leftSizer.Add((-1,-1),1,flag=wx.EXPAND)
        leftSizer.Add(self.btnOk,flag=wx.EXPAND)
        leftSizer.Add(self.btnCancel,flag=wx.EXPAND)

        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        mainSizer.Add(leftSizer,flag=wx.EXPAND)
        mainSizer.Add(self.checklist,1,flag=wx.EXPAND)
        self.SetSizer(mainSizer)

    def GetCheckedItems(self):
        results = ()
        for i in range(self.checklist.GetCount()):
            if self.checklist.IsChecked(i):
                results += (i,)
        return results

    def OnClickFirst(self, event):
        if self.lang == 'thaimm':
            for i in range(10):
                self.checklist.Check(i,True)
        else:
            for i in range(8):
                self.checklist.Check(i,True)
        self.btnOk.Enable()
        event.Skip()
        
    def OnClickSecond(self, event):
        if self.lang == 'thaimm':
            for i in range(10,74):
                self.checklist.Check(i,True)
        else:
            for i in range(8,33):
                self.checklist.Check(i,True)
        self.btnOk.Enable()
        event.Skip()
        
    def OnClickThird(self, event):
        if self.lang == 'thaimm':
            for i in range(74,91):
                self.checklist.Check(i,True)
        else:
            for i in range(33,45):
                self.checklist.Check(i,True)
            
        self.btnOk.Enable()
        event.Skip()
        
    def OnClickSelAll(self, event):
        if self.lang == 'thaimm':
            for i in range(91):
                self.checklist.Check(i,True)
        else:
            for i in range(45):
                self.checklist.Check(i,True)

        self.btnOk.Enable()
        event.Skip()
        
    def OnClickDelAll(self, event):
        if self.lang == 'thaimm':
            for i in range(91):
                self.checklist.Check(i,False)
        else:
            for i in range(45):
                self.checklist.Check(i,False)

        self.btnOk.Disable()    
        event.Skip()
        
    def OnCheckListBox(self, event):
        if len(self.GetCheckedItems()) == 0:
            self.btnOk.Disable()
        else:
            self.btnOk.Enable()
        event.Skip()
        
class NotEmptyValidator(wx.PyValidator):
    def __init__(self):
        wx.PyValidator.__init__(self)
        
    def Clone(self):
        return NotEmptyValidator()
        
    def Validate(self, win):
        textCtrl = self.GetWindow()
        text = textCtrl.GetValue()
        
        if len(text.strip()) == 0:
            wx.MessageBox(u'ช่องนี้ไม่สามารถเว้นว่างได้',u'พบข้อผิดพลาด')
            textCtrl.SetBackgroundColour('pink')
            textCtrl.Refresh()
            return False
        else:
            textCtrl.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
            textCtrl.Refresh()
            return True
    
    def TransferToWindow(self):
        return True
        
    def TransferFromWindow(self):
        return True
        
class DataXferPagesValidator(wx.PyValidator):
    def __init__(self, data, key):
        wx.PyValidator.__init__(self)
        self.data = data
        self.key = key
        self.Bind(wx.EVT_CHAR, self.OnChar)
        
    def Clone(self):
        return DataXferPagesValidator(self.data, self.key)
        
    def Validate(self, win):
        combo = self.GetWindow()
        text = combo.GetValue()
        if len(text.strip()) == 0:
            wx.MessageBox(u'ช่องนี้ไม่สามารถเว้นว่างได้',u'พบข้อผิดพลาด')
            combo.SetBackgroundColour('pink')
            combo.Refresh()
            return False
        else:
            combo.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
            combo.Refresh()
            return True
        
    def TransferToWindow(self):
        combo = self.GetWindow()
        combo.SetSelection(self.data.get(self.key,0))
        return True
        
    def TransferFromWindow(self):
        combo = self.GetWindow()
        self.data[self.key] = int(combo.GetValue())-1
        return True
        
    def OnChar(self, event):
        code = event.GetKeyCode()
        combo = self.GetWindow()
        text = combo.GetValue()
        count = combo.GetCount()
        
        if (code < 48 or code > 57) and code != 8:
            return
            
        if (code >= 48 and code <= 57) and int(text + chr(code)) > count:
            return

        if text == '' and code == 48:
            return
            
        event.Skip()
