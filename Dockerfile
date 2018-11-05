FROM python:3

RUN pip install cis_interface

CMD [ "echo", "Usage: cisrun <yaml_file1> [yaml_file2] [yaml_file3] [...]" ]
