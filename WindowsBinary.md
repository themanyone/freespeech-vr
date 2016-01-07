Development on the Windows binary has stalled while we try to build libgstpocketsphinx as a .DLL. The CygwinVersion has the same problem.

## Dev Preparation ##

  1. Make a c:\Dev folder
  1. Make a GTK folder inside that
  1. Put everything inside that

### Install Python ###

64 bit Python will not work for this. I tried it.

  1. Get python-2.7.3 32 bit from http://www.python.org/getit/
  1. Install to C:\Dev\Python27
  1. take a break while waiting for that to install

### Install GTK+ ###

  * Read instructions on http://www.gtk.org/download/win64.php
  * Open up the README that you just extracted.
  * Verify that their instructions agree with ours.

### Add System Paths ###

  1. Open up My Computer->Properties->Advanced System Settings->Environment Variables
  1. Scroll down to Path
  1. Double-click it
  1. Append the install paths:
  1. ;C:\Dev\GTK\bin;C:\Dev\Python27 to the end of the Path system variable
  1. Ok OK OK
  1. You will probably have to reboot or log out and back in for the path to take effect.

### Install PyGTK ###

Install pygtk-all-in-one-2.24.2.win32-py2.7.msi from http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.24/

Test the installation
Open a terminal: Start Menu->"type in 'cmd'"->Enter
```
python
import gtk
window=gtk.Window()
window.show
```

## Gstreamer for Windows ##

  1. Go to http://code.google.com/p/ossbuild/
  1. Install GStreamer-WinBuilds-LGPL-x86-Beta04-0.10.7
  1. Install GStreamer-WinBuilds-SDK-LGPL-x86-Beta04-0.10.7
  1. Reboot or log out / in
  1. Test with the [tutorial](http://wiki.pitivi.org/wiki/PyGST_Tutorial)

**If the tutorial complains about an outdated version of Python** copy everything in:
```
GStreamer\v0.10.7\sdk\bindings\python\v2.7\lib\site-packages
```
to:
```
GStreamer\v0.10.7\lib\site-packages
```
## PocketSphinx ##

**This is the point where we are stuck:** Getting gst-plugin to work. Refer to http://cmusphinx.sourceforge.net/wiki/gstreamer

Compiling pocketsphinx on Windows, from svn, is going to take some time. Specifically, compiling _gst-plugin_ requires development headers and libraries for all of these packges, and their dependencies. The best way to make sure that all works is to download the sources for them.

  * gstreamer
  * pocketsphinx
  * Python requires zlib, openssl, ncurses, bzip, SQlite3 and libffi.
  * sphinxbase

We tried the following Windows binary download of PocketSphinx but we could not find the _gst-plugin_ binary anywhere in the package. We need this to connect to PocketSphinx via gstreamer in Python. They probably did not compile _gst-plugin_ into this one and I don't blame them because of the above.

  1. <strike>Get from <a href='http://sourceforge.net/projects/cmusphinx/files/pocketsphinx/0.8/pocketsphinx-0.8-win32.zip/download'>http://sourceforge.net/projects/cmusphinx/files/pocketsphinx/0.8/pocketsphinx-0.8-win32.zip/download</a></strike>
  1. Pocketsphinx needs MSVCR100.dll which you can get from MS Visual Studio 2010, Visual C++ 2010 Express (for programmers) or vcredist (32bit) (for users) at http://www.microsoft.com/en-us/download/confirmation.aspx?id=14632

## CMU-Cam\_Toolkit\_v2 ##

We compiled the CMU-Cam\_Toolkit\_v2 for Win32. Copy the .exe files to the freespeech-vr folder (or put them anywhere in the computer's path if you want to use them from the command line).
https://code.google.com/p/freespeech-vr/downloads/detail?name=CMU-Cam_Toolkit_v2-win32.zip