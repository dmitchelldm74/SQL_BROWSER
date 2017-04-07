#!/usr/bin/python3
import tkinter.ttk as ttk
from tkinter.scrolledtext import ScrolledText
import tkinter, sqlite3, random, uuid, os, re, style
import xml.etree.ElementTree as ET
from tkinter import filedialog, messagebox

__appname__ = "SQL Browser"
__apptitle__ = __appname__

root = tkinter.Tk()
root.title(__apptitle__)
root.geometry("800x440")

def edit_name(addition,add=False):
    global __appname__, __apptitle__
    if add:
        __apptitle__ = __apptitle__+addition
        return __apptitle__    
    return __appname__+addition

def MsgBox(body,title="",mboxtype="showinfo"): # showinfo, showwarning, showerror
    getattr(messagebox,mboxtype)(title,body)
    
class TextEditR(tkinter.Canvas):
    def __init__(self, sketch_file, *args, **kwargs):
        tkinter.Canvas.__init__(self, *args, **kwargs)
        self.textwidget = None
        self._style = {"bg":"#ffffff","fg":"#000000","font":None,"font-size":10,"font-weight":"","keyword-fg":"#800020","int-fg":"#008080","string-fg":"#008080","comment-fg":"#d3d3d3","types-fg":"#007f00"}
        self._regex = {}
        tree = ET.parse(sketch_file)
        root = tree.getroot()
        for child in root:
            if child.tag == "map":
                self._regex[child.attrib["name"]] = child.text
            elif child.tag == "for":
                name = child.attrib["id"]
                if name in self._regex:
                    entries = []
                    for entry in child:
                        if entry.tag == "entry":
                            entries.append(entry.text)
                    if "join" in child.attrib:
                        entries = (child.attrib["join"].join(entries))
                    self._regex[name] = self._regex[name] % entries
            elif child.tag == "style":
                fname = child.attrib.get("src")
                if fname != None:
                    if os.path.exists(fname) and os.path.isfile(fname):
                        child.text = str(open(fname,'r').read())
                if child.text != None:
                    style.execute(child.text, self._style)
        for r in self._regex:
            self._style[r] = (self._style.get(r+"-font",self._style.get("font")),self._style.get(r+"-font-size",self._style.get("font-size")),self._style.get(r+"-font-weight",self._style.get("font-weight")))

    def attach(self, text_widget):
        self.textwidget = text_widget
        self.textwidget.config(fg=self._style.get("fg"),bg=self._style.get("bg"),font=(self._style.get("font"),self._style.get("font-size"),self._style.get("font-weight")))
        self.redraw()

    def redraw(self, *args):
        self.delete("all")        
        for tag in self._regex:
            self.textwidget.tag_remove(tag,"1.0",tkinter.END)
            self._find(self._regex[tag],tag)
            self.textwidget.tag_config(tag, foreground=self._style.get(tag+"-fg"), background=self._style.get(tag+"-bg"), font=self._style.get(tag))
        i = self.textwidget.index("@0,0")
        while True:
            dline = self.textwidget.dlineinfo(i)
            if dline is None: break
            y = dline[1]
            linenum = str(i).split(".")[0]
            self.create_text(2,y,anchor="nw", text=linenum)
            i = self.textwidget.index("%s+1line" % i)
        self.after(30,self.redraw)

    def _find(self,regexp,tag="default"):
        first = "1.0"
        count = tkinter.IntVar()
        while(True):
            first = self.textwidget.search(regexp, first, count=count, nocase=True, stopindex=tkinter.END, regexp=True)
            if not first:
                break
            last = first+"+"+str(count.get())+"c"
            self.textwidget.tag_add(tag, first, last)
            first = last
    
