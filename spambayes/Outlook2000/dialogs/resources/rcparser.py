# Windows dialog .RC file parser, by Adam Walker.

# This module is part of the spambayes project, which is Copyright 2003
# The Python Software Foundation and is covered by the Python Software
# Foundation license.
__author__="Adam Walker"

import sys, os, shlex
import win32con
import commctrl

_controlMap = {"DEFPUSHBUTTON":0x80,
               "PUSHBUTTON":0x80,
               "Button":0x80,
               "GROUPBOX":0x80,
               "Static":0x82,
               "CTEXT":0x82,
               "RTEXT":0x82,
               "LTEXT":0x82,
               "LISTBOX":0x83,
               "SCROLLBAR":0x84,
               "COMBOBOX":0x85,
               "EDITTEXT":0x81,
               }

_addDefaults = {"EDITTEXT":win32con.WS_BORDER,
                "GROUPBOX":win32con.BS_GROUPBOX,
                "LTEXT":win32con.SS_LEFT,
                "DEFPUSHBUTTON":win32con.BS_DEFPUSHBUTTON,
                "CTEXT":win32con.SS_CENTER,
                "RTEXT":win32con.SS_RIGHT}

defaultControlStyle = win32con.WS_CHILD | win32con.WS_VISIBLE
class DialogDef:
    name = ""
    id = 0
    style = 0
    styleEx = None
    caption = ""
    font = "MS Sans Serif"
    fontSize = 8
    x = 0
    y = 0
    w = 0
    h = 0
    template = None
    def __init__(self, n, i):
        self.name = n
        self.id = i
        self.styles = []
        self.stylesEx = []
        self.controls = []
        #print "dialog def for ",self.name, self.id
    def createDialogTemplate(self):
        t = None
        self.template = [[self.caption, (self.x,self.y,self.w,self.h), self.style, self.styleEx, (self.fontSize, self.font)]]
        # Add the controls
        for control in self.controls:
            self.template.append(control.createDialogTemplate())
        return self.template

class ControlDef:
    id = ""
    controlType = ""
    subType = ""
    idNum = 0
    style = defaultControlStyle
    label = ""
    x = 0
    y = 0
    w = 0
    h = 0
    def __init__(self):
        self.styles = []
    def toString(self):
        s = "<Control id:"+self.id+" controlType:"+self.controlType+" subType:"+self.subType\
            +" idNum:"+str(self.idNum)+" style:"+str(self.style)+" styles:"+str(self.styles)+" label:"+self.label\
            +" x:"+str(self.x)+" y:"+str(self.y)+" w:"+str(self.w)+" h:"+str(self.h)+">"
        return s
    def createDialogTemplate(self):
        ct = self.controlType
        if "CONTROL"==ct:
            ct = self.subType
        if ct in _addDefaults:
            self.style |= _addDefaults[ct]
        if ct in _controlMap:
            ct = _controlMap[ct]
        t = [ct, self.label, self.idNum, (self.x, self.y, self.w, self.h), self.style]
        #print t
        return t
        

