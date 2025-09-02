
from pymongo.mongo_client import MongoClient

import os
MONGO_DB_URL = os.environ.get("MONGO_DB_URL", "mongodb://localhost:27017/")
uri = MONGO_DB_URL

# Create a new client and connect to the server
client = MongoClient(uri)

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)