class Commands:
    def __init__(self,external):
        self.external = external
        self.filename, self.sql_filename = (), ()
        self.sql_conn = sqlite3.connect('database.db')
        self.sql_curs = self.sql_conn.cursor()
        self.column_get = lambda: None
        
    def __getitem__(self,key):
        if hasattr(self.external,key):
            return getattr(self.external,key)
    
    def set_scroll(self,event):
        self["canvas"].configure(scrollregion=self.external.canvas.bbox('all'))
        
    def OPEN_FILE(self,OPEN=0):
        if self["Tabs"].selected() == 0 or OPEN == 1:
            self.filename = filedialog.askopenfilename(initialdir=".",title="Select a Database",filetypes=(("sql database files","*.db"),("all files","*.*")))
            if self.filename in [(),""]:
                return
            self.sql_conn.close()
            self.sql_conn = sqlite3.connect(self.filename)
            self.sql_curs = self.sql_conn.cursor()
            self.get_tables()
            try:
                self["lbl"].config(text="Select a table to view columns.")
            except:
                MsgBox("Select a table to view columns.")
            self["root"].title("SQL Browser - "+self.filename)
        else:
            self.sql_filename = filedialog.askopenfilename(initialdir=".",title="Select a SQL file.",filetypes=(("sql files","*.sql"),))
            if self.sql_filename in [(),""]:
                return
            try:
                f = open(self.sql_filename,"r")
                self["exetext"].delete("1.0",tkinter.END)
                self["exetext"].insert("1.0",f.read())
                f.close()
            except:
                MsgBox("Error reading %s!"%(self.sql_filename),mboxtype="showwarning")
            self["root"].title("SQL Browser - "+self.sql_filename)
            
    def SAVE_FILE(self):
        if self["Tabs"].selected() == 0:
            self.sql_conn.commit()
            MsgBox("Database Saved!")
            self.get_tables()
            self.get_columns(self["variable"].get())
        else:
            if self.sql_filename == ():
                f = filedialog.asksaveasfile(mode='w', title="Save as...", defaultextension=".sql", filetypes=(("sql files","*.sql"),))
                if f is None:
                    return
            else:
                f = open(self.sql_filename,'w')
            self.sql_filename = f.name
            title = self["root"].title()
            if title[-1] == "*":
                self["root"].title(title[0:-1])
            text = str(self["exetext"].get(1.0, tkinter.END))
            f.write(text)
            f.close()
            self.change_title(None,sfilename=True)
            
    def get_tables(self):
        if self.filename != ():
            self.sql_curs.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = self.sql_curs.fetchall()
            self['table']['menu'].delete(0, 'end')
            for t in tables:
                t = t[0]
                self['table']['menu'].add_command(label=t, command=lambda t=t: self.get_columns(t))
            self['root'].after(1000,self.get_tables)
            
    def get_columns(self,table=None):
        if table not in ["Table...",""]:
            for widget in self["column_frame"].winfo_children():
                widget.destroy()
            self.sql_curs.execute('select * from %s'%(table))
            column = 0
            listboxes = []
            for colname in [member[0] for member in self.sql_curs.description]:
                colidframe = tkinter.Frame(self["column_frame"],width=50,relief=tkinter.SUNKEN)
                lbl = tkinter.Label(colidframe,text=colname,relief=tkinter.SUNKEN)
                lbl.grid(row=1,column=1)
                colidframe.grid(row=1,column=column)
                frame = tkinter.Frame(self["column_frame"],width=50,height=100)
                frame.grid(row=2,column=column)
                first = True
                row = 0
                for entry in self.sql_curs.execute('select %s from %s'%(colname,table)):
                    entry = str(entry[0])
                    if first:
                        first = False
                        w = len(entry)
                        w = w + int(w/5)
                        if len(colname) > w:
                            w = len(colname)+5
                        frame.config(width=w)
                        lbl.config(width=w)
                    e = tkinter.Entry(frame,width=w)
                    e.insert(0,entry)
                    e.bind('<Return>',lambda evt,e=e,table=table,row=row+1,column=colname: self.update_column(table,column,row,e.get()))
                    e.grid(column=1,row=row)
                    row += 1
                column += 1
        self.column_get = lambda table=table: self.get_columns(table)
                
    def update_column(self,table,column,row,data):
        try:
            self.sql_curs.execute("UPDATE %s SET %s=? WHERE rowid=%d;"%(table,column,row),(data,))
        except Exception as e:
            MsgBox("Error Updating...%s"%e)
            
    def change_title(self,evt,sfilename=False):
        global __appname__
        if sfilename:
            fname = self.sql_filename
        else:
            fname = self.filename    
        if fname != ():
            self["root"].title(edit_name(' - '+fname))
        else:
            self["root"].title(__appname__)
            
    def exetext_edited(self,evt):
        char = evt.char
        if char != "" and self["root"].title() != __appname__:
            title = self["root"].title()
            if title[-1] != "*":
                self["root"].title(title+"*")
        
    def run_sql(self,evt=False):
        if self.filename == ():
            self.OPEN_FILE(1)
        try:
            self.sql_curs.executescript(self["exetext"].get(1.0, tkinter.END))
            if self["checkbox_checked"].get() == 1:
                self["exetext"].delete(1.0, 'end')
        except Exception as e:
            MsgBox(e)
        self.get_tables()
        self.column_get()
    
