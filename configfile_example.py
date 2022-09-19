#!/usr/bin/env python

#Twittter API bearer token and path to store compliance results
COMPLIANCE={
            "object_name"  : "compliance_v2_object.txt", 
            "folder_path"  : None,                      # PATH to Location Of Store folder, like "/disk2/mountedDisk/my_storage_folder/" in string type
            "bearer_token" : None,                      #Your TwitterAPI BearerToken in string type
            "job_name"     : None                       #Name Of Your Compliance Job, like "My_first_compliance_job", in string type
           }
#mongo DB address/port and db/collection
DBCONFIG={
          "address"   : None,   #IP address of MongoDB, like '127.0.0.1' in string type
          "port"      : 27017,  #Port of MongoDB, like 27017 in integer type
          "db"        : None,   #Name of MongoDB Database, like 'CollectedDatabase' in string type
          "collection": None    #Name of MongoDB Collection where user object would be collected, like 'MyColection' in string type
          }

