import os
import json
from json import JSONEncoder
from tkinter import *
from tkinter import messagebox

CONFIG_FILE_NAME = 'config.json'
MAX_CONFIG_ITEMS = 8

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
        self.Rect = None
        self.Depth = None

    def SetRectTopLeftPoint(self, xTop: int, yLeft: int):
        self.Rect = Rect(Point(xTop, yLeft))

    def SetRectBottomRightPoint(self, xBottom: int, yRight: int):
        self.Rect.SetBottomRightPoint(Point(xBottom, yRight))

    def SetDepthLowerLevelPoint(self, xLower: int, yLower: int):
        self.Depth = Depth(Point(xLower, yLower))

    def SetDepthUpperLevelPoint(self, xUpper: int, yUpper: int):
        self.Depth.SetUpperLevelPoint(Point(xUpper, yUpper))

def PointFromJson(json: dict):
    point = None
    if 'X' in json and 'Y' in json:
        point = Point(json['X'], json['Y'])
    return point

def AreaFromJson(json: dict):
    rect = None
    if 'TopLeft' in json:
        tl_pt = PointFromJson(json['TopLeft'])
        if tl_pt != None:
            rect = Rect(tl_pt.X, tl_pt.Y)
            if 'BottomRight' in json:
                br_pt = PointFromJson(json['BottomRight'])
                if br_pt != None:
                    rect.SetBottomRightPoint(br_pt.X, br_pt.Y)
    return rect

def DepthFromJson(json: dict):
    depth = None
    if 'LowerLevel' in json:
        lw_pt = PointFromJson(json['LowerLevel'])
        if lw_pt != None:
            depth = Depth(lw_pt.X, lw_pt.Y)
            if 'UpperLevel' in json:
                up_pt = PointFromJson(json['UpperLevel'])
                if up_pt != None:
                    depth.SetUpperLevelPoint(up_pt.X, up_pt.Y)
    return depth

def PickingItemFromJson(json: dict):
    item = None
    if 'Name' in json:
        item = PickingItem(json['Name'])
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
        self.Root.wm_title('Picking Detection')
        self.Root.geometry('1280x720')
        
        self.SettingsFrame = Frame(self.Root, bg='yellow', width=440, height=680)
        self.SettingsFrame.place(x=780, y=20)

    def StartMainLoop(self):
        self.Root.mainloop()

