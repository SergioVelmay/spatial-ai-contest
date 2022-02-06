import os
import json
from json import JSONEncoder
from tkinter import *
from tkinter import messagebox

CONFIG_FILE_NAME = 'config.json'
MAX_PICKING_ITEMS = 8

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
        if 'Rect' in json:
            item.Rect = AreaFromJson(json['Rect'])
        if 'Depth' in json:
            item.Depth = DepthFromJson(json['Depth'])
    return item

class CustomEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__

def DisableWidget(widget):
    widget['state'] = DISABLED

def EnableWidget(widget):
    widget['state'] = NORMAL

class Window():
    def __init__(self):
        self.Root = Tk()
        self.Root.wm_title('Picking Detection')
        self.Root.geometry('1280x720')
        
        self.SettingsFrame = Frame(self.Root, bg='yellow', width=440, height=680)
        self.SettingsFrame.place(x=780, y=20)

        self.VideoFrame = Frame(self.Root, bg='cyan', width=640, height=360)
        self.VideoFrame.place(x=70, y=20)

    def StartMainLoop(self):
        self.Root.mainloop()

class SettingsItem():
    def __init__(self, master: Frame, video: Frame, pick: PickingItem, index: int, length: int, 
        move: classmethod, update: classmethod, delete: classmethod):
        self.Master = master
        self.Video = video
        self.PickingItem = pick
        self.Index = index
        self.Length = length
        self.Move = move
        self.Update = update
        self.Delete = delete
        self.EditItem = None
        self.MouseX = None
        self.MouseY = None

        self.SetAllVariables()
        self.SetAllIconImages()
        self.SetAllWidgets()
        self.SetOrderAndArrows()
        self.PlaceAllWidgets()
        self.BindMouseEvents()

    def SetAllVariables(self):
        self.EyeValue = BooleanVar(value=False)
        self.BulbValue = BooleanVar(value=False)
        self.EditValue = BooleanVar(value=False)
        self.NameValue = StringVar(value='')
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

    def SetAllWidgets(self):
        font_bold = ('arial', 12, 'bold')
        font_normal = ('arial', 12, 'normal')
        self.OrderLabel = Label(self.Master, font=font_bold, relief=SOLID)
        self.NameLabel = Label(self.Master, text=self.PickingItem.Name, font=font_bold, relief=SOLID)
        self.EyeButton = Checkbutton(self.Master, image=self.EyeOffIcon, selectimage=self.EyeOnIcon,
            variable=self.EyeValue, onvalue=True, offvalue=False, indicatoron=False)
        self.BulbButton = Checkbutton(self.Master, image=self.BulbOffIcon, selectimage=self.BulbOnIcon,
            variable=self.BulbValue, onvalue=True, offvalue=False, indicatoron=False)
        self.EditButton = Checkbutton(self.Master, image=self.EditIcon, command=self.EditButtonClick,
            variable=self.EditValue, onvalue=True, offvalue=False, indicatoron=False)
        self.DeleteButton = Button(self.Master, image=self.DeleteIcon, command=self.DeleteButtonClick)
        self.UpButton = Button(self.Master, image=self.UpIcon, command=self.MoveUpButtonClick)
        self.DownButton = Button(self.Master, image=self.DownIcon, command=self.MoveDownButtonClick)
        self.NameEntry = Entry(self.Master, textvariable=self.NameValue, font=font_normal, justify=CENTER)
        self.RectButton = Checkbutton(self.Master, image=self.RectIcon, command=self.EditRectButtonClick,
            variable=self.RectValue, onvalue=True, offvalue=False, indicatoron=False)
        self.DepthButton = Checkbutton(self.Master, image=self.DepthIcon, command=self.EditDepthButtonClick,
            variable=self.DepthValue, onvalue=True, offvalue=False, indicatoron=False)
        self.SaveButton = Button(self.Master, image=self.SaveIcon, command=self.SaveButtonClick)
        self.CancelButton = Button(self.Master, image=self.CancelIcon, command=self.CancelButtonClick)
        self.EditOptionsLabel = Label(self.Master)

    def GetItemOrder(self):
        return self.Index + 1

    def GetPositionY(self):
        return self.Index * 80

    def PlaceAllWidgets(self):
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
        self.PlaceEditOptionsLabel()

    def BindMouseEvents(self):
        self.Video.bind('<Motion>', self.CaptureMouseMotionEvent, add="+")
        self.Video.bind('<Button-1>', self.CaptureMouseLeftClickEvent, add="+")
        self.Video.bind('<Button-3>', self.CaptureMouseRightClickEvent, add="+")
        self.NameEntry.bind('<Button-1>', self.EditNameEntryClick)

    def RemoveAllWidgets(self):
        self.OrderLabel.place_forget()
        self.NameLabel.place_forget()
        self.EyeButton.place_forget()
        self.BulbButton.place_forget()
        self.EditButton.place_forget()
        self.DeleteButton.place_forget()
        self.UpButton.place_forget()
        self.DownButton.place_forget()
        self.NameEntry.place_forget()
        self.RectButton.place_forget()
        self.DepthButton.place_forget()
        self.SaveButton.place_forget()
        self.CancelButton.place_forget()
        self.EditOptionsLabel.place_forget()

    def PlaceEditOptionsLabel(self):
        self.EditOptionsLabel.place(w=312, h=32, x=40, y=self.GetPositionY()+40)

    def SetOrderAndArrows(self):
        self.OrderLabel['text'] = str(self.GetItemOrder())
        EnableWidget(self.UpButton)
        EnableWidget(self.DownButton)
        if self.GetItemOrder() == 1:
            DisableWidget(self.UpButton)
        if self.GetItemOrder() == self.Length:
            DisableWidget(self.DownButton)

    def CopyPickingItem(self):
        self.EditItem = PickingItem(self.PickingItem.Name)
        if self.PickingItem.Rect is not None:
            self.EditItem.SetRectTopLeftPoint(self.PickingItem.Rect.TopLeft.X, self.PickingItem.Rect.TopLeft.Y)
            if self.PickingItem.Rect.BottomRight is not None:
                self.EditItem.SetRectBottomRightPoint(self.PickingItem.Rect.BottomRight.X, self.PickingItem.Rect.BottomRight.Y)
        if self.PickingItem.Depth is not None:
            self.EditItem.SetDepthLowerLevelPoint(self.PickingItem.Depth.LowerLevel.X, self.PickingItem.Depth.LowerLevel.Y)
            if self.PickingItem.Depth.UpperLevel is not None:
                self.EditItem.SetDepthUpperLevelPoint(self.PickingItem.Depth.UpperLevel.X, self.PickingItem.Depth.UpperLevel.Y)

    def RestoreEditOptions(self):
        self.Edit = None
        self.EditValue.set(False)
        self.NameValue.set('')
        self.RectValue.set(False)
        self.DepthValue.set(False)
        self.PlaceEditOptionsLabel()

    def EditButtonClick(self):
        if self.EditValue.get():
            self.EditOptionsLabel.place_forget()
            self.CopyPickingItem()
            self.NameValue.set(self.EditItem.Name)
        else:
            self.RestoreEditOptions()

    def EditNameEntryClick(self, event):
        if self.EditValue.get():
            self.DepthValue.set(False)
            self.RectValue.set(False)

    def EditRectButtonClick(self):
        if self.EditValue.get() and self.RectValue.get():
            self.DepthValue.set(False)

    def EditDepthButtonClick(self):
        if self.EditValue.get() and self.DepthValue.get():
            self.RectValue.set(False)

    def DeleteButtonClick(self):
        answer = messagebox.askyesno(title='Delete Confirmation', message='Do you want to delete this item?')
        if answer:
            self.Delete(self.Index)

    def SaveButtonClick(self):
        answer = messagebox.askyesno(title='Save Confirmation', message='Do you want to save the settings?')
        if answer:
            self.EditItem.Name = self.NameValue.get()
            self.PickingItem = self.EditItem
            self.NameLabel['text'] = self.PickingItem.Name
            self.Update()
            self.RestoreEditOptions()

    def CancelButtonClick(self):
        answer = messagebox.askyesno(title='Cancel Confirmation', message='Do you want to cancel your changes?')
        if answer:
            self.RestoreEditOptions()

    def MoveUpButtonClick(self):
        old_index = self.Index
        new_index = self.Index - 1
        self.Move(old_index, new_index)

    def MoveDownButtonClick(self):
        old_index = self.Index
        new_index = self.Index + 1
        self.Move(old_index, new_index)

    def CaptureMouseMotionEvent(self, event):
        if self.EditValue.get():
            self.MouseX, self.MouseY = event.x, event.y
            if self.RectValue.get():
                if self.EditItem.Rect is not None and self.EditItem.Rect.TopLeft is not None:
                    pass # print rectangle
                else:
                    pass #print cursor
            if self.DepthValue.get():
                pass # print circle

    def CaptureMouseLeftClickEvent(self, event):
        if self.EditValue.get():
            if self.RectValue.get():
                if self.EditItem.Rect is not None and self.EditItem.Rect.BottomRight is None:
                    self.EditItem.SetRectBottomRightPoint(event.x, event.y)
                else:
                    self.EditItem.SetRectTopLeftPoint(event.x, event.y)
            if self.DepthValue.get():
                if self.EditItem.Depth is not None and self.EditItem.Depth.UpperLevel is None:
                    self.EditItem.SetDepthUpperLevelPoint(event.x, event.y)
                else:
                    self.EditItem.SetDepthLowerLevelPoint(event.x, event.y)

    def CaptureMouseRightClickEvent(self, event):
        if self.EditValue.get():
            if self.RectValue.get():
                if self.EditItem.Rect is not None and self.EditItem.Rect.BottomRight is None:
                    self.EditItem.Rect = None

