"""
tkModule.py: A module containing useful complex tk widgets.
"""

__author__ = "Michael J. Harms"
__date__ = "070621"

from copy import copy
from Tkinter import *

VALID_ENTRY_COLOR = "white"
INVALID_ENTRY_COLOR = "pink"


# ----- Helper functions/classes ----- #

class curry:
    """
    Class that allows the GUI to call a function with arguments.
    """

    def __init__(self, function, *args, **kwargs):
        """
        Initialize instance, grabbing args and kwargs.
        """

        self.function = function
        self.pending = args[:]
        self.kwargs = kwargs.copy()

    def __call__(self, *args, **kwargs):
        """
        Call the function, passing it args and kwargs.
        """

        if kwargs and self.kwargs:
            kw = self.kwargs.copy()
            kw.update(kwargs)
        else:
            kw = kwargs or self.kwargs

        return self.function(*(self.pending + args), **kw)

# -----
#       Atomic objects (made up of quarks, etc.) but used to make up more
#       complicated objects
# -----

class SimpleTkObject:
    """
    The class from which all other basic objects are derived.
    """

    def __init__(self,parent,*args,**kwargs):
        """
        Initialize the object by creating surrounding frame, then calling the
        generic createObjec method.
        """

        self.parent = parent
        self.args = args[:]
        self.kwargs = kwargs.copy()

        if "tag" in self.kwargs.keys():
            self.tag = self.kwargs["tag"]

        self.frame = Frame(parent)

        self._createObject(*self.args,**self.kwargs)

    def _createObject(self,*args,**kwargs):
        """
        Default method to create the object.  Dummy in this initial class
        definition.
        """

        pass

    def _checkObject(self,event=None):
        """
        Default method to check the object for errors.  Makes sure that none of
        the objects in object_list return None.
        """

        self.valid = True

        value_list = [obj.get() for obj in self.object_list]

        if None in value_list:
            self.valid = False

        if len(value_list) == 0:
            self.valid = False


    def get(self):
        """
        Extract the value(s) from the object.
        """

        self._checkObject()

        if self.valid:
            if len(self.object_list) == 1:
                return self.object_list[0].get()
            else:
                return tuple([v.get() for v in self.object_list])
        else:
            return None


    def destroy(self):
        """
        Destroy method.
        """

        self.frame.destroy()


    def grid(self,**kwargs):
        """
        Grid method.
        """

        self.frame.grid(**kwargs)

    def config(self,**kwargs):
        """
        Config method.
        """

        for obj in self.object_list:
            obj.config(**kwargs)

    def isValid(self):
        """
        Make sure the entry is valid, return bool.
        """

        self._checkObject()
        
        return self.valid

    def addTag(self,tag):
        """
        Place something in the tag attribute.
        """

        self.tag = tag

    def getTag(self):
        """
        Retrieve tag attribute.  Raises AttributeError if tag has not been 
        added.
        """
       
        return self.tag


class Divider(SimpleTkObject):
    """
    Makes a nice divider.
    """

    def _createObject(self,arrangement="h"):
        """
        Create divider.
        """

        self.arrangement = arrangement

        if self.arrangement == "h":
            self.frame = Frame(self.parent,height=2,bd=10,relief=SUNKEN)
            self.frame.grid(pady=5,sticky=W+E)
        elif self.arrangement == "v":
            self.frame = Frame(self.parent,width=2,bd=10,relief=SUNKEN)
            self.frame.grid(padx=5,sticky=N+S)
        else:
            err = "arrangement must be \"h\" or \"v\", not %s" \
                    % self.arrangement
            raise AttributeError(err)


class StandardLabel(SimpleTkObject):
    """
    A standardized label for use in complicated widgets.
    """

    def _createObject(self,label_text,label_width=None):
        """
        """

        self.label_text = label_text.strip()
        self.label_width = label_width

        # Use simple rule to determine width of widget
        if self.label_width == None:
            self.label_width = max([len(l)
                                    for l in self.label_text.split("\n")])
            if self.label_width < 15:
                self.label_width = 15
            
        # Create label
        self.label = Label(self.frame,text=self.label_text)
        self.label.config(width=self.label_width,anchor=W,justify=LEFT)
        self.label.grid(sticky=W)

        self.object_list = [self.label]

