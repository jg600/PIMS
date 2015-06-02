#This is the source code for the Pipeline Interface and Management System (PIMS). PIMS was created by Joseph Gardner, Dept. of Genetics, University of Cambridge, UK. PIMS is licensed under the Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0) license. In particular, you are free to use, adapt, and share this software, under terms that include the following: it is attributed to the author named above; it is not used for commercial purposes; if you make contributions, it must be distributed under the same license (CC BY-NC-SA 4.0). A full description of this license is available at http://creativecommons.org/licenses/by-sa/4.0/ or on the PIMS GitHub repository at https://github.com/jg600/PIMS.

#PIMS is designed to make bioinformatics (and other) pipelines easy to create and edit, while keeping records of the work done. For usage, see the full manual (available online). At present, the most extensive testing has taken place on Ubuntu 14.04 with Python 2.7.6. The author does not guarantee any degree of functionality on any computer or operating system. While PIMS has been designed to be as flexible as possible, and is compatible with all command line tools tested, the author does not guarantee that every piece of software is compatible. If you find a piece of software that does not work with this, please contact the author.

print('Pipeline Interface and Management System (PIMS). Created by Joseph Gardner, and licensed under the Creative Commons Attribution-ShareAlike 4.0 International license. For a usage manual and full licensing information go to https://github.com/jg600/PIMS')

#Import the necessary modules
from Tkinter import *
import ttk, tkFont
import subprocess as sub
import os
import re
import time

#Create the directory structure needed, if it isn't in place already. This is a possible issue for cross-platforming, and needs to be checked (although os.getenv might work across the board).
pipeline_path = os.getenv("HOME")+'/pipeline'
if (not os.path.isdir(pipeline_path)):
	os.makedirs(pipeline_path)
for folder in ['/tools/', '/config/', '/scripts/', '/outputs/']:
	if (not os.path.isdir(pipeline_path+folder)):
		os.makedirs(pipeline_path+folder)

#Each bioinformatics tool is assigned a purpose when it is added to the list of tools in PIMS. This function creates a list of all the purposes found in the current tool set.
global purposes_list

def make_purposes_list():
	global purposes_list
	purposes_list = []
	for filename in os.listdir(pipeline_path+'/tools/'):
			#In case another file has ended up in there
			if (re.search(r'\.tool$', filename)):
				tool_file = open(pipeline_path+"/tools/%s" % filename, 'r')
				for line in tool_file:
					if (re.search(r'^PURPOSE', line)):
						line_list = line.rstrip().split(':')
						if (line_list[1] not in purposes_list):
							purposes_list.append(line_list[1])	
	return None

#Initialise the list of purposes
make_purposes_list()
				
#Set up the root for the Tkinter GUI and hide it
root = Tk()
root.withdraw()

#Function that calls an error message, with the message depending on the option it is called with. A call with no option given will result in nothing happening.
def error_message(opt=None, problem_string=None):
	error_msgs = {
0:'%s has already been entered.' % problem_string, 
1:'%s is not a valid entry. Please check the documentation.' % problem_string, 
2:'Tool %s deleted' % problem_string, 
3:'%s is not a valid file name. File names should contain only alphanumeric characters, underscores and hyphens.' % problem_string, 
4:'A file with the name %s already exists. Please choose another name.' % problem_string, 
5:'The tool %s was found in the selected configuration file but does not seem to exist. Skipping to next line.' % problem_string, 
6:'A tool file with the name %s already exixts. Please choose another name or delete the existing tool.' % problem_string,
7:'Please choose a tool to edit.',
8:'The tool %s does not exist. Please choose another, or create a new tool.' % problem_string,
9:'Please choose a script to view.',
10:'The script %s does not exist. Please choose another, or create a new script.' % problem_string,
11:'Please choose at least one purpose'
}
	if ((opt != None) & (opt in error_msgs.keys())):
		popup = Toplevel()
		popup.title('Error')
		popup.geometry("200x200")
		msg = Message(popup, text = error_msgs[opt])
		msg.pack()
		ok_button = ttk.Button(popup, text = 'OK', command = popup.destroy)
		ok_button.pack()
	else:
		return None

#Define the class purpose_frame. Each purpose in the list has a frame associated with it. The purpose frame contains a tool frame for each tool with the relevant purpose. These tool_frames are stored in a dictionary, with tool names used as keys.
class purpose_frame:
	def __init__(self, parent, purpose, row_num):
		#Define the LabelFrame widget and place it
		self.frame = ttk.LabelFrame(parent, padding = "3 3 12 12", text = purpose, borderwidth = '2m', relief = GROOVE)
		self.frame.grid(column=0, row = row_num, sticky = (N,W))
		self.frame.columnconfigure(0, weight=1)
		self.frame.rowconfigure(0, weight=1)

		#Create the dictionary used to hold the tool frames
		self.tool_frame_dict = dict()
		col_num = 0
		#Populate the dictionary by searching through the pipeline file system and opening each tool file in turn
		for filename in os.listdir(pipeline_path+'/tools/'):
			if (re.search(r'\.tool$', filename)):
				#Open each tool file and save the fields as a dictionary for use by the tool_frame class
				tool_name = filename.split('.')[0]
				tool_file = open(pipeline_path+"/tools/%s" % filename, 'r')
				tool_dict = dict()
				for line in tool_file:
					line_list = line.rstrip().split(':')
					tool_dict[line_list[0]] = line_list[1]
				#If the tool is of the correct purpose, create a tool frame for it, which is made inactive
				if tool_dict['PURPOSE'] == purpose:
					self.tool_frame_dict[tool_name] = tool_frame(self.frame, tool_dict, col_num)
					self.tool_frame_dict[tool_name].make_inactive()
					#Bind a a click to the frame to change activity state
					self.tool_frame_dict[tool_name].frame.bind('<Button-1>', lambda event, this_tool=tool_name: self.change_state(this_tool))
					col_num += 1
	#Define the function used to change the state of a tool frame
	def change_state(self, this_tool):
		if self.tool_frame_dict[this_tool].state == 'inactive':
			for tool in self.tool_frame_dict.keys():
				if (tool != this_tool) & (self.tool_frame_dict[tool].tool_dict['PURPOSE']==self.tool_frame_dict[this_tool].tool_dict['PURPOSE']):
					self.tool_frame_dict[tool].make_inactive()
				elif tool == this_tool:
					self.tool_frame_dict[tool].make_active()
		elif self.tool_frame_dict[this_tool].state == 'active':
			self.tool_frame_dict[this_tool].make_inactive()

