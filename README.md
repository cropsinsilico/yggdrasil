# Model Integration and Communications Architecture

## Overview
The CiS model system provides integration and communications support for model providers.
Modelers add simple communications interfaces within their model code, and provide a simple declarative specification that informs the system of the names and types of inputs and outputs of the model and the commands required to run the model.

The system uses the specification to configure the communications channels and bind them into the model.   The complexity of the particular communications system is managed by a model driver that performns communication setup, binds the communications to a simple interface within the model, and manages the model's exection.   The complexities of model registration and discovery, as well as the complexities of setup and management of the communications system are handled by the model driver under direction of the model specification, freeing the model programmer from implementing communications protocols of any particular messaging infrastructure.   The model programmer is provided with a very simple and easy to use abstract send/receive message interface using basic IPC mechanisms available in that binds  in virtually every language and platform.

The model communications interface consists of 2 pairs of very simple functions - one pair to create channels and one pair to accomplish data tranfer.   Each pair represents a read-side and a write-side.
```
psi_input(name)  - create a named input channel
psi_output(name) - create a named output channel

psi_send(name, data)   - send a message through the managed channel
data = psi_recv(name)  - receive message from channel - block if empty channel
```
C-style is shown, but as these interfaces are thin wrappers around System V IPC message queues, equivalent thin-wrappers are implemented easily in almost any language.
Models may create and use as many channels as necessary, depending on the number of interfaces that they require.

The only other model requirement is to provide a YAML specification file that declares the channels that the model uses, and the system command required to start the model executing.
```
model:
  name: hellopython
  driver: ModelDriver
  args: [ "python", "hellopython.py" ]

  inputs:
    - name: inputFile
      driver: FileInputDriver
      args: inputdata/input.txt
      onexit: delete    # delete the queue when the model exits
    - name: fooInputChannel
      driver: RMQInputDriver
      args: fooqueue
      onexit: delete    # delete the queue when the model exits
 
  outputs:
    - name: fooOutput
      driver: RMQOutputDriver

```
This example tells the system to run your model as if you typed "python hellopython.py" and to connect the file inputdata/input.txt
to the psi_input named 'inputFile' in your model, so when you recv() on it, you'll get the file contents.   Likewise
when you send(data_to_send) to the channel you made in your code with psi_output('fooOutput') the data will go to
the message queue names FooOutput.

You may have multiple inputs and multiple outputs as you need.   If you send to a RMQOutput named 'fred' your
another model can use fred as a RMQInput to read from and get your messages.
By keeping multiple yml files around with different inputs and outputs but the same model stanza you can test
with different data inputs and outputs conveniently without changing the model code.

The finel part is the model wrapper, PsiRun.py - to which you pass your yml file.   The model wrapper reads the
specification, arranges for your inputs and outputs to come and go as you've specified, and then calls your model
with the arguments as specified in the model stanza.   The model runs, using the send and recv calls as needed, 
and when the model exits, the communications get cleaned up bu the wrapper.
The exmaple hellopython.py under examples is run like this (in examples/python):
```
python ../../interface/PsiRun.py hellopython.yml
```
The code in hellopython.py uses the channels:
``` 
    inf = PsiInput('infile')
    outf = PsiOutput('outfile')
    inq = PsiInput('helloQueue')
    outq = PsiOutput('helloQueue')

    buf = inf.recv()
    outq.send(buf)
    buf = inq.recv()
    outf.send(buf)

```
The yaml file says to run the model, and connects the inputs and outputs:
```
model:
  name: hellopython
  driver: ModelDriver
  args: [ "python", "hellopython.py" ]

  inputs:
    - name: infile
      driver: FileInputDriver
      filename: input.txt
    - name: helloQueue    
      driver: RMQInputDriver

  outputs:
    - name: helloQueue    
      driver: RMQOutputDriver
    - name: outFile
      driver: FileOutputDriver
      filename: output.txt
```



## Installation notes
* Matlab
  * Matlab uses the python interface directly
  * Remove the matlab crypto and ssl libraries and install the python engine
sudo -s
rm -f ./R2015b/toolbox/compiler_sdk/mps_clients/c/glnxa64/lib/libcrypto.so.1
rm -f ./R2015b/toolbox/compiler_sdk/mps_clients/c/glnxa64/lib/libcrypto.so
rm -f ./R2015b/toolbox/compiler_sdk/mps_clients/c/glnxa64/lib/libcrypto.so.1.0.0
rm -f ./R2015b/bin/glnxa64/libcrypto.so.1
rm -f ./R2015b/bin/glnxa64/libcrypto.so.1.0.0
rm -f ./R2015b/toolbox/compiler_sdk/mps_clients/c/glnxa64/lib/libssl.so.1
rm -f ./R2015b/toolbox/compiler_sdk/mps_clients/c/glnxa64/lib/libssl.so.1.0.0
rm -f ./R2015b/toolbox/compiler_sdk/mps_clients/c/glnxa64/lib/libssl.so
rm -f ./R2015b/sys/jxbrowser/glnxa64/xulrunner/xulrunner-linux-64/libssl3.so
rm -f ./R2015b/bin/glnxa64/libssl.so.1
rm -f ./R2015b/bin/glnxa64/libssl.so.1.0.0
cd /usr/local/MATLAB/R2015b/extern/engines/python
python setup.py

## Contents

* **build** - model build help and container builders
  * docker - build containers (in progress)
* **edge-example** - full example in python, matlab, C(++)
  * models - models and specifications
  * app
* **lib** - Common services and drivers
  * drivers - inputs, outputs, messaging, model-wrapper
  * yml - yaml specification support
  * controller - cli PSi system setup/run

## Functional Architecture

* Models
  * Provide callable functions (ml, c, python)
    * Function(s) take an input, returns an output
    * A function to set optional parameters
  * Provide a specification - yaml file
    * Describes the model, inputs, outputs, function names, files to use, filenames to store output
* Driver
  * A driver is a 'wrapper' or adapter that encapsulates other objects or functions, perhaps in other languages or platforms, into a callable python object - for example the MatlabCaller encapsulates the Matlab runtime and callable function in a clean python object.
* Controller - A python cli program that runs and feeds the models
  * Reads the specifications
  * Setup and connect the queues
  * Setup the models inside model drivers
  * Setup the input and output drivers
  * Sets all drivers to running
    * Input drivers send data into queues
    * Model drivers receive inputs, call model processing functions, send outputs to downstream queue drivers and/or output drivers

## Advantages

* The demands on model providers is greatly simplified
  * Model contains only domain-specific model code - focused
  * No coding based on unfamilar techniques, languages, etc.
    * System code, protocols, services, and languages outside of a modelers area of expertise
  * The specification is much simpler to create and maintain than code
  * Declare what the model wants, take inputs, produce outputs and let the system do the rest
* Single system modules and drivers are easier to maintain and evolve
  * Messaging, data-handling, and system run-time facilities become shared and isolated, bounded in their impact
  * Easier to understand, easier to maintain
    * Fixing a shared driver is preferrable to system code embedded in multiple models

## Development Notes:  Installation and test code fragments

Python to matlabs setup:
cd /usr/local/MATLAB/R2015b/extern/engines/python
sudo python setup.py install.

### Python protocols Matlab

from psimsg import *
import matlab.engine
eng = matlab.engine.connect_matlab()

### Matlab to Python

Matlab only seems limited to storing basic data (ints/floats/arrays), unable to receive objects from python for storage/calling
P = py.sys.path;
append(P, pwd);
import psimsg.*
