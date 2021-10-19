#!/bin/bash

export YGG_DEBUG="INFO"
export YGG_NAMESPACE="ode4"

yaml='ode4.yml'

yggrun $yaml