#Define the class for a tool frame, which requires a parent widget (i.e., a purpose_frame), a dictionary with tool information (name, purpose, command, etc.), and its column within the parent's grid. Tool frames can be active or inactive - if they are active they will be used in the final pipeline script. Activity control is through the purpose_frame class, as this makes it easier to control all tool_frames at once (and, in particular, to make sure at most one is active at a time).
class tool_frame:
	def __init__(self, parent, tool_dict, col_num):
		self.tool_dict = tool_dict
		#Initialise the state field, which records whether the frame is active or not
		self.state = ''
		#Create the LabelFrame widget and place it in the parent
		self.frame = ttk.LabelFrame(parent, padding = "3 3 12 12", text = self.tool_dict['NAME'])
		self.frame.grid(column = col_num, row = 0)
		self.frame.columnconfigure(0, weight = 1)
		self.frame.rowconfigure(0, weight = 1)
		row_num = 1
		#Tools can have flags (on/off switches), options (i.e., keyword arguments), and arguments (non-keyword, order-dependent arguments). For each of FLAGS, OPTIONS and ARGUMENTS, check if any have been given, then create a dictionary to hold a list of widgets/vars for each
		if self.tool_dict['FLAGS'] != '':
			flags_list = self.tool_dict['FLAGS'].split(',')
			self.flags_dict = {flag:[] for flag in flags_list}
			self.flags_label = ttk.Label(self.frame, text = 'FLAGS')
			self.flags_label.grid(column=0,row = 0)
			for flag in flags_list:
				if flag != '':
					self.flags_dict[flag].append(ttk.Label(self.frame, text = flag))
					self.flags_dict[flag][0].grid(column=0, row = row_num, sticky = (N,E))
					self.flags_dict[flag].append(IntVar())
					self.flags_dict[flag].append(Checkbutton(self.frame, variable = self.flags_dict[flag][1]))
					self.flags_dict[flag][2].grid(column=1, row = row_num, sticky = (N,W))
					row_num += 1
				else:
					continue

		if self.tool_dict['OPTIONS'] != '':
			options_list = self.tool_dict['OPTIONS'].split(',')
			self.options_dict = {opt:[] for opt in options_list}
			self.options_label = ttk.Label(self.frame, text = 'OPTIONS')
			self.options_label.grid(column=0,row = row_num)
			row_num += 1		
			for opt in options_list:
				if opt != '':
					self.options_dict[opt].append(ttk.Label(self.frame, text = opt))
					self.options_dict[opt][0].grid(column=0, row = row_num, sticky = (N,W))
					self.options_dict[opt].append(StringVar())
					self.options_dict[opt].append(ttk.Entry(self.frame, textvariable = self.options_dict[opt][1]))
					self.options_dict[opt][2].grid(column=1, row = row_num, sticky = (N,W))
					row_num += 1
				else:
					continue

		if self.tool_dict['ARGUMENTS'] != '':
			arguments_list = self.tool_dict['ARGUMENTS'].split(',')
			self.arguments_dict = {arg:[] for arg in arguments_list}
			self.arguments_label = ttk.Label(self.frame, text = 'ARGUMENTS')
			self.arguments_label.grid(column=0,row = row_num)
			row_num += 1
			for arg in arguments_list:
				if arg != '':
					self.arguments_dict[arg].append(ttk.Label(self.frame, text = '<'+arg+'>'))
					self.arguments_dict[arg][0].grid(column=0, row = row_num, sticky = (N,W))
					self.arguments_dict[arg].append(StringVar())
					self.arguments_dict[arg].append(ttk.Entry(self.frame, textvariable = self.arguments_dict[arg][1]))
					self.arguments_dict[arg][2].grid(column=1, row = row_num, sticky = (N,W))
					row_num += 1
				else:
					continue
	#These are called by the purpose_frame parent to change the activity state of a given tool_frame.
	def make_inactive(self):
		self.frame.configure(relief = SUNKEN)
		if self.tool_dict['FLAGS'] != '':
			for flag in self.flags_dict.keys():
				self.flags_dict[flag][2].configure(state=DISABLED)
		if self.tool_dict['OPTIONS'] != '':
			for opt in self.options_dict.keys():
				self.options_dict[opt][2].configure(state=DISABLED)
		if self.tool_dict['ARGUMENTS'] != '':
			for arg in self.arguments_dict.keys():
				self.arguments_dict[arg][2].configure(state=DISABLED)
		self.state = 'inactive'
	
	def make_active(self):
		self.frame.configure(relief = RAISED)
		if self.tool_dict['FLAGS'] != '':
			for flag in self.flags_dict.keys():
				self.flags_dict[flag][2].configure(state=NORMAL)
		if self.tool_dict['OPTIONS'] != '':
			for opt in self.options_dict.keys():
				self.options_dict[opt][2].configure(state=NORMAL)
		if self.tool_dict['ARGUMENTS'] != '':
			for arg in self.arguments_dict.keys():
				self.arguments_dict[arg][2].configure(state=NORMAL)
		self.state = 'active'


#Define the basic class for a new window. This is the parent class for all windows (except error messages and similar popups). It opens a toplevel window, and places a canvas widget inside this. This canvas has vertical and horizontal scrollbars associated with it. A frame is put inside the canvas as a holder for subsequent widgets.

class window(Frame):
	def __init__(self):
		self.top = Toplevel()
		Frame.__init__(self, self.top)
		self.canvas = Canvas(self.top)
		self.mainframe = Frame(self.canvas)
		self.vsb = Scrollbar(self.top, orient=VERTICAL, command = self.canvas.yview)
		self.hsb = Scrollbar(self.top, orient=HORIZONTAL, command = self.canvas.xview)
		self.canvas.configure(yscrollcommand = self.vsb.set)
		self.canvas.configure(xscrollcommand = self.hsb.set)
		self.vsb.pack(side="right", fill="y")
		self.hsb.pack(side = "bottom", fill="x")
		self.canvas.pack(side="left", fill="both", expand=True)
		self.canvas.create_window((4,4), window = self.mainframe, anchor = "nw")
		self.mainframe.bind("<Configure>", self.OnFrameConfigure)

	def OnFrameConfigure(self, event):
		self.canvas.configure(scrollregion = self.canvas.bbox("all"))

