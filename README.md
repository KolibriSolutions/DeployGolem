# Deploy Golem
This repo holds the source code for the Kolibri Deploy Golem. It is a simple flask webapplication that listens to configurable webhooks and auto deploys repositories.

## Deployement
For deployement a simple gunicorn setup will suffice. Gunicorn example command:  
```gunicorn -b unix:/tmp/gunicorn.sock app:app --workers 4```  
For more information consult the flask and gunicorn documentation on deployement.

## Configuration
The app itself needs two config files, one called ```secrets.py``` with a ```SECRET_KEY_FLASK``` defined in it for the application to import.  
The other file needed is a ```config.yaml``` with the following structure:  
```
<repo name>:
	event: push (or another event)
	key: <secret key>
	cwd: <the folder in which the application/repo lives>
	branch: master (or another branch if applicable)
	actions:
		- git pul
		- action 1
		- action 2
```

For the webhook itself, choose json encoded webhook and fill in the same secret key as in your config.yaml.  
The webhook url is setup in the following way:  
```https://<domain>/hooks/<type>/<repo name>/```  
In which the type can either be ```github``` or ```gitea```
