import os
import subprocess

env_client = os.environ.copy()
env_client['component_name'] = 'client'
client = subprocess.Popen(['python', 'client.py'], env=env_client)

env_server = os.environ.copy()
env_server['component_name'] = 'server'
server = subprocess.Popen(['python', 'server.py'], env=env_server)


client.wait()
server.wait()