class CheckButton(SimpleTkObject):
    """
    Class that holds a label and Checkbutton widget.
    """

    def _createObject(self,label_text=None,button_default=False,
                      label_width=None,tag=None):
        """
        """

        self.label_text = label_text
        self.button_default = button_default
        self.label_width = label_width

        if tag != None:
            self.tag = tag

        # Label for entry box
        if self.label_text != None:
            self.label = StandardLabel(self.frame,label_text=self.label_text,
                                       label_width=self.label_width)
            self.label.grid(row=0,column=0)

        # Create entry box
        self.var = IntVar()
        self.cbutton = Checkbutton(self.frame,var=self.var)

        if self.button_default == True:
            self.cbutton.select()

        # Grid the entry box
        self.cbutton.grid(row=0,column=1)

        self.object_list = [self.cbutton]

    def get(self):
        """
        Determine whether option is selected or not.
        """

        return bool(self.var.get())

    def isValid(self):
        """
        By definition, a checkbutton entry is always valid."
        """

        return True


class EntryBox(SimpleTkObject):
    """
    Class that holds entry widget.
    """
    
    def _createObject(self,entry_type,label_text=None,
                     entry_default=None,allow_blank=False,value_limits=None,
                     entry_width=10,label_width=None,tag=None):
        """
        """

        self.entry_type = entry_type
        self.label_text = label_text
        self.entry_default = entry_default
        self.allow_blank = allow_blank
        self.value_limits = value_limits
        self.entry_width = entry_width
        self.label_width = label_width

        if tag != None:
            self.tag = tag

        # Label for entry box
        if self.label_text != None:
            self.label = StandardLabel(self.frame,label_text=self.label_text,
                                       label_width=self.label_width)
            self.label.grid(row=0,column=0)

        # Create entry box
        self.entry = Entry(self.frame)
        self.entry.config(width=self.entry_width)
        self.entry.bind("<FocusOut>",self._checkObject)

        if self.entry_default != None:
            self.entry.insert(0,self.entry_default)

        # Decide what color to make the entry
        self._checkObject()

        # Grid the entry box
        self.entry.grid(row=0,column=1)

        self.object_list = [self.entry]

    def _checkObject(self,event=None):
        """
        Extract value from entry box.  If the value is of the wrong type, set
        self.valid to False and change the background of the entry box to the
        "fail" color.
        """

        self.valid = True

        value = self.entry.get()
        if str(value).strip() == "":
            if not self.allow_blank:
                self.valid = False
        else:
            try:
                value = self.entry_type(value)

                # Verify that this is an allowed value
                if self.value_limits != None:
                    if value < self.value_limits[0] or \
                       value > self.value_limits[1]: self.valid = False
            except ValueError:
                self.valid = False

        if not self.valid:
            self.entry.config(background=INVALID_ENTRY_COLOR)
        else:
            self.entry.config(background=VALID_ENTRY_COLOR)

    def get(self):
        """
        Redefined get function that makes sure the entry is valid before
        returning.
        """

        self._checkObject()

        if self.valid:
            try:
                value = self.entry_type(self.entry.get())
                return value
            except ValueError:
                return None
        else:
            return None



class OptionBox(SimpleTkObject):
    """
    Class that creates an option box.  If "Other" is selected in the optionbox,
    a text entry box appears.
    """

    def _createObject(self,option_list,label_text=None,allow_other=True,
                      tag=None):
        """
        """

        self.label_text = label_text
        self.option_list = option_list

        if tag != None:
            self.tag = tag

        # Label for option box
        if self.label_text != None:
            self.label = StandardLabel(self.frame,label_text=self.label_text)
            self.label.grid()

        # Add ability for user to enter value to option box
        if allow_other and "Other" not in option_list:
            self.option_list.append("Other")

        # Actually create the option box
        self.option_value = StringVar(self.frame)
        self.option_value.set(self.option_list[0])

        self.optionmenu = OptionMenu(self.frame,self.option_value,
                                     command=self._checkOptionBox,
                                     *self.option_list)

        self.optionmenu.grid(row=0,column=1)

        self.object_list = [self.optionmenu]


    def _checkOptionBox(self,event):
        """
        When self.optionmenu is manipulated, extract the value that it has into
        self.option_value.  If "Other" is the value, create an entry box to take
        a user specified value.
        """

        # Grab value, making sure that no option_entry exists if "Other" is
        # not specified.  If "Other" is specified, create an entry box.
        if self.option_value.get() == "Other":
            self.option_entry = EntryBox(self.frame,entry_type=str)
            self.option_entry.grid(row=0,column=2)
        else:
            try:
                self.option_entry.destroy()
            except AttributeError:
                pass


    def get(self):
        """
        Re-defined get method that checks the entry object first (if it exists)
        and then the optionmenu object.
        """

        try:
            value = self.option_entry.get()
        except AttributeError:
            value = self.option_value.get()
        except TclError:
            value = self.option_value.get()

        return value

    def _checkObject(self):
        """
        """

        try:
            self.valid = self.option_entry.isValid()
        except AttributeError:
            self.valid = True            



