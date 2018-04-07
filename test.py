

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
            "atribute":'"DATA editor {}".format(data_tree[-1]["DATA"]["atribute"]["URL"])',
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

def create_gui_from_dic(config_dic):

	iterator_list = range(0,len(config_dic),1) #Get all data out from dic in ordered manner


	for key in iterator_list:
		create_element_command = config_dic[str(key)]["DATA"]["text"]
		if create_element_command != "":
			print create_element_command

	for key in iterator_list:
		root_id = config_dic[str(key)]["PARENT"]
		if root_id != "":
			root_element = config_dic[root_id]["DATA"]["element"]	
			child_element = config_dic[str(key)]["DATA"]["element"]
			setting = config_dic[str(key)]["DATA"]["atribute"]

			print "{}.{}({})".format(root_element, child_element, setting)


create_gui_from_dic(config_dic)			