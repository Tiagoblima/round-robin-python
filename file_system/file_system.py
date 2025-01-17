import argparse
import datetime
import json
import math
import random
import time
from io_system.io_system import System
from io_system.io_system import MIN_BLOCK, MAX_BLOCK
from security.security import cryptography, MAX_SIZE
from security.security import break_code

io = System()


def name_exists(dir_, element_info):
    for element in dir_:
        print(element)
        if dir_[element]["name"] == element_info["name"]:
            return True
    return False


class Block:
    CAPACITY = 10  # KB

    def __init__(self, id_):
        self.id = id_

        self.size = self.CAPACITY
        self.available = True

    def is_available(self):
        return self.available

    def fragmentation_status(self):
        print()
        print(f"BLOCK-{self.id} FRAGMENTATION STATUS", end='')
        print('-' * 20)
        if self.size > 0:
            print("\tInternal Fragmentation")
            print(f"\tMemory Available Now: {self.size}MBs")
        else:
            print("\tNo Internal Fragmentation")
            print(f"\tMemory Available Now: {self.size}MBs")
        print("END FRAGMENTATION STATUS", end='')
        print('-' * 20)
        print()

    def push_item(self, space_required):
        remaining_size = 0
        if space_required >= self.size:
            remaining_size = space_required - self.size  # Alocando arquivo no bloco
            self.size = 0
            self.available = False

        elif space_required < self.size:
            self.size -= space_required

        self.fragmentation_status()
        return remaining_size

    def block_status(self):
        return self.id, f"Availability {(self.size / self.CAPACITY) * 100}%"

    def block_info(self):
        return {"block_id": self.id, "space_available": self.size}


class FileSystem:
    TOTAL_CAPACITY = 100000  # MB
    ROOT_DIR = 'usr'

    def __init__(self):
        self.memory = []

        self.disk_1 = json.load(open("disk_1_status.json"))
        self.current_dir = self.ROOT_DIR
        self.existing_names = []
        search_dir = self.disk_1

        for key in self.disk_1.keys():
            self.existing_names.append(key)
            search_dir = search_dir[key]["archives"]
            for key2 in search_dir.keys():
                self.existing_names.append(key2)
        print(self.existing_names)

    def set_blocks(self, element_info):
        element_info["block"] = []

        space_required = element_info["size"]
        for elem in range(math.ceil(element_info["size"] / Block.CAPACITY)):

            # Evita mesmo id de bloco
            block_id = random.randint(MIN_BLOCK, MAX_BLOCK)
            while block_id in self.memory:
                block_id = random.randint(MIN_BLOCK, MAX_BLOCK)

            block = Block(block_id)
            space_required = block.push_item(space_required)
            element_info["block"].append(block.block_info())

            self.memory.append(block_id)

        return element_info

    def allocate(self, path_to_element, element_info):

        is_dir = element_info["is_dir"]
        path = path_to_element.split('/')

        if len(path) == 1:
            path = ['usr', path[0]]

        element_info = self.set_blocks(element_info)

        if element_info["name"] in self.existing_names:
            raise Warning("Name already exists file or director not created!")
        if len(path) == 1:
            self.disk_1[self.current_dir][path[0]] = element_info
        # usr/sys/

        elif not is_dir:

            search_dir = self.disk_1
            for i, path_part in enumerate(path):

                if i == len(path) - 2:  # Achou diretório final
                    inode = element_info["name"]
                    search_dir[path_part]["archives"][inode] = element_info
                    break
                else:
                    search_dir = search_dir[path_part]["archives"]

            search_dir = self.disk_1
            time.sleep(3)
            for part_path in path[:-1]:
                search_dir[part_path]["size"] += element_info["size"]
                search_dir = search_dir[part_path]["archives"]

        else:
            element_info["archives"] = {}
            search_dir = self.disk_1

            for i, path_part in enumerate(path):

                if i == len(path) - 2:
                    print(path_part)
                    search_dir[path_part]["archives"] = {path[-1]: element_info}
                    break
                else:
                    search_dir = search_dir[path_part]["archives"]

    def delete(self, archive_path):

        try:
            path = archive_path.split('/')
            if len(path) == 1:
                path = ['usr', path[0]]

            search_dir = self.disk_1

            for i, path_part in enumerate(path):
                if i == len(path) - 1:
                    break
                else:
                    search_dir = search_dir[path_part]["archives"]

            if search_dir[path[-1]]["secure"]:

                code = search_dir[path[-1]]["user_password"]

                password_attempt = input('Insert password: ')
                while not cryptography(password_attempt) == code:
                    print("Senha incorreta!")
                    password_attempt = input('Insert password: ')

            element_info = search_dir[path[-1]]
            search_dir.pop(path[-1])
            search_dir = self.disk_1
            for part_path in path[:-1]:
                search_dir[part_path]["size"] -= element_info["size"]
                search_dir = search_dir[part_path]["archives"]

            if element_info["is_dir"]:
                print("Folder deleted!")
            else:
                print("File deleted!")

            return search_dir
        except KeyError:
            print("File or Dir does not exists!")

    def get_file(self, file_path):

        path = file_path.split('/')

        if len(path) == 1:
            path = ['usr', path[0]]

        search_dir = self.disk_1
        for i, path_part in enumerate(path):
            if i == len(path) - 1:
                search_dir = search_dir[path_part]
            else:
                search_dir = search_dir[path_part]["archives"]
        if search_dir["secure"]:

            code = search_dir["user_password"]
            password_attempt = input('Insert password: ')
            while not cryptography(password_attempt) == code:
                print("Senha incorreta!")
                password_attempt = input('Insert password: ')

            block_list = [block["block_id"] for block in search_dir["block"]]
            io.seek_blocks(block_list)

        return search_dir

    def show_allocation(self):

        print("#" * 20, end='')
        print("Allocation", end='')
        print("#" * 20)

        your_json = json.dumps(self.disk_1)

        parsed = json.loads(your_json)
        print(json.dumps(parsed, indent=4, sort_keys=True))

    def list_dir(self, dir_):
        path = dir_.split('/')

        search_dir = self.disk_1
        for i, path_part in enumerate(path):
            search_dir = search_dir[path_part]["archives"]

        your_json = json.dumps(search_dir)
        parsed = json.loads(your_json)
        print(json.dumps(parsed, indent=4, sort_keys=True))

    def show_status(self):

        print(f"Consumed capacity: {self.disk_1['usr']['size'] / self.TOTAL_CAPACITY}%")

    def save_status(self):
        your_json = json.dumps(self.disk_1)
        parsed = json.loads(your_json)
        print("Saving on the Main Disk")
        json.dump(parsed, open("disk_1_status.json", "w", encoding="utf-8"), indent=4, sort_keys=True)
        print("RAID 1: Saving on backup")
        json.dump(parsed, open("disk_2_status.json", "w", encoding="utf-8"), indent=4, sort_keys=True)


