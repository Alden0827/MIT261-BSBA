import matplotlib.pyplot as plt
from pymongo import MongoClient
from collections import defaultdict
import numpy as np
from functools import wraps
import os
import pandas as pd
import hashlib
import pickle
import time
from functools import wraps

print('Connecting to db..')
# ------------------------------
# MongoDB Connection
# ------------------------------
uri = "mongodb+srv://aldenroxy:N53wxkFIvbAJjZjc@cluster0.l7fdbmf.mongodb.net/mit261"
# client = MongoClient(uri)

# ------------------------------
# Mongodb timeout
# ------------------------------
client = MongoClient(
    uri,
    serverSelectionTimeoutMS=30000,  # 5 seconds for server selection
    connectTimeoutMS=30000,          # 5 seconds to establish connection
    socketTimeoutMS=30000           # 10 seconds for queries
)

db = client["mit261"]

programs = list(db.curriculum.find({}, {'programCode': 1, '_id': 0}))

# To get a list of just the program codes
program_codes_list = [p['programCode'] for p in programs]

# Now, printing this list will give you the desired output
print(program_codes_list)
