from tkinter import *

class Window(Frame):

    def __init__(self, master=None):
        Frame.__init__(self, master)        
        self.master = master
        self.pack(fill=BOTH, expand=1)

        self.eye_value = BooleanVar(value=True)
        self.eye_on_icon = PhotoImage(file='./assets/icon-eye-on.png')
        self.eye_off_icon = PhotoImage(file='./assets/icon-eye-off.png')
        Checkbutton(self, variable=self.eye_value,
            image=self.eye_off_icon, selectimage=self.eye_on_icon,
            onvalue=True, offvalue=False, indicatoron=False).pack()

        self.bulb_value = BooleanVar(value=True)
        self.bulb_on_icon = PhotoImage(file='./assets/icon-bulb-on.png')
        self.bulb_off_icon = PhotoImage(file='./assets/icon-bulb-off.png')
        Checkbutton(self, variable=self.bulb_value,
            image=self.bulb_off_icon, selectimage=self.bulb_on_icon,
            onvalue=True, offvalue=False, indicatoron=False).pack()

        Button(self, text="Test", command=self.test_click).pack()

        Button(self, text="Exit", command=self.exit_click).pack()
    
    def test_click(self):
        print("EYE :", self.eye_value.get())
        print("BULB:", self.bulb_value.get())

    def exit_click(self):
        exit()
        
root = Tk()
app = Window(root)
root.wm_title("Tkinter UI")
root.geometry("200x400")
root.mainloop()
