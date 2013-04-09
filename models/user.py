import mongo

class User():
	@classmethod
	def create(cls, username, email, openid):
		data_explorer = mongo.get_mongo()
		data_explorer.users.update(
			{'username': username, 'openid': openid}, 
			{"$set": {'email': email}},
			upsert = True);
	
	@classmethod
	def get_by_openid(cls, openid):
		data_explorer = mongo.get_mongo()
		if data_explorer:
			return data_explorer.users.find_one({"openid": openid})

		return None