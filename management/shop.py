



class Shop:
    def __init__(self):
        self.items = {
            "🍎 Apple": {
                "price": 10,
                "desc": "A juicy red apple. Ahh, classic."
            },
            "🍌 Banana": {
                "price": 15,
                "desc": "A ripe yellow banana. Don't slip!"
            },
            "🍊 Orange": {
                "price": 20,
                "desc": "A sweet orange. No, The Orange Squad is not named after this."
            },
            "🍇 Grape": {
                "price": 18,
                "desc": "A bunch of grapes. They're not sour, don't worry."
            },
            "🍉 Watermelon": {
                "price": 25,
                "desc": "A big watermelon. It's heavy!"
            },
            "🍓 Strawberry": {
                "price": 12,
                "desc": "A red strawberry. Often used in desserts, and for a reason."
            },
            "🍑 Peach": {
                "price": 22,
                "desc": "A soft peach. Fuzzy thing!"
            },
            "🎁 Gift Box": {
                "price": 400,
                "desc": "A gift box that contains a random item (literally).",
                "funcstr": "open_giftbox(ctx)"
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
    
    def pair(self, processed):
        # find the item of the same id in the raw dict
        if processed in self.processed:
            # get the id of the item in the processed dict
            id = list(self.processed.keys()).index(processed)
            # get the item in the raw dict
            return list(self.items.keys())[id]