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
            }
        }
        self.processed = {}

        def process():
            # this removes the first two characters of the key, which is the emoji and a space
            for item in self.items:
                self.processed[item[2:]] = self.items[item]
        
        def process_single(item):
            return item[2:]
        
        def is_valid_item(item):
            return item in self.processed
        
        def get_price(item):
            return self.processed[item]["price"]
        
        def get_desc(item):
            return self.processed[item]["desc"]
        
        def get_processed():
            return self.processed
    
        def get_raw():
            return self.items