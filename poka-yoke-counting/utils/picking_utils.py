from json import JSONEncoder
from tkinter import *
from tkinter import messagebox

class Point:
    def __init__(self, x: int, y: int):
        self.X = x
        self.Y = y

class Rect:
    def __init__(self, xTop: int, yLeft: int):
        self.TopLeft = Point(xTop, yLeft)
        self.BottomRight = None

    def SetBottomRightPoint(self, xBottom: int, yRight: int):
        self.BottomRight = Point(xBottom, yRight)

class Depth:
    def __init__(self, xLower: int, yLower: int):
        self.LowerLevel = Point(xLower, yLower)
        self.UpperLevel = None
    
    def SetUpperLevelPoint(self, xUpper: int, yUpper: int):
        self.UpperLevel = Point(xUpper, yUpper)

class PickingItem:
    def __init__(self, name: str):
        self.Name = name
        self.Amount = 0
        self.Image = None
        self.Rect = None
        self.Depth = None

    def SetRectTopLeftPoint(self, xTop: int, yLeft: int):
        self.Rect = Rect(xTop, yLeft)

    def SetRectBottomRightPoint(self, xBottom: int, yRight: int):
        self.Rect.SetBottomRightPoint(xBottom, yRight)

    def SetDepthLowerLevelPoint(self, xLower: int, yLower: int):
        self.Depth = Depth(xLower, yLower)

    def SetDepthUpperLevelPoint(self, xUpper: int, yUpper: int):
        self.Depth.SetUpperLevelPoint(xUpper, yUpper)

def PointFromJson(json: dict):
    if json is None:
        return None
    point = None
    if 'X' in json and 'Y' in json:
        point = Point(json['X'], json['Y'])
    return point

def AreaFromJson(json: dict):
    if json is None:
        return None
    rect = None
    if 'TopLeft' in json:
        tl_pt = PointFromJson(json['TopLeft'])
        if tl_pt is not None:
            rect = Rect(tl_pt.X, tl_pt.Y)
            if 'BottomRight' in json:
                br_pt = PointFromJson(json['BottomRight'])
                if br_pt is not None:
                    rect.SetBottomRightPoint(br_pt.X, br_pt.Y)
    return rect

def DepthFromJson(json: dict):
    if json is None:
        return None
    depth = None
    if 'LowerLevel' in json:
        lw_pt = PointFromJson(json['LowerLevel'])
        if lw_pt is not None:
            depth = Depth(lw_pt.X, lw_pt.Y)
            if 'UpperLevel' in json:
                up_pt = PointFromJson(json['UpperLevel'])
                if up_pt is not None:
                    depth.SetUpperLevelPoint(up_pt.X, up_pt.Y)
    return depth

def PickingItemFromJson(json: dict):
    if json is None:
        return None
    item = None
    if 'Name' in json:
        item = PickingItem(json['Name'])
        if 'Amount' in json:
            item.Amount = json['Amount']
        if 'Image' in json:
            item.Image = json['Image']
        if 'Rect' in json:
            item.Rect = AreaFromJson(json['Rect'])
        if 'Depth' in json:
            item.Depth = DepthFromJson(json['Depth'])
    return item

class CustomEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__

class Window():
    def __init__(self):
        self.Root = Tk()
        self.Root.wm_title('Poka-yoke Picking')
        self.Root.geometry('1280x720')
        self.Root.resizable(True, True)

        self.MainFrame = Frame(self.Root, width=1280, height=720)
        self.MainFrame.pack(expand=True)
        
        self.SettingsFrame = Frame(self.MainFrame, width=580, height=680)
        self.SettingsFrame.place(x=680, y=20)

        self.StreamingFrame = Frame(self.MainFrame, width=640, height=680)
        self.StreamingFrame.place(x=20, y=20)

        self.VideoLabel = Label(self.StreamingFrame, borderwidth=0, bg='white')
        self.VideoLabel.place(w=640, h=360, x=0, y=0)

        self.CropLabel = Label(self.StreamingFrame, borderwidth=0, bg='white')
        self.CropLabel.place(w=280, h=280, x=0, y=400)

        self.Root.protocol('WM_DELETE_WINDOW', self.OnClosingEvent)

    def StartMainLoop(self):
        self.Root.mainloop()
    
    def OnClosingEvent(self):
        answer = messagebox.askokcancel('Quit', 'Do you want to exit the program?')
        if answer:
            self.Root.destroy()