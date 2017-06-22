import yaml
from openstack_helpers import get_image_info, get_flavors, get_instances, delete_instance, shutdown_instance, start_instance, get_server_info
import sys
import subprocess
from tempfile import NamedTemporaryFile
from novaclient.exceptions import Conflict


progress_bar = None
tree_columns = ("name", "ip", "id")

def load_defaults():
    with open("launcher.conf", 'r') as stream:
        conf_yaml = yaml.load(stream)
        return conf_yaml['default_flavor'], conf_yaml['default_image'], conf_yaml['default_yaml_file_path'], conf_yaml['default_instance_name']

default_flavor, default_image, default_yaml_file_path, default_instance_name = load_defaults()
servers = None

os_flavors = None



def get_instance_flavors(refresh=False):
    global os_flavors
    if refresh:
        return get_flavors(refresh=True)
    if os_flavors is None:
        return get_flavors()
    return os_flavors

default_flavor_id = get_flavors().get_id_from_flavor(default_flavor)

def get_servers():
    global servers
    servers = get_instances()
    return servers.all

#baudes = servers.find_instances()
#print(len(baudes))

def check_if_python2():
    if int(sys.version_info[0]) < 3:
        return True
    else:
        return False
if check_if_python2():
    from Tkinter import *
    import tkMessageBox as messagebox
    import ttk
else:
    from tkinter import *
    from tkinter import ttk
    from tkinter import tkMessageBox as messagebox




def submit(listbox, flavors, mainframe, *args):
    def add_name_and_counter(name, flavor):
        new_name = "{}-{}-".format(name, flavor)
        global servers
        _servers = servers.find_instances(search_value=new_name)
        print("$$$$$$$$$$$$$")
        print(len(_servers))
        print("$$$$$$$$$$$$$")
        if len(_servers) < 1:
            return new_name + "1"
        else:
            print("y")
            print(new_name)
            used_counters = []
            count_range = range(1,11)
            print(count_range)
            for i in [x.name for x in _servers]:
                print("-->{}".format(i))
                used_counters.append(int(i.replace(new_name,"")))
            print(used_counters)
            new_counter = min([x for x in range(1,11) if x not in used_counters])
            return new_name + "{}".format(new_counter)

    global entry_name
    _name = entry_name.get()
    try:
        index_select = int(listbox.curselection()[0])
        flavor_select = int(flavors.curselection()[0])
    except IndexError:
        Label(mainframe, text="You must select a flavor and image.").grid(row = 9, column = 5, columnspan=4)
        return

    image = get_image_info().list_of_names()[index_select]
    flavor_name = get_instance_flavors().list_of_names()[flavor_select]
    id = get_instance_flavors().get_id_from_flavor(flavor_name)
    instance_name = add_name_and_counter(_name, flavor_name)
    launch_instance(image, instance_name, id)

def refresh(listbox):
    listbox.delete(0, END)
    images = get_image_info(refresh=True)
    for item in images.list_of_names():
        listbox.insert(END, item)


def refresh_flavor(listbox):
    listbox.delete(0, END)
    flavors = get_instance_flavors(refresh=True)
    for item in flavors.list_of_names():
        listbox.insert(END, item)


def _exit():
    sys.exit(0)


def form_yaml(image, name, id):
    input_yml_file = default_yaml_file_path
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

def foo():
    global tree
    bar = tree.focus()
    id = tree.item(bar)['values'][2]
    return servers.get_instance_by_id(id)

def launch_instance(image, name, id):
    # ansible-playbook  osp7-testing.yml -e 'name=baude image=Fedora-Cloud-Base-26-20170605.n.0'
    yaml_file_name = form_yaml(image, name, id)
    cmd = ['ansible-playbook', '-vvv', yaml_file_name]
    print(" ".join(cmd))
    subp(cmd)

def subp(cmd):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print output.strip()
        rc = process.poll()
    return rc

def populate_listbox(listbox, values):
    for item in values:
        listbox.insert(END, item)