#Window for adding new tools to those available
class addtool_window(window):

	def __init__(self):
		window.__init__(self)
		self.top.title('Add tool')

		#List of fields that need to be populated for a tool
		self.labels_list = ['NAME', 'PURPOSE', 'COMMAND', 'FLAGS', 'OPTIONS', 'ARGUMENTS']

		#Define and fill a dictionary that use the above labels as keys. Values are a
		#list of either [Label_widget, StringVar, Entry_widget] or [Label_widget, Text_widget]. The textvariable for the entry
		#widget is the StringVar in the list. The widgets in each value list are gridded 
		#next to each other, with one row per field.
		self.rows_dict = {lab:[] for lab in self.labels_list}
		row_num = 0
		for lab in self.labels_list:
			self.rows_dict[lab].append(ttk.Label(self.mainframe, text = lab))
			self.rows_dict[lab][0].grid(column = 0, row = row_num, sticky = (N,W))
			if lab in ['NAME', 'PURPOSE', 'COMMAND']:
				self.rows_dict[lab].append(StringVar())
				self.rows_dict[lab].append(ttk.Entry(self.mainframe, textvariable = self.rows_dict[lab][1], width=30))
				self.rows_dict[lab][2].grid(column = 1, row = row_num, sticky = (N,W))
			elif lab in ['FLAGS', 'OPTIONS', 'ARGUMENTS']:
				self.rows_dict[lab].append(Text(self.mainframe, height=10, width=30))
				self.rows_dict[lab][1].grid(column = 1, row = row_num, sticky = (N,W))
			row_num += 1
		
		#Create empty lists that will later be used to store flags, options and arguments
		self.list_dict = {'FLAGS':[], 'OPTIONS':[], 'ARGUMENTS':[]}

		#Define the regex patterns for each type of input.
		flag_pattern = re.compile('^-{1,2}[a-zA-Z0-9]{1}[\w-]*$') #One or two hyphens followed by at least one alphanumeric, then any number of alphanumerics, underscores and hyphens
		opt_pattern = re.compile('^-{1,2}[a-zA-Z0-9]{1}[\w-]*[=\s]{1}<{1}>{1}$') #As for flags, but followed by either an equals OR a space, then "<>" to indicate where the value goes
		arg_pattern = re.compile('^[\w-]+$') #Any number of alphanumerics, underscores and hyphens (in particular, no whitespace)
		self.pattern_dict = {'FLAGS':flag_pattern, 'OPTIONS':opt_pattern, 'ARGUMENTS':arg_pattern}

		#The add flag button adds flags to the list
		self.add_flag_button = ttk.Button(self.mainframe, text = 'Add flag', command = lambda: self.add_to_list('FLAGS'))
		self.add_flag_button.grid(column = 2, row = 3, sticky = (N,E))
		
		#The add option button adds options to the list
		self.add_option_button = ttk.Button(self.mainframe, text = 'Add option', command = lambda: self.add_to_list('OPTIONS'))
		self.add_option_button.grid(column = 2, row = 4, sticky = (N,E))

		self.add_argument_button = ttk.Button(self.mainframe, text = 'Add argument', command = lambda: self.add_to_list('ARGUMENTS'))
		self.add_argument_button.grid(column=2, row = 5, sticky = (N,E))

		#The add tool button calls the add tool function
		self.addtool_button = ttk.Button(self.mainframe, text = 'Add tool', command = self.add_tool)
		self.addtool_button.grid(column = 0, row = row_num, sticky = (N,W))

		self.done_button = ttk.Button(self.mainframe, text = 'Done', command = self.top.destroy)
		self.done_button.grid(column = 1, row = row_num, sticky = (N,W))

	#The function for adding input from the appropriate entry widget to the 
	#current list of flags/options/arguments. Get the text entered into the relevant Entry widget and add to the 
	#list if it is not already there and if it is not empty. Options can be added 
	#several at a time, but should be entered one per line. 

	def add_to_list(self, which_list):
		if str(self.rows_dict[which_list][1].get('1.0',END)) != '\n':
			names = str(self.rows_dict[which_list][1].get('1.0',END).rstrip()).split('\n')
			for name in names:
				if (re.match(self.pattern_dict[which_list], name)):
					if (name not in self.list_dict[which_list]):
						self.list_dict[which_list].append(name)
						self.rows_dict[which_list][1].delete('1.0',END)
						print(which_list+':')
						print(self.list_dict[which_list])
					elif (name in self.list_dict[which_list]):
						self.rows_dict[which_list][1].delete('1.0',END)
						error_message(opt=0, problem_string=name)
				else:
					error_message(opt=1, problem_string=name)
		return None
	
	#Function for adding a new tool. The directory is checked to see if the file already exists. The file is created and populated, and the purposes list
	#is updated. The entry widgets are cleared to make way for a new tool entry.
	def add_tool(self):
		if "%s.tool" % self.rows_dict['NAME'][2].get() in os.listdir(pipeline_path+"/tools/"):
			error_message(opt=6, problem_string=self.rows_dict['NAME'][2].get())
			return None
		self.add_to_list('FLAGS')
		self.add_to_list('OPTIONS')
		self.add_to_list('ARGUMENTS')
		tool_path = pipeline_path+"/tools/%s.tool" % self.rows_dict['NAME'][2].get()
		tool_file = open(tool_path,'w')
		tool_file.seek(0,0)
		tool_file.write("NAME:%s\n" % self.rows_dict['NAME'][1].get())
		tool_file.write("PURPOSE:%s\n" % self.rows_dict['PURPOSE'][1].get())
		tool_file.write("COMMAND:%s\n" % self.rows_dict['COMMAND'][1].get())
		for k in self.list_dict.keys():
			inputs_str = ','.join(map(str, self.list_dict[k]))
			tool_file.write("%s:%s\n" % (k, inputs_str))
		tool_file.close()
		make_purposes_list()
		for lab in self.labels_list:
			if lab in ['NAME', 'PURPOSE', 'COMMAND']:
				self.rows_dict[lab][2].delete(0,END)
			elif lab in ['FLAGS', 'OPTIONS', 'ARGUMENTS']:
				self.rows_dict[lab][1].delete('1.0',END)
		for k in self.list_dict.keys():
			self.list_dict[k] = []
		return None

