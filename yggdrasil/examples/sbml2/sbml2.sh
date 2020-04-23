#!/bin/bash

export YGG_DEBUG="INFO"
export YGG_NAMESPACE="sbml2"

yaml='sbml2.yml'

yggrun $yaml