class TabsSelector:
    def __init__(self,nb):
        self.nb = nb
    def selected(self):
        return self.nb.index(self.nb.select())

class Window:
    def __init__(self,root):
        self.root = root
        self._commands = Commands(self)
        self._create_elements()
        self._bind_elements()
        self._set_variables()
        self._attach_add_elements()
        self._configure()
        self._print_elements()
        self.Tabs = TabsSelector(self.nb)
        
    def _bind_elements(self):
        self.root.bind("<Control-o>", lambda event: self.openbtn.invoke())
        self.root.bind("<Control-s>", lambda event: self.savebtn.invoke())
        self.root.bind("<Control-r>", self._commands.run_sql)
        
        self.page1.bind('<Visibility>',self._commands.change_title)
        self.page2.bind('<Visibility>',lambda evt: self._commands.change_title(evt, sfilename=True))
        
        self.exetext.bind('<Key>', self._commands.exetext_edited)
        
        self.column_frame.bind('<Configure>', self._commands.set_scroll)
        
        self.root.bind("<Left>",  lambda event: self.canvas.xview_scroll(-1, "units"))
        self.root.bind("<Right>", lambda event: self.canvas.xview_scroll( 1, "units"))
        self.root.bind("<Up>",    lambda event: self.canvas.yview_scroll(-1, "units"))
        self.root.bind("<Down>",  lambda event: self.canvas.yview_scroll( 1, "units"))

        self.root.after(1000,self._commands.get_tables)
        
    def _attach_add_elements(self):
        self.texteditor.attach(self.exetext)
        
        self.nb.add(self.page1, text='View')
        self.nb.add(self.page2, text='Execute')
        
    def _configure(self):
        self.yscrollbar.configure(command=self.canvas.yview)
        self.xscrollbar.configure(command=self.canvas.xview)

        self.canvas.configure(xscrollcommand=self.xscrollbar.set,yscrollcommand=self.yscrollbar.set)
        
    def _set_variables(self):
        self.variable.set("Table...")
        
    def _print_elements(self):
        self.menubar.pack(side=tkinter.TOP,fill="x")
        
        self.openbtn.grid(row=1,column=1)
        self.savebtn.grid(row=1,column=2)
        
        self.table.grid(row=2,column=1,columnspan=2)
        
        self.yscrollbar.pack(side=tkinter.RIGHT, fill='y')
        self.xscrollbar.pack(side=tkinter.BOTTOM, fill='x')
        
        self.nb.pack(fill=tkinter.BOTH)
        
        self.execontrols.pack(fill="x")
        self.exerun.grid(row=1,column=1)
        self.cbox.grid(row=1,column=2)
        
        self.exetext.pack()
        self.texteditor.pack(expand=1, fill="both")
        
        self.canvas.pack(fill=tkinter.BOTH)
        
        self.lbl.grid(row=1,column=1)
        self.canvas.create_window((0,0), window=self.column_frame, anchor=tkinter.NW)
        
    def _create_elements(self):
        self.variable = tkinter.StringVar(self.root)

        self.menubar = tkinter.Frame(self.root)
        
        self.openbtn = tkinter.Button(self.menubar,text="Open",command=self._commands.OPEN_FILE)
        self.savebtn = tkinter.Button(self.menubar,text="Save",command=self._commands.SAVE_FILE)
        
        self.table = tkinter.OptionMenu(self.menubar, self.variable, "")
        
        self.yscrollbar = tkinter.Scrollbar(self.root)
        self.xscrollbar = tkinter.Scrollbar(self.root, orient=tkinter.HORIZONTAL)

        self.nb = ttk.Notebook(self.root) # nb for notebook
        
        self.page1 = ttk.Frame(self.nb)
        self.page2 = ttk.Frame(self.nb)
        
        self.execontrols = ttk.Frame(self.page2)
        self.exerun = tkinter.Button(self.execontrols,text="Run",command=self._commands.run_sql)
        
        self.checkbox_checked = tkinter.IntVar()
        self.cbox = tkinter.Checkbutton(self.execontrols, text="Clear Text Editor on Execution", variable=self.checkbox_checked) #cbox for checkbox

        self.texteditor = TextEditR('sql.sketch',self.page2)
        self.exetext = ScrolledText(self.texteditor,width=100)
        
        self.canvas = tkinter.Canvas(self.page1,height=340)
        self.column_frame = tkinter.Frame(self.canvas)

        self.lbl = tkinter.Label(self.column_frame,text="Open a database to view columns.")
        
    def mainloop(self):
        self.root.mainloop()
  
window = Window(root)
window.mainloop()
