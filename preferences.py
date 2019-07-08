from pymongo import MongoClient


class UserPreferences:

    def __init__(self):
        self.client = MongoClient("YOUR_MONGODB_CONNECTION_STRING")
        self.db = self.client["ex-rate-line-bot"]
        self.col = self.db["user_preferences"]

    def create(self, user_id, bank, ccy):
        user_preferences = {
            "_id": user_id,
            "bank": bank,
            "ccy": ccy
        }
        self.col.insert_one(user_preferences)

    def get(self, user_id):
        return self.col.find_one({"_id": user_id})

    def update(self, user_id, bank, ccy):
        user_preferences = {
            "_id": user_id,
            "bank": bank,
            "ccy": ccy
        }
        self.col.replace_one({"_id": user_id}, user_preferences)