class TextWithScroll(SimpleTkObject):
    """
    """
    
    def _createObject(self,height=5,width=50,allow_blank=True,tag=None):
        """
        Create an text object that has an attached scrollbar.
        """

        self.height = height
        self.width = width
        self.allow_blank = allow_blank
        
        if tag != None:
            self.tag = tag

        self.text = Text(self.frame)
        self.scrollbar = Scrollbar(self.frame)

        self.text.config(yscrollcommand=self.scrollbar.set,
                         height=self.height,width=self.width,wrap=WORD)
        self.scrollbar.config(command=self.text.yview)

        self.text.grid(column=0,row=0)
        self.scrollbar.grid(column=1,row=0,sticky=NS)

        self.object_list = [self.text]

    def _checkObject(self,event=None):
        """
        Default method to check the object for errors.  Makes sure that none of
        the objects in object_list return None.
        """

        self.valid = True

        value = self.get()

        if value == None and not self.allow_blank:
            self.valid = False

    
    def get(self):
        """
        Redefine the get method.
        """

        t = self.text.get(1.0,END)
        t = t.strip()
        if t == "":
            t = None

        return t



class EntryOptBox(SimpleTkObject):
    """
    Create entry box followed by an option box.
    """

    def _createObject(self,entry_type,option_list,
                      label_text=None,entry_default=None,allow_blank=False,
                      tag=None):
        """
        Method to actually create object.
        """

        self.entry_type = entry_type
        self.option_list = option_list
        self.label_text = label_text
        self.entry_default = entry_default
        self.allow_blank = allow_blank

        if tag != None:
            self.tag = tag

        # Label?
        if self.label_text != None:
            self.label = StandardLabel(self.frame,label_text=self.label_text)
            self.label.grid(row=0,column=0)

        # Create entry_box
        self.entry_box = EntryBox(self.frame,
                                  entry_type=self.entry_type,
                                  entry_default=self.entry_default,
                                  allow_blank=self.allow_blank)

        # Create option_box
        self.option_box = OptionBox(parent=self.frame,
                                    option_list=self.option_list)

        # Grid objects
        self.entry_box.grid(row=0,column=1)
        self.option_box.grid(row=0,column=2)

        # Create object list, allowing us to use default .get and .config
        # methods.
        self.object_list = [self.entry_box,self.option_box]


class MultiObject(SimpleTkObject):
    """
    Container for multiple objects of the same type that allows them to be
    gridded and accessed as a unit.  Can be "dynamic", which allows the user to
    add and subtract fields.
    """

    def _createObject(self,contained_class,num_objects,
                      arrangement="h",label_text=None,dynamic=False,
                      *class_args,**class_kwargs):
        """
        Create num_objects objects of type contained_class in frame derived from
        parent, arranged horizontally orvertically, given label object_label.
        """

        # Grab arguments specific to the multi object class
        self.num_objects = num_objects
        self.arrangement = arrangement
        self.label_text = label_text
        self.dynamic = dynamic

        # Grab arguments to be passed to the contained class
        self.contained_class = contained_class
        self.class_args = class_args[:]
        self.class_kwargs = class_kwargs.copy()

        # Make sure number of objects makes sense
        if self.num_objects < 0:
            err = "Number of objects must not be negative!"
            raise AttributeError(err)

        # Make sure that the arrangement specified is sane
        if self.arrangement != "h" and self.arrangement != "v":
            err = "arrangement must be \"h\" or \"v\", not \"%s\"." \
                  % self.arrangement
            raise AttributeError(err)


        if self.label_text != None:
            self.label = StandardLabel(self.frame,label_text=self.label_text)
            self.label.grid(row=0,column=0)

        # Actually create object
        self.createAddRemButtons()
        self.object_list = []
        for i in range(self.num_objects):
            self.addObject()

        # If this is not a dynamic object, destroy the add & remove buttons
        if not self.dynamic:
            self.add_rem_frame.destroy()

    def addObject(self):
        """
        Add object to object list.
        """

        # Remove the add and remove buttons, create the new object, then rebuild
        # the buttons.
        self.add_rem_frame.destroy()

        self.object_list.append(self.contained_class(self.frame,
                                                     *self.class_args,
                                                     **self.class_kwargs))

        if self.arrangement == "h":
            self.object_list[-1].grid(row=0,column=len(self.object_list))
        elif self.arrangement == "v":
            self.object_list[-1].grid(row=len(self.object_list)-1,column=1)

        self.createAddRemButtons()

    def removeObject(self):
        """
        Remove object from object list.
        """

        if len(self.object_list) > 0:
            self.object_list[-1].destroy()
            self.object_list = self.object_list[:-1]

    def createAddRemButtons(self):
        """
        Create add and remove buttons.
        """

        # Create frame that holds button
        self.add_rem_frame = Frame(self.frame)
        self.add_rem_frame.grid(column=1)

        # Create add button
        self.add_button = Button(self.add_rem_frame,text="Add",
                                 command=self.addObject)
        self.add_button.grid(row=0,column=0)

        # Create remove button
        self.rem_button = Button(self.add_rem_frame,text="Remove",
                                 command=self.removeObject)
        self.rem_button.grid(row=0,column=1)

    def config(self,**kwargs):
        """
        Modified config method that passes to add and rem buttons.
        """

        for obj in self.object_list:
            obj.config(**kwargs)

        if self.dynamic:
            self.add_button.config(**kwargs)
            self.rem_button.config(**kwargs)
    
    def _checkObject(self,event=None):
        """
        Default method to check the object for errors.  Makes sure that none of
        the objects in object_list return None.
        """

        self.valid = True

        value_list = [obj.get() for obj in self.object_list]

        if None in value_list:
            self.valid = False


