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
        else:
            self.roles = {}
    
    def save(self):
        with open("data/rewardroles.json", "w") as f:
            json.dump(self.roles, f)

    def add(self, level, role, guild):
        self.roles[guild][level] = role
        self.save()
    
    def remove(self, level, guild):
        del self.roles[guild][level]
        self.save()
    
    def get(self, level, guild):
        return self.roles[guild][level]
    
    def hasreward(self, level, guild):
        return level in self.roles[guild]