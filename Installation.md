Official page http://thenerdshow.com/freespeech.html

# Installation #

Windows: Installation should work using [ossbuild](https://code.google.com/p/ossbuild/) for gstreamer. Will update this once we get a windows machine to test it.

### Linux/Cygwin ###
The following packages should be installed through the package manager.

  * [Python 2.7](http://www.python.org/)
  * [pygtk2](http://www.pygtk.org/)
  * [python-xlib](http://python-xlib.sourceforge.net/)
  * [python-simplejson](http://undefined.org/python/#simplejson)
  * [gstreamer, including gstreamer-python](http://gstreamer.freedesktop.org/)
  * [pocketsphinx and sphinxbase](http://cmusphinx.sourceforge.net/)
  * [CMU-Cambridge Statistical Language Modeling Toolkit v2](http://www.speech.cs.cmu.edu/SLM/CMU-Cam_Toolkit_v2.tar.gz) ([documentation](http://www.speech.cs.cmu.edu/SLM/toolkit_documentation.html))

## Fedora ##

```
su -c 'yum groupinstall "C Development Tools and Libraries"'
su -c 'yum -y install gstreamer-python sphinxbase-libs \
pocketsphinx-libs pocketsphinx sphinxbase pocketsphinx-plugin \
python-simplejson python-xlib pygtk2 svn'
```

## Ubuntu ##

Open a terminal and install the pocketsphinx repository:

```
sudo add-apt-repository ppa:dhuggins/cmusphinx
```

Enter password and press Enter twice.

Get updates and install dependencies.

```
sudo apt-get update

sudo apt-get python-xlib python-simplejson python-gtk2 python-gst0.1 \
gstreamer0.10-pocketsphinx sphinx-common python-sphinxbase \
python-pocketsphinx sphinxbase-utils svn
```

If installation balks and says it can't find /media/cdrom the location may be different. The trick is to use the mount command from a terminal to discover where the cd is mounted and make it a link to /media/cdrom

```
sudo ln -s (location, change this) /media/cdrom
```

# Testing #

Before we begin, load pavucontrol, Audacity (or some other audio recording program that has a recording monitor) and check sound levels.
Users should be able to record and play back audio.

```
arecord temp.wav -r 16000
aplay
```

Test pocketsphinx

```
pocketsphinx_continuous
```

Say something. (It should print lots of spam while doing some (very basic) speech recognition).

Download [CMU-Cam\_Toolkit\_v2](http://www.speech.cs.cmu.edu/SLM/CMU-Cam_Toolkit_v2.tar.gz) and unpack it. Read the instructions in the README and edit the Makefile. To summarize, most little-endian PC hardware requires this change. Edit `CMU-Cam_Toolkit_v2/src/Makefile` and remove the # sign in front of this line:

```
BYTESWAP_FLAG	= -DSLM_SWAP_BYTES
```


Run `make` to build the tools.

```
cd CMU-Cam_Toolkit_v2/src
make
```

Manually copy the tools from ../bin to somewhere in $PATH like: `/usr/local/bin`

```
sudo cp ../bin/* /usr/local/bin/
```

The tools expect to write to /usr/tmp

```
sudo ln -s /tmp /usr/tmp
```

Language files and preferences are copied to /home/$USER/.config but the location may be changed by changing or adding the environment variable, `$XDG_CONFIG_HOME`

```
export XDG_CONFIG_HOME=$HOME/.config
```

Get FreeSpeech using svn because downloads are outdated. (Install svn from the Software Center if necessary.)

```
cd ~/Downloads
svn checkout http://freespeech-vr.googlecode.com/svn/trunk/ freespeech-vr-read-only
```

## Using FreeSpeech ##

There is no desktop icon yet. Right-click on the desktop to create one.
Launching the program may be done via the Python interpreter.

```
cd ~/Downloads/frees*
python freespeech.py
```

Position the microphone somewhere near enough and begin talking. To end of the sentence, say "period" (or "colon", "question-mark", "exclamation-point") Look at the dictionary, "custom.dic" for ideas.

Voice commands are included. A list of commands pops up at start-up or say "show commands" to show them again. The following voice commands are supported (except only "scratch that" is available when using X keyboard emulation).

  * file quit - quits the program
  * file open - open a text file in the editor
  * file save (as) - save the file
  * show commands - pops up a customize-able list of spoken commands
  * editor clear - clears all text in the editor and starts over
  * delete - delete `[text]` or erase selected text
  * insert - move cursor after word or punctuation example: "Insert after period"
  * select - select `[text]` example: "select the states"
  * go to the end - put cursor at end of document
  * scratch that - erase last spoken text
  * back space - erase one character
  * new paragraph - equivalent to pressing Enter twice

# Troubleshooting #

Make sure the various requirements work. For example, `pocketsphinx_continuous`, which may be tested from the command line in a terminal.

In case of messages like this:

```
Trouble writing /home/*/.config/FreeSpeech/freespeech.idngram
Trouble writing...
```

It usually means nobody installed [CMU-Cambridge Statistical Language Modeling Toolkit v2](http://www.speech.cs.cmu.edu/SLM/CMU-Cam_Toolkit_v2.tar.gz) or there is a problem with the tools themselves. Edit the Makefile and follow the instructions therein before running `make`. Manually copy the files in the bin directory somewhere in your `$PATH` like `/usr/local/bin` on Linux or `C:\windows\system32` on Windows.

For some reason, the toolkit expects to be able to write to /usr/tmp. The `tmpfile()` function uses the P\_tmpdir defined in `<stdio.h>`, but the Makefile installs everything under `/usr`. The quick-fix is to provide /usr/tmp for machines that don't have it.

```
sudo ln -s /tmp /usr/tmp
```