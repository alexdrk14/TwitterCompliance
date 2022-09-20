# Twtitter API user compliance module

This repository utilize Twitter API v2 endpoint for user compliance check. 
Developed Python module allow to load user ids from simple txt file or stored json responces in MongoDB. 
In case of mongoDB stored data see configuration file example in order to provide location (ip:port) and database/collection names.


Developed method load user ids, and create compliance job in Twitter endpoint. 
And check every 15 minutes if endpoint has the result. 
When execution is finished script store compliance result for each user in single txt file (file contain timestamp in order to track request dates). 
In case when user id is not in result file, this user is alive and publicly available. 
In other case user may have the following labels: Deleted, protected ,removed and suspended.

## Execution via cron process

In order to check user compliance in daily basis, script should be executed via crontab process like:
```bash
 croantab -e 
```
find last line of file and write:
```bash
59 23 * * * python3 /PathToRepository/TwitterCompliance/compliance_batch.py >> /PathToRepository/TwitterCompliance/logs.txt 2>&1
```

using this type of execution script will be executed at the last minute of the day every day.
