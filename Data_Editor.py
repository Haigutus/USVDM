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
                try:
                    value =       values[n]
                except IndexError:
                    value = ""   

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

def show_meta_table(event):
    """Updates atributes filed in side table"""

    ID = element_tree.focus()

    for i in meta_tree.get_children(): #Deletes pervious values
        meta_tree.delete(i)

    for key in data_tree[int(ID)]["DATA"]["atribute"]:
        #
        meta_tree.insert("", "end" , str(key) , text = key , value = str(data_tree[int(ID)]["DATA"]["atribute"][key]))        



def generate_treeview_columns_from_keys(tree_view_element,data_dic_example_row,default_column_width):

    """Treeview element, sample data for a row -> dcitionary of added column names(key): id-s(value)"""

    tree_view_element["columns"]=("#1",) # All columns expect first one have to be define, first column ID is #0 so we are just continuing same numbering, but we need to add first tuple to then extend on it

    column_dic=OrderedDict({})

    for column_n,key in enumerate(data_dic_example_row.keys()):

        column_id = "#{}".format(column_n)
        
        column_dic[key] = column_id

        if column_n > 1:

            tree_view_element["columns"]+=(column_id,)

    
    for key, column_id in column_dic.iteritems(): 
    
        tree_view_element.column(column_id, width = default_column_width )
        tree_view_element.heading(column_id, text = key)

    return column_dic


def tree_view(root,data_tree):

    element_tree   = ttk.Treeview(root)
    element_tree["selectmode"]="extended"
    default_column_width=100  

    
    #Generate all columns

    column_dic = generate_treeview_columns_from_keys(element_tree,data_tree[1]["DATA"],default_column_width)              

    #Fill all generated columns with data

    for key, value in data_tree.iteritems(): 


        text = ""
        values = [] # in case no value is present

        for item in value["DATA"]:

            if column_dic[item] == "#0":
                text = value["DATA"][item]

            else:
                values.append(value["DATA"][item])
        if not values: values = [""]

        element_tree.insert(value["PARENT"], "end" , str(key) , text = text  , value= values)

    ##,value["DATA"]["atribute"]
    element_tree.pack(fill=BOTH, expand=YES, side=LEFT)
    element_tree.bind("<<TreeviewSelect>>", show_meta_table)
    element_tree.bind("<Double-Button-1>", edit_tree_field)

    return element_tree

def configure_element(element_name,config_dic):
    for key, value in config_dic[element_name].iteritems():

        print key, value        

        eval("{}.{}({})".format(element_name,key,config_dic[element_name][key]))

def create_gui_from_dic(config_dic):

    iterator_list = range(0,len(config_dic),1) #Get all data out from dic in ordered manner


    for key in iterator_list:
        create_element_command = config_dic[str(key)]["DATA"]["text"]
        if create_element_command != "":
            exec(create_element_command)

    for key in iterator_list:
        root_id = config_dic[str(key)]["PARENT"]
        if root_id != "":
            root_element = config_dic[root_id]["DATA"]["element"]   
            child_element = config_dic[str(key)]["DATA"]["element"]
            setting = config_dic[str(key)]["DATA"]["atribute"]

            eval("{}.{}({})".format(root_element, child_element, setting))
# Process start - Load file

#file_paths=["C:/USVDM/valid/20170621T2230Z_1D_LATVIANABRAKADABRA_SV_001-valid.xml"]


# GUI load up

#Root window creation

#"DATA editor {}".format(data_tree[-1]["DATA"]["atribute"]["URL"])

config_dic = {
"0":{"DATA":{"element":"root",
                "text": "root = Tk()",
            "atribute":"",
           "namespace":""},                        
     "PARENT":""},

"1":{"DATA":{"element":"minsize",
                "text": "",
            "atribute":"width=1000, height=600",
           "namespace":""},                        
     "PARENT":"0"},

"2":{"DATA":{"element":"title",
                "text": "",
            "atribute":"'Editor'",
           "namespace":""},                        
     "PARENT":"0"}, 

"3":{"DATA":{"element":"config",
                "text": "",
            "atribute":"menu=main_menu",
           "namespace":""},                        
     "PARENT":"0"},             

"4":{"DATA":{"element":"main_menu",
                "text": "main_menu = Menu(root)",
            "atribute":"",
           "namespace":""},                        
     "PARENT":""},

"5":{"DATA":{"element":"add_cascade",
                "text": "",
            "atribute":"label='File', menu=file_menu",
           "namespace":""},                        
     "PARENT":"4"}, 

"6":{"DATA":{"element":"add_cascade",
                "text": "",
            "atribute":"label='Edit', menu=edit_menu",
           "namespace":""},                        
     "PARENT":"4"},           

"7":{"DATA":{"element":"file_menu",
                "text":"file_menu = Menu(main_menu,tearoff=False)",
            "atribute":"",
           "namespace":""}, 
     "PARENT":""},

"8":{"DATA":{"element":"add_command",
                "text": "",
            "atribute":"label='Open', command=select_file",
           "namespace":""},                        
     "PARENT":"7"},

"9":{"DATA":{"element":"add_command",
                "text": "",
            "atribute":"label='Quit', command=root.quit",
           "namespace":""},                        
     "PARENT":"7"}, 

"10":{"DATA":{"element":"edit_menu",
                "text":"edit_menu = Menu(main_menu,tearoff=False)",
            "atribute":"",
           "namespace":""}, 
     "PARENT":""},

"11":{"DATA":{"element":"add_command",
                "text": "",
            "atribute":"label='Open', command=select_file",
           "namespace":""},                        
     "PARENT":"10"},

"12":{"DATA":{"element":"add_command",
                "text": "",
            "atribute":"label='Quit', command=root.quit",
           "namespace":""},                        
     "PARENT":"10"},           
     
}


#Set up root window


iterator_list = range(0,len(config_dic),1) # to get all data out from dic in ordered manner


for key in iterator_list:
    create_element_command = config_dic[str(key)]["DATA"]["text"]
    if create_element_command != "":
        exec(create_element_command)

for key in iterator_list:
    root_id = config_dic[str(key)]["PARENT"]
    if root_id != "":
        root_element = config_dic[root_id]["DATA"]["element"]   
        child_element = config_dic[str(key)]["DATA"]["element"]
        setting = config_dic[str(key)]["DATA"]["atribute"]

        eval("{}.{}({})".format(root_element, child_element, setting))

  
file_paths = select_files()

new_element = {}

XML_trees=loadXMLs(file_paths)

data_tree = xml_to_dic(XML_trees[0]) #currenlty only first file

#Define Tabels


meta_tree    = ttk.Treeview(root)
meta_tree["columns"]=("#1")
meta_tree.column("#0", width=100 )
meta_tree.heading("#0", text="Atribute")
meta_tree.column("#1", width=100 )
meta_tree.heading("#1", text="Value")
meta_tree.bind("<Double-Button-1>", edit_tree_field)
meta_tree.pack(fill=BOTH, expand=YES, side=LEFT)

element_tree = tree_view(root, data_tree)



def print_cursorlocation(event):
    print "X = {} !! Y = {}".format(event.x, event.y)

#root.bind("<Button-1>", print_cursorlocation)

root.mainloop()