class SettingsItem():
    def __init__(self, master: Frame, pick: PickingItem, index: int):
        self.Master = master
        self.Picking = pick
        self.Index = index

        font_bold = ('arial', 12, 'bold')
        font_normal = ('arial', 12, 'normal')

        self.SetAllVariables()
        self.SetAllIconImages()

        self.OrderLabel = Label(self.Master, font=font_bold, relief=SOLID)
        self.NameLabel = Label(self.Master, text=self.Picking.Name, font=font_bold, relief=SOLID)
        self.EyeButton = Checkbutton(self.Master, image=self.EyeOffIcon, selectimage=self.EyeOnIcon,
            variable=self.EyeValue, onvalue=True, offvalue=False, indicatoron=False)
        self.BulbButton = Checkbutton(self.Master, image=self.BulbOffIcon, selectimage=self.BulbOnIcon,
            variable=self.BulbValue, onvalue=True, offvalue=False, indicatoron=False)
        self.EditButton = Checkbutton(self.Master, image=self.EditIcon, command=self.edit_click,
            variable=self.EditValue, onvalue=True, offvalue=False, indicatoron=False)
        self.DeleteButton = Button(self.Master, image=self.DeleteIcon, command=self.delete_click)
        self.UpButton = Button(self.Master, image=self.UpIcon, command=self.up_click)
        self.DownButton = Button(self.Master, image=self.DownIcon, command=self.down_click)
        self.NameEntry = Entry(self.Master, textvariable=self.NameValue, font=font_normal, justify=CENTER)
        self.RectButton = Checkbutton(self.Master, image=self.RectIcon,
            variable=self.RectValue, onvalue=True, offvalue=False, indicatoron=False)
        self.DepthButton = Checkbutton(self.Master, image=self.DepthIcon,
            variable=self.DepthValue, onvalue=True, offvalue=False, indicatoron=False)
        self.SaveButton = Button(self.Master, image=self.SaveIcon, command=self.save_click)
        self.CancelButton = Button(self.Master, image=self.CancelIcon, command=self.cancel_click)
        self.SettingsLabel = Label(self.Master)

        self.PlaceAllWidgets()

        self.Master.bind('<Motion>', self.mouse_motion)
        self.Master.bind('<Button-1>', self.mouse_left_click)
        self.Master.bind('<Button-3>', self.mouse_right_click)

    def SetAllVariables(self):
        self.EyeValue = BooleanVar(value=False)
        self.BulbValue = BooleanVar(value=False)
        self.EditValue = BooleanVar(value=False)
        self.NameValue = StringVar(value=self.Picking.Name)
        self.RectValue = BooleanVar(value=False)
        self.DepthValue = BooleanVar(value=False)

    def SetAllIconImages(self):
        self.EyeOnIcon = PhotoImage(file='./assets/icon-eye-on.png')
        self.EyeOffIcon = PhotoImage(file='./assets/icon-eye-off.png')
        self.BulbOnIcon = PhotoImage(file='./assets/icon-bulb-on.png')
        self.BulbOffIcon = PhotoImage(file='./assets/icon-bulb-off.png')
        self.EditIcon = PhotoImage(file='./assets/icon-pen.png')
        self.DeleteIcon = PhotoImage(file='./assets/icon-trash.png')
        self.UpIcon = PhotoImage(file='./assets/icon-arrow-up.png')
        self.DownIcon = PhotoImage(file='./assets/icon-arrow-down.png')
        self.RectIcon = PhotoImage(file='./assets/icon-square.png')
        self.DepthIcon = PhotoImage(file='./assets/icon-depth.png')
        self.SaveIcon = PhotoImage(file='./assets/icon-save.png')
        self.CancelIcon = PhotoImage(file='./assets/icon-cancel.png')

    def GetItemOrder(self):
        return self.Index + 1

    def GetPositionY(self):
        return self.Index * 80

    def PlaceAllWidgets(self):
        self.OrderLabel['text'] = str(self.GetItemOrder())

        if self.GetItemOrder() == 1:
            self.UpButton['state'] = DISABLED
        if self.GetItemOrder() == MAX_CONFIG_ITEMS:
            self.DownButton['state'] = DISABLED

        self.OrderLabel.place(w=32, h=32, x=0, y=self.GetPositionY())
        self.NameLabel.place(w=150, h=32, x=40, y=self.GetPositionY())
        self.EyeButton.place(w=32, h=32, x=200, y=self.GetPositionY())
        self.BulbButton.place(w=32, h=32, x=240, y=self.GetPositionY())
        self.EditButton.place(w=32, h=32, x=280, y=self.GetPositionY())
        self.DeleteButton.place(w=32, h=32, x=320, y=self.GetPositionY())
        self.UpButton.place(w=32, h=32, x=360, y=self.GetPositionY())
        self.DownButton.place(w=32, h=32, x=400, y=self.GetPositionY())
        self.NameEntry.place(w=150, h=32, x=40, y=self.GetPositionY()+40)
        self.RectButton.place(w=32, h=32, x=200, y=self.GetPositionY()+40)
        self.DepthButton.place(w=32, h=32, x=240, y=self.GetPositionY()+40)
        self.SaveButton.place(w=32, h=32, x=280, y=self.GetPositionY()+40)
        self.CancelButton.place(w=32, h=32, x=320, y=self.GetPositionY()+40)
        self.PlaceSettingsLabel()

    def PlaceSettingsLabel(self):
        self.SettingsLabel.place(w=312, h=32, x=40, y=self.GetPositionY()+40)

    def edit_click(self):
        if self.EditValue.get():
            self.SettingsLabel.place_forget()
            print('EDITING ITEM...')
        else:
            self.PlaceSettingsLabel()

    def delete_click(self):
        answer = messagebox.askyesno(title='Delete Confirmation', message='Do you want to delete this item?')
        if answer:
            print('DELETING ITEM...')

    def up_click(self):
        number = int(self.OrderLabel['text'])
        number -= 1
        self.OrderLabel['text'] = str(number)
        if number == 1:
            self.disable_widget(self.UpButton)
        else:
            self.enable_widget(self.DownButton)

    def down_click(self):
        number = int(self.OrderLabel['text'])
        number += 1
        self.OrderLabel['text'] = str(number)
        if number == MAX_CONFIG_ITEMS:
            self.disable_widget(self.DownButton)
        else:
            self.enable_widget(self.UpButton)

    def disable_widget(self, widget):
        widget['state'] = DISABLED

    def enable_widget(self, widget):
        widget['state'] = NORMAL

    def save_click(self):
        answer = messagebox.askyesno(title='Save Confirmation', message='Do you want to save the settings?')
        if answer:
            print('SAVING SETTINGS...')

    def cancel_click(self):
        answer = messagebox.askyesno(title='Cancel Confirmation', message='Do you want to cancel your changes?')
        if answer:
            print('CANCELLING SETTINGS...')

    def mouse_motion(self, event):
        if self.EyeValue.get():
            print('(x:%s, y:%s)' % (event.x, event.y))

    def mouse_left_click(self, event):
        if self.BulbValue.get():
            print('(x:%s, y:%s) LEFT CLICK' % (event.x, event.y))

    def mouse_right_click(self, event):
        if self.BulbValue.get():
            print('(x:%s, y:%s) RIGHT CLICK' % (event.x, event.y))

def Main():
    if os.path.isfile(CONFIG_FILE_NAME):
        with open(CONFIG_FILE_NAME, 'r') as json_file:
            config_data = json.load(json_file)
            json_file.close()
    else:
        config_data = []
        default_json = json.dumps(config_data)
        with open(CONFIG_FILE_NAME, 'w') as json_file:
            json_file.write(default_json)
            json_file.close()

    ui = Window()

    for index, json_item in enumerate(config_data):
        pick_item = PickingItemFromJson(json_item)
        if pick_item != None:
            SettingsItem(ui.SettingsFrame, pick_item, index)
        
    ui.StartMainLoop()

if __name__ == '__main__':
    Main()