# -*- coding: utf-8 -*-
#!python

import wx
class ScrollbarFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self,None,-1,'ScrollbarExample',
        size=(300,200))
        self.scroll=wx.ScrolledWindow(self,-1)
        self.scroll.SetScrollbars(1,1,600,400)
        self.button=wx.Button(self.scroll,-1,"ScrollMe",pos=(50,20))
        self.Bind(wx.EVT_BUTTON,self.OnClickTop,self.button)
        self.button2=wx.Button(self.scroll,-1,"ScrollBack",pos=(500,350))
        self.Bind(wx.EVT_BUTTON,self.OnClickBottom,self.button2)
    def OnClickTop(self,event):
        self.scroll.Scroll(600,400)

    def OnClickBottom(self,event):
        self.scroll.Scroll(1,1)

if __name__ == '__main__':
    res = []
    res2 = []
    for r1 in (1.0,2.2,3.3,6.6,12.0,20.0):
        for r2 in (3.6,13.0,25.0,57.0,61.0,78.0,87.8,98.0):
            res.append((r1+r2)/r1)
    res2 = res.sort()
    print res2
    for i in res:
        print i

