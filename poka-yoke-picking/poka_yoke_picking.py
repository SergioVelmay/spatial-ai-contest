import os
import json
import cv2
import threading
import numpy as np
import depthai as dai
import mediapipe_utils as mpu
from json import JSONEncoder
from tkinter import *
from tkinter import messagebox
from pathlib import Path
from PIL import ImageTk, Image

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
        self.Root.resizable(True, True)

        self.MainFrame = Frame(self.Root, width=1280, height=720)
        self.MainFrame.pack(expand=True)
        
        self.SettingsFrame = Frame(self.MainFrame, bg='yellow', width=440, height=680)
        self.SettingsFrame.place(x=780, y=20)

        self.StreamingLabel = Frame(self.MainFrame, bg='cyan', width=640, height=520)
        self.StreamingLabel.place(x=70, y=20)

        self.VideoFrame = Label(self.StreamingLabel, borderwidth=0, bg='white')
        self.VideoFrame.place( w=640, h=360, x=0, y=80)

        self.Root.protocol("WM_DELETE_WINDOW", self.OnClosingEvent)

    def StartMainLoop(self):
        self.Root.mainloop()
    
    def OnClosingEvent(self):
        answer = messagebox.askokcancel("Quit", "Do you want to exit the program?")
        if answer:
            self.Root.destroy()