parser = argparse.ArgumentParser()
parser.add_argument('--path', type=str, required=True, help="The path to the file or folder.")

parser.add_argument('--list_dir', action="store_true", required=False, help="Option to list the dir.")

parser.add_argument('--get_file', action="store_true", required=False, help="Option to list the dir.")

parser.add_argument('--password', type=str, default=None, required=False, help="Chose use"
                                                                               "password to secure the dir or file")
parser.add_argument('--is_folder', action="store_true")

parser.add_argument('--delete', action="store_true")
# Default size of a folder is 10
parser.add_argument('--size', type=int, default=10, help="The size of"
                                                         "the file is required"
                                                         "when you want to allocate a file ")
args = parser.parse_args()


def demo():
    file_sys = FileSystem()
    file_sys.show_allocation()
    file_sys.allocate("usr/sys/myfile.txt", {"name": "myfile.txt", "size": 10})
    file_sys.allocate("usr/sys/myfile1.txt", {"name": "myfile1.txt", "size": 25})
    file_sys.show_allocation()
    file_sys.allocate("usr/myfile", {"name": "myfile", "size": 10, "archives": {}})
    file_sys.show_allocation()
    file_sys.show_status()
    file_sys.save_status()


def main():
    file_sys = FileSystem()
    # file_sys.show_allocation()

    if args.list_dir:
        file_sys.list_dir(args.path)

    elif args.get_file:
        file = file_sys.get_file(args.path)
        your_json = json.dumps(file)
        parsed = json.loads(your_json)
        print(json.dumps(parsed, indent=4, sort_keys=True))
    elif args.delete:
        file_sys.delete(args.path)
        file_sys.show_allocation()
        file_sys.show_status()
        file_sys.save_status()
    else:
        now = datetime.datetime.now()

        # dd/mm/YY H:M:S
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        name = args.path.split('/')[-1]

        has_password = False
        if args.password:
            has_password = True
            user_password = args.password

            assert len(user_password) <= MAX_SIZE, f"Password must have max size of {MAX_SIZE}"
        else:
            user_password = ""

        element_info = {"name": name,
                        "size": args.size,
                        "secure": has_password,
                        "user_password": cryptography(user_password),
                        "time_stamp": dt_string,
                        "is_dir": args.is_folder}

        file_sys.allocate(args.path,
                          element_info
                          )

        file_sys.show_allocation()
        file_sys.show_status()
        file_sys.save_status()


if __name__ == '__main__':
    main()
