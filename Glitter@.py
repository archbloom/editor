
from Tkinter import *
import ttk
import tkFileDialog
import tkMessageBox
import threading
import md5

#worker thread sets up new instances of SimpleEditor
#in its own thread whenever there is a request for a
#new file or to open a file
class newFileThread(threading.Thread):
    def __init__(self, filename=""):
        threading.Thread.__init__(self)
        self.filename = filename

    def run(self):
        if self.filename == "":
            root = Tk()
            newEditor = SimpleEditor(root)
            root.mainloop()
        else:
            root = Tk()
            newEditor = SimpleEditor(root, self.filename)
            root.mainloop()

#Sets up window for find. findNext does all the actual work
class findGUI:
    def __init__(self, parent_win, editor):
        self.parent_win = parent_win
        self.editor = editor

        self.find_win = Toplevel(self.parent_win)
        self.index = "1.0"
        
        self.find_win.title("Find")
        self.frame = ttk.Frame(self.find_win, padding=(12,12,12,12))
        ttk.Style().configure("Tframe", background="beige")

        self.search_label = ttk.Label(self.frame, text="Find:")
        self.search_entry = ttk.Entry(self.frame)

        self.next_but = ttk.Button(self.frame, text="Next", command=lambda: self.findNext(self.search_entry.get()))
        self.cancel_but = ttk.Button(self.frame, text="Cancel", command=lambda: self.find_win.destroy())

        self.frame.grid(column=0, row=0, columnspan=3, rowspan=2)
        self.search_label.grid(column=1, row=0, sticky=(N,W,E,S))
        self.search_entry.grid(column=0, row=1, columnspan=3, pady=4, sticky=(N,W,E,S))
        self.next_but.grid(column=2, row=2, sticky=(N,W,E,S))
        self.cancel_but.grid(column=3,row=2, sticky=(N,W,E,S))

        self.find_win.columnconfigure("all", weight=1)
        self.find_win.rowconfigure("all", weight=1)
        self.frame.columnconfigure("all", weight=1)
        self.frame.rowconfigure("all", weight=1)

#Each click of next should call findNext which will highlight
    #and cycle through found instances of text
    def findNext(self, text):
        txt_index = self.editor.search(text, self.index, "end")
        if txt_index:
            txt_end = txt_index + "+%dc"%len(text)
            self.editor.tag_remove("sel", "1.0", "end")
            self.editor.tag_add("sel", txt_index, txt_end)
            self.editor.mark_set("insert", txt_end)
            self.editor.see("insert")
            self.index = txt_end
            if self.editor.compare(self.index, ">=", "end-1c"):
                self.index = "1.0"

class fontGUI:
    def __init__(self, parent_win, editor):
        self.parent_win = parent_win
        self.editor = editor

        self.font_win = Toplevel(self.parent_win)
        self.font_win.title("Font options")

        self.frame = ttk.Frame(self.font_win, padding=(12,12,12,12))
        ttk.Style().configure("Tframe", background="beige")

        self.fontsize_options = []
        for i in range(4, 74, 2):
            self.fontsize_options.append(str(i))
        
        self.fontstyle_options = ["Arial", "Comic Sans", "Courier New", "Helvetica", "Times New Roman"]

        self.fontsize_var = StringVar()
        self.fontstyle_var = StringVar()

        self.fontsize_optbox = apply(OptionMenu, (self.frame, self.fontsize_var) + tuple(self.fontsize_options))
        self.fontstyle_optbox = apply(OptionMenu, (self.frame, self.fontstyle_var) + tuple(self.fontstyle_options))

        self.fontsize_var.set("12")
        self.fontstyle_var.set("Arial")

        self.fontsize_label = ttk.Label(self.frame, text="Font Size")
        self.fontstyle_label = ttk.Label(self.frame, text="Font Style")

        self.accept_butt = ttk.Button(self.frame, text="Accept", command=self.accept)
        self.cancel_butt = ttk.Button(self.frame, text="Cancel", command=lambda: self.font_win.destroy())

        self.frame.grid(column=0, row=0, columnspan=3, rowspan=5)
        self.fontsize_label.grid(column=0, row=0, sticky=(N,W,E,S))
        self.fontsize_optbox.grid(column=0, row=1, sticky=(N,W,E,S))
        self.fontstyle_label.grid(column=0, row=2, columnspan=2, sticky=(N,W,E,S))
        self.fontstyle_optbox.grid(column=0, row=3, columnspan=2, sticky=(N,W,E,S))
        self.accept_butt.grid(column=1, row=4, padx=4, pady=6, sticky=(N,W,E,S))
        self.cancel_butt.grid(column=2, row=4, pady=6, sticky=(N,W,E,S))

        self.font_win.columnconfigure("all", weight=1)
        self.font_win.rowconfigure("all", weight=1)
        self.frame.columnconfigure("all", weight=1)
        self.frame.rowconfigure("all", weight=1)

    def accept(self):
        fontsize = self.fontsize_var.get()
        fontstyle = self.fontstyle_var.get()
        self.editor.config(font=(fontstyle, int(fontsize)))
        self.font_win.destroy()
        
        
        