class Detection:
    def __init__(self, drawImage: classmethod):
        self.DrawImage = drawImage
        self.QueueNames = []

        self.PalmInputLength = 128
        self.PalmScoreThreshold = 0.6
        self.PalmNmsThreshold = 0.3

    def CreatePipeline(self):
        pipeline = dai.Pipeline()
        
        cam_color = pipeline.create(dai.node.ColorCamera)
        cam_left = pipeline.create(dai.node.MonoCamera)
        cam_right = pipeline.create(dai.node.MonoCamera)
        stereo_depth = pipeline.create(dai.node.StereoDepth)

        color_out = pipeline.create(dai.node.XLinkOut)
        depth_out = pipeline.create(dai.node.XLinkOut)

        color_out.setStreamName("color")
        self.QueueNames.append("color")
        depth_out.setStreamName("depth")
        self.QueueNames.append("depth")

        fps = 30

        cam_color.setBoardSocket(dai.CameraBoardSocket.RGB)
        cam_color.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
        cam_color.setFps(fps)
        cam_color.setIspScale(1, 3)
        cam_color.initialControl.setManualFocus(48)

        cam_left.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
        cam_left.setBoardSocket(dai.CameraBoardSocket.LEFT)
        cam_left.setFps(fps)

        cam_right.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
        cam_right.setBoardSocket(dai.CameraBoardSocket.RIGHT)
        cam_right.setFps(fps)

        stereo_depth.initialConfig.setMedianFilter(dai.MedianFilter.MEDIAN_OFF)
        stereo_depth.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_ACCURACY)
        stereo_depth.setLeftRightCheck(True)
        stereo_depth.setExtendedDisparity(False)
        stereo_depth.setSubpixel(False)
        stereo_depth.setDepthAlign(dai.CameraBoardSocket.RGB)
        
        self.MaxDisparity = stereo_depth.initialConfig.getMaxDisparity()

        cam_color.isp.link(color_out.input)
        cam_left.out.link(stereo_depth.left)
        cam_right.out.link(stereo_depth.right)
        stereo_depth.disparity.link(depth_out.input)

        palm_nn = pipeline.createNeuralNetwork()
        palm_nn.setBlobPath(str(Path("models/palm_detection.blob").resolve().absolute()))
        palm_in = pipeline.createXLinkIn()
        palm_in.setStreamName("palm_in")
        palm_in.out.link(palm_nn.input)
        palm_out = pipeline.createXLinkOut()
        palm_out.setStreamName("palm_out")
        palm_nn.out.link(palm_out.input)

        return pipeline
    
    def ToPlanar(self, array, shape):
        resized = cv2.resize(array, shape, interpolation=cv2.INTER_NEAREST).transpose(2,0,1)
        return resized

    def PalmPostprocess(self, inference):
        anchor_options = mpu.SSDAnchorOptions(
            num_layers=4, 
            min_scale=0.1484375,
            max_scale=0.75,
            input_size_height=128,
            input_size_width=128,
            anchor_offset_x=0.5,
            anchor_offset_y=0.5,
            strides=[8, 16, 16, 16],
            aspect_ratios= [1.0],
            reduce_boxes_in_lowest_layer=False,
            interpolated_scale_aspect_ratio=1.0,
            fixed_anchor_size=True)

        anchors = mpu.generate_anchors(anchor_options)
        
        nb_anchors = anchors.shape[0]

        scores = np.array(inference.getLayerFp16("classificators"), dtype=np.float16) 
        boxes = np.array(inference.getLayerFp16("regressors"), dtype=np.float16).reshape((nb_anchors, 18))
        
        self.regions = mpu.decode_bboxes(self.PalmScoreThreshold, scores, boxes, anchors)
        self.regions = mpu.non_max_suppression(self.regions, self.PalmNmsThreshold)

        mpu.detections_to_rect(self.regions)
        mpu.rect_transformation(self.regions, self.frame_size, self.frame_size)

    def StartMainLoop(self):
        threading.Thread(target=self.Run, daemon=True).start()

    def Run(self):
        device = dai.Device(self.CreatePipeline())
        device.startPipeline()

        frame_color = None
        frame_depth = None

        q_palm_in = device.getInputQueue(name="palm_in")
        q_palm_out = device.getOutputQueue(name="palm_out", maxSize=4, blocking=True)

        while True:
            latestPacket = {}
            latestPacket["color"] = None
            latestPacket["depth"] = None

            queueEvents = device.getQueueEvents(("color", "depth"))
            for queueName in queueEvents:
                packets = device.getOutputQueue(queueName).tryGetAll()
                if len(packets) > 0:
                    latestPacket[queueName] = packets[-1]

            copiaColor = None

            if latestPacket["color"] is not None:
                frame_color = latestPacket["color"].getCvFrame()

                h, w = frame_color.shape[:2]
                self.frame_size = max(h, w)
                self.pad_h = int((self.frame_size - h)/2)
                self.pad_w = int((self.frame_size - w)/2)

                copiaColor = cv2.copyMakeBorder(frame_color, self.pad_h, self.pad_h, self.pad_w, self.pad_w, cv2.BORDER_CONSTANT)
                
                frame_nn = dai.ImgFrame()
                frame_nn.setWidth(self.PalmInputLength)
                frame_nn.setHeight(self.PalmInputLength)
                frame_nn.setData(self.ToPlanar(copiaColor, (self.PalmInputLength, self.PalmInputLength)))
                q_palm_in.send(frame_nn)
                
                inference = q_palm_out.get()
                self.PalmPostprocess(inference)
            
            if latestPacket["depth"] is not None:
                frame_depth = latestPacket["depth"].getFrame()
                frame_depth = (frame_depth * 255. / self.MaxDisparity).astype(np.uint8)
                frame_depth[frame_depth<128] = 0
                frame_depth = cv2.applyColorMap(frame_depth, cv2.COLORMAP_JET)
                frame_depth = np.ascontiguousarray(frame_depth)

            if frame_color is not None and frame_depth is not None:
                self.DrawImage(frame_color, frame_depth, self.regions)
                frame_color = None
                frame_depth = None