#Window for viewing scripts that have already been generated. Error messages are generated if no tool is selected, or if the selected tool does not exist for some reason (although that should not happen - I think it could only occur if someone opened this window and generated the list and then deleted the relevant script before trying to view it). 
class viewscripts_window(window):
	def __init__(self):
		window.__init__(self)
		self.top.title("View scripts")
		self.script_dict = dict()
		for filename in os.listdir(pipeline_path+'/scripts/'):
			if (re.search(r'\.script$', filename)):
				script_name = filename.split('.')[0]
				self.script_dict[script_name] = open(pipeline_path+"/scripts/%s" % filename, 'r')
		self.script_sel_label = ttk.Label(self.mainframe, text = "Select script: ")
		self.script_sel_label.grid(column=0, row=0, sticky = (N,W))
		self.selected_script = StringVar()
		self.script_combobox = ttk.Combobox(self.mainframe, values = self.script_dict.keys(), textvariable = self.selected_script)
		self.script_combobox.grid(column=1, row=0, sticky=(N,W))
		self.view_button = ttk.Button(self.mainframe, text = 'View', command = self.view_script)
		self.view_button.grid(column=2, row=0, sticky = (N,W))
		self.cancel_button = ttk.Button(self.mainframe, text = 'Cancel', command = self.top.destroy)
		self.cancel_button.grid(column=3, row=0, sticky = (N,W))
		self.script_text = Text(self.mainframe, width = 100, height = 50)

	#Shows the Text widget and displays the script
	def view_script(self):
		if str(self.selected_script.get()) == '':
			error_message(opt=9, problem_string = None)
			return None
		elif str(self.selected_script.get()) not in self.script_dict.keys():
			error_message(opt=10, problem_string = str(self.selected_script.get()))
			return None
		self.script_combobox.configure(state=DISABLED)
		selected_script_file = self.script_dict[self.selected_script.get()]
		self.script_text.grid(column=0, row = 1, columnspan=4)
		i = 1
		for line in selected_script_file.readlines():
			self.script_text.insert('%d.0' % i, line)
			i += 1
		selected_script_file.close()
		self.script_text.configure(state = DISABLED)
		self.view_button.configure(state=DISABLED)
		
		
#Window for editing tools that have already been created. Similar to the script view window in many ways, just with more widgets to hold all the different fields. In particular, the error-handling is veruy similar - see above.
class edittool_window(window):
	
	def __init__(self):
		window.__init__(self)
		self.top.title('Edit tools')
		self.tool_file_dict = dict()
		for filename in os.listdir(pipeline_path+'/tools/'):
			if (re.search(r'\.tool$', filename)):
				tool_name = filename.split('.')[0]
				self.tool_file_dict[tool_name] = open(pipeline_path+"/tools/%s" % filename, 'a+r')
		self.tool_sel_label = ttk.Label(self.mainframe, text = "Select tool: ")
		self.tool_sel_label.grid(column = 0, row = 0)
		self.selected_tool = StringVar()
		self.tool_combobox = ttk.Combobox(self.mainframe, values = self.tool_file_dict.keys(), textvariable = self.selected_tool)
		self.tool_combobox.grid(column = 1, row = 0)
		self.goedit_button = ttk.Button(self.mainframe, text = 'Go', command = self.go_edit)
		self.goedit_button.grid(column=2, row=0)

		self.labels_list = ['NAME', 'PURPOSE', 'COMMAND', 'FLAGS', 'OPTIONS', 'ARGUMENTS']
		self.rows_dict = {lab:[] for lab in self.labels_list}

		for lab in self.labels_list:
			self.rows_dict[lab].append(ttk.Label(self.mainframe, text = lab))
			if lab in ['NAME', 'PURPOSE', 'COMMAND']:
				self.rows_dict[lab].append(StringVar())
				self.rows_dict[lab].append(ttk.Entry(self.mainframe, textvariable = self.rows_dict[lab][1]))
			elif lab in ['FLAGS', 'OPTIONS', 'ARGUMENTS']:
				self.rows_dict[lab].append(Text(self.mainframe, height=10, width=30))

		self.saveedit_button = ttk.Button(self.mainframe, text = 'Save', command = self.save_edit)
		self.canceledit_button = ttk.Button(self.mainframe, text = 'Cancel', command = self.top.destroy)
		self.deletetool_button = ttk.Button(self.mainframe, text = 'Delete tool', command = self.delete_tool)
		self.selected_tool_file = None

		
	#Displays the widgets for the tool's fields, and populates them from the tool file.
	def go_edit(self):
		if str(self.selected_tool.get()) == '':
			error_message(opt=7, problem_string=None)
			return None
		elif str(self.selected_tool.get()) not in self.tool_file_dict.keys():
			error_message(opt=8, problem_string=str(self.selected_tool.get()))
			return None
		self.tool_combobox.configure(state=DISABLED)
		self.selected_tool_file = self.tool_file_dict[self.selected_tool.get()]
		this_tool_dict = dict()
		for line in self.selected_tool_file:
			line_list = line.rstrip().split(':')
			this_tool_dict[line_list[0]] = line_list[1]
		row_num = 1
		for lab in self.labels_list:
			self.rows_dict[lab][0].grid(column = 0, row = row_num)
			if lab in ['NAME', 'PURPOSE', 'COMMAND']:
				self.rows_dict[lab][2].insert(0,this_tool_dict[lab])
				self.rows_dict[lab][2].grid(column = 1, row = row_num)
			elif lab in ['FLAGS', 'OPTIONS', 'ARGUMENTS']:
				comma_pattern = re.compile(',')
				to_insert = comma_pattern.sub('\\n',this_tool_dict[lab])
				self.rows_dict[lab][1].insert('1.0', to_insert)
				self.rows_dict[lab][1].grid(column=1, row = row_num)
			row_num += 1
		self.saveedit_button.grid(column=0, row = row_num, sticky = (N,W))
		self.canceledit_button.grid(column = 1, row = row_num, sticky = (N,W))
		self.deletetool_button.grid(column = 2, row = row_num, sticky = (N,E))
		self.goedit_button.configure(state=DISABLED)
		
	#Saves the edited values, as long as they match the regex (or are blank).
	def save_edit(self):
		new_vals_dict = dict()
		for lab in self.rows_dict.keys():
			if lab in ['NAME', 'PURPOSE', 'COMMAND']:
				if re.search(r',$', self.rows_dict[lab][1].get()):
					new_vals_dict[lab] = self.rows_dict[lab][1].get()[:-1]
				else:
					new_vals_dict[lab] = self.rows_dict[lab][1].get()
			elif lab in ['FLAGS', 'OPTIONS', 'ARGUMENTS']:
				flag_pattern = re.compile('^-{1,2}[a-zA-Z0-9]{1}[\w-]*$')
				opt_pattern = re.compile('^-{1,2}[a-zA-Z0-9]{1}[\w-]*[=\s]{1}<{1}>{1}$')
				arg_pattern = re.compile('^[\w-]+$')

				line_list = str(self.rows_dict[lab][1].get('1.0',END).rstrip()).split('\n')
				for l in line_list:
					if lab == 'FLAGS':
						if not re.match(flag_pattern,l) and l != '':
							error_message(opt=1, problem_string=l)
							return None
					if lab =='OPTIONS':
						if not re.match(opt_pattern, l) and l != '':
							error_message(opt=1, problem_string=l)
							return None
					if lab =='ARGUMENTS':
						if not re.match(arg_pattern, l) and l != '':
							error_message(opt=1, problem_string=l)
							return None
				
				new_vals_dict[lab] = ','.join(line_list)
		
		#The new tool values are saved by deleting the old file and then creating a new file and writing to it in the same way as adding a new tool.
		os.remove(pipeline_path+"/tools/%s.tool" % self.selected_tool.get())
		tool_path = pipeline_path+"/tools/%s.tool" % new_vals_dict['NAME']
		tool_file = open(tool_path,'w')
		tool_file.seek(0,0)
		for l in self.labels_list:
			tool_file.write("%s:%s\n" % (l, new_vals_dict[l]))
		tool_file.close()
		make_purposes_list()
		self.selected_tool_file.close()
		self.top.destroy()
		return None
	#Used to delete and existing tool.
	def delete_tool(self):
		sure_popup = Toplevel()
		sure_popup.title('Warning')
		sure_msg = Message(sure_popup, text = 'This will permanently delete the file for the selected tool. Are you sure you want to proceed?')
		sure_msg.grid(column=0, columnspan=2, row = 0)
		def sure_delete():
			os.remove(pipeline_path+"/tools/%s.tool" % self.selected_tool.get())
			sure_popup.destroy()
			self.top.destroy()
		yes_button = ttk.Button(sure_popup, text = 'Yes', command = sure_delete)
		yes_button.grid(column=0,row=1)
		no_button = ttk.Button(sure_popup, text = 'No', command = sure_popup.destroy)
		no_button.grid(column=1,row=1)
		
		return None

