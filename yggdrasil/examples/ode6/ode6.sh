#!/bin/bash

export YGG_DEBUG="INFO"
export YGG_NAMESPACE="ode6"

yaml='ode6.yml'

yggrun $yaml
