Integration Tips
################

#. Determine the communication pattern you want
   * Does the communication only need to go in one direction? Connections can be made by pairing inputs/outputs between models.
   * Will one model be calling another like a function? An RPC, client/server communication pattern will allow the client model to call the server model.
   * Are the models both/all time dependent? A timesync patter will allow you to synchronize and aggregate variables across time steps.
#. Write the model yaml without connections. This should require no modification of the model source code and will allow you to sort out any compilation errors or dependency conflicts before introduction communication.
#. Write a yaml with connections to files (or dummy models) for testing. Using files (or dummy models) allows you to pin down any type conflicts and add transformations/units to the YAML as necessary.
#. Write a yaml with connections between models. If the previous steps were sucessful, this will mainly consist of nailing down the communication pattern (e.g. identifying mismatches in expected message counts, optimizing for parallel execution).