#Simply opens the main pipeline generation window
def open_pipeline(selected_purposes_list):
	run1 = runpipeline_window(selected_purposes_list)
	return None

#A class defining a Tkinter button for each purpose found which is used to define the order in which the tools are displayed and run in the script.
class purpose_button:
	def __init__(self, parent, text, to_list):
		self.text = text
		self.button = ttk.Button(parent, text = self.text, command = lambda:self.add_to_list(to_list))
	def add_to_list(self, to_list):
		current = to_list.get()
		edge_pattern = re.compile("['\(\)]")
		temp = edge_pattern.sub('', current)
		comma_pattern = re.compile(",")
		temp2 = comma_pattern.sub(' ', temp)
		to_list.set(temp2 +' %s' % self.text)

#A window in which the user gives PIMS the running order of the tools by clicking purpose_buttons (see above) in the desired order. As they are clicked, purposes will appear in a listbox. Purposes that have already been added can be removed individually, or the whole listbox can be emptied. Users cannot proceed unless they have selected at least one purpose.
class purpose_select_window(window):
	def __init__(self):
		window.__init__(self)
		self.top.title('Select tool types')
		self.instruct_label = ttk.Label(self.mainframe, text = 'Select tool types, in running order')
		self.instruct_label.grid(column=0, row=0, columnspan = 2, sticky = (N,W))
		self.selected_list = StringVar()
		self.purpose_button_dict = dict()
		row_num = 1
		for p in purposes_list:
			self.purpose_button_dict[p] = purpose_button(self.mainframe, p, self.selected_list)
			self.purpose_button_dict[p].button.grid(column=0, row = row_num, sticky = (N,W))
			row_num += 1

		self.selected_listbox = Listbox(self.mainframe, listvariable = self.selected_list, selectmode = SINGLE)
		self.selected_listbox.grid(column=1, row = 1, rowspan = row_num-1, sticky = (N,W))

		self.button_frame = ttk.Frame(self.mainframe, padding = "3 3 12 12", borderwidth = '2m', relief = GROOVE)
		self.button_frame.grid(column=0, row = row_num, columnspan = 2, sticky = (N,W))

		self.go_button = ttk.Button(self.button_frame, text = 'Go', command = self.go)
		self.go_button.grid(column = 0, row = 0, sticky = (N,W))

		self.removehighlighted_button = ttk.Button(self.button_frame, text = 'Delete selected', command = self.remove_highlighted)
		self.removehighlighted_button.grid(column = 1, row = 0, sticky = (N,W))

		self.reset_button = ttk.Button(self.button_frame, text = 'Reset', command = self.reset_selection)
		self.reset_button.grid(column=2, row = 0, sticky = (N,W))

		self.cancel_button = ttk.Button(self.button_frame, text = 'Cancel', command = self.top.destroy)
		self.cancel_button.grid(column=3, row = 0, sticky = (N,W))
		
	def reset_selection(self):
		self.selected_listbox.delete(first = 0, last = END)
	
	def remove_highlighted(self):
		try:
			self.selected_listbox.delete(self.selected_listbox.curselection())
		except TclError:
			return None

		
	def go(self):
		final_list_raw = self.selected_list.get()
		if final_list_raw == '':
			error_message(opt=11, problem_string = None)
			return None
		else:
			edge_pattern = re.compile("['\(\)\s+]")
			temp = edge_pattern.sub('', final_list_raw)
			final_list = temp.split(',')
			open_pipeline(final_list)
			self.top.destroy()
		
