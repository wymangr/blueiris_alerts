# Blue Iris Alerts
Alerting tool for Blue Iris. Sends an alert that allows the user to view alert image, recording, live feed and the option to pause the alerts.
Current supported clients:
* Slack

### Requirements
1. Blue Iris
2. Slack Account
3. Publicly accessible domain or IP address to host web server (via port forward and/or proxy)
4. Publicly accessible Blue Iris web server (via port forward and/or proxy)

### Server
APIs for interacting with the alert. Pause button, live feed, recording.

[Server Documentation](/server/README.md)

### Client
Python script to execute from BlueIris to send the alert.

[Client Documentation](/client/README.md)

### todo:
- Add More Documentation
- Error Handling
- Github Action