from dotenv import load_dotenv
import os
from management.shop import Shop
from data.user import User

shop = Shop()
shop.process()

print(shop.get_processed())

load_dotenv()

TOKEN = os.getenv("TOKEN")