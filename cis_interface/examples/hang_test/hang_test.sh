#!/bin/bash

export PSI_NAMESPACE="hang_test"

yaml1='client.yml' 
yaml2='server.yml'

cisrun $yaml1 $yaml2
