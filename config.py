import json


class ConfigMananger():
    def __init__(self,path):
        self.path = path
        self.root = {}
        self.load()

    def load(self):
        try:
            with open(self.path,"r") as f:
                json_data = f.read()
                self.root = json.loads(json_data)
        except FileNotFoundError:
            self.save()

    def save(self):
        with open(self.path,"w") as f:
            json_data = self.to_json()
            f.write(json_data)


    def create(self,key_path,default=None):
        key_path = key_path.split(".")
        current = self.root
        for key in key_path[:-1]:
            try:
                current = current[key]
            except KeyError:
                current[key] = {}
                current = current[key]
        try:
            current = current[key_path[-1]]
        except KeyError:
            current[key_path[-1]] = default

    def get(self,key_path):
        key_path = key_path.split(".")
        current = self.root
        for key in key_path[:-1]:
            current = current[key]
        return current[key_path[-1]]

    def set(self,key_path,value):
        key_path = key_path.split(".")
        current = self.root
        for key in key_path[:-1]:
            current = current[key]
        current[key_path[-1]] = value
        self.save()

    def to_json(self):
        return json.dumps(self.root,sort_keys=True, indent=4)