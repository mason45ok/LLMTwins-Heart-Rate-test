# LLMTwins-Heart-Rate-test
This Repository is a heart-rate agent of LLTwins
# Agent Function
This AI Agent **cannot** operate independently and relies on the LLMTwins architecture.   
Within this architecture, the Agent module will automatically retrieve all available AI Agents.   
Below are the items you need to prepare.
* Google Sheet API & Access json file
* Device for heart rate & blood oxygen val (Optional)
## HeartRateSetting.py
This file is for access device from [e2live](https://www.e2-live.com/) and upload val to google sheet.
## script.py
This file is designed for periodic and repeated execution by a cronjob. It obtains functions from other files to facilitate execution and maintenance.
