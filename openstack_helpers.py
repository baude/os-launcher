from shade import *
import json
import os
from munch import Munch

IMAGE_FILE = os.path.join(os.path.expanduser('~'), ".openstack_images.json")
FLAVORS = os.path.join(os.path.expanduser('~'), ".openstack_flavors.json")

simple_logging(debug=True)
conn = openstack_cloud(cloud='e2e')

class OS_Distros(object):
    def __init__(self, image):
        self.name = None
        self.status = None
        self.os_distro = None
        self.major_version = None
        self.orig = None
        self.input = image

    def create_from_openstack(self):
        self.name = self.input.get("name", "") or ""
        self.status = self.input.get("status", "") or ""
        self.major_version = "" if not hasattr(self.input, "os_major_ver") else getattr(self.input, "os_major_ver")
        self.os_type = "" if not hasattr(self.input, "os_type") else getattr(self.input, "os_type")
        self.os_variant = "" if not hasattr(self.input, "os_variant") else getattr(self.input, "os_variant")
        self.os_distro = "" if not hasattr(self.input, "os_distro") else getattr(self.input, "os_distro")

    def create_from_cache(self):
        self.status = self.input["status"]
        self.name = self.input["name"]
        self.os_distro = self.input["os_distro"]
        self.major_version = getattr(self.input, "major_version", '')
        self.os_variant = self.input["os_variant"]
        self.os_type = self.input["os_type"]

    def get_value(self, value):
        return self.__getattribute__(value)

    def to_dict(self):
        return { "name": self.name.encode('utf-8'),
                 "status": self.status.encode('utf-8'),
                 "major_version:": self.major_version.encode('utf-8'),
                 "os_type": self.os_type.encode('utf-8'),
                 "os_variant": self.os_variant.encode('utf-8'),
                 "os_distro": self.os_distro.encode('utf-8')
                 }

class Images(object):
    def __init__(self, input_images):
        self.input_images = input_images
        self.image_list = []

    def create(self):
        for i in self.input_images:
            _tmp = OS_Distros(i)
            if isinstance(i, Munch):
                _tmp.create_from_openstack()
            else:
                _tmp.create_from_cache()

            self.image_list.append(_tmp)

    def dump(self, value_to_dump=None):
        for i in self.image_list:
            if not value_to_dump:
                print(vars(i))
            else:
                print(i.get_value(value_to_dump))

    def sort_by(self, value):
        newlist = sorted([x for x in self.image_list if x.os_type == "linux"], key=lambda k: k.name)
        return newlist

    def to_json(self):
        my_list = []
        for i in self.image_list:
            if i.os_type == 'linux':
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
    if not os.path.exists(IMAGE_FILE):
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