class PokaYokePicking():
    def __init__(self, json: list):
        self.Window = Window()
        self.Detection = Detection(self.DrawImage)

        self.FONT_BOLD = ('arial', 12, 'bold')
        self.FONT_NORMAL = ('arial', 12, 'normal')

        self.SetAllAttributes()
        self.SetAllIconImages()
        self.SetAllPickingItems(json)
        self.BindAllMouseEvents()
        self.SetAddNewItemButton()

    def SetAllAttributes(self):
        self.PickingItems = []
        self.CurrentItem = 2
        self.CurrentLowerZ = None
        self.CurrentUpperZ = None
        self.EditItem = None
        self.MouseX = None
        self.MouseY = None
        # widgets lists
        self.OrderLabels = []
        self.NameLabels = []
        self.EyeButtons = []
        self.BulbButtons = []
        self.EditButtons = []
        self.DeleteButtons = []
        self.UpButtons = []
        self.DownButtons = []
        self.NameEntries = []
        self.RectButtons = []
        self.DepthButtons = []
        self.SaveButtons = []
        self.CancelButtons = []
        self.HiddenLabels = []
        # variables lists
        self.EyeValues = []
        self.BulbValues = []
        self.EditValues = []
        self.NameValues = []
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
        self.EyeValues.append(BooleanVar(value=False))
        self.BulbValues.append(BooleanVar(value=False))
        self.EditValues.append(BooleanVar(value=False))
        self.NameValues.append(StringVar(value=''))
        self.RectValues.append(BooleanVar(value=False))
        self.DepthValues.append(BooleanVar(value=False))

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
        self.AddIcon = PhotoImage(file='./assets/icon-add.png')

    def AssignCommands(self, index: int):
        self.EditButtons[index]['command'] = lambda: self.EditButtonClick(index)
        self.DeleteButtons[index]['command'] = lambda: self.DeleteButtonClick(index)
        self.UpButtons[index]['command'] = lambda: self.MoveUpButtonClick(index)
        self.DownButtons[index]['command'] = lambda: self.MoveDownButtonClick(index)
        self.RectButtons[index]['command'] = lambda: self.EditRectButtonClick(index)
        self.DepthButtons[index]['command'] = lambda: self.EditDepthButtonClick(index)
        self.SaveButtons[index]['command'] = lambda: self.SaveButtonClick(index)
        self.CancelButtons[index]['command'] = lambda: self.CancelButtonClick(index)
        self.NameEntries[index].bind('<Button-1>', lambda _: self.EditNameEntryClick(index))
    
    def AssignVariables(self, index: int):
        self.EyeButtons[index]['variable'] = self.EyeValues[index]
        self.BulbButtons[index]['variable'] = self.BulbValues[index]
        self.EditButtons[index]['variable'] = self.EditValues[index]
        self.NameEntries[index]['textvariable'] = self.NameValues[index]
        self.RectButtons[index]['variable'] = self.RectValues[index]
        self.DepthButtons[index]['variable'] = self.DepthValues[index]

    def SetWidgets(self, index: int):
        self.OrderLabels.append(Label(self.Window.SettingsFrame, font=self.FONT_BOLD, relief=SOLID))
        self.NameLabels.append(Label(self.Window.SettingsFrame, text=self.PickingItems[index].Name, font=self.FONT_BOLD, relief=SOLID))
        self.EyeButtons.append(Checkbutton(self.Window.SettingsFrame, image=self.EyeOffIcon, selectimage=self.EyeOnIcon,
            onvalue=True, offvalue=False, indicatoron=False))
        self.BulbButtons.append(Checkbutton(self.Window.SettingsFrame, image=self.BulbOffIcon, selectimage=self.BulbOnIcon,
            onvalue=True, offvalue=False, indicatoron=False))
        self.EditButtons.append(Checkbutton(self.Window.SettingsFrame, image=self.EditIcon,
            onvalue=True, offvalue=False, indicatoron=False))
        self.DeleteButtons.append(Button(self.Window.SettingsFrame, image=self.DeleteIcon))
        self.UpButtons.append(Button(self.Window.SettingsFrame, image=self.UpIcon))
        self.DownButtons.append(Button(self.Window.SettingsFrame, image=self.DownIcon))
        self.NameEntries.append(Entry(self.Window.SettingsFrame, font=self.FONT_NORMAL, justify=CENTER))
        self.RectButtons.append(Checkbutton(self.Window.SettingsFrame, image=self.RectIcon,
            onvalue=True, offvalue=False, indicatoron=False))
        self.DepthButtons.append(Checkbutton(self.Window.SettingsFrame, image=self.DepthIcon,
            onvalue=True, offvalue=False, indicatoron=False))
        self.SaveButtons.append(Button(self.Window.SettingsFrame, image=self.SaveIcon))
        self.CancelButtons.append(Button(self.Window.SettingsFrame, image=self.CancelIcon))
        self.HiddenLabels.append(Label(self.Window.SettingsFrame))
        self.AssignVariables(index)
        self.AssignCommands(index)
    
    def SetOrderAndArrows(self, index: int, length: int):
        self.OrderLabels[index]['text'] = str(index + 1)
        EnableWidget(self.UpButtons[index])
        EnableWidget(self.DownButtons[index])
        if index == 0:
            DisableWidget(self.UpButtons[index])
        if index == length - 1:
            DisableWidget(self.DownButtons[index])

    def PlaceHiddenLabel(self, index: int):
        self.HiddenLabels[index].place(w=312, h=32, x=40, y=index*80+40)

    def PlaceWidgets(self, index: int):
        self.OrderLabels[index].place(w=32, h=32, x=0, y=index*80)
        self.NameLabels[index].place(w=150, h=32, x=40, y=index*80)
        self.EyeButtons[index].place(w=32, h=32, x=200, y=index*80)
        self.BulbButtons[index].place(w=32, h=32, x=240, y=index*80)
        self.EditButtons[index].place(w=32, h=32, x=280, y=index*80)
        self.DeleteButtons[index].place(w=32, h=32, x=320, y=index*80)
        self.UpButtons[index].place(w=32, h=32, x=360, y=index*80)
        self.DownButtons[index].place(w=32, h=32, x=400, y=index*80)
        self.NameEntries[index].place(w=150, h=32, x=40, y=index*80+40)
        self.RectButtons[index].place(w=32, h=32, x=200, y=index*80+40)
        self.DepthButtons[index].place(w=32, h=32, x=240, y=index*80+40)
        self.SaveButtons[index].place(w=32, h=32, x=280, y=index*80+40)
        self.CancelButtons[index].place(w=32, h=32, x=320, y=index*80+40)
        self.PlaceHiddenLabel(index)

    def BindAllMouseEvents(self):
        self.Window.VideoFrame.bind('<Motion>', self.CaptureMouseMotionEvent, add="+")
        self.Window.VideoFrame.bind('<Button-1>', self.CaptureMouseLeftClickEvent, add="+")
        self.Window.VideoFrame.bind('<Button-3>', self.CaptureMouseRightClickEvent, add="+")

    def SetAddNewItemButton(self):
        self.AddButton = Button(self.Window.SettingsFrame, text='Add new item', font=self.FONT_NORMAL,
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
        pick_name = "NewItem#" + str(index + 1)
        pick_item = PickingItem(pick_name)
        self.PickingItems.append(pick_item)
        length = self.GetListLength()
        if index > 0:
            self.SetOrderAndArrows(index - 1, length)
        self.SetSettingsInterface(index, length)
        self.PlaceAddNewItemButton()
        self.SaveConfigurationFile()

    def SwapWidgets(self, index: int, new_index: int):
        self.OrderLabels[index], self.OrderLabels[new_index] = self.OrderLabels[new_index], self.OrderLabels[index]
        self.NameLabels[index], self.NameLabels[new_index] = self.NameLabels[new_index], self.NameLabels[index]
        self.EyeButtons[index], self.EyeButtons[new_index] = self.EyeButtons[new_index], self.EyeButtons[index]
        self.BulbButtons[index], self.BulbButtons[new_index] = self.BulbButtons[new_index], self.BulbButtons[index]
        self.EditButtons[index], self.EditButtons[new_index] = self.EditButtons[new_index], self.EditButtons[index]
        self.DeleteButtons[index], self.DeleteButtons[new_index] = self.DeleteButtons[new_index], self.DeleteButtons[index]
        self.UpButtons[index], self.UpButtons[new_index] = self.UpButtons[new_index], self.UpButtons[index]
        self.DownButtons[index], self.DownButtons[new_index] = self.DownButtons[new_index], self.DownButtons[index]
        self.NameEntries[index], self.NameEntries[new_index] = self.NameEntries[new_index], self.NameEntries[index]
        self.RectButtons[index], self.RectButtons[new_index] = self.RectButtons[new_index], self.RectButtons[index]
        self.DepthButtons[index], self.DepthButtons[new_index] = self.DepthButtons[new_index], self.DepthButtons[index]
        self.SaveButtons[index], self.SaveButtons[new_index] = self.SaveButtons[new_index], self.SaveButtons[index]
        self.CancelButtons[index], self.CancelButtons[new_index] = self.CancelButtons[new_index], self.CancelButtons[index]
        self.HiddenLabels[index], self.HiddenLabels[new_index] = self.HiddenLabels[new_index], self.HiddenLabels[index]

    def SwapVariables(self, index: int, new_index: int):
        self.EyeValues[index], self.EyeValues[new_index] = self.EyeValues[new_index], self.EyeValues[index]
        self.BulbValues[index], self.BulbValues[new_index] = self.BulbValues[new_index], self.BulbValues[index]
        self.EditValues[index], self.EditValues[new_index] = self.EditValues[new_index], self.EditValues[index]
        self.NameValues[index], self.NameValues[new_index] = self.NameValues[new_index], self.NameValues[index]
        self.RectValues[index], self.RectValues[new_index] = self.RectValues[new_index], self.RectValues[index]
        self.DepthValues[index], self.DepthValues[new_index] = self.DepthValues[new_index], self.DepthValues[index]

    def ForgetWidgets(self, index: int):
        self.OrderLabels[index].place_forget()
        self.NameLabels[index].place_forget()
        self.EyeButtons[index].place_forget()
        self.BulbButtons[index].place_forget()
        self.EditButtons[index].place_forget()
        self.DeleteButtons[index].place_forget()
        self.UpButtons[index].place_forget()
        self.DownButtons[index].place_forget()
        self.NameEntries[index].place_forget()
        self.RectButtons[index].place_forget()
        self.DepthButtons[index].place_forget()
        self.SaveButtons[index].place_forget()
        self.CancelButtons[index].place_forget()
        self.HiddenLabels[index].place_forget()

    def RemoveWidgets(self, index: int):
        self.ForgetWidgets(index)
        del self.OrderLabels[index]
        del self.NameLabels[index]
        del self.EyeButtons[index]
        del self.BulbButtons[index]
        del self.EditButtons[index]
        del self.DeleteButtons[index]
        del self.UpButtons[index]
        del self.DownButtons[index]
        del self.NameEntries[index]
        del self.RectButtons[index]
        del self.DepthButtons[index]
        del self.SaveButtons[index]
        del self.CancelButtons[index]
        del self.HiddenLabels[index]

    def RemoveVariables(self, index: int):
        del self.EyeValues[index]
        del self.BulbValues[index]
        del self.EditValues[index]
        del self.NameValues[index]
        del self.RectValues[index]
        del self.DepthValues[index]
    
    def SaveConfigurationFile(self):
        with open(CONFIG_FILE_NAME, "w") as json_file:
            json.dump(self.PickingItems, json_file, cls=CustomEncoder, indent=4)
            json_file.close()

    def CopyPickingItem(self, index: int):
        self.EditItem = PickingItem(self.PickingItems[index].Name)
        if self.PickingItems[index].Rect is not None:
            self.EditItem.SetRectTopLeftPoint(self.PickingItems[index].Rect.TopLeft.X, self.PickingItems[index].Rect.TopLeft.Y)
            if self.PickingItems[index].Rect.BottomRight is not None:
                self.EditItem.SetRectBottomRightPoint(self.PickingItems[index].Rect.BottomRight.X, self.PickingItems[index].Rect.BottomRight.Y)
        if self.PickingItems[index].Depth is not None:
            self.EditItem.SetDepthLowerLevelPoint(self.PickingItems[index].Depth.LowerLevel.X, self.PickingItems[index].Depth.LowerLevel.Y)
            if self.PickingItems[index].Depth.UpperLevel is not None:
                self.EditItem.SetDepthUpperLevelPoint(self.PickingItems[index].Depth.UpperLevel.X, self.PickingItems[index].Depth.UpperLevel.Y)

    def RestoreEditOptions(self, index: int):
        self.Edit = None
        self.EditValues[index].set(False)
        self.NameValues[index].set('')
        self.RectValues[index].set(False)
        self.DepthValues[index].set(False)
        self.PlaceHiddenLabel(index)

    def EditButtonClick(self, index: int):
        if self.EditValues[index].get():
            self.HiddenLabels[index].place_forget()
            self.CopyPickingItem(index)
            self.NameValues[index].set(self.EditItem.Name)
        else:
            self.RestoreEditOptions(index)

    def EditNameEntryClick(self, index: int):
        if self.EditValues[index].get():
            self.DepthValues[index].set(False)
            self.RectValues[index].set(False)

    def EditRectButtonClick(self, index: int):
        if self.EditValues[index].get() and self.RectValues[index].get():
            self.DepthValues[index].set(False)

    def EditDepthButtonClick(self, index: int):
        if self.EditValues[index].get() and self.DepthValues[index].get():
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

    def DeleteButtonClick(self, index: int):
        answer = messagebox.askyesno(title='Delete Confirmation', message='Do you want to delete this item?')
        if answer:
            del self.PickingItems[index]
            self.SaveConfigurationFile()
            self.RemoveWidgets(index)
            self.RemoveVariables(index)
            self.PlaceAffectedItems(index)
            self.PlaceAddNewItemButton()

    def SaveButtonClick(self, index: int):
        answer = messagebox.askyesno(title='Save Confirmation', message='Do you want to save the settings?')
        if answer:
            self.EditItem.Name = self.NameValues[index].get()
            self.PickingItems[index] = self.EditItem
            self.NameLabels[index]['text'] = self.PickingItems[index].Name
            self.SaveConfigurationFile()
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
        editing, index = self.IsAnyItemBeingEdited()
        if editing:
            self.MouseX, self.MouseY = event.x, event.y
            if self.RectValues[index].get():
                pass # TODO print cursor
                if self.EditItem.Rect is not None and self.EditItem.Rect.TopLeft is not None:
                    pass # TODO print rectangle
            if self.DepthValues[index].get():
                pass # TODO print circle
                if self.EditItem.Depth is not None and self.EditItem.Rect.TopLeft is not None:
                    pass # TODO print line

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
        if len(color_image.shape) < 3:
            frame_color = cv2.cvtColor(color_image, cv2.COLOR_GRAY2RGB)
        else:
            frame_color = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
        if len(depth_image.shape) < 3:
            frame_depth = cv2.cvtColor(depth_image, cv2.COLOR_GRAY2RGB)
        else:
            frame_depth = cv2.cvtColor(depth_image, cv2.COLOR_BGR2RGB)
        blended_image = cv2.addWeighted(frame_color, 0.9, frame_depth, 0.1, 0)
        return blended_image

    def GetRectFromRegion(self, frame, region):
        x1_float = region.pd_box[0]
        y1_float = region.pd_box[1]
        x2_float = x1_float + region.pd_box[2]
        y2_float = y1_float + region.pd_box[3]
        h, w = frame.shape[:2]
        frame_size = max(h, w)
        pad_h = int((frame_size - h)/2)
        pad_w = int((frame_size - w)/2)
        x1 = int(x1_float*frame_size) - pad_w
        y1 = int(y1_float*frame_size) - pad_h
        x2 = int(x2_float*frame_size) - pad_w
        y2 = int(y2_float*frame_size) - pad_h
        return x1, y1, x2, y2

    def GetRoiByPercent(self, percent, xMin, yMin, xMax, yMax):
        delta_x = int((xMax - xMin) * percent / 2)
        delta_y = int((yMax - yMin) * percent / 2)
        xMin += delta_x
        yMin += delta_y
        xMax -= delta_x
        yMax -= delta_y
        return xMin, yMin, xMax, yMax

    def GetRoiByRadius(self, radius:int, point: Point):
        x1 = point.X - radius
        y1 = point.Y - radius
        x2 = point.X + radius
        y2 = point.Y + radius
        return x1, y1, x2, y2

    def CalculateRectFromRegion(self, color_image, region):
        x1, y1, x2, y2 = self.GetRectFromRegion(color_image, region)
        xMin, yMin, xMax, yMax = self.GetRoiByPercent(0.5, x1, y1, x2, y2)
        return xMin, yMin, xMax, yMax
    
    def CalculateDepthFromCoords(self, depth_image, xMin, yMin, xMax, yMax):
        depth_roi = depth_image[yMin:yMax, xMin:xMax]
        float_mean = np.mean(depth_roi[True])
        if np.isnan(float_mean):
            average_depth = None
        else:
            average_depth = int(float_mean)
        return average_depth

    def CalculateTextPoints(self, xMin: int, yMin: int, xMax: int, yMax: int):
        centroid_x = int((xMax - xMin) / 2) + xMin
        centroid_y = int((yMax - yMin) / 2) + yMin
        point_x = (centroid_x - 13, centroid_y + 4)
        point_y = (centroid_x - 4, centroid_y + 4)
        point_z = (centroid_x + 5, centroid_y + 4)
        return point_x, point_y, point_z

    def CalculateDepthRange(self, depth_image: np.ndarray, current_depth: Depth):
        min_x1, min_y1, min_x2, min_y2 = self.GetRoiByRadius(10, current_depth.LowerLevel)
        max_x1, max_y1, max_x2, max_y2 = self.GetRoiByRadius(10, current_depth.UpperLevel)
        min_depth = self.CalculateDepthFromCoords(depth_image, min_x1, min_y1, min_x2, min_y2)
        max_depth = self.CalculateDepthFromCoords(depth_image, max_x1, max_y1, max_x2, max_y2)
        return min_depth, max_depth

    def IsRectInRangeX(self, rect: Rect, x1: int, x2: int):
        left_value = rect.TopLeft.X < x1
        right_value = rect.BottomRight.X > x2
        return left_value and right_value

    def IsRectInRangeY(self, rect: Rect, y1: int, y2: int):
        top_value = rect.TopLeft.Y < y1
        bot_value = rect.BottomRight.Y > y2
        return top_value and bot_value
    
    def IsRectInsideItemRect(self, rect: Rect, x1: int, y1: int, x2: int, y2: int):
        top_left_value = rect.TopLeft.X < x1 and rect.TopLeft.Y < y1
        bot_right_value = rect.BottomRight.X > x2 and rect.BottomRight.Y > y2
        return top_left_value and bot_right_value

    def IsDepthInRangeZ(self, depth: int, lower_z: int, upper_z: int):
        lower_value = lower_z > depth
        upper_value = upper_z < depth
        return lower_value and upper_value

    def DrawImage(self, color_image: np.ndarray, depth_image: np.ndarray, hand_regions: list):
        blended_image = self.GetBlendedImage(color_image, depth_image)

        if self.CurrentItem is not None:
            hand_color = (255, 255, 255)
            x_color = (255, 255, 255)
            y_color = (255, 255, 255)
            z_color = (255, 255, 255)
            current_rect = self.PickingItems[self.CurrentItem].Rect
            current_point1 = (current_rect.TopLeft.X, current_rect.TopLeft.Y)
            current_point2 = (current_rect.BottomRight.X, current_rect.BottomRight.Y)
            cv2.rectangle(blended_image, current_point1, current_point2, hand_color, 2)

            if self.CurrentLowerZ is None and self.CurrentUpperZ is None:
                current_depth = self.PickingItems[self.CurrentItem].Depth
                self.CurrentLowerZ, self.CurrentUpperZ = self.CalculateDepthRange(depth_image, current_depth)

            for region in hand_regions:
                xMin, yMin, xMax, yMax = self.CalculateRectFromRegion(blended_image, region)

                if self.IsRectInsideItemRect(current_rect, xMin, yMin, xMax, yMax):
                    hand_color = (14, 168, 75)
                else:
                    hand_color = (236, 31, 36)

                x_point, y_point, z_point = self.CalculateTextPoints(xMin, yMin, xMax, yMax)

                if self.IsRectInRangeX(current_rect, xMin, xMax):
                    x_color = (14, 168, 75)
                else:
                    x_color = (236, 31, 36)

                if self.IsRectInRangeY(current_rect, yMin, yMax):
                    y_color = (14, 168, 75)
                else:
                    y_color = (236, 31, 36)

                depth_value = self.CalculateDepthFromCoords(depth_image, xMin, yMin, xMax, yMax)
                
                if self.IsDepthInRangeZ(depth_value, self.CurrentLowerZ, self.CurrentUpperZ):
                    z_color = (14, 168, 75)
                else:
                    z_color = (236, 31, 36)

                blended_image_copy = blended_image.copy()
                cv2.rectangle(blended_image_copy, (xMin, yMin), (xMax, yMax), z_color, cv2.FILLED)
                blended_image = cv2.addWeighted(blended_image, 0.8, blended_image_copy, 0.2, 0)
                cv2.rectangle(blended_image, (xMin, yMin), (xMax, yMax), hand_color, 2)
                cv2.putText(blended_image, 'X', x_point, cv2.FONT_HERSHEY_DUPLEX, 0.4, x_color, 1)
                cv2.putText(blended_image, 'Y', y_point, cv2.FONT_HERSHEY_DUPLEX, 0.4, y_color, 1)
                cv2.putText(blended_image, 'Z', z_point, cv2.FONT_HERSHEY_DUPLEX, 0.4, z_color, 1)

        pil_image = Image.fromarray(blended_image)
        image_tk = ImageTk.PhotoImage(image=pil_image)
        self.Window.VideoFrame.image_tk = image_tk
        self.Window.VideoFrame['image'] = image_tk

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