from tkinter import *

class Window(Frame):

    def __init__(self, master=None):
        Frame.__init__(self, master)        
        self.master = master
        self.pack(fill=BOTH, expand=1)
        
        Label(self, text="111AAA111", font=('arial', 12, 'bold'), relief=SOLID).place(w=128, h=32, x=32, y=32)

        self.eye_value = BooleanVar(value=False)
        self.eye_on_icon = PhotoImage(file='./assets/icon-eye-on.png')
        self.eye_off_icon = PhotoImage(file='./assets/icon-eye-off.png')
        Checkbutton(self, variable=self.eye_value,
            image=self.eye_off_icon, selectimage=self.eye_on_icon,
            onvalue=True, offvalue=False, indicatoron=False).place(w=32, h=32, x=160, y=32)

        self.bulb_value = BooleanVar(value=False)
        self.bulb_on_icon = PhotoImage(file='./assets/icon-bulb-on.png')
        self.bulb_off_icon = PhotoImage(file='./assets/icon-bulb-off.png')
        Checkbutton(self, variable=self.bulb_value,
            image=self.bulb_off_icon, selectimage=self.bulb_on_icon,
            onvalue=True, offvalue=False, indicatoron=False).place(w=32, h=32, x=192, y=32)

        self.edit_value = BooleanVar(value=False)
        self.edit_icon = PhotoImage(file='./assets/icon-pen.png')
        Checkbutton(self, variable=self.edit_value, image=self.edit_icon, command=self.edit_click,
            onvalue=True, offvalue=False, indicatoron=False).place(w=32, h=32, x=224, y=32)
        
        self.delete_icon = PhotoImage(file='./assets/icon-trash.png')
        Button(self, image=self.delete_icon, command=self.delete_click).place(w=32, h=32, x=256, y=32)

        self.name_value = StringVar(value="111AAA111")
        Entry(self, textvariable=self.name_value, font=('arial', 12, 'normal'), justify=CENTER).place(w=128, h=32, x=32, y=64)

        self.square_value = BooleanVar(value=False)
        self.square_icon = PhotoImage(file='./assets/icon-square.png')
        Checkbutton(self, variable=self.square_value, image=self.square_icon,
            onvalue=True, offvalue=False, indicatoron=False).place(w=32, h=32, x=160, y=64)

        self.depth_value = BooleanVar(value=False)
        self.depth_icon = PhotoImage(file='./assets/icon-depth.png')
        Checkbutton(self, variable=self.depth_value, image=self.depth_icon,
            onvalue=True, offvalue=False, indicatoron=False).place(w=32, h=32, x=192, y=64)
        
        self.save_icon = PhotoImage(file='./assets/icon-file.png')
        Button(self, image=self.save_icon, command=self.save_click).place(w=32, h=32, x=224, y=64)
        
        self.cancel_icon = PhotoImage(file='./assets/icon-cancel.png')
        Button(self, image=self.cancel_icon, command=self.cancel_click).place(w=32, h=32, x=256, y=64)

        self.edit_label = Label(self)
        self.edit_label.place(w=256, h=32, x=32, y=64)

        Button(self, text="Test", command=self.test_click).place(x=100, y=200)

        Button(self, text="Exit", command=self.exit_click).place(x=350, y=250)

        master.bind('<Motion>', self.mouse_motion)
        master.bind('<Button-1>', self.mouse_left_click)
        master.bind('<Button-3>', self.mouse_right_click)
    
    def edit_click(self):
        if self.edit_value.get():
            self.edit_label.place_forget()
        else:
            self.edit_label.place(w=256, h=32, x=32, y=64)
    
    def delete_click(self):
        None
    
    def save_click(self):
        None
    
    def cancel_click(self):
        None
    
    def test_click(self):
        print("EYE :", self.eye_value.get())
        print("BULB:", self.bulb_value.get())

    def exit_click(self):
        exit()

    def mouse_motion(self, event):
        if self.eye_value.get():
            print("(x:%s, y:%s)" % (event.x, event.y))

    def mouse_left_click(self, event):
        if self.bulb_value.get():
            print("(x:%s, y:%s) LEFT CLICK" % (event.x, event.y))

    def mouse_right_click(self, event):
        if self.bulb_value.get():
            print("(x:%s, y:%s) RIGHT CLICK" % (event.x, event.y))

root = Tk()
app = Window(root)
root.wm_title("Tkinter UI")
root.geometry("400x300")
root.mainloop()
