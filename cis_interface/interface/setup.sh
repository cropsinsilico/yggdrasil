# Paths
export PSIBASE=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd "../.." && pwd )
export PATH=${PSIBASE}/pycis/pycis/interface:${PATH}
export CPATH=${CPATH}:${PSIBASE}/pycis/interface

# Message passing constants
# export PSI_MSG_MAX=65536  # 1024*64
# export PSI_MSG_EOF="EOF!!!"

# Set PSi debugging level to your liking, or turn off if you prefer
# one of: CRITICAL 	ERROR 	WARNING 	INFO 	DEBUG 	NOTSET
export PSI_DEBUG="INFO"
export RMQ_DEBUG="WARNING"
export PSI_CLIENT_DEBUG="INFO"

# RMQ server info
export PSI_MSG_SERVER=141.142.211.110
export PSI_MSG_USER="psi"
export PSI_MSG_PW="hz8F3J8waizz"
export PSI_CLUSTER="141.142.211.42,141.142.211.43,141.142.211.44,141.142.211.45,141.142.211.46,141.142.211.47,141.142.211.48"


