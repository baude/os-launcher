import yaml
from openstack_helpers import get_image_info, get_flavors
import sys
import subprocess
from tempfile import NamedTemporaryFile


def load_defaults():
    with open("launcher.conf", 'r') as stream:
        conf_yaml = yaml.load(stream)
        return conf_yaml['default_flavor'], conf_yaml['default_image'], conf_yaml['default_yaml_file_path']

default_flavor, default_image, default_yaml_file_path = load_defaults()
default_flavor_id = get_flavors().get_id_from_flavor(default_flavor)

def check_if_python2():
    if int(sys.version_info[0]) < 3:
        return True
    else:
        return False
if check_if_python2():
    from Tkinter import *
else:
    from tkinter import *

def submit(listbox, flavors, mainframe, *args):
    try:
        index_select = int(listbox.curselection()[0])
        flavor_select = int(flavors.curselection()[0])
    except IndexError:
        Label(mainframe, text="You must select a flavor and image.").grid(row = 9, column = 5, columnspan=4)
        return

    image = get_image_info().list_of_names()[index_select]
    name = get_flavors().list_of_names()[flavor_select]
    id = get_flavors().get_id_from_flavor(name)
    launch_instance(image, name, id)

def refresh(listbox):
    listbox.delete(0, END)
    images = get_image_info(refresh=True)
    for item in images.list_of_names():
        listbox.insert(END, item)


def refresh_flavor(listbox):
    listbox.delete(0, END)
    flavors = get_flavors(refresh=True)
    for item in flavors.list_of_names():
        listbox.insert(END, item)


def _exit():
    sys.exit(0)


def form_yaml(image, name, id):
    input_yml_file = "/home/bbaude/ansible/nodes/osp7-testing.default"
    with open(input_yml_file, 'r') as stream:
        input_yaml = yaml.load(stream)
    tasks = input_yaml[0]['tasks']
    for i in tasks:
        if 'os_server' in i.keys():
            i['os_server']['image'] = image
            i['os_server']['name'] = name
            i['os_server']['flavor'] = id
    print(input_yaml)
    f = NamedTemporaryFile(delete=False)
    print(f.name)
    f.write(yaml.dump(input_yaml))
    f.close()
    return f.name



def launch_instance(image, name, id):
    # ansible-playbook  osp7-testing.yml -e 'name=baude image=Fedora-Cloud-Base-26-20170605.n.0'
    yaml_file_name = form_yaml(image, 'baude', id)
    cmd = ['ansible-playbook', '-vvv', yaml_file_name]
    print(" ".join(cmd))
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print output.strip()
        rc = process.poll()
    _exit()

def populate_listbox(listbox, values):
    for item in values:
        listbox.insert(END, item)

images = get_image_info()
root = Tk()
root.title("Tk dropdown example")

# Add a grid
mainframe = Frame(root)
mainframe.grid(column=0,row=0) #sticky=(N,W,E,S) )
mainframe.columnconfigure(0, weight = 1)
mainframe.rowconfigure(0, weight = 1)
mainframe.pack(pady = 300, padx = 200)

# Create a Tkinter variable
tkvar = StringVar(root)

choices = images.list_of_names()
max_image_length = max([len(x) for x in images.list_of_names()])


scrollbar = Scrollbar(mainframe, orient=VERTICAL)
fscrollbar = Scrollbar(mainframe, orient=VERTICAL)
listbox = Listbox(mainframe, width=max_image_length, yscrollcommand=scrollbar.set, exportselection=0)
flavors = Listbox(mainframe, yscrollcommand=fscrollbar.set, exportselection=0)

listbox.grid(row=1, column=6, columnspan=2, rowspan=4)
flavors.grid(row=1, column=2, columnspan=2, rowspan=4)
scrollbar.grid(row=1, column=8, rowspan=4, sticky=N+S)
fscrollbar.grid(row=1, column=4, rowspan=4, sticky=N+S)
scrollbar['command'] = listbox.yview
fscrollbar['command'] = flavors.yview
populate_listbox(listbox, images.list_of_names())
populate_listbox(flavors, get_flavors().list_of_names())
Label(mainframe, text="Images").grid(row = 0, column = 6, columnspan=2)
Label(mainframe, text="Flavors").grid(row = 0, column = 2, columnspan=2)

Label(mainframe, text = '').grid(row=5, column=0)
Button(mainframe, text="OK", command=lambda: submit(listbox, flavors, mainframe)).grid(row=7, column=6, rowspan=2)
Button(mainframe, text="Exit", command=_exit).grid(row=7, column=7, rowspan=2)
Button(mainframe, text="Refresh", command=lambda: refresh(listbox)).grid(row=2, column=5, rowspan=3)
Button(mainframe, text="Refresh", command=lambda: refresh_flavor(flavors)).grid(row=2, column=0, rowspan=3)


# Set Defaults
listbox.select_set(get_image_info().list_of_names().index(default_image))
flavors.select_set(get_flavors().list_of_names().index(default_flavor))

root.mainloop()