class MultiPane(SimpleTkObject):
    """
    Class that creates identical objects in an arbitrary number of panes, with
    each pane enabled/disabled by a checkbox.
    """

    def _createObject(self,pane_list,object_list,arrangement="h"):
        """
        """

        self.pane_list = pane_list
        self.object_list = object_list
        self.arrangement = arrangement

        # Create frame for each pane, placing divider between each one
        self.pane_frames = {}
        self.d = []
        for i, p in enumerate(self.pane_list):
            self.pane_frames.update([(p,Frame(self.frame))])

            # Decide whether to place horizontally or vertically
            if self.arrangement == "h":
                self.pane_frames[p].grid(row=0,column=2*i)
                self.d.append(Divider(self.frame,"v"))
                self.d[-1].grid(row=0,column=2*i+1)
            elif self.arrangement == "v":
                self.pane_frames[p].grid(row=2*i,column=0)
                self.d.append(Divider(self.frame,"h"))
                self.d[-1].grid(row=0,column=2*i+1)
            else:
                err = "arrangement must be \"h\" or \"v\", not %s" \
                        % self.arrangement

        # Remove extra divider
        self.d[-1].destroy()

        # Create checkbuttons, keying state to checkbuttons_var.
        self.checkbuttons = {}
        self.checkbutton_var = {}
        for p in self.pane_list:

            self.checkbutton_var.update([(p,IntVar())])

            f = self.pane_frames[p]
            self.checkbuttons.update(
                [(p,Checkbutton(f,text=p,
                                command=curry(self.updateCheck,p),
                                var=self.checkbutton_var[p]))])

            # Default the checkbuttons to "on" and grid them.
            self.checkbuttons[p].select()
            self.checkbuttons[p].grid(sticky=W)

        # Create set of unique objects in each pane and place in pane_objects
        # dictionary.
        self.pane_objects = {}
        for p in self.pane_list:

            local_object_list = []
            for obj in copy(self.object_list):
                local_object_list.append(obj[0](self.pane_frames[p],**obj[1]))
                local_object_list[-1].grid()

                # Remove objects from list that do not have get method (i.e.
                # dividers, labels, etc.)
                try:
                    local_object_list[-1].get()
                except AttributeError:
                    local_object_list = local_object_list[:-1]



            self.pane_objects.update([(p,local_object_list)])




    def updateCheck(self,pane):
        """
        Update enabled/disabled status of pane.  (Note: this function is called
        via the "curry" class so the GUI can pass the "pane" argument).
        """

        # Disabled or disable each pane based if the status of the checkbutton
        # changes.
        if self.checkbutton_var[pane].get() == 0:
            for obj in self.pane_objects[pane]:
                obj.config(state=DISABLED)
        else:
            for obj in self.pane_objects[pane]:
                obj.config(state=NORMAL)


    def get(self):
        """
        Get value of each object and return in dictionary keyed to pane name.
        """

        # Only return value for each object if that pane is enabled.
        self.obj_values = {}
        for p in self.pane_list:
            if self.checkbutton_var[p].get() == 1:
                self.obj_values.update([(p,[])])
                for o in self.pane_objects[p]:
                    self.obj_values[p].append(o.get())

        return self.obj_values

    def _checkObject(self):
        """
        Check the validity of every entry.  One invalid entry --> valid = False.
        """

        self.valid = True

        self.obj_values = {}
        for p in self.pane_list:
            if self.checkbutton_var[p].get() == 1:
                for o in self.pane_objects[p]:
                    if not o.isValid():
                        self.valid = False
                        break

    def getTags(self):
        """
        Get tags for each object in panels.
        """

        tag_dict = dict([(p,[]) for p in self.pane_list])
        for p in self.pane_list:
            if self.checkbutton_var[p].get() == 1:
                for o in self.pane_objects[p]:
                    try:
                        tag = o.getTag()
                        tag_dict[p].append(tag)
                    except AttributeError:
                        pass

        return tag_dict

