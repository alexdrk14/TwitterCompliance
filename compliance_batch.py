import time, os, requests, json, random, sys

from mongo_connector import MongoLoader
from dateutil.parser import parse
from datetime import datetime
from os.path import isfile, join
from os import listdir
from collections import defaultdict
#---------------------------------------------------------------------------------------#
#import config file (change configfile_example.py to configfile.py with your config data)
#---------------------------------------------------------------------------------------#
#sys.path.insert(1, '../')
import configfile as cnf

class TwCompliance:

    def __init__ (self, loading_from_file=None, loading_from_mongo=False):
      
        if cnf.COMPLIANCE["folder_path"]  is None:
            raise Exception("Compliance: folder path is None")
        if cnf.COMPLIANCE["bearer_token"] is None:
            raise Exception("Compliance: bearer_token is None")
        if cnf.COMPLIANCE["job_name"] is None:
            raise Exception("Compliance: job name is None")

        self.object_name = cnf.COMPLIANCE["folder_path"]+cnf.COMPLIANCE["object_name"]
        self.PATH = cnf.COMPLIANCE["folder_path"]
        self.setup = cnf.DBCONFIG 
        self.data = cnf.COMPLIANCE["folder_path"] + "collected_ids.txt"
        self.bearer_token = cnf.COMPLIANCE["bearer_token"]

        self.compliance_job_url = "https://api.twitter.com/2/compliance/jobs"
        if os.path.isfile(self.object_name):
            self.object = json.loads(open(self.object_name, "r").read())
        else:
            self.object = defaultdict(lambda: None)
        self.users = None
        if loading_from_mongo:
           user_loader = MongoLoader()
           self.users = user_loader.get_user_ids()
        elif not loading_from_file is None:
           pass

    # For User Compliance Job, replace the type value with users instead of tweets
    # Also replace the name value with your desired job name
    #type may be tweets for defined user tweet ids and users for defined user ids 

    ###############################
    #Create compliance job
    ##############################
    def bearer_oauth(self, r):
        """ 
        Method required by bearer token authentication.
        """
        r.headers["Authorization"] = f"Bearer {self.bearer_token}"
        r.headers["User-Agent"] = "v2BatchCompliancePython"
        return r


    ##########################
    #Connect to endpoint
    ##########################
    def connect_to_endpoint(self, url, params=None, auth=None, headers=None):
        if params!= None:
            #connect in order to create compliance job
            response = requests.request("POST", url, auth=auth, json=params)
        elif headers!= None:
            #create in order to upload data
            response = requests.put(url, data=open(self.data, 'rb'), headers=headers)
        elif auth != None:
            #connect for job status
            response = requests.request("GET", url, auth=auth)
        else:
            #connect for result download
            response = requests.request("GET", url)
        print(response.status_code)
        if response.status_code != 200:
            raise Exception(response.status_code, response.text)
        if params == None  and auth == None:
            return response.text
        return response.json()

    ##########################
    #Create compliance job
    ##########################
    def CreateCompl(self):
        json_response = self.connect_to_endpoint(self.compliance_job_url, auth=self.bearer_oauth, params={"type": "users", "name": cnf.COMPLIANCE["job_name"]})
        #json_response["token"] = self.bearer_token
        f_out = open(self.object_name,"w+")
        f_out.write("{}".format(json.dumps(json_response, indent=4, sort_keys=True)))
        f_out.close()
        self.object = json_response

    ##########################
    #Upload data
    ##########################
    def UploadData(self):
        upload_url = self.object["data"]["upload_url"]
        response = self.connect_to_endpoint(upload_url, headers = {'Content-Type': "text/plain"})
        print(response)

    ############################
    #Get status
    ############################
    def GetStatus(self):
        job_id = self.object["data"]["id"]
        compliance_job_url = f"https://api.twitter.com/2/compliance/jobs/{job_id}".format(job_id)
        try:
            new_object = self.connect_to_endpoint(compliance_job_url, auth=self.bearer_oauth)
        except Exception as e:
            print("Error:{}".format(e))
            sys.exit(-1)
        if new_object["data"]["status"] != self.object["data"]["status"]:
            f_out = open(self.object_name,"w+")
            f_out.write("{}".format(json.dumps(new_object, indent=4, sort_keys=True)))
            f_out.close()
            self.object = new_object
        
    ##############################
    #Download
    ##############################
    def DownloadRes(self, date=""):
        #object_c = json.loads(open(PATH + object_name, "r").read())
        download_url = self.object["data"]["download_url"]
        response = self.connect_to_endpoint(download_url)
        entries = response.splitlines()
        outfile = "compliance_results_{}.txt".format(date).replace(" ","_")
        f_out = open(self.PATH + outfile ,"w+")
        for entry in entries:
            f_out.write("{}\n".format(entry))
        f_out.close()


    ##############################
    #Collect user ids from MongoDB
    ##############################
    def collect_users(self):
        client, db, collection = self.connect_to_db()
        collection_users = db["users"]
        for item in collection_users.find({},{"id": 1 }):
            self.users.add(item["id"])
        client.close()

    def remove_suspend(self):
        known = set()
        filenames = [isfile(join(self.PATH, f)) for f in listdir(self.PATH) if isfile(join(self.PATH, f)) and "compliance_results_" in f]
        for filename in filenames:
            data = [line for line in open(filename, "r").read().split("\n") if "suspend" in line]
            for line in data:
                line = ast.literal_eval(line)
                known.add(int(line["id"]))
        print("All: {} known suspend:{}".format(len(self.users), len(known)))
        self.users = self.users - known 
        print("After filtering:{}".format(len(self.users)))


    def connect_to_db(self):
        #connect to mongo db collection
        client = MongoClient(self.setup["address"], self.setup["port"])
        db = client[self.setup["db"]]
        collection = db[self.setup["collection"]]
        return client, db, collection


    def main(self):
        date = datetime.now()
        if not os.path.isfile(self.object_name):
            self.collect_users()
            
            f_out = open(self.data,"w+")
            for user in self.users:
                f_out.write("{}\n".format(user))
            f_out.close()
            print("\t with {} users".format(len(self.users)))
            date = datetime.now()
            self.CreateCompl()
            self.UploadData()
        while True:
            self.GetStatus()
            if self.object["data"]["status"] == "complete":
                break
            elif self.object["data"]["status"] == "failed":
                print("Job failed")
                sys.exit(-1)
            print("\tStatus:{}".format(self.object["data"]["status"]))
            time.sleep(60*15)

        self.DownloadRes(date=date)
        os.remove(self.object_name) 
        os.remove(self.data)
        print("\tFinished at {}".format(datetime.now()))
   
def main():
    comp = TwCompliance()
    comp.main()

if __name__ == "__main__":
    print("New execution: {}".format(datetime.now()))
    main()