def context_menu(event):
    global popup
    try:
        #popup.tk_popup(event.x_root, event.y_root, 0)
        popup.post(event.x_root, event.y_root)
    except Exception as e:
        print(str(e))
        sys.exit()

def delete_instances(tree):
    for i in tree.get_children():
        tree.delete(i)

def refresh_instances(tree):
    global progress_bar
    global servers
    progress_bar.start()
    delete_instances(tree)
    populate_servers(get_servers())
    progress_bar.stop()

def delete_server():
    server = foo()
    delete_instance(server.id)

def stop_server():
    server = foo()
    try:
        shutdown_instance(server.id)
    except Conflict as e:
        return messagebox.showerror("Error", str(e))

def start_server():
    server = foo()
    try:
        start_instance(server.id)
    except Conflict as e:
        return messagebox.showerror("Error", str(e))

def copy_to_clipboard():
    global root
    server = foo()
    root.clipboard_clear()
    root.clipboard_append(server.ip)

def run_playbook():
    global root
    server = foo()
    cmd = ['ansible-playbook', '-vv', '-i', '{},'.format(server.ip), '-u', 'cloud-user', 'playbook.yml']
    print(cmd)
    subp(cmd)

def populate_servers(servers):
    global tree
    print("Server Type is : {}".format(servers))
    for server in servers:
        id = tree.insert('', 'end', values=(server.name, server.ip, server.id))
        tree.insert(id, 'end', values=("", "State", server.state))
        tree.insert(id, 'end', values=("", "Flavor ID", server.flavor))
        tree.insert(id, 'end', values=("", "Flavor Name", get_instance_flavors().get_flavor_name_from_id(server.flavor)))


def server_filter(filter_var, tree):
    global servers
    _filter = filter_var.get()
    delete_instances(tree)
    if servers is None:
        servers = get_instances()
    if _filter is not None:
        print("here1")
        filtered_servers = servers.find_instances(search_value=_filter)
        print("here2")
    else:
        filtered_servers = servers
    populate_servers(filtered_servers)

def image_filter():
    def filter_for_value(_image_name_list, value):
        _filtered = []
        for i in _image_name_list:
            if i.lower().find(value.lower()) > -1:
                _filtered.append(i)
        return _filtered

    global _fedora
    global _rhel
    global _windows
    global images
    global listbox
    fedora = _fedora.get()
    rhel = _rhel.get()
    windows = _windows.get()
    filtered_images = []
    # populate_listbox(listbox, images.list_of_names())
    image_name_list = images.list_of_names()
    listbox.delete(0, END)
    if not fedora and not rhel and not windows:
        populate_listbox(listbox, image_name_list)
    if fedora:
        filtered_images += filter_for_value(image_name_list, "fedora")
    if rhel:
        filtered_images += filter_for_value(image_name_list, "rhel")
    if windows:
        filtered_images += filter_for_value(image_name_list, "windows")

    populate_listbox(listbox, filtered_images)




images = get_image_info()
root = Tk()
root.title("Tk dropdown example")

_fedora = IntVar()
_rhel = IntVar()
_windows = IntVar()

# Add a grid
mainframe = Frame(root)
mainframe.grid(column=0,row=0) #sticky=(N,W,E,S) )
mainframe.columnconfigure(0, weight = 1)
mainframe.rowconfigure(0, weight = 1)
#mainframe.pack(pady = 300, padx = 200)
bottom_frame = Frame(root)

# Create a Tkinter variable
tkvar = StringVar(root)

choices = images.list_of_names()
max_image_length = max([len(x) for x in images.list_of_names()])


scrollbar = Scrollbar(mainframe, orient=VERTICAL)
fscrollbar = Scrollbar(mainframe, orient=VERTICAL)
listbox = Listbox(mainframe, width=max_image_length, yscrollcommand=scrollbar.set, exportselection=0)
flavors = Listbox(mainframe, yscrollcommand=fscrollbar.set, exportselection=0)
entry_name = Entry(mainframe, textvariable="foobar")
entry_name.insert(0, default_instance_name)