class PokaYoke():
    def __init__(self, json: list):
        self.Length = len(json)
        self.PickingSettings = []
        self.Window = Window()

        for index, item in enumerate(json):
            pick = PickingItemFromJson(item)
            if pick is not None:
                self.AppendPickingSetting(pick, index)
        self.SetAddNewItemButton()

    def AppendPickingSetting(self, pick: PickingItem, index: int):
        self.PickingSettings.append(
            SettingsItem(self.Window.SettingsFrame, self.Window.VideoFrame, pick, index, self.Length, 
                self.MoveItemButtonClick, self.UpdateItemButtonClick, self.DeleteItemButtonClick))
    
    def SetAddNewItemButton(self):
        self.AddIcon = PhotoImage(file='./assets/icon-add.png')
        font_normal = ('arial', 12, 'normal')
        self.AddButton = Button(self.Window.SettingsFrame, text='Add new item', font=font_normal,
            image=self.AddIcon, compound=LEFT, command=self.AddNewItemButtonClick)
        if self.Length == MAX_PICKING_ITEMS:
            DisableWidget(self.AddButton)
        self.PlaceAddNewItemButton()

    def PlaceAddNewItemButton(self):
        if self.Length == MAX_PICKING_ITEMS:
            DisableWidget(self.AddButton)
        else:
            EnableWidget(self.AddButton)
        self.AddButton.place(w=150, h=32, x=40, y=self.Length * 80)

    def AddNewItemButtonClick(self):
        self.Length += 1
        pick_name = "NewItem#" + str(self.Length)
        pick_item = PickingItem(pick_name)
        list_index = self.Length - 1
        if list_index > 0:
            for item in self.PickingSettings:
                item.Length = self.Length
            self.PickingSettings[list_index - 1].SetOrderAndArrows()
        self.AppendPickingSetting(pick_item, list_index)
        self.PlaceAddNewItemButton()
        self.SaveConfigurationFile()
    
    def DeleteItemButtonClick(self, index: int):
        self.PickingSettings[index].RemoveAllWidgets()
        del self.PickingSettings[index]
        self.Length = len(self.PickingSettings)
        for index, item in enumerate(self.PickingSettings):
            item.Length = self.Length
            item.Index = index
            item.SetOrderAndArrows()
            item.PlaceAllWidgets()
        self.PlaceAddNewItemButton()
        self.SaveConfigurationFile()

    def UpdateItemButtonClick(self):
        self.SaveConfigurationFile()

    def MoveItemButtonClick(self, old: int, new: int):
        self.PickingSettings[old].Index = new
        self.PickingSettings[new].Index = old
        self.PickingSettings[old], self.PickingSettings[new] = self.PickingSettings[new], self.PickingSettings[old]
        self.PickingSettings[old].SetOrderAndArrows()
        self.PickingSettings[new].SetOrderAndArrows()
        self.PickingSettings[old].PlaceAllWidgets()
        self.PickingSettings[new].PlaceAllWidgets()
    
    def SaveConfigurationFile(self):
        config_data = [item.PickingItem for item in self.PickingSettings]
        with open(CONFIG_FILE_NAME, "w") as json_file:
            json.dump(config_data, json_file, cls=CustomEncoder, indent=4)
            json_file.close()

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

    poka_yoke = PokaYoke(config_data)
        
    poka_yoke.Window.StartMainLoop()

if __name__ == '__main__':
    Main()