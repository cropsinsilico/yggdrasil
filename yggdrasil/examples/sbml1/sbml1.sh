#!/bin/bash

export YGG_DEBUG="INFO"
export YGG_NAMESPACE="sbml1"

yaml='sbml1.yml'

yggrun $yaml
