#Frequently Asked Questions

Q. Can you use freespeech to transcribe existing audio files?

A. No, but [Pythonism](https://pythonism.wordpress.com/2013/06/06/pocketsphinx-voice-recognition-with-python/) has a small Python module that would be easy to incorporate into FreeSpeech if more people desire this functionality. It would add dependencies on [Pyaudio](http://people.csail.mit.edu/hubert/pyaudio/#downloads) and [Portaudio](http://www.portaudio.com/). We're not sure if we want to go that direction because it might make it harder to set up, document, and support (we're rafting together enough extreme alpha software as it is), but it would still be portable, open, and cross-platform. Leave a comment to us know if you want it in the next version.

Here are some other possible solutions.

  * [Guapol](https://wiki.gnome.org/Gaupol/SpeechRecognition) can transcribe video files. It might work on audio or if you can convert audio to video.
  * https://github.com/pranavrc/audio-transcribe
  * http://stackoverflow.com/questions/9404099/python-speech-compare
  * https://code.google.com/p/dragonfly/

# Operating System #

Q. "What operating system are you developing it for?"

A. Program ought to work on multiple platforms, Windows, Linux, Android, Mac..., providing they can successfully compile or otherwise install the following prerequisites:
  * gstreamer multimedia framework
  * pocketsphinx
  * [CMU-Cambridge Statistical Language Modeling Toolkit v2](http://www.speech.cs.cmu.edu/SLM/toolkit_documentation.html)

# Graphical Interface #

Q. "I personally know quite a few graphics artists if you already have graphics in mind, I'd be happy to refer yo to them."

A. I'm no stranger to graphics myself, but the project is currently open to contributions...

# Todo #

Q. "Can I contribute? What needs to be done around here?"

A. There is much to be done. This is just the beginning. Here are some of the areas I will be working on over the coming months.

When a user types or pastes text into the editor, I would like it to...
  * Have a button to check for unrecognised words
  * Allow editing the dictionary and pronunciations
  * Automatically generate or suggest new pronunciations

$$ Yes, FreeSpeech could use some funding! $$. Send [bitcoin](http://bitcoin.org/) to 1KjEBYUh9WJ2z8UBhhu5hX8t6XTsBUFH4G