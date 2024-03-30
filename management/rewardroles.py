import json
import os

class RewardRoles:
    def __init__(self):
        self.roles = {}
        
    def load(self):
        if os.path.exists("data/rewardroles.json"):
            with open("data/rewardroles.json", "r") as f:
                self.roles = json.load(f)
                temp = {}
                for key, value in self.roles.items():
                    temp[int(key)] = value
                self.roles = temp
                # Also convert the keys of the children to int
                temp = {}
                for key in self.roles:
                    temp[key] = {}
                    for key2 in self.roles[key]:
                        temp[key][int(key2)] = self.roles[key][key2]

                self.roles = temp
        else:
            self.roles = {}
    
    def save(self):
        with open("data/rewardroles.json", "w") as f:
            json.dump(self.roles, f)
    
    def init(self, guild):
        if guild not in self.roles:
            self.roles[guild] = {}
            self.save()

    def add(self, level, role, guild):
        if guild not in self.roles:
            self.roles[guild] = {}
        self.roles[guild][level] = role
        self.save()
    
    def remove(self, level, guild):
        if guild not in self.roles:
            self.roles[guild] = {}
            return False
        del self.roles[guild][level]
        self.save()
    
    def get(self, level, guild):
        if guild not in self.roles:
            return False
        return self.roles[guild][level]
    
    def hasreward(self, level, guild):
        if guild not in self.roles:
            self.roles[guild] = {}
        return level in self.roles[guild]