FROM python:3

RUN pip install yggdrasil

CMD [ "echo", "Usage: yggrun <yaml_file1> [yaml_file2] [yaml_file3] [...]" ]
