from shade import *
import json
import os
from munch import Munch
from novaclient import client
from keystoneauth1 import loading
from keystoneauth1 import session
import glanceclient.v2.client as glclient


IMAGE_FILE = os.path.join(os.path.expanduser('~'), ".openstack_images.json")
FLAVORS = os.path.join(os.path.expanduser('~'), ".openstack_flavors.json")

simple_logging(debug=True)
conn = openstack_cloud(cloud='e2e')
loader = loading.get_plugin_loader('password')
auth = loader.load_from_options(auth_url=os.environ['OS_AUTH_URL'],
                                username=os.environ['OS_USERNAME'],
                                password=os.environ['OS_PASSWORD'],
                                project_id=os.environ['OS_TENANT_ID'])
sess = session.Session(auth=auth)
nova = client.Client(2, session=sess)
glance = glclient.Client(session=sess)


class OS_Distros(object):
    def __init__(self, image):
        self.name = None
        self.status = None
        self.os_type = None
        #self.os_distro = None
        #self.major_version = None
        self.input = image
        '''
                    meta_os_type = None if not hasattr(i, "meta_os_type") else i.meta_os_type
            if meta_os_type is None and hasattr(i, "os_type"):
                meta_os_type = i.os_type
        '''

    def create_from_openstack(self):
        self.name = self.input.get("name", "") or ""
        self.status = self.input.get("status", "") or ""
        self.os_type = None if not hasattr(self.input, "meta_os_type") else self.input.meta_os_type
        if self.os_type is None and hasattr(self.input, "os_type"):
            self.os_type = self.input.os_type
        elif self.os_type is None and hasattr(self.input, "metadata"):
            if hasattr(self.input.metadata, 'meta_os_type'):
                self.os_type = self.input.metadata.meta_os_type
            else:
                self.os_type = ""

    #def create_from_cache(self):
    #    self.status = self.input["status"]
    #    self.name = self.input["name"]
    #    self.os_type = self.input["os_type"]

    def get_value(self, value):
        return self.__getattribute__(value)

    def to_dict(self):
        return { "name": self.name.encode('utf-8'),
                 "status": self.status.encode('utf-8'),
                 "os_type": self.os_type.encode('utf-8'),
                 }

class Images(object):
    def __init__(self, input_images):
        self.input_images = input_images
        self.image_list = []

    def create(self):
        for i in self.input_images:
            _tmp = OS_Distros(i)
            _tmp.create_from_openstack()
            self.image_list.append(_tmp)

    def dump(self, value_to_dump=None):
        for i in self.image_list:
            if not value_to_dump:
                print(vars(i))
            else:
                print(i.get_value(value_to_dump))

    def sort_by(self, value):
        newlist = sorted([x for x in self.image_list if x.name is not ""], key=lambda k: k.name)
        return newlist

    def to_json(self):
        my_list = []
        for i in self.image_list:
            if i.name is not "":
                my_list.append(i.to_dict())
        return my_list

    def to_file(self, image_json):
        with open(IMAGE_FILE, 'w') as outfile:
            json.dump(image_json, outfile)

    def list_of_names(self):
        return [x.name.encode("utf-8") for x in self.sort_by("foo")]


class Flavor(object):
    def __init__(self, input):
        self.input = input
        self.name = None
        self.ram = None
        self.disk = None
        self.vcpus = None
        self.id = None

    def create_from_openstack(self):
        self.name = self.input.name
        self.disk = self.input.disk
        self.vcpus = self.input.vcpus
        self.ram = self.input.ram
        try:
            self.id = int(self.input.id)
        except ValueError:
            self.id = self.input.id

    def create_from_cache(self):
        self.name= self.input["name"]
        self.ram = self.input["ram"]
        self.disk = self.input["disk"]
        self.vcpus = self.input["vcpus"]
        self.id = self.input["id"]

    def get_value(self, value):
        return self.__getattribute__(value)

    def to_dict(self):
        return { "name": self.name.encode('utf-8'),
                 "disk": self.disk,
                 "vcpus": self.vcpus,
                 "ram": self.ram,
                 "id": self.id
                 }


