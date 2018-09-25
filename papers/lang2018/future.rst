

Future Development
##################

cis_interface in being actively developed to expand the number of models 
that can be used in integration networks and the complexity of integration 
networks that can be handled.


Language Support
================

The biggest barrier to running new models is language support. Plant models 
are written in many different languages. While the current language support 
covers many, additional languages must be added to unlock the full potential. 
Surveys of the plant modeling community have helped identify the core languages 
that models have been written in. Based on these results, we plan to expand 
cis_interface to support models written in R, Fortran, and Java. In addition, 
we plan to add support for running Matlab models using Octave [CITE]. Matlab 
models require a Matlab license to run. Given that plant modelers do not all 
use Matlab, it cannot be assumed that everyone will have access to a Matlab 
license. Octave is open source and provides much of the same functionality 
as Matlab and can run many Matlab codes. Support for Octave will improve 
modelers ability to collaborate without worrying about access to a Matlab 
license.


Distributed Systems
===================

High performance computing (HPC) and cloud compute resources are powerful 
tools in the current computing ecosystem that could be used for running 
complex integration networks. To this end, we plan to expand cis_interface 
support for running integration networks on distributed compute resources. 
cis_interface already uses communicaiton tools that can be adapted for use 
in a distributed pattern. We will leverage tools like libsubmit [CITE] for 
automating the submission process to HPC and compute resources. In addition, 
we will add tools for running models as a service and using RabbitMQ to 
permit access to these models within integration networks.


Control Flow
============

Currently, modelers must explicitly specify how a model should process input 
within the model code including things like which input variables are static 
and read in once versus which variables change and should be looped over. 
We plan on adding options to cis_interface for dynamically generating model code 
based a user provided function call and list of static/variable input channels. 
This will allow better reusability of model code such as during parameter studies.


Data Aggregation
================

Much of the original version of cis_interface centered around the use of 
tabular input data. While tabular data is used heavily by plant models, it 
presents several barriers for constructing integration networks. Tabular input 
data only works when one model outputs the same columns that are expected as 
input by another model. However, this is unlikely to be the case if two models 
are developed independently. Future improvements to cis_interface will allow 
tabular input to models to be composed by aggregating output data from more than 
one model and/or file.


JSON Data Type Specification
============================

While cis_interface supports serialization of several data types/formats, we 
would like to make serialization as flexible as possible. To this end, 
cis_interface will be adapted to read JSON schema [CITE] for user defined types that 
can be used to automatically create the appropriate data structures alongside
methods for parsing and serializing them.