class SimpleEditor:
    def __init__(self, parent, filename=None):
        #index is used by find
        self.index = "1.0"
        self.parent = parent

        self.parent.option_add("*tearOff", False)
        self.parent.protocol("WM_DELETE_WINDOW", self.exitProgram)

        #sets up all menu options for the GUI
        self.setUpMenu()

        self.frame = ttk.Frame(self.parent, name="f1", width=800, height=600)
        self.frame.grid_propagate(False)

        self.editor = Text(self.frame, width=110, undo=1, wrap="word", name="editor")
        self.s = ttk.Scrollbar(self.frame, orient="vertical", command=self.editor.yview)
        self.editor["yscrollcommand"] = self.s.set
        self.editor.bind("<space>", lambda event: self.editor.edit_separator())

        self.frame.grid(column=0, row=0, sticky=(N,W,E,S))
        self.editor.grid(column=0, row=0, sticky=(N,W,E,S))
        self.s.grid(column=1,row=0, sticky=(N,S))

        self.parent.columnconfigure("all", weight=1)
        self.parent.rowconfigure("all", weight=1)
        self.frame.columnconfigure("all", weight=1)
        self.frame.rowconfigure("all", weight=1)

        #set up all menu shortcut bindings
        self.setUpBindings()

        #empty passed in filename indicates new window. Otherwise we read from a file.
        if filename is None:
            self.parent.title("Glitter@")
        else:
            self.parent.title(filename)
            try:
                f = open(filename, 'r')
            except:
                tkMessageBox.showinfo(title="Unknown file type", message="Unknown file type: Couldn't open file")
                self.parent.quit()
                self.parent.destroy()
                return

            text = f.read()
            self.editor.insert("1.0", text)
            f.close()

        #initial signature of contents. We check again on saves/program exits
        #to determine if should/should not save
        self.signature = md5.md5(self.editor.get("1.0", "end")).digest()

    def setUpMenu(self):
        menubar = Menu(self.parent)
        menubar.configure(background="beige", activebackground="#B09B4A")
        menu_file = Menu(menubar)
        menu_file.configure(background="beige", activebackground="#B09B4A")
        menu_edit = Menu(menubar)
        menu_edit.configure(background="beige", activebackground="#B09B4A")
        menu_format = Menu(menubar)
        menu_format.configure(background="beige", activebackground="#B09B4A")
        self.parent["menu"] = menubar
        menubar.add_cascade(menu=menu_file, label="File")
        menubar.add_cascade(menu=menu_edit, label="Edit")
        menubar.add_cascade(menu=menu_format, label="Format")

        menu_file.add_command(label="New", accelerator="Ctrl+N", command=self.newFile)
        menu_file.add_command(label="Open", accelerator="Ctrl+O", command=self.openFile)
 #       menu_file.add_command(label="Save", accelerator="Ctrl+S", command=self.saveFile)
        menu_file.add_command(label="Save as", accelerator="Ctrl+Shift+S", command=self.saveAsFile)
        menu_file.add_separator()
        menu_file.add_command(label="Exit", accelerator="Ctrl+Q", command=self.exitProgram)

        menu_edit.add_command(label="Undo", accelerator="Ctrl+Z", command=self.undoEdit)
        menu_edit.add_command(label="Redo", accelerator="Ctrl+Shift+Z", command=self.redoEdit)
        menu_edit.add_separator()
        menu_edit.add_command(label="Cut", accelerator="Ctrl+X", command=lambda: self.editText("cut"))
        menu_edit.add_command(label="Copy", accelerator="Ctrl+C", command=lambda: self.editText("copy"))
        menu_edit.add_command(label="Paste", accelerator="Ctrl+P", command=lambda: self.editText("paste"))
        menu_edit.add_command(label="Select All", accelerator="Ctrl+A", command=lambda: self.editText("selall"))
        menu_edit.add_separator()
        menu_edit.add_command(label="Find", accelerator="Ctrl+F", command=self.findText)

        menu_format.add_command(label="Font", command=self.setFont)

    #lambda is used to catch the event that would be passed to these functions.
    #Since none of them make use of the event, it's either this or make all the
    #functions take in a dummy event parameter.
    def setUpBindings(self):
        self.parent.bind("<Control-n>", lambda event: self.newFile)
        self.parent.bind("<Control-o>", lambda event: self.openFile)
        self.parent.bind("<Control-s>", lambda event: self.saveFile)
        self.parent.bind("<Control-S>", lambda event: self.saveAsFile)
        self.parent.bind("<Control-q>", lambda event: self.exitProgram)
        self.parent.bind("<Control-z>", lambda event: self.undoEdit)
        self.parent.bind("<Control-Z>", lambda event: self.redoEdit)
        self.parent.bind("<Control-x>", lambda event: self.editText("cut"))
        self.parent.bind("<Control-c>", lambda event: self.editText("copy"))
        self.parent.bind("<Control-p>", lambda event: self.editText("paste"))
        self.parent.bind("<Control-a>", lambda event: self.editText("selall"))
        self.parent.bind("<Control-f>", lambda event: self.findText)

    #newFile and openFile both create a separate thread for a new SimpleEditor instance
    def newFile(self):
        t = newFileThread()
        t.start()

    def openFile(self):
        fn = tkFileDialog.askopenfilename(title="Choose a file")
        t = newFileThread(fn)
        t.start()

    #Saving brand new files is delegated to saveAsFile because the desired behavior is
    #the same. Otherwise we check if there are any actual changes before we do any file
    #I/O.
