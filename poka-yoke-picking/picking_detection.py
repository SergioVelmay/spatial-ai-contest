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
        
        self.SettingsFrame = Frame(self.Root, bg='yellow', width=440, height=680)
        self.SettingsFrame.place(x=780, y=20)

        self.VideoFrame = Frame(self.Root, bg='cyan', width=640, height=520)
        self.VideoFrame.place(x=70, y=20)

        self.Root.protocol("WM_DELETE_WINDOW", self.OnClosingEvent)

    def StartMainLoop(self):
        self.Root.mainloop()
    
    def OnClosingEvent(self):
        answer = messagebox.askokcancel("Quit", "Do you want to exit the program?")
        if answer:
            self.Root.destroy()

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

class DepthCalculation:
    def __init__(self, video: Frame):
        self.VideoFrame = video
        self.ColorWeight = 0.5
        self.DepthWeight = 0.5
        self.QueueNames = []

        self.PalmInputLength = 128
        self.PalmScoreThreshold = 0.6
        self.PalmNmsThreshold = 0.3

        self.StreamingLabel = Label(self.VideoFrame, borderwidth=0, bg='white')
        self.StreamingLabel.place( w=640, h=360, x=0, y=80)

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

                for i, region in enumerate(self.regions):
                    self.DrawPalmRectangle(frame_color, copiaColor, region)
            
            if latestPacket["depth"] is not None:
                frame_depth = latestPacket["depth"].getFrame()
                frame_depth = (frame_depth * 255. / self.MaxDisparity).astype(np.uint8)
                frame_depth[frame_depth<128] = 0
                frame_depth = cv2.applyColorMap(frame_depth, cv2.COLORMAP_JET)
                frame_depth = np.ascontiguousarray(frame_depth)

                for i, region in enumerate(self.regions):
                    self.AverageDepth, self.CentroidX, self.CentroidY = self.CalcSpatials(self.X1, self.Y1, self.X2, self.Y2, frame_depth)
                    xMin, yMin, xMax, yMax = self.GetRoiByPercent(0.5, self.X1, self.Y1, self.X2, self.Y2)
                    cv2.rectangle(frame_depth, (xMin, yMin), (xMax, yMax), (255, 255, 255), 2)
                    self.DrawPalmText(frame_depth, self.AverageDepth, self.CentroidX-10, self.CentroidY)

            if frame_color is not None and frame_depth is not None:
                frame_color = cv2.cvtColor(frame_color, cv2.COLOR_BGR2RGB)
                if len(frame_depth.shape) < 3:
                    frame_depth = cv2.cvtColor(frame_depth, cv2.COLOR_GRAY2RGB)
                else:
                    frame_depth = cv2.cvtColor(frame_depth, cv2.COLOR_BGR2RGB)
                blended = cv2.addWeighted(frame_color, self.ColorWeight, frame_depth, self.DepthWeight, 0)
                pil_image = Image.fromarray(blended)
                image_tk = ImageTk.PhotoImage(image=pil_image)
                self.StreamingLabel.image_tk = image_tk
                self.StreamingLabel['image'] = image_tk
                frame_color = None
                frame_depth = None

    def DrawPalmRectangle(self, frame, copy, region):
        x1_float = region.pd_box[0]
        y1_float = region.pd_box[1]
        x2_float = x1_float + region.pd_box[2]
        y2_float = y1_float + region.pd_box[3]
        new_h, new_w = copy.shape[:2]
        self.X1 = int(x1_float*new_w) - self.pad_w
        self.Y1 = int(y1_float*new_h) - self.pad_h
        self.X2 = int(x2_float*new_w) - self.pad_w
        self.Y2 = int(y2_float*new_h) - self.pad_h
        cv2.rectangle(frame, (self.X1, self.Y1), (self.X2, self.Y2), (255, 255, 255), 2)
    
    def DrawPalmText(self, frame, depth, point1, point2):
        cv2.putText(frame, str(depth), (point1, point2), cv2.FONT_HERSHEY_DUPLEX, 0.4, (255, 255, 255))
    
    def CalcSpatials(self, xMin, yMin, xMax, yMax, depth):
        xMin, yMin, xMax, yMax = self.GetRoiByPercent(0.5, xMin, yMin, xMax, yMax)

        depth_roi = depth[yMin:yMax, xMin:xMax]

        average_depth = int(np.mean(depth_roi[True]))

        centroid_x = int((xMax - xMin) / 2) + xMin
        centroid_y = int((yMax - yMin) / 2) + yMin

        return (average_depth, centroid_x, centroid_y)

    def GetRoiByPercent(self, percent, xMin, yMin, xMax, yMax):
        delta_x = int((xMax - xMin) * percent / 2)
        delta_y = int((yMax - yMin) * percent / 2)
        xMin += delta_x
        yMin += delta_y
        xMax -= delta_x
        yMax -= delta_y
        return xMin, yMin, xMax, yMax

class PickingPokaYoke():
    def __init__(self, json: list):
        self.Length = len(json)
        self.PickingSettings = []
        self.Interface = Window()
        self.Detection = DepthCalculation(self.Interface.VideoFrame)

        for index, item in enumerate(json):
            pick = PickingItemFromJson(item)
            if pick is not None:
                self.AppendPickingSetting(pick, index)
        self.SetAddNewItemButton()

    def AppendPickingSetting(self, pick: PickingItem, index: int):
        self.PickingSettings.append(
            SettingsItem(self.Interface.SettingsFrame, self.Interface.VideoFrame, pick, index, self.Length, 
                self.MoveItemButtonClick, self.UpdateItemButtonClick, self.DeleteItemButtonClick))
    
    def SetAddNewItemButton(self):
        self.AddIcon = PhotoImage(file='./assets/icon-add.png')
        font_normal = ('arial', 12, 'normal')
        self.AddButton = Button(self.Interface.SettingsFrame, text='Add new item', font=font_normal,
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

    picking_poka_yoke = PickingPokaYoke(config_data)
    picking_poka_yoke.Detection.StartMainLoop()
    picking_poka_yoke.Interface.StartMainLoop()

if __name__ == '__main__':
    Main()