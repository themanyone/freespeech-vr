## About

FreeSpeech is a free and open-source (FOSS), cross-platform desktop application front-end for PocketSphinx dictation, voice transcription, and realtime speech recognition. FreeSpeech enables speaker-independent voice recognition with dynamic language learning capability using the PocketSphinx speech recognition engine. Get FreeSpeech via git from Github (https://github.com/themanyone/freespeech-vr).

Author: Henry Kroll III http://thenerdshow.com

In addition to dictation, FreeSpeech provides voice commands and keyboard 
emulation, so users can dictate into other apps, remote terminals, and virtual machines.

## Installation

Windows: Installation should work using ossbuild (http://code.google.com/p/ossbuild/) for 
gstreamer. We will update this once we get a windows machine to test it.

## Linux/Cygwin

**Update:** A Python3 branch is available. Some packages listed here may need updated 
versions if planning to check out new python3 branch.

The following packages may be installed through the package manager.

* [Python 2.7] (http://www.python.org/)
* [pygtk2] (http://www.pygtk.org/)
* [python-xlib] (http://python-xlib.sourceforge.net/)
* [python-simplejson] (http://undefined.org/python/#simplejson)
* [gstreamer-python gstreamer] (http://gstreamer.freedesktop.org/)
* [pocketsphinx and sphinxbase] (http://cmusphinx.sourceforge.net/)
* [CMU-Cambridge Statistical Language Modeling Toolkit v2] (http://www.speech.cs.cmu.edu/SLM/CMU-Cam_Toolkit_v2.tar.gz)
* [documentation] (http://www.speech.cs.cmu.edu/SLM/toolkit_documentation.html)

## Fedora

```bash
su -c 'yum groupinstall "C Development Tools and Libraries"'
su -c 'yum -y install gstreamer-python sphinxbase-libs \
gstreamer-0.10 gstreamer-plugins-good-0.10 gstreamer-plugins-base-0.10 \
pocketsphinx-libs pocketsphinx sphinxbase pocketsphinx-plugin \
python-simplejson python-xlib pygtk2 git'
```

## Ubuntu

Searches for a cmusphinx ppa for recent versions of Ubuntu haven't returned good 
results, but [this 
site](http://jrmeyer.github.io/asr/2016/01/09/Installing-CMU-Sphinx-on-Ubuntu.html) 
contains recent walkthroughs to help build from source.

For older versions of Ubuntu, open a terminal and install the pocketsphinx repository: 

```bash
sudo add-apt-repository ppa:dhuggins/cmusphinx
```

Enter password and press Enter twice.

Get updates and install dependencies.

```bash
sudo apt-get update

sudo apt-get python-xlib python-simplejson python-gtk2 python-gst0.1 \
gstreamer0.10-pocketsphinx gstreamer0.10-plugins-base gstreamer0.10-plugins-good \
sphinx-common python-sphinxbase python-pocketsphinx sphinxbase-utils git \
jackd libjack0 libjack-dev
```

If installation balks and says it can't find /media/cdrom the location may be different. The 
trick is to use the mount command from a terminal to discover where the CD is mounted and 
make it a link to /media/cdrom

```bash
sudo ln -s (location, change this) /media/cdrom
```

## Testing

Before we begin, load pavucontrol, Audacity (or some other audio recording program that has a recording monitor) and check sound levels.
Users should be able to record and play back audio at good volume, but not so high that it starts clipping.

```bash
arecord temp.wav -r 16000
aplay temp.wav
``` 

Test pocketsphinx

```bash
pocketsphinx_continuous
```

Say something. (It should print lots of spam while doing some (very basic) speech recognition).

[Download CMU-Cam_Toolkit_v2] 
(http://www.speech.cs.cmu.edu/SLM/CMU-Cam_Toolkit_v2.tar.gz) and unpack 
it. Read the instructions in the README and edit the Makefile. To 
summarize, most PC hardware is what they call "little-endian" and it 
requires this change: Edit `CMU-Cam_Toolkit_v2/src/Makefile` and remove 
the # sign in front of this line:

```bash
BYTESWAP_FLAG	= -DSLM_SWAP_BYTES
```


Run `make` to build the tools.

```bash
cd CMU-Cam_Toolkit_v2/src
make
```

Manually copy the tools from ../bin to somewhere in $PATH like: `/usr/local/bin`

```bash
sudo cp ../bin/* /usr/local/bin/
```

The tools expect to write to /usr/tmp

```bash
sudo ln -s /tmp /usr/tmp
```

Language files and preferences are copied to /home/$USER/.config but the location may be changed by changing or adding the environment variable, `$XDG_CONFIG_HOME`

```bash
export XDG_CONFIG_HOME=$HOME/.config
```

## Get FreeSpeech Using Git.

```bash
cd ~/Downloads
git clone https://github.com/themanyone/freespeech-vr.git
```

Optionally check out the python3 branch. View the new README.md and install python3 dependencies before using.

```bash
git checkout python3
```

## Using FreeSpeech

There is no desktop icon yet. Right-click on the desktop to create one.
Launching the program may be done via the Python interpreter.

```bash
cd ~/Downloads/frees*
python freespeech.py
```

Position the microphone somewhere near enough and begin talking. To end of the sentence, say "period" (or "colon", "question-mark", "exclamation-point") Look at the dictionary, "custom.dic" for ideas.

Voice commands are included. A list of commands pops up at start-up or say "show commands" to show them again. The following voice commands are supported (except only "scratch that" is available when using sendkeys X keyboard emulation).

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

## Troubleshooting

Prior to blaming freespeech, test audio recording and pocksphinx. Run 
`pocketsphinx_continuous` from the command line in a terminal window and make sure that it 
recognizes speech. If not, check the pocketsphinx installation. We regret that we are not 
affiliated with pocketsphinx and do not have the resources to support it.

In case of messages like this:

```bash
Trouble writing /home/*/.config/FreeSpeech/freespeech.idngram
Trouble writing...
```

It usually means nobody installed [CMU-Cambridge Statistical Language Modeling Toolkit v2] (http://www.speech.cs.cmu.edu/SLM/CMU-Cam_Toolkit_v2.tar.gz) or there is a problem with the tools themselves. Edit the Makefile and follow the instructions therein before running `make`. Manually copy the files in the bin directory somewhere in your `$PATH` like `/usr/local/bin` on Linux or `C:\windows\system32` on Windows.

For some reason, the toolkit expects to be able to write to /usr/tmp. The `tmpfile()` function uses the P_tmpdir defined in `<stdio.h>`, but the Makefile installs everything under `/usr`. The quick-fix is to provide /usr/tmp for machines that don't have it.

```bash
sudo ln -s /tmp /usr/tmp
```

## Improving accuracy

The biggest improvements in accuracy have been achieved by adjusting the microphone position. Open up the volume control app. On systems that use pulseaudio (Fedora) volume level and microphone selection may be found using pavucontrol. Try making a recording with Audacity (http://audacity.sourceforge.net) and checking the noise levels to make sure it sounds like intelligible speech when played back. Make sure freespeech is using the same mic levels in the volume controls recording tab.

Adapt PocketSphinx to a particular voice or accent for better accuracy.
See http://cmusphinx.sourceforge.net/wiki/tutorialadapt

## Language corpus

The language corpus that ships with this download, "freespeech.ref.txt" is likely to be very limited. Our excuse is that the small size saves memory while providing room to learn spoken grammar. Don't be surprised if it does not work very well at first. Use the keyboard to manually edit the text in the box until it says what was intended to say. Then hit the "Learn" button. It will try to do better at understanding next time! One may also train personalized grammar by pasting in gobs of text from previously authored websites and documents.

It seems that the PocketSphinx folks were trying to add support for capitalized words. If 
there is a word in the dictionary which could also be capitalized as part of a proper name, 
as in "New" from "New 
Mexico" it is enough to insert a duplicate, capitalized entry into the dictionary after the 
original like so:

```
    new  N UW
    New  N UW
```

After this, it is possible to retrain the system by using the capatalized form in a few 
sentences and pressing the Learn button. 
PocketSphinx will henceforth decide the capitalization depending on the context in which it appears. We tested it and it works! It capitalizes words like "New Mexico" and "The United States of America" but does not capitalize "altered states" nor "new pants". This is a wild idea, but maybe we could make a dictionary containing _both_ capitalized and un-capitalized words. That would save us the effort of going through and capitalizing all the proper names. The only question is would the resulting dictionary be too big? The solution is probably to propose a patch to make make PocketSphinx ignore case in the dictionary, using the capatalization as it is found in the corpus, not the dictionary.

Don't worry if PocketSphinx learns bad grammar. It's not strictly necessary, but our corpus file, "lm/freespeech.ref.txt" may be manually corrected if it develops poor speech habits. Changes will apply next time anybody presses the "Learn" button.

The language model may be further [tweaked and improved] (http://www.speech.cs.cmu.edu/SLM/toolkit_documentation.html#evallm).

## Dictionary

If there is a word that FreeSpeech stubbornly refuses to recognize, even after teaching it 
with several sentences, edit the dictionary: "custom.dic"

Sometimes the dictionary pronunciation can be little bit off. Notice that some other words have alternate pronunciations denoted with (2). Go ahead and change the pronunciation or add an alternate and see if it doesn't improve immediately the next time the program starts.

Our dictionary is based on Pocketsphinx's cmu07a.dic because it contains punctuation, such 
".full-stop" and "?question-mark"). See "custom.dic" for the list of punctuation and 
their pronunciations. Adding new words to the dictionary may be done manually, along with their phonetic representation, but we are working on incorporating a word trainer.

More about the CMU Pronouncing Dictionary
http://www.speech.cs.cmu.edu/cgi-bin/cmudict

## Security and privacy

FreeSpeech does not send any information over the network. Speech recognition is done locally using pocketsphinx. Learned speech patterns are stored in "plain text" format in "$HOME/.config/FreeSpeech/freespeech.ref.txt". Although the file should not be accessible to other users, it is nevertheless good practice not to teach FreeSpeech sensitive or private information like passwords, especially if others share access to the PC.
