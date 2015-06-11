# OpenShift VMW Chargepoint App
This git repo contains all the code required to run the VMW Chargepoint Dashboard (http://wreckr.net/vmw). 

## Setup Instructions
1. Sign up for a free OpenShift Account at https://www.openshift.com/
2. Install the Openshift Client tools: https://developers.openshift.com/en/managing-client-tools.html. (*I like to use Ubunutu for most of my dev work.*)
3. Setup rhc for your openshift account. Instructions are in the same link as step #2
4. Create the App and deploy the application code
    ```sh
    $> rhc app create vmwcp python-2.7 cron-1.4 --from-code=git://github.com/wrecker/vmw-chargepoint
    ```
    Here *vmwcp* is the name of the application. You can use any valid name instead of *vmwcp*. This step will take a few minutes. Be patient.
    
5. The `app create` step above will also clone locally the private git repo backing your app. This repo contains a full copy of the repo on github. In your local repo edit the file `wsgi/.cp_passwd` and put your chargepoint username & password in this format `username:password` on the first line. Commit and update the app. 
    ```sh
    $> git add wsgi/.cp_passwd
    $> git commit
    $> git push
    ```
    Once the git commit is pushed to the private remote repo, you will see a lot of messages about python packages and finally the app will be restarted.
6. Wait for a few minutes for the first cron run to trigger. Open the url http://vmwcp-[openshift-domain].rhcloud.com/vmw

## Enable Pushbullet Notifications
The app has support for generating notifications using PushBullet. By default its turned off and can be enabled with a couple of lines of changes.
1. Sign up for a PushBullet Account and get your API Key/Access Token from this page https://www.pushbullet.com/account. Edit the file `wsgi/.pb_key` and paste this key as the first line of the file.
2. At the top of file `wsgi/get_json.py`, look for the comment block that starts with "Garages & Pushbullet Channels". After this block there is a dict variable named `GARAGES`. This dict is initialized with the three garage names and a corresponding pushbullet tag.
3. Create three pushbullet channels at https://www.pushbullet.com/my-channel and update the dict `GARAGES` in `wsgi/get_json.py`.
4. Edit file `.openshift/cron/minutely/get_json.sh` and go to line 36. Delete or comment out the line that says `notify=""`. The lines above in this line are doing some calculations based on the current time & day to decided if the app should generate pushbullet notifications. Make any changes to the schedule.
5. Commit all the changes to the three files and push the changes to the remote git repo.

## Questions / Comments
If you have any questions email me at coder@mahesh.net
