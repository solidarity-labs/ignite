# Ignite!
Red Team tooling for cloud credentials gathering

'''
Cloud Credentials Gathering
WANNABE

* Passive
    - credentials files
    - env vars
    - user data
    - from lambda env vars

* Active
    - Generate config file based on discovery
    - Enrich with caller identity (aws user, account_id)
    - Check lateral movement and persistance permissions
    - Session token restore?

python3 ignite.py gather --aws <credentials | role | lambda | user_data | metadata> > json file with configss

'''

