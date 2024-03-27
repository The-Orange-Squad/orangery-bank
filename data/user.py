import json
import os

basexpreq = 100
basexpreqmod = 1.5  # only applied at lvl 2+

class User:
    def __init__(self):
        self.id = "undefined"
        self.balance = {}
        self.inventory = {}
        self.msgc = {}
        self.banned = False
        self.pos = "norm"
        self.lvl = {}
        self.xp = {}

    def save(self):
        with open(f"data/users/{self.id}.json", "w") as f:
            json.dump(self.__dict__, f)
    
    def savefor(self, id, adv=False):
        with open(f"data/users/{id}.json", "w") as f:
            data = self.__dict__
            if adv:
                data.id = id
            json.dump(data, f)
    
    def load(self, id, returner=False):
        self.id = id
        filename = f"data/users/{id}.json"
        if os.path.exists(filename):
            with open(filename, "r") as f:
                data = json.load(f)
                self.balance = data.get("balance", {})
                self.inventory = data.get("inventory", {})
                self.msgc = data.get("msgc", {})
                self.banned = data.get("banned", False)
                self.pos = data.get("pos", "norm")
                self.lvl = data.get("lvl", {})
                self.xp = data.get("xp", {})
                if returner:
                    return self
                return False
        else:
            self.save()
            if returner:
                return self
            return False

    def exists(self, id):
        filename = f"data/users/{id}.json"
        return os.path.exists(filename)

    def ban(self):
        self.banned = True
        self.save()

    def give_xp(self, amount, guildid):
        self.xp[guildid] += amount
        # if lvl 0 -> 1, don't apply the mod
        if self.lvl[guildid] == 0 and self.xp[guildid] >= basexpreq:
            self.lvl[guildid] += 1
            self.save()
            return "newlvl"
        elif self.lvl[guildid] > 0 and self.xp[guildid] >= basexpreq * (basexpreqmod ** self.lvl[guildid]):
            self.lvl[guildid] += 1
            self.save()
            return "newlvl"

    def syncwith(self, id_):
        self.savefor(id_, True)
        return True
    
    def erase(self):
        os.remove(f"data/users/{self.id}.json")
        return True
    
    def edit_money(self, amount, guildid):
        self.balance[guildid] += amount
        self.save()
    
    def add_item(self, item, amount, guildid):
        if item in self.inventory[guildid]:
            self.inventory[guildid][item] += amount
        else:
            self.inventory[guildid][item] = amount
        self.save()
    
    def remove_item(self, item, amount, guildid):
        if item in self.inventory:
            self.inventory[guildid][item] -= amount
            if self.inventory[guildid][item] <= 0:
                del self.inventory[guildid][item]
        self.save()

    def unload(self):
        self.__init__()
        return True