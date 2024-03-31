import json
import os


class GuildSetup:
    def __init__(self):
        self.settings = {
            "modrole": "undefined",
            "adminrole": "undefined",
            "ignorechannel": [],
        }
    
    def save(self, guildid):
        with open(f"data/guilds/{guildid}.json", "w") as f:
            json.dump(self.settings, f)
    
    def load(self, guildid):
        filename = f"data/guilds/{guildid}.json"
        if os.path.exists(filename):
            with open(filename, "r") as f:
                self.settings = json.load(f)
                return self.settings
        else:
            self.save(guildid)
            return self.settings
    
    def set(self, guildid, key, value):
        self.settings[key] = value
        self.save(guildid)
    
    def set_ic(self, guildid, channelid):
        if "ignorechannel" not in self.settings:
            self.settings["ignorechannel"] = []
        if channelid not in self.settings["ignorechannel"]:
            self.settings["ignorechannel"].append(channelid)
            self.save(guildid)
        
    def rem_ic(self, guildid, channelid):
        if "ignorechannel" in self.settings and channelid in self.settings["ignorechannel"]:
            self.settings["ignorechannel"].remove(channelid)
            self.save(guildid)
    
    def is_ic(self, channelid):
        if "ignorechannel" in self.settings and channelid in self.settings["ignorechannel"]:
            return True
        return False