
<img src="logo-alation.png" width="500"  align="center"/>

# Alation Upgrade Readiness Check

## This python script is designed to extract and analyze certain environmental variables to confirm that an Alation upgrade can proceed.

## The checks run by the script are:

    1. Replication mode check
    2. Minimum space requirement check
    3. Data drive and backup drive space and mount point check
    4. Backup System health check
    5. postgreSQL size check
    6. Datadog activation check
    


## Instructions

For your convenience, we have developed an automated python tool to run these checks and outputs a simple file for our development team to work with. Here are the instructions to run the script:
Copy (using scp, winscp) the preUpgradeCheck.py to your home directory on the Alation instance:

    cp preUpgradeCheck.py ~/.
Or directly download the code from GitHub:

    curl https://raw.githubusercontent.com/Alation/sanity_tools/master/preUpgradeCheck.py --output preUpgradeCheck.py
Run the python code as sudo: (outside the Alation shell)

    sudo python preUpgradeCheck.py 
If the script ran without any errors, copy the python output and email it to Alation CSM.

## Example of a run:

<img src="example.png" width="1000"  align="center"/>




```python

```
