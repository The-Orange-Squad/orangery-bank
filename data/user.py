import json
import os

basexpreq = 100
basexpreqmod = 1.5 # only applied at lvl 2+

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
        self.altids = []
    
    def exists(self, id):
        with open(f"data/users/basehandler.json", "r") as f:
            data = json.load(f)
            return str(id) in data

    def save(self):
        with open(f"data/users/basehandler.json", "w") as f:
            json.dump(self.__dict__, f)
    
    def load(self, id, returner=False):
        with open(f"data/users/basehandler.json", "r") as f:
            data = json.load(f)
            self.id = id
            conv = {}
            # to int
            for key in data:
                conv[key] = int(data[key])
            
            data = conv

            try:
                if returner:
                    causeerror = 1 / 0
                self.balance = data[id]["balance"]
                self.inventory = data[id]["inventory"]
                self.msgc = data[id]["msgc"]
                self.banned = data[id]["banned"]
                self.pos = data[id]["pos"]
                self.lvl = data[id]["lvl"]
                self.xp = data[id]["xp"]
                self.altids = data[id]["altids"]
            except:
                pass
            
            if returner:
                return self
            
            return False
    
    def ban(self):
        self.banned = True
        self.save()
    
    def give_xp(self, amount):
        self.xp += amount
        # if lvl 0 -> 1, don't apply the mod
        if self.lvl == 0 and self.xp >= basexpreq:
            self.lvl += 1
        elif self.lvl > 0 and self.xp >= basexpreq * (basexpreqmod ** self.lvl):
            self.lvl += 1
        self.save()
    
    def set_alt(self, id):
        self.altids.append(id)
        self.save()
    
    def isaltof(self, id):
        return id in self.altids
    
    def syncwith(self, id_):
        targetdata = self.load(id_, True)
        mydata = self.__dict__

        for key in targetdata.__dict__:
            mydata[key] = targetdata.__dict__[key]
        