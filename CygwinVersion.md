#Development work in progress


# Windows Setup #

_FreeSpeech Windows development is stalled while we try to build libgstpocketsphinx.dll_

This is the progress we have so far...

## Cygwin ##

Install [Cygwin](http://cygwin.com/) Linux emulation layer for Windows and run setup.exe to search and install these dependencies:

  * pkg-config
  * python
  * python-cairo
  * python-gobject
  * python-gobject-devel
  * python-gtk2.0
  * python-gtk2.0-demo
  * python-gtk2.0-devel
  * gtk2.0lc
  * liblzma-devel-5.0.2
  * libgstreamer0.10-devel
  * libgstreamerinterfaces0.10-devel
  * Xorg
  * Xorg-common
  * cairo
  * xwin

  1. Launch xterm: ProgramFiles->CygwinX->xterm
  1. Test pygtk: pygtk-demo
  1. Test gstreamer: gst-inspect-0.10.exe |grep source

Get a development environment together.

  * libgcc1: GCC compiler support shared runtime
  * libmpfr4: A library for multiple-precision floating point
  * gcc4: GCC Release series 4 compiler (C & C++ install helper)
  * gcc4-core: Core C++ compiler subpackage
  * gcc4-g++: G++ subpackage
  * make: The GNU version of the 'make' utility
  * subversion: A version control system
  * autoconf: Wrapper scripts for autoconf commands
  * libtool: A shared library generation tool
  * automake: Wrapper scripts for automake and aclocal
  * libiconv: GNU character set conversion library and utilities

Download and unpack from http://sourceforge.net/projects/cmusphinx/files
**Do not download the zipfile (22.7MB)** Get sources from Files tab.

  * [pocketsphinx-0.8.tar.gz](http://sourceforge.net/projects/cmusphinx/files/sphinxbase/0.8/sphinxbase-0.8.tar.gz/download)
  * [sphinxbase-0.8.tar.gz](http://sourceforge.net/projects/cmusphinx/files/pocketsphinx/0.8/pocketsphinx-0.8.tar.gz/download)
  * [CMU-Cambridge Statistical Language Modeling Toolkit v2](http://www.speech.cs.cmu.edu/SLM/CMU-Cam_Toolkit_v2.tar.gz)

Copy the archives to C:\cygwin\home\dev or wherever you want to build.

Using xterm, change directory to the folders, unpack, and install
```
cd /home/dev
tar xvf sphinxbase*
tar xvf pocketsph*
cd sphinxb*
./configure --prefix=/usr
make
make install
```
### Test pocketsphinx. ###

You should be able to get access to the plugin.
```
gst-inspect-0.10.exe|grep pocket
```

Of course the plugin is not there. It is being built as the wrong type of library. Look in /lib/gstreamer-0.10 for the plugin:
```
cd /lib/gstreamer-0.10
ls libgst*
libgstpocketsphinx.a
libgstpocketsphinx.la*
```
It should be libgstpocketsphinx.dll now there is probably some option to setup.py to build it as a dll. Maybe --compiler=cygwin or try installing Mingw32 and --compiler=mingw32

Once we get that DLL built, continue with FreeSpeech setup...

(Optional) Try building the native WindowsBinary