class Flavors(object):
    def __init__(self, input):
        self.input = input
        self.flavor_list = []

    def _conv_to_int_clean(self, id):
        try:
            int(id)
        except ValueError:
            return False
        return True


    def create(self):
       for i in self.input:
        _tmp = Flavor(i)
        if isinstance(i, Munch):
            _tmp.create_from_openstack()
        else:
           _tmp.create_from_cache()

        self.flavor_list.append(_tmp)

    def dump(self, value_to_dump=None):
        for i in self.flavor_list:
            if not value_to_dump:
                print(vars(i))
            else:
                print(i.get_value(value_to_dump))

    def sort_by(self, value):
        newlist = sorted([x for x in self.flavor_list if self._conv_to_int_clean(x.id)], key=lambda k: k.name)
        return newlist

    def to_json(self):
        my_list = []
        for i in self.flavor_list:
            if self._conv_to_int_clean(i.id):
                my_list.append(i.to_dict())
        return my_list

    def to_file(self, flavor_json):
        with open(FLAVORS, 'w') as outfile:
            json.dump(flavor_json, outfile)

    def list_of_names(self):
        return [x.name.encode("utf-8") for x in self.sort_by("foo")]

    def get_id_from_flavor(self, name):
        for x in self.sort_by("foo"):
            if x.name == name:
                return x.get_value('id')

    def get_flavor_name_from_id(self, id):
        for x in self.sort_by("foo"):
            if x.id == int(id):
                return x.get_value('name')

class Instance(object):
    def __init__(self, input):
        self.input = input
        self.name = None
        self.id = None
        self.state = None
        self.user_id = None
        self.ip = None
        self.flavor = None

    def create(self):
        self.name = self.input['name']
        self.id = self.input['id']
        self.state = self.input['vm_state']
        self.user_id = self.input['user_id']
        self.ip = self.input['accessIPv4']
        self.flavor = self.input['flavor']['id']


    def get_value(self, value):
        return self.__getattribute__(value)

    def dump(self):
        print("name={}, id={}, state={}, user_id={}, ip={}, input={}".format(self.name,
                                                                   self.id,
                                                                   self.state,
                                                                   self.user_id,
                                                                   self.ip,
                                                                             self.input))

class Instances(object):
    def __init__(self, input):
        self.input = input
        self.instance_list = []

    def create(self):
        for i in self.input:
            _tmp = Instance(i)
            _tmp.create()
            self.instance_list.append(_tmp)

    def dump(self, value_to_dump=None):
        for i in self.instance_list:
            if not value_to_dump:
                print(vars(i))
            else:
                print(i.get_value(value_to_dump))

    def find_instances(self, search_value=None):
        if not search_value:
            return self.instance_list

        search_list = []
        for i in self.instance_list:
            print("searching for {} in {}".format(search_value, i.name))
            if i.name.find(search_value) > -1:
                search_list.append(i)
        print("search list is {}".format(search_list))
        return search_list

    def get_instance_by_id(self, id):
        for i in self.instance_list:
            if i.id == id:
                return i
        return None

    @property
    def all(self):
        return [x for x in self.instance_list]

def load_images_from_cache():
    return json.loads(open(IMAGE_FILE, "r").read())


def load_flavors_from_cache():
    return json.loads(open(FLAVORS, "r").read())

def get_image_info(refresh=False):
    if refresh or not os.path.exists(IMAGE_FILE):
        os_images = conn.list_images()
    else:
        os_images = load_images_from_cache()
    images = Images(os_images)
    images.create()
    if refresh or not os.path.exists(IMAGE_FILE):
        images.to_file(images.to_json())
    return images


def get_flavors(refresh=False):
    if refresh or not os.path.exists(FLAVORS):
        flavors_list =  conn.list_flavors()
    else:
        flavors_list = load_flavors_from_cache()
    flavors = Flavors(flavors_list)
    flavors.create()
    if not os.path.exists(FLAVORS):
        flavors.to_file(flavors.to_json())
    return flavors

def get_instances():
    servers_list = conn.list_servers()
    servers = Instances(servers_list)
    servers.create()
    return servers

def delete_instance(server_id):
    conn.delete_server(server_id, wait=False)

def shutdown_instance(server_id):
    server = nova.servers.find(id=server_id)
    server.stop()

def start_instance(server_id):
    server = nova.servers.find(id=server_id)
    server.start()

def get_server_info(server_id):
    server = nova.servers.find(id=server_id)
    print(server)
    print(vars(server))
    print("@@@@@@@@@@@@@@@@2")
    print("keys: {}".format([x for x in vars(server)]))
    #print("image flavor: {}".format(server['flavor']['id']))
    #print(server['OS-EXT-STS:task_state'])
    print("**************")
    print(server.flavor['id'])
    print(server.name)
    print(server.id)
    print(server.addresses)
    print(server.to_dict())
    print("**************")
#def redeploy_instance(server_id):
#    server = nova.servers.find(id=server_id)
#    server.()
