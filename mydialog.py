#-*- coding:utf-8 -*-

import wx
import wx.lib.buttons as buttons
import wx.html
from wx.lib.combotreebox import ComboTreeBox

import cPickle, re, os.path, sys, codecs
from utils import arabic2thai,thai2arabic
import manifest

class BookmarkFolderDialog(wx.Dialog):
    def __init__(self, parent, items, source=None):
        wx.Dialog.__init__(self, parent, -1, u'เลือกกลุ่ม', size=(300, 350))
        self.source = source
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Center()
        self.items = items
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.tree = wx.TreeCtrl(self, -1, style=wx.TR_DEFAULT_STYLE)
        sizer.Add(self.tree, 1, wx.EXPAND|wx.ALL, 10)
        selectButton = wx.Button(self, -1, u'ตกลง')
        selectButton.Bind(wx.EVT_BUTTON, self.OnSelectButton)
        sizer.Add(selectButton, 0, wx.ALIGN_CENTER|wx.BOTTOM, 10)
        self.SetSizer(sizer)
        self.CreateTree()

    def OnSelectButton(self, event):
        self.value = self.tree.GetPyData(self.tree.GetSelection())
        self.EndModal(wx.ID_OK)

    def GetValue(self):
        return getattr(self, 'value', None)

    def CreateTree(self):
            
        def Create(tree, root, items):
            for item in items:
                if isinstance(item ,dict) and item is not self.source:
                    folder = item.keys()[0]
                    child = tree.AppendItem(root, folder)
                    tree.SetPyData(child, item[folder])
                    tree.SetItemImage(child, self.fldridx, wx.TreeItemIcon_Normal)
                    tree.SetItemImage(child, self.fldropenidx, wx.TreeItemIcon_Expanded)
                    Create(tree, child, item[folder])
            
        isz = (16,16)
        il = wx.ImageList(isz[0], isz[1])
        self.fldridx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, isz))
        self.fldropenidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN, wx.ART_OTHER, isz))
        self.tree.SetImageList(il)        
        self.il = il
            
        root = self.tree.AddRoot(u'หลัก')
        self.tree.SetPyData(root, self.items)
        Create(self.tree, root, self.items)
        self.tree.ExpandAll()

    def OnClose(self, event):
        self.tree.DeleteAllItems()
        event.Skip()
        