class TestWindow:
    """
    Test window that exhibits each class in this module.
    """

    def __init__(self,parent):
        """
        Initialize test window.
        """

        # Initialize window
        self.parent = parent
        self.frame = Frame(self.parent)
        self.frame.grid(sticky=W)

        # StandardLabel Object:
        self.sl_label = StandardLabel(self.frame,label_text="A StandardLabel")
        self.sl_label.grid(sticky=W)
        Divider(self.frame,arrangement="h")

        # Divider Object:
        self.d_label = StandardLabel(self.frame,"A Divider:")
        self.d_label.grid(sticky=W)
        Divider(self.frame,arrangement="h")

        # CheckButton Object:
        self.cb_label = StandardLabel(self.frame,"A CheckButton:")
        self.cb_label.grid(sticky=W)
        self.cb = CheckButton(self.frame,label_text="An option",
                              button_default=False,label_width=None)
        self.cb.grid(sticky=W)
        Divider(self.frame,arrangement="h")

        # EntryBox Object:
        self.eb_label = StandardLabel(self.frame,"An EntryBox:")
        self.eb_label.grid(sticky=W)
        self.eb = EntryBox(self.frame,entry_type=float,label_text="A float",
                           allow_blank=True,entry_default=1.0)
        self.eb.grid(sticky=W)

        Divider(self.frame,arrangement="h")

        # OptionBox Object:
        self.ob_label = StandardLabel(self.frame,"An OptionBox:")
        self.ob_label.grid(sticky=W)
        self.ob = OptionBox(self.frame,["x","y","z"])
        self.ob.grid(sticky=W)

        Divider(self.frame,arrangement="h")

        # TextWithScroll object
        self.tws_label = StandardLabel(self.frame,"A TextWithScroll:")
        self.tws_label.grid(sticky=W)
        self.tws = TextWithScroll(self.frame)
        self.tws.grid()

        Divider(self.frame,arrangement="h")

        # EntryBoxWithOpt Object:
        self.eob_label = StandardLabel(self.frame,"An EntryBoxWithOpt:")
        self.eob_label.grid(sticky=W)
        self.eob = EntryOptBox(parent=self.frame,
                               entry_type=int,
                               option_list=["a","b","c"],
                               label_text="Enter integer")
        self.eob.grid(sticky=W)

        Divider(self.frame,arrangement="h")

        # MultiObject Object:
        self.mo_label = StandardLabel(self.frame,"A MultiObject:")
        self.mo_label.grid(sticky=W)
        self.mo = MultiObject(self.frame,contained_class=EntryOptBox,
                              num_objects=3,arrangement="v",dynamic=True,
                              entry_type=float,option_list=["x","y","z"],
                              label_text="Salt (mM)")
        self.mo.grid(sticky=W)

        Divider(self.frame,arrangement="h")

        # MultiPanel Object:
        self.mp_label = StandardLabel(self.frame,"A MultiPanel:")
        self.mp_label.grid(sticky=W)
        pane_list = ["Sample","Reference"]
        object_list = [(EntryBox,{"entry_type":float,
                                  "label_text":"Buffer blank",
                                  "entry_default":1.3335}),
                       (EntryBox,{"entry_type":float,
                                  "label_text":"Titrant blank"}),
                       (OptionBox,{"label_text":"A decision",
                                   "option_list":[1,2,3]})]

        self.mp = MultiPane(self.frame,pane_list,object_list)
        self.mp.grid(sticky=W)

        ok_button = Button(self.frame,text="OK",command=self.runOK)
        ok_button.grid()


    def runOK(self):

        for v in self.__dict__.keys():
            try:
                value = self.__dict__[v].get()
                valid = self.__dict__[v].isValid()
                print v, "Value:", value, "Valid:", valid

            except AttributeError:
                print "Fail?", v
                pass

if __name__ == "__main__":

    # Run the test window if this is called from the command line.
    root = Tk()
    app = TestWindow(root)
    root.mainloop()


