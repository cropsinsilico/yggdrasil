#!/bin/sh
# All of this assumes installation on Python 2.7 as higher versions not
# currently supported as of 5/15/2018

# Install LPy from conda
conda install openalea.lpy boost=1.66.0 -c openalea

# # Install dependencies
# sudo apt-get update
# sudo apt-get install -y \
#      qt4-qmake libqt4-dev \
#      qt4-dev-tools

# # boost
# BOOST_VER=1.66.0
# BOOST_VER_U=1_66_0
# BOOST_URL=https://dl.bintray.com/boostorg/release/$BOOST_VER/source/boost_$BOOST_VER_U.tar.gz -O boost.tar.gz
# tar -xvzf boost.tar.gz
# cd boost_$BOOST_VER_U
# ./bootstrap.sh
# ./b2 install
# cd ..

# # libpng
# PNG_VER=1.6.34
# PNG_URL=ftp://ftp-osl.osuosl.org/pub/libpng/src/libpng16/libpng-$PNG_VER.tar.gz
# wget $PNG_URL -O libpng.tar.gz
# tar -xvzf libpng.tar.gz
# cd libpng-$PNG_VER
# ./autogen.sh
# ./configure
# sudo make install
# sudo ldconfig  # Don't do for MAC
# cd ..

# # SIP (for installing PyQt4)
# SIP_VER=4.19.8
# SIP_URL=https://sourceforge.net/projects/pyqt/files/sip/sip-$SIP_VER/sip-$SIP_VER.tar.gz
# wget $SIP_URL -O sip.tar.gz
# tar -xvzf sip.tar.gz
# cd sip-$SIP_VER
# python configure.py
# sudo make
# sudo make install
# sudo ldconfig  # Don't do for MAC
# cd ..

# # PyQt4
# PYQT4_VER=4.12.1
# PYQT4_URL=http://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-$PYQT4_VER/PyQt4_gpl_x11-$PYQT4_VER.tar.gz
# wget $PYQT4_URL -O PyQt4.tar.gz
# tar -xvzf PyQt4.tar.gz
# cd PyQt4-$PYQT4_VER
# python configure-ng.py 
# sudo make
# sudo make install
# sudo ldconfig  # Don't do for MAC
# cd ..

# # Python install
# pip install PyOpenGL PyOpenGL_accelerate setuptools scons

# # Install OpenAlea.Deploy
# git clone git://github.com/openalea/deploy.git
# cd deploy
# python setup.py install
# cd ..

# # Install OpenAlea.SConsX
# git clone git://github.com/openalea/sconsx.git
# cd sconsx
# python setup.py install
# cd ..

# # Install OpenAlea.PlantGL
# git clone git://github.com/openalea/plantgl.git
# cd plantgl
# python setup.py install
# cd ..

# # Install LPy
# git clone git://github.com/openalea/lpy.git
# cd lpy
# scons
# python setup.py install
# cd ..
