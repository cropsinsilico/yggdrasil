FROM continuumio/miniconda3
RUN conda config --add channels conda-forge
RUN conda create -n env python=3.6 yggdrasil
RUN echo "source activate env" > ~/.bashrc
ENV PATH /opt/conda/envs/env/bin:$PATH

CMD [ "echo", "Usage: yggrun <yaml_file1> [yaml_file2] [yaml_file3] [...]" ]
