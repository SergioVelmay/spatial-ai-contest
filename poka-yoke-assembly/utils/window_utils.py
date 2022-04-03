import cv2
import numpy as np
from tkinter import *
from tkinter import messagebox
from PIL import ImageTk
from PIL import Image as PIL_Image

from utils.drawing_utils import *

def SetLabelImageFromPath(label: Widget, path: str):
    image_pil = PIL_Image.open(path)
    image_tk = ImageTk.PhotoImage(image=image_pil)
    label.configure(image=image_tk)
    label.image_tk = image_tk
    label['image'] = image_tk

def SetLabelImageFromArray(label: Widget, array: np.ndarray):
    image_rgb = cv2.cvtColor(array, cv2.COLOR_BGR2RGB)
    image_pil = PIL_Image.fromarray(image_rgb)
    image_tk = ImageTk.PhotoImage(image=image_pil)
    label.configure(image=image_tk)
    label.image_tk = image_tk
    label['image'] = image_tk

class AssemblyWindow():
    def __init__(self):
        self.Root = Tk()
        self.Root.wm_title('Poka-yoke Assembly')
        self.Root.geometry('1280x720')
        self.Root.resizable(True, True)

        self.MainFrame = Frame(self.Root, width=1280, height=720)
        self.MainFrame.pack(expand=True)
        
        self.PrimaryLabel = Label(self.MainFrame, borderwidth=0, bg=COLOR_TK_WHITE)
        self.PrimaryLabel.place(w=400, h=400, x=20, y=20)
        
        self.ModelLabel = Label(self.MainFrame, borderwidth=0, bg=COLOR_TK_WHITE)
        self.ModelLabel.place(w=400, h=400, x=440, y=20)
        
        self.SecondaryLabel = Label(self.MainFrame, borderwidth=0, bg=COLOR_TK_WHITE)
        self.SecondaryLabel.place(w=400, h=400, x=860, y=20)

        self.LegoPartsLabel = Label(self.MainFrame, borderwidth=0, bg=COLOR_TK_WHITE)
        self.LegoPartsLabel.place(w=400, h=120, x=20, y=440)
        SetLabelImageFromPath(self.LegoPartsLabel, './assets/lego-parts.jpg')

        self.LegoAssemblyLabel = Label(self.MainFrame, borderwidth=0, bg=COLOR_TK_WHITE)
        self.LegoAssemblyLabel.place(w=400, h=120, x=20, y=580)
        SetLabelImageFromPath(self.LegoAssemblyLabel, './assets/lego-assembly.jpg')

        self.InfoFrame = Label(self.MainFrame, width=400, height=260)
        self.InfoFrame.place(x=440, y=440)

        self.TextLabel = Label(self.InfoFrame, borderwidth=0, text='Detections:', font=FONT_TK_NORMAL, anchor=NW, bg=COLOR_TK_YELLOW)
        self.TextLabel.place(w=400, h=260, x=0, y=0)

        self.ValidationFrame = Frame(self.MainFrame, width=400, height=260)
        self.ValidationFrame.place(x=860, y=440)

        self.PartALabel = Label(self.ValidationFrame, borderwidth=0, bg=COLOR_TK_WHITE)
        self.PartALabel.place(w=72, h=72, x=0, y=0)
        SetLabelImageFromPath(self.PartALabel, './images/a_6285647.jpg')

        self.PartBLabels = []

        for index in range(5):
            self.PartBLabels.append(Label(self.ValidationFrame, borderwidth=0, bg=COLOR_TK_WHITE))
            self.PartBLabels[index].place(w=72, h=72, x=index*80, y=80)
            SetLabelImageFromPath(self.PartBLabels[index], './images/b_4565452.jpg')

        self.PartCLabel = Label(self.ValidationFrame, borderwidth=0, bg=COLOR_TK_WHITE)
        self.PartCLabel.place(w=72, h=72, x=0, y=160)
        SetLabelImageFromPath(self.PartCLabel, './images/c_6285646.jpg')

        self.PartDLabel = Label(self.ValidationFrame, borderwidth=0, bg=COLOR_TK_WHITE)
        self.PartDLabel.place(w=72, h=72, x=80, y=160)
        SetLabelImageFromPath(self.PartDLabel, './images/d_6130007.jpg')

        self.Root.protocol('WM_DELETE_WINDOW', self.OnClosingEvent)

    def StartMainLoop(self):
        self.Root.mainloop()
    
    def OnClosingEvent(self):
        answer = messagebox.askokcancel('Quit', 'Do you want to exit the program?')
        if answer:
            self.Root.destroy()