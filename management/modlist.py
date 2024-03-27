import json
import os


class GuildSetup:
    def __init__(self):
        self.settings = {
            "modrole": "undefined",
            "adminrole": "undefined"
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