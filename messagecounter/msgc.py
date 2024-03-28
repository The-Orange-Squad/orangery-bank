import json
import os
import time

class LastMessage:
    def __init__(self):
        self.lastmsgtime = {}
    
    def set_lastmsgtime(self, userid, guildid):
        if not userid in self.lastmsgtime:
            self.lastmsgtime[userid] = {}
        self.lastmsgtime[userid][guildid] = time.time()
        self.save()
    
    def is_passed(self, userid, time_, guildid):
        if not userid in self.lastmsgtime:
            self.lastmsgtime[userid][guildid] = 0
            return False
        return time.time() - self.lastmsgtime[userid][guildid] > time_
    
    def get_lastmsgtime(self, userid, guildid):
        if not userid in self.lastmsgtime:
            self.lastmsgtime[userid][guildid] = 0
        return self.lastmsgtime[userid][guildid]

    def save(self):
        with open("data/lastmsg.json", "w") as f:
            json.dump(self.lastmsgtime, f)
    
    def load(self):
        if os.path.exists("data/lastmsg.json"):
            with open("data/lastmsg.json", "r") as f:
                self.lastmsgtime = json.load(f)
                temp = {}
                for key in self.lastmsgtime:
                    temp[int(key)] = self.lastmsgtime[key]
                self.lastmsgtime = temp
                # For all users, convert their children keys to int
                temp = {}
                for key in self.lastmsgtime:
                    temp[key] = {}
                    for key2 in self.lastmsgtime[key]:
                        temp[key][int(key2)] = self.lastmsgtime[key][key2]
                
                self.lastmsgtime = temp
        else:
            self.save()