#The window where the desired tools are selected (i.e., made active), and all flags/options/arguments are either selected or given values, as appropriate. Once values have been input, they can be saved as a config file and loaded again from that file. When all all the required fields have been selected/filled, the script can be generated.
class runpipeline_window(window):
	def __init__(self, used_purposes):
		window.__init__(self)
		self.top.title('Run pipeline')
		#Set up all of the purpose frames needed, based on the list of purposes selected and their order. Each purpose frame is populated with relevant tool frames.
		self.purposes_list = used_purposes
		self.purpose_frame_dict = dict()
		row_num = 1
		for p in self.purposes_list:
			self.purpose_frame_dict[p] = purpose_frame(self.mainframe, p, row_num)
			row_num += 1
		self.button_frame = ttk.Frame(self.mainframe, padding = "3 3 12 12", borderwidth = '2m', relief = GROOVE)
		self.button_frame.grid(column=0, row = row_num, sticky = (N,W))

		self.go_button = ttk.Button(self.button_frame, text = 'Run', command = self.make_pipeline_script)
		self.go_button.grid(column=0, row = row_num, sticky = (N,W))
		self.save_config_button = ttk.Button(self.button_frame, text = 'Save configuration', command = self.save_config)
		self.save_config_button.grid(column = 1, row = row_num, sticky = (N,W))
		self.load_config_button = ttk.Button(self.button_frame, text = 'Load configuration', command = self.load_config)
		self.load_config_button.grid(column = 2, row = row_num, sticky = (N,W))
		self.cancel_run_button = ttk.Button(self.button_frame, text = 'Cancel', command = self.top.destroy)
		self.cancel_run_button.grid(column=3, row = row_num, sticky = (N,W))
	
	#Writes the script to a file. The script will crete a new, timestamped directory from which the script will be run, and which should hold all of the output files from each tool. It will also place a copy of itself in this new directory, for the sake of record-keeping. At the end, it will delete itself.
	def make_pipeline_script(self):
		
		pipeline_name_window = Toplevel()
		pipeline_name_window.title("Script name")

		name_label = ttk.Label(pipeline_name_window, text = "Script name:")
		name_label.grid(column=0, row=0, sticky = (N,W))

		name_var = StringVar()
		name_entry = ttk.Entry(pipeline_name_window, textvariable = name_var)
		name_entry.grid(column=1, row=0, sticky = (N,W))

		note_label = ttk.Label(pipeline_name_window, text = 'Please enter any notes on this run')
		note_label.grid(column=0,row=1,sticky = (N,W))

		note_var = StringVar()
		note_entry = ttk.Entry(pipeline_name_window, textvariable = note_var)
		note_entry.grid(column=1,row=1,sticky = (N,W))

		go_button = ttk.Button(pipeline_name_window, text = 'Go', command = lambda:write_script(name_var.get(), note_var.get()))
		go_button.grid(column=0, row=2, sticky = (N,W))

		def reset_name_note():
			name_entry.delete(0,END)
			note_entry.delete(0,END)
			return None

		reset_button = ttk.Button(pipeline_name_window, text = 'Reset', command = reset_name_note)
		reset_button.grid(column=1,row=2,sticky = (N,W))

		cancel_button = ttk.Button(pipeline_name_window, text = 'Cancel', command = pipeline_name_window.destroy)
		cancel_button.grid(column=2,row=2,sticky = (N,W))
		
		def write_script(script_name, note_str):
			if (re.match(r'^[\w-]+$', script_name)):
				if ('%s.script' % script_name) in  os.listdir(pipeline_path+"/scripts/"):
					error_message(opt=3, problem_string=script_name)
					return None
				else:
					print('Making script %s ... ' % script_name)
					script_file = open(pipeline_path+"/scripts/%s.script" % script_name, 'a')
					script_file.write("#!/bin/bash\n")
					new_dir = script_name+'_'+time.strftime("%Y%m%d_%H%M%S")
					script_file.write("mkdir %s\n" % new_dir)
					script_file.write("cp %s.script %s/%s.script\n" % (script_name, new_dir, script_name))
					script_file.write("cd %s\n" % new_dir)
					script_file.write("echo \"%s\" > NOTE\n" % note_str)
					for purpose in self.purposes_list:
						for tool in self.purpose_frame_dict[purpose].tool_frame_dict.keys():
							if self.purpose_frame_dict[purpose].tool_frame_dict[tool].state == 'active':
								tool_file = open(pipeline_path+"/tools/%s.tool" % tool, 'r')
								for line in tool_file:
									if re.search(r'^COMMAND:', line):
										tool_cmd = line.split(':')[1][:-1]
									elif re.search(r'^FLAGS:', line):
										tool_flags = line.split(':')[1][:-1].split(',')
									elif re.search(r'OPTIONS:', line):
										tool_opts = line.split(':')[1][:-1].split(',')
									elif re.search(r'^ARGUMENTS:', line):
										tool_args = line.split(':')[1][:-1].split(',')
								script_file.write(tool_cmd+' ')
								if tool_flags[0] != '':
									for flag in tool_flags:
										flag_state = self.purpose_frame_dict[purpose].tool_frame_dict[tool].flags_dict[flag][1].get()
										if flag_state == 1:
											script_file.write('%s ' % flag)
								if tool_opts[0] != '':
									for opt in tool_opts:
										opt_val = self.purpose_frame_dict[purpose].tool_frame_dict[tool].options_dict[opt][1].get()
										if opt_val != '':
											gtlt_pattern = re.compile('<{1}>{1}')
											opt_to_write = gtlt_pattern.sub('',opt)
											script_file.write('%s%s ' % (opt_to_write, opt_val))
								if tool_args[0] != '':
									for arg in tool_args:
										arg_val = self.purpose_frame_dict[purpose].tool_frame_dict[tool].arguments_dict[arg][1].get()
										if arg_val != '':
											script_file.write('%s ' % arg_val)
							script_file.write('\n')
					script_file.write("cd ..\nrm %s.script\n" % script_name)
					print('Done')
					script_file.close()
					pipeline_name_window.destroy()
				
			else:
				error_message(opt=2, problem_string=script_name)
				return None
		

	def load_config(self):
		choose_file_window = Toplevel()
		choose_file_window.title('Choose configuration')
		choose_label = ttk.Label(choose_file_window, text = 'Choose a configuration')
		choose_label.grid(column=0, row=0, sticky = (N,W))
		
		existing_configs_list = ''
		existing_configs = StringVar()
		for filename in os.listdir(pipeline_path+'/config/'):
			if (re.search(r'\.config$', filename)):
				config_name = filename.split('.')[0]
				existing_configs_list = existing_configs_list+'%s ' % config_name
		existing_configs_list.rstrip()
		existing_configs.set(existing_configs_list)
		config_listbox = Listbox(choose_file_window, listvariable = existing_configs, selectmode = SINGLE)
		config_listbox.grid(column=0, row=1, columnspan = 3, sticky = (N,W))

		def load_file(to_destroy):
			selected_file_name = str(config_listbox.get(int(config_listbox.curselection()[0])))
			selected_file = open(pipeline_path+'/config/%s.config' % selected_file_name, 'r')
			for line in selected_file:
				line_list = line.rstrip().split(':')
				if (line_list[2] != '') & (line_list[3] != '') & (line_list[4] != ''):
					continue

				tool_name = line_list[0]
				try:
					tool_file = open(pipeline_path+'/tools/%s.tool' % tool_name, 'r')
				except IOError:
					error_message(opt = 5, problem_string=tool_name)
					continue

				for line in tool_file:
					if re.search(r'^PURPOSE:', line):
						tool_purpose = line.rstrip().split(':')[1]
				tool_file.close()
				if tool_purpose in self.purposes_list:
					self.purpose_frame_dict[tool_purpose].tool_frame_dict[tool_name].make_active()
					flag_list = line_list[2].split(';') if line_list[2] != '' else []
					opt_list = line_list[3].split(';') if line_list[3] != '' else []
					arg_list = line_list[4].split(';') if line_list[4] != '' else []

					for pair in flag_list:
						key_val = pair.split('$')
						flag_widgets_list = self.purpose_frame_dict[tool_purpose].tool_frame_dict[tool_name].flags_dict[key_val[0]]
						flag_widgets_list[2].select()

					for pair in opt_list:
						key_val = pair.split('$')
						opt_widgets_list = self.purpose_frame_dict[tool_purpose].tool_frame_dict[tool_name].options_dict[key_val[0]]
						opt_widgets_list[2].delete(0, last = len(opt_widgets_list[1].get())+1)
						opt_widgets_list[2].insert(0, key_val[1])

					for pair in arg_list:
						key_val = pair.split('$')
						arg_widgets_list = self.purpose_frame_dict[tool_purpose].tool_frame_dict[tool_name].arguments_dict[key_val[0]]
						arg_widgets_list[2].delete(0, last = len(arg_widgets_list[1].get())+1)
						arg_widgets_list[2].insert(0, key_val[1])

					if line_list[1] == 'active':
						continue
					elif line_list[1] == 'inactive':
						self.purpose_frame_dict[tool_purpose].tool_frame_dict[tool_name].make_inactive()
				else:
					continue
			
			to_destroy.destroy()
		
		def delete_file():
			sure_window = Toplevel()
			sure_window.title('Confirm')

			sure_window_label = ttk.Label(sure_window, text = 'This will permanently delete the selected configuration file.\nAre you sure you want to continue?')
			sure_window_label.grid(column=0,row=0,columnspan=2)

			def confirm_delete():
				selected_file_name = str(config_listbox.get(int(config_listbox.curselection()[0])))
				os.remove(pipeline_path+'/config/%s.config' % selected_file_name)
				new_file_list = existing_configs_list.split(' ')
				new_file_list.remove(selected_file_name)
				existing_configs.set(' '.join(new_file_list))
				sure_window.destroy()
			def cancel_delete():
				sure_window.destroy()
				return None

			sure_window_yes_button = ttk.Button(sure_window, text = 'Yes', command = lambda:confirm_delete())
			sure_window_yes_button.grid(column=0,row=1,sticky = (N,W))

			sure_window_no_button = ttk.Button(sure_window, text = 'No', command = lambda:cancel_delete())
			sure_window_no_button.grid(column=1,row=1, sticky = (N,W))


		load_button = ttk.Button(choose_file_window, text = 'Load selected file', command = lambda:load_file(choose_file_window))
		load_button.grid(column = 0, row = 2, sticky = (N,W))

		delete_button = ttk.Button(choose_file_window, text = 'Delete selected file', command = lambda:delete_file())
		delete_button.grid(column = 2, row = 2, sticky = (N,W))

		cancel_load_button = ttk.Button(choose_file_window, text = 'Cancel', command = choose_file_window.destroy)
		cancel_load_button.grid(column=1, row = 2, sticky = (N,W))
	#Config files are saved in the following format. Each tool has one line consisting if colon (:) separated fields, as follows: NAME:STATE:FLAGS:OPTIONS:ARGUMENTS. STATE records whether the tool's frame is active or inactive at the time of saving. FLAGS, OPTIONS and ARGUMENTS are all semicolon (;) separated lists, where each item in the list consists of NAME$VALUE, where NAME is the name of the flag/opt/arg, and VALUE is the value input by the user. Fields left empty are ignored. If the tool has, for example, no flags, there will simply be two colons, and this will be interpreted as an empty string when the line is split.
	def save_config(self):

		def make_config_file(to_destroy, config_name):
			config_file = open(pipeline_path+'/config/%s.config' % config_name, 'a')
			for purpose in self.purpose_frame_dict.keys():
				for tool_name in self.purpose_frame_dict[purpose].tool_frame_dict.keys():
					tool_state = self.purpose_frame_dict[purpose].tool_frame_dict[tool_name].state
					config_file.write('%s:%s:' % (tool_name, tool_state))
					flag_list_to_write = []
					opt_list_to_write = []
					arg_list_to_write = []
					try:
						for flag_name in self.purpose_frame_dict[purpose].tool_frame_dict[tool_name].flags_dict.keys():
							flag_state = self.purpose_frame_dict[purpose].tool_frame_dict[tool_name].flags_dict[flag_name]
							if flag_state[1].get() == 1:
								flag_list_to_write.append("%s$1" % flag_name)
							else:
								continue
					except AttributeError:
						flag_list_to_write.append('')

					try:
						for opt_name in self.purpose_frame_dict[purpose].tool_frame_dict[tool_name].options_dict.keys():
							opt_val = self.purpose_frame_dict[purpose].tool_frame_dict[tool_name].options_dict[opt_name]
							if len(opt_val[1].get()) != 0:
								opt_list_to_write.append('%s$%s' % (opt_name, opt_val[1].get()))
							else:
								continue
					except AttributeError:
						opt_list_to_write.append('')
					
					try:
						for arg_name in self.purpose_frame_dict[purpose].tool_frame_dict[tool_name].arguments_dict.keys():
							arg_val = self.purpose_frame_dict[purpose].tool_frame_dict[tool_name].arguments_dict[arg_name]
							if len(arg_val[1].get()) != 0:
								arg_list_to_write.append('%s$%s' % (arg_name, arg_val[1].get()))
							else:
								continue
					except AttributeError:
						arg_list_to_write.append('')

					config_file.write(";".join(flag_list_to_write)+':'+";".join(opt_list_to_write)+':'+";".join(arg_list_to_write)+"\n")
			config_file.close()

			to_destroy.destroy()
			print('Configuration %s saved' % config_name)		
		
		def check_config_file(to_destroy, config_name):
			#Check entry input does not contain illegal characters
			if (re.match(r'^[\w-]+$', config_name)):
				#Open the file to write to. If it already exists, give the option to overwrite
				if ('%s.config' % config_name) in os.listdir(pipeline_path+'/config/'):
					file_exists_popup = Toplevel()
					file_exists_popup.title('File already exists!')
					file_exists_msg = Message(file_exists_popup, text = 'A file with this name already exists. Would you like to overwrite this file?')
					file_exists_msg.grid(column=0,row=0)

					def edit_file():
						os.remove(pipeline_path+'/config/%s.config' % config_name)
						make_config_file(to_destroy, config_name)
						file_exists_popup.destroy()
						
					save_cancel_button = ttk.Button(file_exists_popup, text = 'Cancel', command = file_exists_popup.destroy)
					save_cancel_button.grid(column=1,row=1,sticky = (N,W))
					
					edit_file_button = ttk.Button(file_exists_popup, text = 'Overwrite', command = edit_file)
					edit_file_button.grid(column=0,row=1,sticky = (N,W))
				else:
					make_config_file(to_destroy, config_name)
			else:
				error_message(opt=2, problem_string=config_name)
				return None

		config_name_popup = Toplevel()
		config_name_label = ttk.Label(config_name_popup, text = 'Configuration name:')
		config_name_label.grid(column = 0, row = 0)
		config_name_variable = StringVar()
		config_name_entry = ttk.Entry(config_name_popup, textvariable = config_name_variable)
		config_name_entry.grid(column = 1, row = 0, sticky = (N,W))
		cancel_config_button = ttk.Button(config_name_popup, text = 'Cancel', command = config_name_popup.destroy)
		cancel_config_button.grid(column=1, row = 1, sticky = (N,W))
		save_config_button = ttk.Button(config_name_popup, text = 'Save', command = lambda:check_config_file(config_name_popup, config_name_variable.get()))
		save_config_button.grid(column=0, row = 1, sticky = (N,W))

