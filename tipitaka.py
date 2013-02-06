#!/usr/bin/env python

#-*- coding:utf-8 -*-

"""
E-Tipitaka: Thai Tipitaka Reading Tools
"""

import wx, os.path, sys, random
from search_window import SearchToolFrame

class MySplashScreen(wx.SplashScreen):
    """
Create a splash screen widget.
    """
    def __init__(self, parent=None):
        # This is a recipe to a the screen.
        # Modify the following variables as necessary.

        files = os.listdir(os.path.join(sys.path[0],'resources','screens'))
        files = filter(lambda x: x.split('.')[-1].lower() == 'png',files)
        aBitmap = wx.Image(name = os.path.join(sys.path[0],'resources','screens',random.choice(files))).ConvertToBitmap()
        #aBitmap = wx.Bitmap(os.path.join(sys.path[0],'resources','screens',random.choice(files)), wx.BITMAP_TYPE_PNG)


        splashStyle = wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT
        splashDuration = 10000 # milliseconds
        windowStyle = wx.NO_BORDER | wx.FRAME_NO_TASKBAR | wx.STAY_ON_TOP
        # Call the constructor with the above arguments in exactly the
        # following order.
        wx.SplashScreen.__init__(self, aBitmap, splashStyle,
                                 splashDuration, parent, style=windowStyle)
        self.Bind(wx.EVT_CLOSE, self.OnExit)
        wx.Yield()

    def OnExit(self, evt):
        self.Hide()
        evt.Skip()  # Make sure the default handler runs too...

class TipitakaApp(wx.App):
    """Application Class"""
    
    def ShowSplashScreen(self):
        self.mySplash.Show()

    def OnInit(self):
        self.mySplash = MySplashScreen()
        wx.CallAfter(self.ShowSplashScreen)
        self.searchFrame = SearchToolFrame()
        wx.CallAfter(self.HideSplashScreen)
        self.searchFrame.Show()
        self.searchFrame.Maximize()
        return True 

    def HideSplashScreen(self):
        self.mySplash.Hide()

def main():
    app = TipitakaApp(redirect=False)
    app.MainLoop()
    
if __name__ == '__main__':
    main()