class BookmarkManagerDialog(wx.Dialog):
    def __init__(self, parent, items):
        wx.Dialog.__init__(self, parent, -1, u'ตัวจัดการที่คั่นหน้า', size=(600, 400))
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Center()
        self.items = items
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.tree = wx.TreeCtrl(self, -1, style=wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT)

        sizer.Add(self.tree, 1, wx.EXPAND|wx.ALL, 10)        
        bottomSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.CreateButton = wx.Button(self, -1, u'สร้างกลุ่ม')
        self.CreateButton.Bind(wx.EVT_BUTTON, self.OnCreateButton)
        self.DeleteButton = wx.Button(self, -1, u'ลบ')
        self.DeleteButton.Bind(wx.EVT_BUTTON, self.OnDeleteButton)
        self.MoveButton = wx.Button(self, -1, u'ย้ายกลุ่ม')
        self.MoveButton.Bind(wx.EVT_BUTTON, self.OnMoveButton)
        self.EditButton = wx.Button(self, -1, u'แก้ไข')
        self.EditButton.Bind(wx.EVT_BUTTON, self.OnEditButton)

        bottomSizer.Add((10,-1), 0)
        bottomSizer.Add(self.CreateButton, 1, wx.EXPAND)
        bottomSizer.Add(self.MoveButton, 1, wx.EXPAND)
        bottomSizer.Add(self.EditButton, 1, wx.EXPAND)        
        bottomSizer.Add(self.DeleteButton, 1, wx.EXPAND)        
        bottomSizer.Add((10,-1), 0)                
        
        sizer.Add(bottomSizer, 0, wx.EXPAND|wx.BOTTOM, 10)
        self.SetSizer(sizer)
        self.Reload()        
        
    def OnClose(self, event):
        self.tree.DeleteAllItems()
        event.Skip()
        
    def OnEditButton(self, event):
        item = self.tree.GetPyData(self.tree.GetSelection())
        if isinstance(item ,dict):
            dialog = wx.TextEntryDialog(self, u'กรุณาป้อนชื่อกลุ่ม', u'เปลี่ยนชื่อกลุ่ม')
            dialog.SetValue(item.keys()[0])
            dialog.Center()
            if dialog.ShowModal() == wx.ID_OK:
                item[dialog.GetValue().strip()] = item.pop(item.keys()[0])
                self.Reload()
            dialog.Destroy()
        elif isinstance(item, tuple):
            dialog = wx.TextEntryDialog(self, u'กรุณาป้อนข้อมูลของคั่นหน้า', u'เปลี่ยนข้อมูลคั่นหน้า')
            dialog.SetValue(':'.join(item[2].split(':')[1:]).strip())
            dialog.Center()
            if dialog.ShowModal() == wx.ID_OK:
                container = self.FindContainer(item, self.items)
                note = item[2].split(':')[0].strip() + ' : ' + dialog.GetValue().strip()
                container.append((item[0], item[1], note))
                self.Delete(container, item)
                self.Reload()
            dialog.Destroy()
        
    def OnMoveButton(self, event):
        source = self.tree.GetPyData(self.tree.GetSelection())
        if source != None:
            dialog = BookmarkFolderDialog(self, self.items, source)
            if dialog.ShowModal() == wx.ID_OK:
                target = dialog.GetValue()
                if isinstance(target, list):
                    self.Delete(self.items, source)
                    target.append(source)
                    self.Reload()
            dialog.Destroy()
    
    def FindContainer(self, item, items):
        for i in xrange(len(items)):
            if item is items[i]:
                return items
            elif isinstance(items[i], dict):
                container = self.FindContainer(item, items[i].values()[0])
                if container != None: return container
        return None

        
    def OnCreateButton(self, event):    
        dialog = wx.TextEntryDialog(self, u'กรุณาป้อนชื่อกลุ่ม', u'สร้างกลุ่ม')
        dialog.Center()
        if dialog.ShowModal() == wx.ID_OK:
            item = self.tree.GetPyData(self.tree.GetSelection()) if self.tree.GetSelection() else None
            container = self.FindContainer(item, self.items) if item != None else self.items
            folder = dialog.GetValue().strip()
            container.append({folder:[]})
            container.sort()
            self.Reload()
        dialog.Destroy()
        
    def Delete(self, items, item):
        for i,child in enumerate(items):
            if child is item:
                del items[i]
                break;
            elif isinstance(child, dict):
                self.Delete(child.values()[0], item)
        
    def OnDeleteButton(self, event):    
        item = self.tree.GetPyData(self.tree.GetSelection())
        if item != None:
            dialog = wx.MessageDialog(self, u'คุณต้องการลบการจดจำนี้หรือไม่?' + 
                u' (ถ้าลบกลุ่ม การจดจำทั้งหมดในกลุ่มจะถูกลบไปด้วย)', u'ยืนยันการลบ', 
                wx.YES_NO | wx.ICON_INFORMATION)
            dialog.Center()
            if dialog.ShowModal() == wx.ID_YES:
                self.Delete(self.items, item)
                self.Reload()                
            dialog.Destroy()
        
    def Reload(self):

        def Load(tree, root, items):
            for item in items:
                if isinstance(item, dict):
                    folder = item.keys()[0]
                    child = tree.AppendItem(root, folder)
                    tree.SetPyData(child, item)
                    tree.SetItemImage(child, self.fldridx, wx.TreeItemIcon_Normal)
                    tree.SetItemImage(child, self.fldropenidx, wx.TreeItemIcon_Expanded)
                    Load(tree, child, item[folder])
                elif isinstance(item, tuple):
                    child = tree.AppendItem(root, item[2])
                    tree.SetPyData(child, item)
                    tree.SetItemImage(child, self.fileidx, wx.TreeItemIcon_Normal)
                    
        self.tree.DeleteAllItems()

        isz = (16,16)
        il = wx.ImageList(isz[0], isz[1])
        self.fldridx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, isz))
        self.fldropenidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN, wx.ART_OTHER, isz))
        self.fileidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, isz))
        self.tree.SetImageList(il)        
        self.il = il
        
        root = self.tree.AddRoot("root")
        self.tree.SetPyData(root, None)
        Load(self.tree, root, self.items)
        self.tree.ExpandAll()
        
class AboutDialog(wx.Dialog):
    def __init__(self,parent,pos):
        wx.Dialog.__init__(self,parent,-1, u'เกี่ยวกับโปรแกรม E-Tipitaka',size=(530,180),pos=pos)
        label1 = wx.StaticText(self,-1,u'E-Tipitaka %s - พัฒนาโดย นายสุธี สุดประเสริฐ สงวนลิขสิทธิ์ (C) 2010\nเขียนด้วย Python 2.7.3 และ wxPython 2.8 (unicode)' % (manifest.__version__))
        label2 = wx.StaticText(self,-1,u'โปรแกรมนี้เป็นซอฟแวร์เสรีและสามารถแจกจ่ายได้ตามสนธิสัญญา Apache License, Version 2.0')
        label3 = wx.StaticText(self,-1,u'หากมีคำแนะนำ หรือ พบข้อผิดพลาดของโปรแกรม \nกรุณาแจ้งที่ <etipitaka@gmail.com>')
        btnOk = wx.Button(self,wx.ID_OK,u'ตกลง')
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        bottomSizer = wx.BoxSizer(wx.HORIZONTAL)
        bottomSizer.Add(label3,flag=wx.ALIGN_CENTER_VERTICAL)
        bottomSizer.Add((20,20),1,wx.EXPAND)
        bottomSizer.Add(btnOk)
                
        mainSizer.Add((-1,10),1,flag=wx.EXPAND)
        mainSizer.Add(label1,0, wx.EXPAND|wx.ALL, 10)
        mainSizer.Add(label2,0, wx.EXPAND|wx.ALL, 10)                
        mainSizer.Add(bottomSizer,0,wx.EXPAND|wx.ALL, 10)
        mainSizer.Add((-1,10),1,flag=wx.EXPAND)        
        self.SetSizer(mainSizer)
                                 
