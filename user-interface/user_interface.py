from tkinter import *
from tkinter import messagebox

class Window(Frame):

    def __init__(self, master=None):
        Frame.__init__(self, master)        
        self.master = master
        self.pack(fill=BOTH, expand=1)

        self.number_label = Label(self, text="1", font=('arial', 12, 'bold'), relief=SOLID)
        self.number_label.place(w=32, h=32, x=0, y=0)
        
        Label(self, text="111AAA111", font=('arial', 12, 'bold'), relief=SOLID).place(w=150, h=32, x=40, y=0)

        self.eye_value = BooleanVar(value=False)
        self.eye_on_icon = PhotoImage(file='./assets/icon-eye-on.png')
        self.eye_off_icon = PhotoImage(file='./assets/icon-eye-off.png')
        Checkbutton(self, variable=self.eye_value,
            image=self.eye_off_icon, selectimage=self.eye_on_icon,
            onvalue=True, offvalue=False, indicatoron=False).place(w=32, h=32, x=200, y=0)

        self.bulb_value = BooleanVar(value=False)
        self.bulb_on_icon = PhotoImage(file='./assets/icon-bulb-on.png')
        self.bulb_off_icon = PhotoImage(file='./assets/icon-bulb-off.png')
        Checkbutton(self, variable=self.bulb_value,
            image=self.bulb_off_icon, selectimage=self.bulb_on_icon,
            onvalue=True, offvalue=False, indicatoron=False).place(w=32, h=32, x=240, y=0)

        self.edit_value = BooleanVar(value=False)
        self.edit_icon = PhotoImage(file='./assets/icon-pen.png')
        Checkbutton(self, variable=self.edit_value, image=self.edit_icon, command=self.edit_click,
            onvalue=True, offvalue=False, indicatoron=False).place(w=32, h=32, x=280, y=0)
        
        self.delete_icon = PhotoImage(file='./assets/icon-trash.png')
        Button(self, image=self.delete_icon, command=self.delete_click).place(w=32, h=32, x=320, y=0)

        self.up_icon = PhotoImage(file='./assets/icon-arrow-up.png')
        self.up_button = Button(self, image=self.up_icon, command=self.up_click)
        self.up_button.place(w=32, h=32, x=360, y=0)
        self.up_button['state'] = DISABLED

        self.down_icon = PhotoImage(file='./assets/icon-arrow-down.png')
        self.down_button = Button(self, image=self.down_icon, command=self.down_click)
        self.down_button.place(w=32, h=32, x=400, y=0)

        self.name_value = StringVar(value="111AAA111")
        Entry(self, textvariable=self.name_value, font=('arial', 12, 'normal'), justify=CENTER).place(w=150, h=32, x=40, y=40)

        self.square_value = BooleanVar(value=False)
        self.square_icon = PhotoImage(file='./assets/icon-square.png')
        Checkbutton(self, variable=self.square_value, image=self.square_icon,
            onvalue=True, offvalue=False, indicatoron=False).place(w=32, h=32, x=200, y=40)

        self.depth_value = BooleanVar(value=False)
        self.depth_icon = PhotoImage(file='./assets/icon-depth.png')
        Checkbutton(self, variable=self.depth_value, image=self.depth_icon,
            onvalue=True, offvalue=False, indicatoron=False).place(w=32, h=32, x=240, y=40)
        
        self.save_icon = PhotoImage(file='./assets/icon-save.png')
        Button(self, image=self.save_icon, command=self.save_click).place(w=32, h=32, x=280, y=40)
        
        self.cancel_icon = PhotoImage(file='./assets/icon-cancel.png')
        Button(self, image=self.cancel_icon, command=self.cancel_click).place(w=32, h=32, x=320, y=40)

        self.settings_label = Label(self)
        self.place_settings_label()
        
        self.add_icon = PhotoImage(file='./assets/icon-add.png')
        Button(self, text='Add new item', font=('arial', 12, 'normal'), image=self.add_icon,
            compound=LEFT, command=self.add_click).place(w=150, h=32, x=40, y=120)

        Button(self, text="Test", command=self.test_click).place(x=100, y=200)

        Button(self, text="Exit", command=self.exit_click).place(x=350, y=250)

        master.bind('<Motion>', self.mouse_motion)
        master.bind('<Button-1>', self.mouse_left_click)
        master.bind('<Button-3>', self.mouse_right_click)
    
    def edit_click(self):
        if self.edit_value.get():
            self.settings_label.place_forget()
            print('EDITING ITEM...')
        else:
            self.place_settings_label()
    
    def place_settings_label(self):
        self.settings_label.place(w=312, h=32, x=40, y=40)
    
    def delete_click(self):
        answer = messagebox.askyesno(title='Delete Confirmation', message='Do you want to delete this item?')
        if answer:
            print('DELETING ITEM...')
    
    def up_click(self):
        number = int(self.number_label['text'])
        number -= 1
        self.number_label['text'] = str(number)
        if number == 1:
            self.disable_widget(self.up_button)
        else:
            self.enable_widget(self.down_button)
    
    def down_click(self):
        number = int(self.number_label['text'])
        number += 1
        self.number_label['text'] = str(number)
        if number == 8:
            self.disable_widget(self.down_button)
        else:
            self.enable_widget(self.up_button)
    
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
    
    def test_click(self):
        print("EYE :", self.eye_value.get())
        print("BULB:", self.bulb_value.get())
        print("PEN :", self.edit_value.get())
        print("BOX :", self.square_value.get())
        print("DEP.:", self.depth_value.get())

    def exit_click(self):
        answer = messagebox.askyesno(title='Exit Confirmation', message='Do you want to exit the app?')
        if answer:
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

    def add_click(self):
        print('NEW ITEM CREATED')

root = Tk()
app = Window(root)
root.wm_title("Tkinter UI")
root.geometry("440x300")
root.mainloop()
