#!/bin/bash

# these are set by mercury localstack_init.sh during entrypoint
# we re-set them after that script is run here
export AWS_SECRET_ACCESS_KEY=$LOCALSTACK_AWS_SECRET_ACCESS_KEY
export AWS_ACCESS_KEY_ID=$LOCALSTACK_AWS_ACCESS_KEY_ID
