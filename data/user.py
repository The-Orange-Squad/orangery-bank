import json
import os
import time

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
        self.modifiers = {}

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
                self.modifiers = data.get("modifiers", {})
                temp = {}
                # for all dicts, convert the keys to int
                for key in self.balance:
                    temp[int(key)] = self.balance[key]
                self.balance = temp
                temp = {}
                for key in self.inventory:
                    temp[int(key)] = self.inventory[key]
                self.inventory = temp
                temp = {}
                for key in self.msgc:
                    temp[int(key)] = self.msgc[key]
                self.msgc = temp
                temp = {}
                for key in self.lvl:
                    temp[int(key)] = self.lvl[key]
                self.lvl = temp
                temp = {}
                for key in self.xp:
                    temp[int(key)] = self.xp[key]
                self.xp = temp
                temp = {}
                for key in self.modifiers:
                    temp[int(key)] = self.modifiers[key]
                self.modifiers = temp
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

    def unban(self):
        self.banned = False
        self.save()

    def give_xp(self, amount, guildid):
        if not guildid in self.xp:
            self.xp[guildid] = 0
        if not guildid in self.lvl:
            self.lvl[guildid] = 0
        self.xp[guildid] += amount
        # if lvl 0 -> 1, don't apply the mod
        if self.lvl[guildid] == 0 and self.xp[guildid] >= basexpreq:
            self.lvl[guildid] += 1
            # Remove all user xp
            self.xp[guildid] = 0
            self.save()
            return "newlvl"
        elif self.lvl[guildid] > 0 and self.xp[guildid] >= basexpreq * (basexpreqmod ** self.lvl[guildid]):
            self.lvl[guildid] += 1
            # Remove all user xp
            self.xp[guildid] = 0
            self.save()
            return "newlvl"
        self.save()
        return False

    def syncwith(self, id_):
        self.savefor(id_, True)
        return True
    
    def erase(self, guildid=None):
        if guildid:
            del self.balance[guildid]
            del self.inventory[guildid]
            del self.msgc[guildid]
            del self.lvl[guildid]
            del self.xp[guildid]
        else:
            os.remove(f"data/users/{self.id}.json")
        return True
    
    def edit_money(self, amount, guildid):
        if not guildid in self.balance:
            self.balance[guildid] = 0
        self.balance[guildid] += amount
        if self.balance[guildid] < 0:
            self.balance[guildid] = 0
        self.save()
    
    def add_item(self, item, amount, guildid):
        if not guildid in self.inventory:
            self.inventory[guildid] = {}
        if item in self.inventory[guildid]:
            self.inventory[guildid][item] += amount
        else:
            self.inventory[guildid][item] = amount
        self.save()
    
    def remove_item(self, item, amount, guildid):
        if not guildid in self.inventory:
            self.inventory[guildid] = {}
        if item in self.inventory[guildid]:
            self.inventory[guildid][item] -= amount
            if self.inventory[guildid][item] <= 0:
                del self.inventory[guildid][item]
        self.save()

    def unload(self):
        self.__init__()
        return True
    
    def get_balance(self, guildid):
        if not guildid in self.balance:
            self.balance[guildid] = 0
        return self.balance[guildid]
    
    def get_inventory(self, guildid):
        if not guildid in self.inventory:
            self.inventory[guildid] = {}
        return self.inventory[guildid]
    
    def get_lvl(self, guildid):
        if not guildid in self.lvl:
            self.lvl[guildid] = 0
        return self.lvl[guildid]
    
    def get_xp(self, guildid):
        if not guildid in self.xp:
            self.xp[guildid] = 0
        return self.xp[guildid]
    
    def get_msgc(self, guildid):
        if not guildid in self.msgc:
            self.msgc[guildid] = 0
        return self.msgc[guildid]

    def set_mod(self, guildid, mod):
        self.modifiers[guildid] = mod
        self.save()
    
    def get_mod(self, guildid):
        if not guildid in self.modifiers:
            self.modifiers[guildid] = 1
        return self.modifiers[guildid]

    def give_msgc(self, guildid):
        if not guildid in self.msgc:
            self.msgc[guildid] = 0
        self.msgc[guildid] += 1
        self.save()
    
    def getxpreq(self, level):
        if level == 0:
            return basexpreq
        return basexpreq * (basexpreqmod ** level)
    
    def getmodifiers(self, guildid):
        if not guildid in self.modifiers:
            self.modifiers[guildid] = 1
        return self.modifiers[guildid]
    
    def refresh(self):
        self.load(self.id)
        return True

    def lose_xp(self, amount, guildid):
        # a tad bit complicated, as we'll also need to check if the user levels down
        if not guildid in self.xp:
            self.xp[guildid] = 0

        if not guildid in self.lvl:
            self.lvl[guildid] = 0
        
        self.xp[guildid] -= amount
        # if the user has negative xp, they'll level down
        while self.xp[guildid] < 0:
            if self.lvl[guildid] == 0:
                self.xp[guildid] = 0
                break
            self.lvl[guildid] -= 1
            self.xp[guildid] += self.getxpreq(self.lvl[guildid])
        
    def wipe(self, guildid):
        # not just reset, completely wipe the user's data
        del self.balance[guildid]
        del self.inventory[guildid]
        del self.msgc[guildid]
        del self.lvl[guildid]
        del self.xp[guildid]
        del self.modifiers[guildid]
        self.save()
    