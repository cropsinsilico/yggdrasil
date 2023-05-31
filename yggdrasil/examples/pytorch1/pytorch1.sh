#!/bin/bash

export YGG_DEBUG="INFO"
export YGG_NAMESPACE="pytorch1"

yaml='pytorch1.yml'

yggrun $yaml