class RCParser:
    ids = {"IDOK":1, "IDCANCEL":2, "IDC_STATIC": -1}
    names = {1:"IDOK", 2:"IDCANCEL", -1:"IDC_STATIC"}
    next_id = 1001
    dialogs = {}
    _dialogs = {}
    debugEnabled = False;
    token = ""

    def debug(self, *args):
        if self.debugEnabled:
            print args

    def getToken(self):
        self.token = self.lex.get_token()
        self.debug("getToken returns:", self.token)
        if self.token=="":
            self.token = None
        return self.token
    
    def loadDialogs(self, rcFileName):
        """
        RCParser.loadDialogs(rcFileName) -> None
        Load the dialog information into the parser. Dialog Definations can then be accessed
        using the "dialogs" dictionary member (name->DialogDef). The "ids" member contains the dictionary of id->name.
        The "names" member contains the dictionary of name->id
        """
        f = open(rcFileName)
        self.open(f)
        self.getToken()
        while self.token!=None:
            self.parse()
            self.getToken()
        f.close()
    def open(self, file):
        self.lex = shlex.shlex(file)
        self.lex.commenters = "//#"

    def parse(self):
        deep = 0
        if self.token == None:
            more == None
        elif "BEGIN" == self.token:
            deep = 1
            while deep!=0:
                self.getToken()
                if "BEGIN" == self.token:
                    deep += 1
                elif "END" == self.token:
                    deep -= 1
        elif "IDD_" != self.token[:4]:
            self.getToken()
        else:
            possibleDlgName = self.token
            self.getToken()
            if "DIALOG" == self.token or "DIALOGEX" == self.token:
                self.dialog(possibleDlgName)

    def addId(self, id_name):
        if id_name in self.ids:
            id = self.ids[id_name]
        else:
            id = self.next_id
            self.next_id += 1
            self.ids[id_name] = id
            self.names[id] = id_name
        return id
                
    def lang(self):
        while self.token[0:4]=="LANG" or self.token[0:7]=="SUBLANG" or self.token==',':
            self.getToken();
            
    def dialog(self, name):
        dlg = DialogDef(name,self.addId(name))
        assert len(dlg.controls)==0
        self._dialogs[name] = dlg
        extras = []
        self.getToken()
        while not self.token.isdigit():
            self.debug("extra", self.token)
            extras.append(self.token)
            self.getToken()
        dlg.x = int(self.token)
        self.getToken() # should be ,
        self.getToken() # number
        dlg.y = int(self.token)
        self.getToken() # should be ,
        self.getToken() # number
        dlg.w = int(self.token)
        self.getToken() # should be ,
        self.getToken() # number
        dlg.h = int(self.token)
        self.getToken()
        while not (self.token==None or self.token=="" or self.token=="END"):
            if self.token=="STYLE":
                self.dialogStyle(dlg)
            elif self.token=="EXSTYLE":
                self.dialogExStyle(dlg)
            elif self.token=="CAPTION":
                self.dialogCaption(dlg)
            elif self.token=="FONT":
                self.dialogFont(dlg)
            elif self.token=="BEGIN":
                self.controls(dlg)
            else:
                break
        self.dialogs[name] = dlg.createDialogTemplate()
    
    def dialogStyle(self, dlg):
        dlg.style, dlg.styles = self.styles( [], win32con.WS_VISIBLE | win32con.DS_SETFONT)
    def dialogExStyle(self, dlg):
        self.getToken()
        dlg.styleEx, dlg.stylesEx = self.styles( [], 0)
    
    def styles(self, defaults, defaultStyle):
        list = defaults
        style = defaultStyle
        
        if "STYLE"==self.token:
            self.getToken()
        i = 0
        Not = False
        while ((i%2==1 and ("|"==self.token or "NOT"==self.token)) or (i%2==0)) and not self.token==None:
            Not = False;
            if "NOT"==self.token:
                Not = True
                self.getToken()
            i += 1
            if self.token!="|":
                if self.token in win32con.__dict__:
                    value = getattr(win32con,self.token)
                else:
                    value = getattr(commctrl,self.token)
                if Not:
                    list.append("NOT "+self.token)
                    self.debug("styles add Not",self.token, value)
                    style &= ~value
                else:
                    list.append(self.token)
                    self.debug("styles add", self.token, value)
                    style |= value
            self.getToken()
        self.debug("style is ",style)
            
        return style, list
    
    def dialogCaption(self, dlg):
        if "CAPTION"==self.token:
            self.getToken()
        self.token = self.token[1:-1]
        self.debug("Caption is:",self.token)
        dlg.caption = self.token
        self.getToken()
    def dialogFont(self, dlg):
        if "FONT"==self.token:
            self.getToken()
        dlg.fontSize = int(self.token)
        self.getToken() # ,
        self.getToken() # Font name
        dlg.font = self.token[1:-1] # it's quoted
        self.getToken()
        while "BEGIN"!=self.token:
            self.getToken()
    def controls(self, dlg):
        if self.token=="BEGIN": self.getToken()
        while self.token!="END":
            control = ControlDef()
            control.controlType = self.token;
            #print self.token
            self.getToken()
            if self.token[0:1]=='"':
                control.label = self.token[1:-1]
                self.getToken() # ,
                self.getToken()
            control.id = self.token
            control.idNum = self.addId(control.id)
            self.getToken() # ,
            if control.controlType == "CONTROL":
                self.getToken()
                control.subType = self.token[1:-1]
                # Styles
                self.getToken() #,
                self.getToken()
                control.style, control.styles = self.styles([], defaultControlStyle)
                #self.getToken() #,
            # Rect
            control.x = int(self.getToken())
            self.getToken() # ,
            control.y = int(self.getToken())
            self.getToken() # ,
            control.w = int(self.getToken())
            self.getToken() # ,
            self.getToken()
            control.h = int(self.token)
            self.getToken()
            if self.token==",":
                self.getToken()
                control.style, control.styles = self.styles([], defaultControlStyle)
            #print control.toString()
            dlg.controls.append(control)
def ParseDialogs(rc_file):
    rcp = RCParser()
    rcp.loadDialogs(rc_file)
    return rcp