listbox.grid(row=3, column=6, columnspan=2, rowspan=4)
flavors.grid(row=3, column=2, columnspan=2, rowspan=4)
scrollbar.grid(row=3, column=8, rowspan=4, sticky=N+S)
fscrollbar.grid(row=3, column=4, rowspan=4, sticky=N+S)
entry_name.grid(row=0, column=2, columnspan=2)

scrollbar['command'] = listbox.yview
fscrollbar['command'] = flavors.yview
populate_listbox(listbox, images.list_of_names())
populate_listbox(flavors, get_instance_flavors().list_of_names())
Label(mainframe, text="Images").grid(row = 2, column = 5)
fedora = Checkbutton(mainframe, text="fedora", variable=_fedora, command=image_filter).grid(row=2, column=6)
rhel = Checkbutton(mainframe, text="rhel", variable=_rhel, command=image_filter).grid(row=2, column=7)
windows = Checkbutton(mainframe, text="windows", variable=_windows, command=image_filter).grid(row=2, column=8)

Label(mainframe, text="Flavors").grid(row = 2, column = 2, columnspan=2)
Label(mainframe, text="Instance Name").grid(row = 0, column = 0, columnspan=2)
Label(mainframe, text = '').grid(row=1, column=0)
Label(mainframe, text = '').grid(row=7, column=0)
Button(mainframe, text="Launch", command=lambda: submit(listbox, flavors, mainframe)).grid(row=9, column=6, rowspan=2)
Button(mainframe, text="Exit", command=_exit).grid(row=9, column=7, rowspan=2)
Label(mainframe, text = '').grid(row=11, column=0)
Button(mainframe, text="Refresh", command=lambda: refresh(listbox)).grid(row=4, column=5, rowspan=3)
Button(mainframe, text="Refresh", command=lambda: refresh_flavor(flavors)).grid(row=4, column=0, rowspan=3)


# Set Defaults
listbox.select_set(get_image_info().list_of_names().index(default_image))
flavors.select_set(get_instance_flavors().list_of_names().index(default_flavor))


Label(mainframe, text="Servers").grid(row = 10, column = 0, columnspan=2)
fv = StringVar()
tree = ttk.Treeview(columns=tree_columns, show="headings")
fv.trace("w", lambda name, index, mode, sv=fv, tree=tree: server_filter(sv, tree))

filter_name= Entry(mainframe, textvariable=fv)
filter_name.grid(row=10, column=2, columnspan=2)
vsb = Scrollbar(orient="vertical", command=tree.yview)
hsb = Scrollbar(orient="horizontal", command=tree.xview)
tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
tree.grid(column=2, row=13, columnspan=6, sticky='nsew', in_=mainframe)
mainframe.grid_columnconfigure(0, weight=1)
mainframe.grid_rowconfigure(0, weight=1)
Button(mainframe, text="Refresh", command=lambda: refresh_instances(tree)).grid(row=12, column=0, rowspan=3)

for col in tree_columns:
    tree.heading(col, text=col.title())

popup = Menu(root, tearoff=0)
popup.add_command(label="Delete", command=delete_server) # , command=next) etc...
popup.add_command(label="Stop", command=stop_server)
popup.add_command(label="Start", command=start_server)
popup.add_command(label="Copy to clipboard", command=copy_to_clipboard)
popup.add_command(label="Run playbook", command=run_playbook)
populate_servers(get_servers())
tree.bind("<Button-3>", context_menu)
Label(mainframe, text="").grid(row=14, column=0, columnspan=5)
message = Label(mainframe, text="").grid(row=18, column=0, columnspan=5)
progress_bar = ttk.Progressbar(mainframe, orient=HORIZONTAL, length=200, mode='indeterminate').grid(row=18, columnspan=7)
Label(mainframe, text="").grid(row=19, column=0, columnspan=5)

root.mainloop()