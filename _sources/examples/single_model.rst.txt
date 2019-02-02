Running a Single Model
----------------------

The model communications interface consists of 2 pairs of very simple
functions - one pair to create channels and one pair to accomplish data
tranfer. Each pair represents a read-side and a write-side.

::

    in = YggInput(name)          # create a named input channel
    out = YggOutput(name)        # create a named output channel

    in.send(data)                # send a message through the managed channel
    flag, data = out.recv(name)  # receive message from channel - block if empty channel

Python-style is shown, but as these interfaces are thin wrappers around
System V IPC message queues, equivalent thin-wrappers are implemented
easily in almost any language. Models may create and use as many
channels as necessary, depending on the number of interfaces that they
require.

The only other model requirement is to provide a YAML specification file
that declares the channels that the model uses, and the system command
required to start the model executing.

::

    model:
      name: hellopython
      driver: PythonModelDriver
      args: hellopython.py

      inputs:
      - name: inFile
	driver: FileInputDriver
        args: input.txt
      - name: helloQueueIn
        driver: RMQInputDriver
        args: helloQueue

      outputs:
      - name: helloQueueOut
        driver: RMQOutputDriver
        args: helloQueue
      - name: outFile
        driver: FileOutputDriver
        args: /tmp/output.txt

This example tells the system to run a Python model defined in the script
"hellopython.py" and to connect the file inputdata/input.txt to the
ygg\_input named 'inFile' in your model, so when you recv() on it,
you'll get the file contents. Likewise when you send(data\_to\_send) to
the channel you made in your code with ygg\_output('outFile') the data
will go to the associated files.

In additon to reading/writing to/from files on disk, models can send/recv
messages to/from generic message queues that other models can connect to.
In the example above, there is an output queue named 'helloQueueOut'
messages sent to the channel ygg\_output('helloQueueOut') can be received
by any model with a corresponding input channel. In this example, the model
accesses this queue through the channel ygg\_input('helloQueueIn'). These
two channels are connected because they share the same argument
'helloQueue' in their YAML blocks.

The final part is the model runner, yggrun - to which you pass your
yml file. The model runner reads the specification, arranges for your
inputs and outputs to come and go as you've specified, and then calls
your model with the arguments as specified in the model stanza. The
model runs, using the send and recv calls as needed, and when the model
exits, the communications get cleaned up by the runner. The examaple
hellopython.py under examples is run like this (in examples/python):

::

    yggrun hellopython.yml

The code in hellopython.py uses the channels to read data from
the file input.txt, sends the data to the output queue, receives
it from the input queue, and then sends it to the output file
/tmp/output.txt:

::

        inf = YggInput('inFile')
        outf = YggOutput('outFile')
        inq = YggInput('helloQueueIn')
        outq = YggOutput('helloQueueOut')

        buf = inf.recv()
        outq.send(buf)
        buf = inq.recv()
        outf.send(buf)

This example is very simple and only shows how to run a single model
which could be accomplished by just handling input/output within the
script. The real advantage to using the Ygg framework comes when you
need two models in different languages to communicate.

