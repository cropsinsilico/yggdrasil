#!/bin/bash
echo "Starting RabbitMQ..."
export PATH="${PATH}:/usr/local/sbin"
sudo /bin/sh -c "RABBITMQ_PID_FILE=$TRAVIS_BUILD_DIR/rabbitmq.pid rabbitmq-server &"
sudo rabbitmqctl wait "$TRAVIS_BUILD_DIR/rabbitmq.pid"
echo "Checking rabbitmq status..."
sudo rabbitmqctl status