#     def saveFile(self):
#         if self.parent.title() == "Untitled":
#             self.saveAsFile()
#         else:
#             cur_sig = md5.md5(self.editor.get("1.0", "end")).digest()
#             if cur_sig != self.signature:
#                 try:
#                     f.open(self.parent.title(), 'w')
#                     text = self.editor.get(1.0, "end")
#                     f.write(text)
#                     f.close()
#                     self.signature = cur_sig
#                 except:
#                     tkMessageBox.showinfo(title="Save error", message="Save error: Could not save file")


    def saveAsFile(self):
        filename = tkFileDialog.asksaveasfilename(defaultextension=".txt")
        if filename:
            f = open(filename, 'w')
            text = self.editor.get(1.0, "end")
            f.write(text)
            f.close()
                

    #Unsure if both quit and destroy are necessary
    def exitProgram(self):
        cur_sig = md5.md5(self.editor.get("1.0", "end")).digest()
        if cur_sig != self.signature:
            do_save = tkMessageBox.askyesno(title="Unsaved changes", message="Save unsaved changes?")
            if do_save:
                self.saveFile()
        self.parent.quit()
        self.parent.destroy()

    #undo and redo as they are now are unsatisfactory. Need to find a way
    #to disable undo and redo as an option if they would return errors
    def undoEdit(self):
        try:
            self.editor.edit_undo()
        except:
            tkMessageBox.showinfo(title="Error", message="Nothing to undo")

    def redoEdit(self):
        try:
            self.editor.edit_redo()
        except:
            tkMessageBox.showinfo(title="Error", message="Nothing to redo")
        

    def editText(self, command):
        command = command.lower()

        if command == "cut":
            self.parent.clipboard_clear()
            text = self.editor.get("sel.first", "sel.last")
            text = text[:len(text)-1]
            self.parent.clipboard_append(text)
            self.editor.delete("sel.first", "sel.last")

        elif command == "copy":
            self.parent.clipboard_clear()
            text = self.editor.get("sel.first", "sel.last")
            text = text[:len(text)-1]
            self.parent.clipboard_append(text)

        elif command == "paste":
            text = self.parent.selection_get(selection="CLIPBOARD")
            self.editor.insert("insert", text)

        elif command == "selall":
            self.editor.tag_add("sel", 1.0, "end")

        else:
            print "Err: Improper edit command"

    #Sets up window for find.
    def findText(self):
        fG = findGUI(self.parent, self.editor)

    def setFont(self):
        fG = fontGUI(self.parent, self.editor)


if __name__=="__main__":
    root = Tk()
    newEditor = SimpleEditor(root)
    root.mainloop()