#Class for the initial window to pop up, giving the various options available
class init_window(window):
	def __init__(self):
		window.__init__(self)
		self.top.title("Choose option")
		
		#Button that opens the pipeline run window with options, etc.
		self.runButton = ttk.Button(self.mainframe, text = 'Generate pipeline script', command = self.select_purpose)
		self.runButton.grid(row = 0, column = 0, sticky = (N,W))
		self.run_info_popup = ''
		#self.run_info_popup.withdraw()
		#self.run_info_msg = Message(self.run_info_popup, text = 'Click to run pipeline')
		#self.run_info_msg.pack()
		
		self.runButton.bind('<Enter>', self.hover_info)
		self.runButton.bind('<Leave>', self.hover_info_gone)

		#Button to open the window for adding a new tool to those available
		self.addtoolButton = ttk.Button(self.mainframe, text = 'Add tool', command = self.open_addtool)
		self.addtoolButton.grid(row = 0, column = 1, sticky = (N,W))

		#Button to open the window for editing existing tools
		self.edittoolButton = ttk.Button(self.mainframe, text = 'Edit existing tool', command = self.open_edittool)
		self.edittoolButton.grid(row = 0, column = 2, sticky = (N,W))

		#Button to view scripts
		self.viewscript_button = ttk.Button(self.mainframe, text = 'View scripts', command = self.view_scripts)
		self.viewscript_button.grid(row=1, column=0, sticky = (N,W))

		#Quit button
		self.quitButton = ttk.Button(self.mainframe, text = 'Quit', command = root.destroy)
		self.quitButton.grid(row = 1, column = 1, sticky = (S))
	
	#A tentative feature that would create small information windows when the user hovers a mouse over a given widget. Currently just for testing.
	def hover_info(self,event):
		self.run_info_popup = Toplevel()
		self.run_info_popup.geometry('100x100+%d+%d' % (event.x_root, event.y_root))
		self.run_info_popup.overrideredirect(True)
		run_info_msg = Message(self.run_info_popup, text = 'Message')
		run_info_msg.pack()
		self.run_info_popup.update_idletasks()
	
	def hover_info_gone(self,event):
		self.run_info_popup.destroy()
	
	def select_purpose(self):
		purpsel1 = purpose_select_window()
		return None
	def open_addtool(self):
		add1 = addtool_window()
		return None
	def open_edittool(self):
		edit1 = edittool_window()
		return None
	def view_scripts(self):
		view1 = viewscripts_window()
		return None

init1 = init_window()

root.mainloop()

		


























