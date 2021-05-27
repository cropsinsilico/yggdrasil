Two models, A & B, that send/receive strings. Model A receives input from a file and then sends it's output to model B. Model B receives input from model A and sends it's output to a file. Both models are functions that are automatically wrapped by yggdrasil with the appropriate interface calls. This example demonstrates the use of the `function` model YAML parameter and auto-wrapping.

