#!/bin/bash

export YGG_DEBUG="INFO"
export YGG_NAMESPACE="sbml3"

yaml='sbml3.yml'

yggrun $yaml