class BookMarkDialog(wx.Dialog):
    def __init__(self, parent, pos, items):
        wx.Dialog.__init__(self,parent,-1, u'โปรดใส่ข้อมูลของคั่นหน้า', size=(350,130), pos=pos)
        self.items = items
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer1.Add(wx.StaticText(self, -1, u'หมายเหตุ :', size=(70,-1), style=wx.ALIGN_RIGHT), 0, wx.ALIGN_CENTER)
        self.NoteText = wx.TextCtrl(self, -1)
        sizer1.Add(self.NoteText, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER, 8)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(wx.StaticText(self, -1, u'กลุ่ม :', size=(70,-1), style=wx.ALIGN_RIGHT), 0, wx.ALIGN_CENTER)
        self.ComboBox = self.CreateComboBox()
        sizer2.Add(self.ComboBox, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER, 8)
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        self.CancelButton = wx.Button(self, wx.ID_CANCEL, u'ยกเลิก')
        self.SaveButton = wx.Button(self, -1, u'บันทึก')
        self.SaveButton.Bind(wx.EVT_BUTTON, self.OnSaveButton)
        sizer3.Add((-1,-1), 1, wx.EXPAND)
        sizer3.Add(self.CancelButton, 0, wx.RIGHT, 10)
        sizer3.Add(self.SaveButton, 0, wx.RIGHT, 10)
        mainSizer.Add(sizer1, 0, wx.EXPAND|wx.TOP, 10)
        mainSizer.Add((-1, 5), 0)
        mainSizer.Add(sizer2, 0, wx.EXPAND|wx.TOP)
        mainSizer.Add((-1,-1), 1, wx.EXPAND)
        mainSizer.Add(sizer3, 0, wx.EXPAND|wx.BOTTOM, 10)
        self.SetSizer(mainSizer)

    def GetValue(self):
        return getattr(self, 'value', None)

    def CreateComboBox(self):
        
        def _createComboBox(comboBox, root, items):
            for item in items:
                if isinstance(item, dict):
                    child = comboBox.Append(item.keys()[0], root, clientData=item.values()[0])
                    _createComboBox(comboBox, child, item.values()[0])
                    
        comboBox = ComboTreeBox(self, wx.CB_READONLY) 
        root = comboBox.Append(u'หลัก', clientData=self.items)
        _createComboBox(comboBox, root, self.items)
        comboBox.SetSelection(root)
        comboBox.GetTree().ExpandAll()       
        return comboBox
        
    def OnSaveButton(self, event):
        item = self.ComboBox.GetSelection()
        note = self.NoteText.GetValue()
        if item:
            container = self.ComboBox.GetClientData(item)
            self.value = (container, note.strip())
            self.EndModal(wx.ID_OK)

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
    def __init__(self,parent,title,msg1,msg2,num,data):
        wx.Dialog.__init__(self, parent, -1, title, size=(350,200))
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
        rangeSizer.Add((5,-1)) 
        rangeSizer.Add(wx.StaticText(self,-1,u' ถึง ',style=wx.ALIGN_CENTER),flag=wx.ALIGN_CENTER_VERTICAL)
        rangeSizer.Add((5,-1))        
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

        mainSizer.Add((-1,10),1,flag=wx.EXPAND)
        mainSizer.Add(s1,flag=wx.EXPAND)
        mainSizer.Add((-1,5),flag=wx.EXPAND)
        mainSizer.Add(s2,flag=wx.EXPAND)
        mainSizer.Add((-1,10),flag=wx.EXPAND)
        mainSizer.Add(s3,flag=wx.EXPAND)
        mainSizer.Add((-1,5),flag=wx.EXPAND)
        mainSizer.Add(rangeSizer,flag=wx.EXPAND)
        mainSizer.Add((-1,15),flag=wx.EXPAND)
        mainSizer.Add(btnSizer,flag=wx.EXPAND)
        mainSizer.Add((-1,10),1,flag=wx.EXPAND)
        
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
        if lang == 'thai' or lang == 'pali' or lang == 'thaiwn' or lang == 'thaimc':
            self.checklist = wx.CheckListBox(self, -1, 
                choices=[arabic2thai(u'พระไตรปิฎกเล่มที่ %d %s'%(x,db['thai_'+str(x)].decode('utf8','ignore'))) for x in range(1,46)])
        elif lang == 'thaimm':
            self.checklist = wx.CheckListBox(self, -1, 
                choices=[arabic2thai(u'พระไตรปิฎกเล่มที่ %d %s'%(x,db['thaimm_'+str(x)].decode('utf8','ignore'))) for x in range(1,92)])

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
