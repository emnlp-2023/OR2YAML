USERNAME = ########
PASSWORD = ########

VOLUME = Main
## Findings
CHANNEL = Conference
## ARR_Commitment

MAPFILE = charmap

all:

notes: ${CHANNEL}.npz

# For the first time
# ${CHANNEL}.npz:
# 	python mirror-OR.py -u ${USERNAME} -p ${PASSWORD} -c ${CHANNEL}

# From the second time
${CHANNEL}.npz:
	python mirror-OR.py -u ${USERNAME} -p ${PASSWORD} -c ${CHANNEL} -l ${CHANNEL}.latest.npz

yml: ${CHANNEL}.${VOLUME}.yml

${CHANNEL}.${VOLUME}.yml: ${CHANNEL}.npz
	python notes2yaml.py -n $< -m ${MAPFILE} -v ${VOLUME} -o $@
