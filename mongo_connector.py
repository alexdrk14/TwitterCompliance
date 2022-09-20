from pymongo import MongoClient
import configfile as config

class MongoLoader:

    def __init__ (self):
        self.db = None
        self.client = None
        self.collection = None
        self.uids = set()
        if config.DBCONFIG["address"] is None:
            raise Exception("MongoLoader: Configuration file has 'None' value for server IP address.")
        if config.DBCONFIG["port"] is  None:
            raise Exception("MongoLoader: Configuration file has 'None' value for server port number.")
        if config.DBCONFIG["db"] is None:
            raise Exception("MongoLoader: Configuration file has 'None' value for server database name.")
        if config.DBCONFIG["collection"] is None:
            raise Exception("MongoLoader: Configuration file has 'None' value for server collection name")

    ##############################
    #Collect user ids from MongoDB
    ##############################
    def get_user_ids(self):
        self._connect_to_db_()
        item = self.collection.find_one({})
        if "user" in item and "id" in item["user"]:
            #collection is raw json file collected from twitter with text and another fields
            self._collect_from_raw_()
        elif "id" in item and "screen_name" in item:
            #collection is consist only from user object
            self._collect_from_usercollection_()
        else:
            raise Exception("Mongo Loader can't find user object in provided Collection.")
        self._disconnect_from_db_()
        return_object = list(self.uids)
        self.uids = set()
        return return_object

    def _get_user_id_(self, u_object):
        if "user" in u_object and "id" in u_object["user"]:
            self.uids.add(int(u_object["user"]["id"]))
        if "retweeted_status" in u_object:
            self._get_user_id_(u_object["retweeted_status"])
        if "quoted_status" in u_object:
            self._get_user_id_(u_object["quoted_status"])

    def _collect_from_raw_(self):
        for item in self.collection.find({}, no_cursor_timeout=True):
            self._get_user_id_(item)

    def _collect_from_usercollection_(self):
        for item in self.collection.find({},{"_id": 0, "id": 1 },  no_cursor_timeout=True):
            self.uids.add(int(item["id"]))


    ##############################
    #Connect to MongoDB
    ##############################
    def _connect_to_db_(self):
        #connect to mongo db collection
        self._disconnect_from_db_()
        self.client = MongoClient(config.DBCONFIG["address"], config.DBCONFIG["port"])
        self.db = self.client[config.DBCONFIG["db"]]
        self.collection = self.db[config.DBCONFIG["collection"]]
        
    
    ##############################
    #Disconnect from mongo DB
    ##############################
    def _disconnect_from_db_(self):
        if self.client != None:
            self.client.close()
            self.client = None
            


