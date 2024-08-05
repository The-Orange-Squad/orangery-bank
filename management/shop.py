class Shop:
    def __init__(self):
        self.items = {
            "🍎 Apple": {
                "price": 10,
                "desc": "A juicy red apple. Ahh, classic.",
                "type": "food",
                "funcstr": "eat(ctx)"
            },
            "🍌 Banana": {
                "price": 15,
                "desc": "A ripe yellow banana. Don't slip!",
                "type": "food",
                "funcstr": "eat(ctx)"
            },
            "🍊 Orange": {
                "price": 20,
                "desc": "A sweet orange. No, The Orange Squad is not named after this.",
                "type": "food",
                "funcstr": "eat(ctx)"
            },
            "🍇 Grape": {
                "price": 18,
                "desc": "A bunch of grapes. They're not sour, don't worry.",
                "type": "food",
                "funcstr": "eat(ctx)"
            },
            "🍉 Watermelon": {
                "price": 25,
                "desc": "A big watermelon. It's heavy!",
                "type": "food",
                "funcstr": "eat(ctx)"
            },
            "🍓 Strawberry": {
                "price": 12,
                "desc": "A red strawberry. Often used in desserts, and for a reason.",
                "type": "food",
                "funcstr": "eat(ctx)"
            },
            "🍑 Peach": {
                "price": 22,
                "desc": "A soft peach. Fuzzy thing!",
                "type": "food",
                "funcstr": "eat(ctx)"
            },
            "🎁 Gift Box": {
                "price": 400,
                "desc": "A gift box that contains a random item (literally).",
                "type": "consumable",
                "funcstr": "open_giftbox(ctx)"
            },
            "📦 Mystery Box": {
                "price": 500,
                "desc": "A mystery box... The title says it all. What's inside?",
                "type": "consumable",
                "funcstr": "open_mbox(ctx)"
            },
            "📖 Book": {
                "price": 270,
                "desc": "The container of knowledge and wisdom. Gives you some XP.",
                "type": "consumable",
                "funcstr": "read_book(ctx)"
            },
            "🎣 Fishing Rod": {
                "price": 750,
                "desc": "A sturdy fishing rod. Try your luck at catching some fish!",
                "type": "tool",
                "funcstr": "go_fishing(ctx)"
            },
            "⛏️ Pickaxe": {
                "price": 1000,
                "desc": "A reliable pickaxe. Mine for valuable resources!",
                "type": "tool",
                "funcstr": "go_mining(ctx)"
            },
            "🌱 Magic Seeds": {
                "price": 300,
                "desc": "Mysterious seeds that grow into... something?",
                "type": "consumable",
                "funcstr": "plant_magic_seeds(ctx)"
            },
            "🔮 Crystal Ball": {
                "price": 1500,
                "desc": "A mystical crystal ball. Gaze into the future!",
                "type": "tool",
                "funcstr": "use_crystal_ball(ctx)"
            },
            "🧪 Alchemy Kit": {
                "price": 2000,
                "desc": "A set of tools for magical experiments. What will you create?",
                "type": "tool",
                "funcstr": "perform_alchemy(ctx)"
            },
            "🎭 Disguise Kit": {
                "price": 1200,
                "desc": "A kit full of props and makeup. Perfect for going undercover!",
                "type": "tool",
                "funcstr": "use_disguise_kit(ctx)"
            },
            "🎟️ Lucky Ticket": {
                "price": 1000,
                "desc": "A mysterious ticket. Will it bring you fortune?",
                "type": "consumable",
                "funcstr": "use_lucky_ticket(ctx)"
            }
        }
        self.processed = {}
    def process(self):
        # this removes the first two characters of the key, which is the emoji and a space
        for item in self.items:
            self.processed[item[2:]] = self.items[item]
    
    def process_single(self, item):
        return item[2:]
    
    def is_valid_item(self, item):
        return item in self.processed
    
    def get_price(self, item):
        return self.processed[item]["price"]
    
    def get_desc(self, item):
        return self.processed[item]["desc"]
    
    def get_processed(self):
        return self.processed

    def get_raw(self):
        return self.items

    def get_type(self, item):
        return self.processed[item]["type"]
    
    def pair(self, processed):
        # find the item of the same id in the raw dict
        if processed in self.processed:
            # get the id of the item in the processed dict
            id = list(self.processed.keys()).index(processed)
            # get the item in the raw dict
            return list(self.items.keys())[id]