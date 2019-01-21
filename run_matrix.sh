#!/bin/bash

flake8 yggdrasil

# IPC Comms
export YGG_DEFAULT_COMM="IPCComm"
source activate py27
nosetests -svx --nologcapture yggdrasil
source activate py34
nosetests -svx --nologcapture yggdrasil
source activate py35
nosetests -svx --nologcapture yggdrasil
source activate py36
nosetests -svx --nologcapture yggdrasil


# ZMQ Comms
export YGG_DEFAULT_COMM="ZMQComm"
source activate py27
nosetests -svx --nologcapture yggdrasil
source activate py34
nosetests -svx --nologcapture yggdrasil
source activate py35
nosetests -svx --nologcapture yggdrasil
source activate py36
nosetests -svx --nologcapture yggdrasil


unset YGG_DEFAULT_COMM
