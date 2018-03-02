:: rabbitmq-server -detached
choco info -h
choco info rabbitmq --localonly
refreshenv
rabbitmq-server -detached
