import json
import os

class User:
    def __init__(self):
        self.id = "undefined"
        self.balance = 0
        self.inventory = {}
        self.msgc = 0
        self.banned = False
        self.pos = "norm"
        self.lvl = 0
        self.xp = 0

    def save(self):
        with open(f"data/users/basehandler.json", "w") as f:
            json.dump(self.__dict__, f)
    
    def load(self, id):
        with open(f"data/users/basehandler.json", "r") as f:
            data = json.load(f)
            self.id = id
            conv = {}
            # to int
            for key in data:
                conv[key] = int(data[key])
            
            data = conv

            try:
                self.balance = data[id]["balance"]
                self.inventory = data[id]["inventory"]
                self.msgc = data[id]["msgc"]
                self.banned = data[id]["banned"]
                self.pos = data[id]["pos"]
                self.lvl = data[id]["lvl"]
                self.xp = data[id]["xp"]
            except:
                return False
            
            return True
    
    def ban(self):
        self.banned = True
        self.save()
    
    def give_xp(self, amount):
        self.xp += amount
        self.save()