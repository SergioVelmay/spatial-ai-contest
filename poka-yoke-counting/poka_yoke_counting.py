import os
import json
import cv2
import numpy as np
from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from PIL import ImageTk
from PIL import Image as PIL_Image
from utils.picking_utils import *
from utils.detection_utils import *
from utils.drawing_utils import *

class PokaYokePicking():
    def __init__(self, json: list):
        self.Window = Window()
        self.Detection = Detection(self.DrawImage)

        self.SetAllAttributes()
        self.SetAllIconImages()
        self.SetAllPickingItems(json)
        self.BindAllMouseEvents()
        self.SetAddNewItemButton()
        self.SetBlendScaleSection()

    def SetAllAttributes(self):
        self.PickingItems = []
        self.CurrentItem = None
        self.CurrentLowerZ = None
        self.CurrentUpperZ = None
        self.EditItem = None
        self.MouseX = None
        self.MouseY = None
        # widgets lists
        self.OrderButtons = []
        self.ImageLabels = []
        self.NameLabels = []
        self.XCharLabels = []
        self.AmountLabels = []
        self.EyeButtons = []
        self.BulbButtons = []
        self.EditButtons = []
        self.DeleteButtons = []
        self.UpButtons = []
        self.DownButtons = []
        self.FileButtons = []
        self.NameEntries = []
        self.XEditLabels = []
        self.AmountEntries = []
        self.RectButtons = []
        self.DepthButtons = []
        self.SaveButtons = []
        self.CancelButtons = []
        self.HiddenLabels = []
        # variables lists
        self.OrderValues = []
        self.EyeValues = []
        self.BulbValues = []
        self.EditValues = []
        self.NameValues = []
        self.AmountValues = []
        self.RectValues = []
        self.DepthValues = []

    def SetSettingsInterface(self, index: int, length: int):
        self.SetVariables()
        self.SetWidgets(index)
        self.SetOrderAndArrows(index, length)
        self.PlaceWidgets(index)

    def SetAllPickingItems(self, json: list):
        for index, item in enumerate(json):
            pick = PickingItemFromJson(item)
            if pick is not None:
                self.PickingItems.append(pick)
                self.SetSettingsInterface(index, len(json))

    def GetListLength(self):
        return len(self.PickingItems)

    def SetVariables(self):
        self.OrderValues.append(BooleanVar(value=False))
        self.EyeValues.append(BooleanVar(value=False))
        self.BulbValues.append(BooleanVar(value=False))
        self.EditValues.append(BooleanVar(value=False))
        self.NameValues.append(StringVar(value=''))
        self.AmountValues.append(StringVar(value=''))
        self.RectValues.append(BooleanVar(value=False))
        self.DepthValues.append(BooleanVar(value=False))

    def SetAllIconImages(self):
        self.OrderOnIcon = PhotoImage(file='./assets/icon-check-on.png')
        self.OrderOffIcon = PhotoImage(file='./assets/icon-check-off.png')
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
        self.AddIcon = PhotoImage(file='./assets/icon-add.png')

    def AssignCommands(self, index: int):
        self.OrderButtons[index]['command'] = lambda: self.OrderButtonClick(index)
        self.EditButtons[index]['command'] = lambda: self.EditButtonClick(index)
        self.DeleteButtons[index]['command'] = lambda: self.DeleteButtonClick(index)
        self.UpButtons[index]['command'] = lambda: self.MoveUpButtonClick(index)
        self.DownButtons[index]['command'] = lambda: self.MoveDownButtonClick(index)
        self.FileButtons[index]['command'] = lambda: self.FileButtonClick(index)
        self.RectButtons[index]['command'] = lambda: self.EditRectButtonClick(index)
        self.DepthButtons[index]['command'] = lambda: self.EditDepthButtonClick(index)
        self.SaveButtons[index]['command'] = lambda: self.SaveButtonClick(index)
        self.CancelButtons[index]['command'] = lambda: self.CancelButtonClick(index)
        self.NameEntries[index].bind('<Button-1>', lambda _: self.EditNameEntryClick(index))
        self.AmountEntries[index].bind('<Button-1>', lambda _: self.EditAmountEntryClick(index))
    
    def AssignVariables(self, index: int):
        self.OrderButtons[index]['variable'] = self.OrderValues[index]
        self.EyeButtons[index]['variable'] = self.EyeValues[index]
        self.BulbButtons[index]['variable'] = self.BulbValues[index]
        self.EditButtons[index]['variable'] = self.EditValues[index]
        self.NameEntries[index]['textvariable'] = self.NameValues[index]
        self.AmountEntries[index]['textvariable'] = self.AmountValues[index]
        self.RectButtons[index]['variable'] = self.RectValues[index]
        self.DepthButtons[index]['variable'] = self.DepthValues[index]

    def ApplyBackgrounds(self, index: int):
        warning_count = 0
        non_mandatory = 0
        if self.ApplyFileBackground(index):
            warning_count = warning_count + 1
            non_mandatory = non_mandatory + 1
        if self.ApplyNameBackground(index):
            warning_count = warning_count + 1
            non_mandatory = non_mandatory + 1
        if self.ApplyAmountBackground(index):
            warning_count = warning_count + 1
        if self.ApplyRectBackground(index):
            warning_count = warning_count + 1
        if self.ApplyDepthBackground(index):
            warning_count = warning_count + 1
        if warning_count > 0:
            self.EditButtons[index]['bg'] = COLOR_TK_YELLOW
            if warning_count - non_mandatory > 0:
                DisableWidget(self.OrderButtons[index])
                if self.OrderValues[index].get():
                    self.OrderValues[index].set(False)
                    self.OrderButtonClick(index)
        else:
            self.EditButtons[index]['bg'] = COLOR_TK_DEFAULT
            EnableWidget(self.OrderButtons[index])

    def ApplyFileBackground(self, index: int):
        is_missing = self.PickingItems[index].Image == None
        if is_missing:
            self.FileButtons[index]['bg'] = COLOR_TK_YELLOW
        else:
            self.FileButtons[index]['bg'] = COLOR_TK_DEFAULT
        return is_missing

    def ApplyNameBackground(self, index: int):
        is_missing = self.PickingItems[index].Name.startswith(DEFAULT_NAME)
        if is_missing:
            self.NameEntries[index]['bg'] = COLOR_TK_YELLOW
        else:
            self.NameEntries[index]['bg'] = COLOR_TK_DEFAULT
        return is_missing

    def ApplyAmountBackground(self, index:int):
        is_missing = self.PickingItems[index].Amount == 0
        if is_missing:
            self.AmountEntries[index]['bg'] = COLOR_TK_YELLOW
        else:
            self.AmountEntries[index]['bg'] = COLOR_TK_DEFAULT
        return is_missing
    
    def ApplyRectBackground(self, index:int):
        is_missing = self.PickingItems[index].Rect is None or self.PickingItems[index].Rect.BottomRight is None
        if is_missing:
            self.RectButtons[index]['bg'] = COLOR_TK_YELLOW
        else:
            self.RectButtons[index]['bg'] = COLOR_TK_DEFAULT
        return is_missing
    
    def ApplyDepthBackground(self, index:int):
        is_missing = self.PickingItems[index].Depth is None or self.PickingItems[index].Depth.UpperLevel is None
        if is_missing:
            self.DepthButtons[index]['bg'] = COLOR_TK_YELLOW
        else:
            self.DepthButtons[index]['bg'] = COLOR_TK_DEFAULT
        return is_missing

    def SetImageIfExists(self, index: int):
        if self.PickingItems[index].Image == None:
            self.ImageLabels[index]['image'] = ''
        else:
            image_path = self.PickingItems[index].Image
            image_pil = PIL_Image.open(image_path)
            image_tk = ImageTk.PhotoImage(image=image_pil)
            self.ImageLabels[index].image_tk = image_tk
            self.ImageLabels[index]['image'] = image_tk

    def SetWidgets(self, index: int):
        self.OrderButtons.append(Checkbutton(self.Window.SettingsFrame, image=self.OrderOffIcon, selectimage=self.OrderOnIcon, onvalue=True, offvalue=False, indicatoron=False))
        self.ImageLabels.append(Label(self.Window.SettingsFrame, bg=COLOR_TK_WHITE))
        self.SetImageIfExists(index)
        self.NameLabels.append(Label(self.Window.SettingsFrame, text=self.PickingItems[index].Name, font=FONT_TK_BOLD, relief=SOLID))
        self.XCharLabels.append(Label(self.Window.SettingsFrame, text='x', font=FONT_TK_BOLD))
        self.AmountLabels.append(Label(self.Window.SettingsFrame, text=str(self.PickingItems[index].Amount), font=FONT_TK_BOLD, relief=SOLID))
        self.EyeButtons.append(Checkbutton(self.Window.SettingsFrame, image=self.EyeOffIcon, selectimage=self.EyeOnIcon, onvalue=True, offvalue=False, indicatoron=False))
        self.BulbButtons.append(Checkbutton(self.Window.SettingsFrame, image=self.BulbOffIcon, selectimage=self.BulbOnIcon, onvalue=True, offvalue=False, indicatoron=False))
        self.EditButtons.append(Checkbutton(self.Window.SettingsFrame, image=self.EditIcon, onvalue=True, offvalue=False, indicatoron=False))
        self.DeleteButtons.append(Button(self.Window.SettingsFrame, image=self.DeleteIcon))
        self.UpButtons.append(Button(self.Window.SettingsFrame, image=self.UpIcon))
        self.DownButtons.append(Button(self.Window.SettingsFrame, image=self.DownIcon))
        self.FileButtons.append(Button(self.Window.SettingsFrame, text='File...'))
        self.NameEntries.append(Entry(self.Window.SettingsFrame, font=FONT_TK_NORMAL, justify=CENTER))
        self.XEditLabels.append(Label(self.Window.SettingsFrame, text='x', font=FONT_TK_BOLD))
        self.AmountEntries.append(Entry(self.Window.SettingsFrame, font=FONT_TK_NORMAL, justify=CENTER))
        self.RectButtons.append(Checkbutton(self.Window.SettingsFrame, image=self.RectIcon, onvalue=True, offvalue=False, indicatoron=False))
        self.DepthButtons.append(Checkbutton(self.Window.SettingsFrame, image=self.DepthIcon, onvalue=True, offvalue=False, indicatoron=False))
        self.SaveButtons.append(Button(self.Window.SettingsFrame, image=self.SaveIcon))
        self.CancelButtons.append(Button(self.Window.SettingsFrame, image=self.CancelIcon))
        self.HiddenLabels.append(Label(self.Window.SettingsFrame))
        self.AssignVariables(index)
        self.AssignCommands(index)
        self.ApplyBackgrounds(index)
    
    def SetOrderAndArrows(self, index: int, length: int):
        EnableWidget(self.UpButtons[index])
        EnableWidget(self.DownButtons[index])
        if index == 0:
            DisableWidget(self.UpButtons[index])
        if index == length - 1:
            DisableWidget(self.DownButtons[index])

    def PlaceHiddenWidgets(self, index: int):
        self.HiddenLabels[index].place(w=377, h=32, x=120, y=index*80+40)
        DisableWidget(self.FileButtons[index])
        self.FileButtons[index].place_forget()

    def PlaceWidgets(self, index: int):
        self.OrderButtons[index].place(w=32, h=32, x=0, y=index*80)
        self.ImageLabels[index].place(w=72, h=72, x=40, y=index*80)
        self.NameLabels[index].place(w=150, h=32, x=120, y=index*80)
        self.XCharLabels[index].place(w=10, h=32, x=275, y=index*80)
        self.AmountLabels[index].place(w=47, h=32, x=290, y=index*80)
        self.EyeButtons[index].place(w=32, h=32, x=345, y=index*80)
        self.BulbButtons[index].place(w=32, h=32, x=385, y=index*80)
        self.EditButtons[index].place(w=32, h=32, x=425, y=index*80)
        self.DeleteButtons[index].place(w=32, h=32, x=465, y=index*80)
        self.UpButtons[index].place(w=32, h=32, x=505, y=index*80)
        self.DownButtons[index].place(w=32, h=32, x=545, y=index*80)
        self.FileButtons[index].place(w=72, h=32, x=40, y=index*80+40)
        self.NameEntries[index].place(w=150, h=32, x=120, y=index*80+40)
        self.XEditLabels[index].place(w=10, h=32, x=275, y=index*80+40)
        self.AmountEntries[index].place(w=47, h=32, x=290, y=index*80+40)
        self.RectButtons[index].place(w=32, h=32, x=345, y=index*80+40)
        self.DepthButtons[index].place(w=32, h=32, x=385, y=index*80+40)
        self.SaveButtons[index].place(w=32, h=32, x=425, y=index*80+40)
        self.CancelButtons[index].place(w=32, h=32, x=465, y=index*80+40)
        self.PlaceHiddenWidgets(index)

    def BindAllMouseEvents(self):
        self.Window.VideoLabel.bind('<Motion>', self.CaptureMouseMotionEvent, add='+')
        self.Window.VideoLabel.bind('<Button-1>', self.CaptureMouseLeftClickEvent, add='+')
        self.Window.VideoLabel.bind('<Button-3>', self.CaptureMouseRightClickEvent, add='+')

    def SetAddNewItemButton(self):
        self.AddButton = Button(self.Window.SettingsFrame, text='Add new item', font=FONT_TK_NORMAL,
            image=self.AddIcon, compound=LEFT, command=self.AddNewItemButtonClick)
        self.PlaceAddNewItemButton()

    def PlaceAddNewItemButton(self):
        if self.GetListLength() == MAX_PICKING_ITEMS:
            DisableWidget(self.AddButton)
        else:
            EnableWidget(self.AddButton)
        self.AddButton.place(w=150, h=32, x=40, y=self.GetListLength()*80)

    def AddNewItemButtonClick(self):
        index = self.GetListLength()
        pick_name = DEFAULT_NAME + str(index + 1)
        pick_item = PickingItem(pick_name)
        self.PickingItems.append(pick_item)
        length = self.GetListLength()
        if index > 0:
            self.SetOrderAndArrows(index - 1, length)
        self.SetSettingsInterface(index, length)
        self.PlaceAddNewItemButton()
        self.SaveConfigurationFile()

    def SwapWidgets(self, index: int, new_index: int):
        self.OrderButtons[index], self.OrderButtons[new_index] = self.OrderButtons[new_index], self.OrderButtons[index]
        self.ImageLabels[index], self.ImageLabels[new_index] = self.ImageLabels[new_index], self.ImageLabels[index]
        self.NameLabels[index], self.NameLabels[new_index] = self.NameLabels[new_index], self.NameLabels[index]
        self.XCharLabels[index], self.XCharLabels[new_index] = self.XCharLabels[new_index], self.XCharLabels[index]
        self.AmountLabels[index], self.AmountLabels[new_index] = self.AmountLabels[new_index], self.AmountLabels[index]
        self.EyeButtons[index], self.EyeButtons[new_index] = self.EyeButtons[new_index], self.EyeButtons[index]
        self.BulbButtons[index], self.BulbButtons[new_index] = self.BulbButtons[new_index], self.BulbButtons[index]
        self.EditButtons[index], self.EditButtons[new_index] = self.EditButtons[new_index], self.EditButtons[index]
        self.DeleteButtons[index], self.DeleteButtons[new_index] = self.DeleteButtons[new_index], self.DeleteButtons[index]
        self.UpButtons[index], self.UpButtons[new_index] = self.UpButtons[new_index], self.UpButtons[index]
        self.DownButtons[index], self.DownButtons[new_index] = self.DownButtons[new_index], self.DownButtons[index]
        self.FileButtons[index], self.FileButtons[new_index] = self.FileButtons[new_index], self.FileButtons[index]
        self.NameEntries[index], self.NameEntries[new_index] = self.NameEntries[new_index], self.NameEntries[index]
        self.XEditLabels[index], self.XEditLabels[new_index] = self.XEditLabels[new_index], self.XEditLabels[index]
        self.AmountEntries[index], self.AmountEntries[new_index] = self.AmountEntries[new_index], self.AmountEntries[index]
        self.RectButtons[index], self.RectButtons[new_index] = self.RectButtons[new_index], self.RectButtons[index]
        self.DepthButtons[index], self.DepthButtons[new_index] = self.DepthButtons[new_index], self.DepthButtons[index]
        self.SaveButtons[index], self.SaveButtons[new_index] = self.SaveButtons[new_index], self.SaveButtons[index]
        self.CancelButtons[index], self.CancelButtons[new_index] = self.CancelButtons[new_index], self.CancelButtons[index]
        self.HiddenLabels[index], self.HiddenLabels[new_index] = self.HiddenLabels[new_index], self.HiddenLabels[index]

    def SwapVariables(self, index: int, new_index: int):
        self.OrderValues[index], self.OrderValues[new_index] = self.OrderValues[new_index], self.OrderValues[index]
        self.EyeValues[index], self.EyeValues[new_index] = self.EyeValues[new_index], self.EyeValues[index]
        self.BulbValues[index], self.BulbValues[new_index] = self.BulbValues[new_index], self.BulbValues[index]
        self.EditValues[index], self.EditValues[new_index] = self.EditValues[new_index], self.EditValues[index]
        self.NameValues[index], self.NameValues[new_index] = self.NameValues[new_index], self.NameValues[index]
        self.AmountValues[index], self.AmountValues[new_index] = self.AmountValues[new_index], self.AmountValues[index]
        self.RectValues[index], self.RectValues[new_index] = self.RectValues[new_index], self.RectValues[index]
        self.DepthValues[index], self.DepthValues[new_index] = self.DepthValues[new_index], self.DepthValues[index]

    def ForgetWidgets(self, index: int):
        self.OrderButtons[index].place_forget()
        self.ImageLabels[index].place_forget()
        self.NameLabels[index].place_forget()
        self.XCharLabels[index].place_forget()
        self.AmountLabels[index].place_forget()
        self.EyeButtons[index].place_forget()
        self.BulbButtons[index].place_forget()
        self.EditButtons[index].place_forget()
        self.DeleteButtons[index].place_forget()
        self.UpButtons[index].place_forget()
        self.DownButtons[index].place_forget()
        self.FileButtons[index].place_forget()
        self.NameEntries[index].place_forget()
        self.XEditLabels[index].place_forget()
        self.AmountEntries[index].place_forget()
        self.RectButtons[index].place_forget()
        self.DepthButtons[index].place_forget()
        self.SaveButtons[index].place_forget()
        self.CancelButtons[index].place_forget()
        self.HiddenLabels[index].place_forget()

    def RemoveWidgets(self, index: int):
        self.ForgetWidgets(index)
        del self.OrderButtons[index]
        del self.ImageLabels[index]
        del self.NameLabels[index]
        del self.XCharLabels[index]
        del self.AmountLabels[index]
        del self.EyeButtons[index]
        del self.BulbButtons[index]
        del self.EditButtons[index]
        del self.DeleteButtons[index]
        del self.UpButtons[index]
        del self.DownButtons[index]
        del self.FileButtons[index]
        del self.NameEntries[index]
        del self.XEditLabels[index]
        del self.AmountEntries[index]
        del self.RectButtons[index]
        del self.DepthButtons[index]
        del self.SaveButtons[index]
        del self.CancelButtons[index]
        del self.HiddenLabels[index]

    def RemoveVariables(self, index: int):
        del self.OrderValues[index]
        del self.EyeValues[index]
        del self.BulbValues[index]
        del self.EditValues[index]
        del self.NameValues[index]
        del self.AmountValues[index]
        del self.RectValues[index]
        del self.DepthValues[index]
    
    def SaveConfigurationFile(self):
        with open(CONFIG_FILE_NAME, 'w') as json_file:
            json.dump(self.PickingItems, json_file, cls=CustomEncoder, indent=4)
            json_file.close()

    def CopyPickingItem(self, index: int):
        self.EditItem = PickingItem(self.PickingItems[index].Name)
        self.EditItem.Amount = self.PickingItems[index].Amount
        self.EditItem.Image = self.PickingItems[index].Image
        if self.PickingItems[index].Rect is not None:
            self.EditItem.SetRectTopLeftPoint(self.PickingItems[index].Rect.TopLeft.X, self.PickingItems[index].Rect.TopLeft.Y)
            if self.PickingItems[index].Rect.BottomRight is not None:
                self.EditItem.SetRectBottomRightPoint(self.PickingItems[index].Rect.BottomRight.X, self.PickingItems[index].Rect.BottomRight.Y)
        if self.PickingItems[index].Depth is not None:
            self.EditItem.SetDepthLowerLevelPoint(self.PickingItems[index].Depth.LowerLevel.X, self.PickingItems[index].Depth.LowerLevel.Y)
            if self.PickingItems[index].Depth.UpperLevel is not None:
                self.EditItem.SetDepthUpperLevelPoint(self.PickingItems[index].Depth.UpperLevel.X, self.PickingItems[index].Depth.UpperLevel.Y)

    def RestoreEditOptions(self, index: int):
        self.SetImageIfExists(index)
        self.EditValues[index].set(False)
        self.NameValues[index].set('')
        self.AmountValues[index].set('')
        self.RectValues[index].set(False)
        self.DepthValues[index].set(False)
        self.PlaceHiddenWidgets(index)

    def OrderButtonClick(self, index: int):
        if self.OrderValues[index].get():
            self.CurrentItem = index
            for i, value in enumerate(self.OrderValues):
                if i != index:
                    value.set(False)
        else:
            self.CurrentItem = None

    def FileButtonClick(self, index: int):
        if self.EditValues[index].get():
            file_types=[('Image Files', ('.jpg', '.png', '.gif'))]
            file_name = filedialog.askopenfilename(
                title='Image Selection',
                initialdir='C:/Users/sergi/source/repos/spatial-ai-contest/poka-yoke-picking/images',
                filetypes=file_types)
            if file_name:
                self.SetProvisionalImage(index, file_name)

    def SetProvisionalImage(self, index: int, path: str):
        self.EditItem.Image = path
        image_pil = PIL_Image.open(path)
        image_tk = ImageTk.PhotoImage(image=image_pil)
        self.ImageLabels[index].image_tk = image_tk
        self.ImageLabels[index]['image'] = image_tk

    def EditButtonClick(self, index: int):
        if self.EditValues[index].get():
            self.HiddenLabels[index].place_forget()
            EnableWidget(self.FileButtons[index])
            self.FileButtons[index].place(w=72, h=32, x=40, y=index*80+40)
            self.CopyPickingItem(index)
            self.NameValues[index].set(self.EditItem.Name)
            self.AmountValues[index].set(str(self.EditItem.Amount))
            for i in range(0, len(self.PickingItems)):
                if i != index:
                    self.RestoreEditOptions(i)
        else:
            self.RestoreEditOptions(index)

    def EditNameEntryClick(self, index: int):
        if self.EditValues[index].get():
            self.NameEntries[index]['bg'] = COLOR_TK_WHITE
            self.ApplyAmountBackground(index)
            self.DepthValues[index].set(False)
            self.RectValues[index].set(False)

    def EditAmountEntryClick(self, index: int):
        if self.EditValues[index].get():
            self.AmountEntries[index]['bg'] = COLOR_TK_WHITE
            self.ApplyNameBackground(index)
            self.DepthValues[index].set(False)
            self.RectValues[index].set(False)

    def EditRectButtonClick(self, index: int):
        if self.EditValues[index].get():
            self.ApplyNameBackground(index)
            self.ApplyAmountBackground(index)
            if self.RectValues[index].get():
                self.DepthValues[index].set(False)

    def EditDepthButtonClick(self, index: int):
        if self.EditValues[index].get():
            self.ApplyNameBackground(index)
            self.ApplyAmountBackground(index)
            if self.DepthValues[index].get():
                self.RectValues[index].set(False)

    def PlaceAffectedItems(self, del_index: int):
        length = self.GetListLength()
        if length != 0 and del_index == length:
            self.SetOrderAndArrows(del_index - 1, length)
        else:
            for index in range(del_index, length):
                self.SetOrderAndArrows(index, length)
                self.AssignVariables(index)
                self.AssignCommands(index)
                self.PlaceWidgets(index)
                if self.OrderValues[index].get():
                    self.CurrentItem = index

    def DeleteButtonClick(self, index: int):
        answer = messagebox.askyesno(title='Delete Confirmation', message='Do you want to delete this item?')
        if answer:
            del self.PickingItems[index]
            self.SaveConfigurationFile()
            if self.OrderValues[index].get():
                self.CurrentItem = None
            self.RemoveWidgets(index)
            self.RemoveVariables(index)
            self.PlaceAffectedItems(index)
            self.PlaceAddNewItemButton()

    def SaveButtonClick(self, index: int):
        answer = messagebox.askyesno(title='Save Confirmation', message='Do you want to save the settings?')
        if answer:
            self.EditItem.Name = self.NameValues[index].get()
            self.EditItem.Amount = int(self.AmountValues[index].get())
            self.PickingItems[index] = self.EditItem
            self.SaveConfigurationFile()
            self.SetImageIfExists(index)
            self.NameLabels[index]['text'] = self.PickingItems[index].Name
            self.AmountLabels[index]['text'] = str(self.PickingItems[index].Amount)
            self.ApplyBackgrounds(index)
            self.RestoreEditOptions(index)

    def CancelButtonClick(self, index: int):
        answer = messagebox.askyesno(title='Cancel Confirmation', message='Do you want to cancel your changes?')
        if answer:
            self.RestoreEditOptions(index)

    def MoveSettingsInterface(self, index: int, new_index: int):
        self.PickingItems[index], self.PickingItems[new_index] = self.PickingItems[new_index], self.PickingItems[index]
        self.SaveConfigurationFile()
        self.SwapWidgets(index, new_index)
        self.SwapVariables(index, new_index)
        self.AssignVariables(index)
        self.AssignVariables(new_index)
        self.AssignCommands(index)
        self.AssignCommands(new_index)
        self.PlaceWidgets(index)
        self.PlaceWidgets(new_index)
        length = self.GetListLength()
        self.SetOrderAndArrows(index, length)
        self.SetOrderAndArrows(new_index, length)

    def MoveUpButtonClick(self, index: int):
        new_index = index - 1
        self.MoveSettingsInterface(index, new_index)

    def MoveDownButtonClick(self, index: int):
        new_index = index + 1
        self.MoveSettingsInterface(index, new_index)

    def IsAnyItemBeingEdited(self):
        boolean_list = [value.get() for value in self.EditValues]
        editing_item = True in boolean_list
        if editing_item:
            item_index = boolean_list.index(editing_item)
            return editing_item, item_index
        else:
            return editing_item, None

    def CaptureMouseMotionEvent(self, event: EventType):
        editing, _ = self.IsAnyItemBeingEdited()
        if editing:
            self.MouseX, self.MouseY = event.x, event.y

    def CaptureMouseLeftClickEvent(self, event: EventType):
        editing, index = self.IsAnyItemBeingEdited()
        if editing:
            self.MouseX, self.MouseY = event.x, event.y
            if self.RectValues[index].get():
                if self.EditItem.Rect is not None and self.EditItem.Rect.BottomRight is None:
                    self.EditItem.SetRectBottomRightPoint(self.MouseX, self.MouseY)
                else:
                    self.EditItem.SetRectTopLeftPoint(self.MouseX, self.MouseY)
            if self.DepthValues[index].get():
                if self.EditItem.Depth is not None and self.EditItem.Depth.UpperLevel is None:
                    self.EditItem.SetDepthUpperLevelPoint(self.MouseX, self.MouseY)
                else:
                    self.EditItem.SetDepthLowerLevelPoint(self.MouseX, self.MouseY)

    def CaptureMouseRightClickEvent(self, event: EventType):
        editing, index = self.IsAnyItemBeingEdited()
        if editing:
            self.MouseX, self.MouseY = event.x, event.y
            if self.RectValues[index].get():
                self.EditItem.Rect = None
            if self.DepthValues[index].get():
                self.EditItem.Depth = None

    def GetBlendedImage(self, color_image: np.ndarray, depth_image: np.ndarray):
        blend_depth = self.BlendValue.get() / 100
        blend_color = 1 - blend_depth
        if len(color_image.shape) < 3:
            frame_color = cv2.cvtColor(color_image, cv2.COLOR_GRAY2RGB)
        else:
            frame_color = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
        if len(depth_image.shape) < 3:
            frame_depth = cv2.cvtColor(depth_image, cv2.COLOR_GRAY2RGB)
        else:
            frame_depth = cv2.cvtColor(depth_image, cv2.COLOR_BGR2RGB)
        blended_image = cv2.addWeighted(frame_color, blend_color, frame_depth, blend_depth, 0)
        return blended_image

    def SetBlendScaleSection(self):
        Label(self.Window.StreamingFrame, font=FONT_TK_NORMAL, text='Color').place(w=45, h=32, x=0, y=360)
        Label(self.Window.StreamingFrame, font=FONT_TK_NORMAL, text='Depth').place(w=50, h=32, x=590, y=360)
        self.BlendValue = IntVar(value=50)
        Scale(self.Window.StreamingFrame, from_=0, to=100, orient=HORIZONTAL, showvalue=0, variable=self.BlendValue).place(w=545, h=22, x=45, y=366)

    def DrawImage(self, color_image: np.ndarray, depth_image: np.ndarray, hand_regions: list):
        scaled_color_image = cv2.resize(color_image, (640, 360), interpolation = cv2.INTER_AREA)
        scaled_depth_image = cv2.resize(depth_image, (640, 360), interpolation = cv2.INTER_AREA)
        blended_image = self.GetBlendedImage(scaled_color_image, scaled_depth_image)

        for index, item in enumerate(self.PickingItems):
            if self.EyeValues[index].get():
                if item.Rect is not None:
                    top_l = item.Rect.TopLeft
                    bot_r = item.Rect.BottomRight
                    if top_l is not None:
                        if bot_r is not None:
                            cv2.rectangle(blended_image, (top_l.X, top_l.Y), (bot_r.X, bot_r.Y), COLOR_CV_WHITE, 1)
                        else:
                            cv2.drawMarker(blended_image, (top_l.X, top_l.Y), COLOR_CV_WHITE, cv2.MARKER_CROSS, 24, 1)
            if self.BulbValues[index].get():
                if item.Depth is not None:
                    lower = item.Depth.LowerLevel
                    upper = item.Depth.UpperLevel
                    if lower is not None:
                        if upper is not None:
                            cv2.arrowedLine(blended_image, (lower.X, lower.Y), (upper.X, upper.Y), COLOR_CV_WHITE, 1)
                        else:
                            cv2.circle(blended_image, (lower.X, lower.Y), 12, COLOR_CV_WHITE, 1)

        editing, index = self.IsAnyItemBeingEdited()
        if editing:
            if self.RectValues[index].get():
                cv2.drawMarker(blended_image, (self.MouseX, self.MouseY), COLOR_CV_WHITE, cv2.MARKER_CROSS, 24, 1)
                if self.EditItem.Rect is not None:
                    top_l = self.EditItem.Rect.TopLeft
                    if top_l is not None:
                        cv2.drawMarker(blended_image, (top_l.X, top_l.Y), COLOR_CV_WHITE, cv2.MARKER_CROSS, 24, 1)
                    bot_r = self.EditItem.Rect.BottomRight
                    if bot_r is not None:
                        cv2.drawMarker(blended_image, (bot_r.X, bot_r.Y), COLOR_CV_WHITE, cv2.MARKER_CROSS, 24, 1)
                        cv2.rectangle(blended_image, (top_l.X, top_l.Y), (bot_r.X, bot_r.Y), COLOR_CV_WHITE, 1)
                    else:
                        cv2.rectangle(blended_image, (top_l.X, top_l.Y), (self.MouseX, self.MouseY), COLOR_CV_WHITE, 1)
            if self.DepthValues[index].get():
                cv2.circle(blended_image, (self.MouseX, self.MouseY), 12, COLOR_CV_WHITE, 1)
                if self.EditItem.Depth is not None:
                    lower = self.EditItem.Depth.LowerLevel
                    if lower is not None:
                        cv2.circle(blended_image, (lower.X, lower.Y), 12, COLOR_CV_WHITE, 1)
                    upper = self.EditItem.Depth.UpperLevel
                    if upper is not None:
                        cv2.circle(blended_image, (upper.X, upper.Y), 12, COLOR_CV_WHITE, 1)
                        cv2.line(blended_image, (lower.X, lower.Y), (upper.X, upper.Y), COLOR_CV_WHITE, 1)
                    else:
                        cv2.line(blended_image, (lower.X, lower.Y), (self.MouseX, self.MouseY), COLOR_CV_WHITE, 1)

        if self.CurrentItem is not None:
            hand_color = COLOR_CV_WHITE
            current_rect = self.PickingItems[self.CurrentItem].Rect
            current_point1 = (current_rect.TopLeft.X, current_rect.TopLeft.Y)
            current_point2 = (current_rect.BottomRight.X, current_rect.BottomRight.Y)
            cv2.rectangle(blended_image, current_point1, current_point2, hand_color, 2)

        pil_image = PIL_Image.fromarray(blended_image)
        image_tk = ImageTk.PhotoImage(image=pil_image)
        self.Window.VideoLabel.image_tk = image_tk
        self.Window.VideoLabel['image'] = image_tk

        counting_image = None
        
        if color_image is not None:
            frame_color = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)

        for region in hand_regions:
            xMin, yMin, xMax, yMax = CalculatePalmRectFromRegion(frame_color, region)
            counting_image = frame_color[yMin:yMax, xMin:xMax]
        
        if counting_image is not None:
            predictions = self.part_counting.Infer(counting_image)
            print(predictions)
            pil_crop = PIL_Image.fromarray(counting_image)
            crop_tk = ImageTk.PhotoImage(image=pil_crop)
            self.Window.CropLabel.image_tk = crop_tk
            self.Window.CropLabel['image'] = crop_tk

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

    picking_poka_yoke = PokaYokePicking(config_data)
    picking_poka_yoke.Detection.StartMainLoop()
    picking_poka_yoke.Window.StartMainLoop()

if __name__ == '__main__':
    Main()