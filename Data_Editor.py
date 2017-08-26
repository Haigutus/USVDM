#-------------------------------------------------------------------------------
# Name:        UDEV (Universal Data Editor and Validator)
# Purpose:
#
# Author:      kristjan.vilgo
#
# Created:     20.07.2017
# Copyright:   (c) kristjan.vilgo 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

from ToolBox import *



def show_meta_table(event):


    ID = element_tree.focus()

    #print ID

    #print data_tree[int(ID)]["DATA"]["atribute"]

    for i in meta_tree.get_children():
        meta_tree.delete(i)

    for key in data_tree[int(ID)]["DATA"]["atribute"]:
        #print key

        meta_tree.insert("", "end" , str(key) , text = key , value = str(data_tree[int(ID)]["DATA"]["atribute"][key]))

def get_element(event):

    """  event -> element """

    element = event.widget

    return element

def get_parent_element(element):

    """ TK (child object -> parent object) """

##    parent_name = element.winfo_parent()
##    parent = element._nametowidget(parent_name)
    parent = element.master #Updated - neater solution

    return parent

def close_element(event): #Variable event is passed in with element.bind

    """ event -> None """

    event.widget.destroy()

def close_element_parent(event):

    """ event -> None """

    element = get_element(event)
    parent = get_parent_element(element)
    parent.destroy()







def edit_tree_field(event):



    element = event.widget

    # what row and column was clicked on
    rowid = element.identify_row(event.y)
    column = element.identify_column(event.x)

    # clicked row parent id

    parent = element.parent(rowid)

    #print rowid, column, parent

##
##    # do nothing if item is top-level
##    if parent == '':
##        return
##
    # get column position info
    x,y,width,height = element.bbox(rowid, column)

    edit_filed_frame= Frame(master = element)
    edit_filed_frame["width"] = width
    edit_filed_frame["height"] = height
    edit_filed_frame.place(x=x, y=y)

    edit_filed = Entry(master=edit_filed_frame)
    #print column
    #print rowid
    if column == "#0":
        edit_filed.insert(0,element.item(rowid)["text"]) # Ask current value and set edit filed value to that
    else:
        edit_filed.insert(0,element.item(rowid)["values"][int(column.split("#")[1])-1])


    edit_filed.focus_set()
    edit_filed.bind("<Escape>",close_element_parent)
    #edit_filed.bind("<Button-1>",chekc_if_event_inside_element) #to be implemented, closes Entry filed if clicked on another area
    edit_filed.bind("<Return>",edit_element)


    # Validation to be implemented, rules for validation are to be taken directly from XSD or RDF schemas
    ##    validate=
    ##Specifies when validation should be done. You can use “focus” to validate whenever the widget gets or loses the focus, “focusin” to validate only when it gets focus, “focusout” to validate when it loses focus, “key” on any modification, and ALL for all situations. Default is NONE (no validation). (validate/Validate)
    ##validatecommand=
    ##A function or method to call to check if the contents is valid. The function should return a true value if the new contents is valid, or false if it isn’t. Note that this option is only used if the validate option is not NONE. (validateCommand/ValidateCommand)

    edit_filed.pack()


def edit_element(event): #to be named to edit_field


        element=get_element(event)

        #print "X = {} !! Y = {}".format(element.master.winfo_x(), element.master.winfo_y())


        original_parent = element.master.master #Entry is inside frame wich is insde original element



        # what row and column was clicked on
        rowid = original_parent.focus()
        column = original_parent.identify_column(element.master.winfo_x() + element.master.winfo_width()/2)

        if original_parent.widgetName == "ttk::treeview" :

            DATA = {} #Data container

            #First column is sepcial, its value is in text field no column ID is automatically retunred by columns call

            key = original_parent.heading("#0")["text"]
            value = original_parent.item(rowid)["text"]

            DATA[key] = value

            #Other columns

            columns = original_parent["columns"] #Returns a tuple of column ID-s

            values = original_parent.item(rowid)["values"] #Retruns a list of values, in column order

            for n, column in enumerate(columns):
                key = original_parent.heading(column)["text"]
                value =       values[n]

                DATA[key] = value



            print original_parent.item(rowid)
            new_element[rowid]={"DATA":DATA,"PARENT":""}
            print new_element

        print rowid
        print column

        #Destoy edit window after <"Return"> is pressed and change is passed to main process

        element.master.destroy()

        #if column == "#0":

        #else:

        #original_parent = element.master.master
        #print original_parent.__dick__


def tree_view(root,decription_dic):

    element_tree   = ttk.Treeview(root)
    element_tree["columns"]=(1) #tuple
    element_tree["selectmode"]="extended"

    element_tree.column(1, width=100 )
    element_tree.heading(1, text="Text")
    element_tree.column("#0", width=100 )
    element_tree.heading("#0", text="Element") # Tree column



    for key, value in data_tree.iteritems():


        text = ""
        values = [""]

        if "element" in value["DATA"]:
            text = value["DATA"]["element"]

        if "text" in value["DATA"]:
            values = [value["DATA"]["text"]]


        element_tree.insert(value["PARENT"], "end" , str(key) , text = text  , value= values)

    ##,value["DATA"]["atribute"]
    element_tree.pack(fill=BOTH, expand=YES, side=LEFT)
    element_tree.bind("<<TreeviewSelect>>", show_meta_table)
    element_tree.bind("<Double-Button-1>", edit_tree_field)

    return element_tree


# Process start - Load file

#file_paths=["C:/USVDM/valid/20170621T2230Z_1D_LATVIANABRAKADABRA_SV_001-valid.xml"]
file_paths = select_files()

new_element = {}

XML_trees=loadXMLs(file_paths)

data_tree = xml_to_dic(XML_trees[0])

# GUI load up

#Root window creation

root_config_dic = {
"root":{"minsize":{"width":1000, "height":600},
        "title":'"DATA editor {}".format(data_tree[-1]["DATA"]["atribute"]["URL"])'}
}

##getattr(x, 'y') is equivalent to x.y
##setattr(x, 'y', v) is equivalent to x.y = v
##delattr(x, 'y') is equivalent to del x.y
root = Tk()
#setattr(root,"minsize",(width=1000, height=600))
root.minsize(width=1000, height=600)                                            # Inital size of the window
root.title("DATA editor {}".format(data_tree[-1]["DATA"]["atribute"]["URL"]))   # Window title

#Define Tabels

settings={} # Tree setting are going to be a dictionary that can be read in from XML and also exported as XML

meta_tree    = ttk.Treeview(root)




meta_tree["columns"]=("#1")
meta_tree.column("#0", width=100 )
meta_tree.heading("#0", text="Atribute")
meta_tree.column("#1", width=100 )
meta_tree.heading("#1", text="Value")
meta_tree.bind("<Double-Button-1>", edit_tree_field)

element_tree = tree_view(root, settings)





def print_cursorlocation(event):
    print "X = {} !! Y = {}".format(event.x, event.y)



meta_tree.pack(fill=BOTH, expand=YES, side=LEFT)



#root.bind("<Button-1>", print_cursorlocation)

root.mainloop()
