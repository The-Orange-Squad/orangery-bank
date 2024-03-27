import json
import os

basexpreq = 100
basexpreqmod = 1.5  # only applied at lvl 2+

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

    def save(self):
        with open(f"data/users/{self.id}.json", "w") as f:
            json.dump(self.__dict__, f)
    


    def load(self, id, returner=False):
        self.id = id
        filename = f"data/users/{id}.json"
        if os.path.exists(filename):
            with open(filename, "r") as f:
                data = json.load(f)
                self.balance = data.get("balance", 0)
                self.inventory = data.get("inventory", {})
                self.msgc = data.get("msgc", 0)
                self.banned = data.get("banned", False)
                self.pos = data.get("pos", "norm")
                self.lvl = data.get("lvl", 0)
                self.xp = data.get("xp", 0)
                self.altids = data.get("altids", [])
                if returner:
                    return self
                return False
        else:
            if returner:
                return self
            return False

    def exists(self, id):
        filename = f"data/users/{id}.json"
        return os.path.exists(filename)

    def ban(self):
        self.banned = True
        self.save()

    def give_xp(self, amount):
        self.xp += amount
        # if lvl 0 -> 1, don't apply the mod
        if self.lvl == 0 and self.xp >= basexpreq:
            self.lvl += 1
            self.save()
            return "newlvl"
        elif self.lvl > 0 and self.xp >= basexpreq * (basexpreqmod ** self.lvl):
            self.lvl += 1
            self.save()
            return "newlvl"
        

    def set_alt(self, id):
        self.altids.append(id)
        self.save()
    
    def remove_alt(self, id):
        self.altids.remove(id)
        self.save()

    def isaltof(self, id):
        return id in self.altids

    def syncwith(self, id_):
        targetdata = self.load(id_, True)
        mydata = self.__dict__

        for key in targetdata.__dict__:
            mydata[key] = targetdata.__dict__[key]

        self.save()
    
    def erase(self):
        os.remove(f"data/users/{self.id}.json")
        return True
    
    def edit_money(self, amount):
        self.balance += amount
        self.save()
    
    def add_item(self, item, amount):
        if item in self.inventory:
            self.inventory[item] += amount
        else:
            self.inventory[item] = amount
        self.save()
    
    def remove_item(self, item, amount):
        if item in self.inventory:
            self.inventory[item] -= amount
            if self.inventory[item] <= 0:
                del self.inventory[item]
        self.save()
    
    def 
