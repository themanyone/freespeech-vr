## About ##

FreeSpeech is a free and open-source (FOSS) cross-platform dictation, voice transcription, and realtime speech recognition application for the desktop. Offline speaker-independent voice recognition with dynamic language learning capability using the PocketSphinx speech recognition engine.

## Installation ##

See [Installation](Installation.md) instructions.

## Improving accuracy ##

The biggest improvements in accuracy have been achieved by adjusting the microphone position. The volume level is adjusted automatically and tweaking it is not likely to improve much. You may try making a recording with [Audacity](http://audacity.sourceforge.net) and checking the noise levels to make sure it sounds like intelligible speech when played back. If your distro uses pulseaudio, pavucontrol may be needed to adjust the sound input.

Adapt PocketSphinx to your voice for better accuracy.
See http://cmusphinx.sourceforge.net/wiki/tutorialadapt

### Language corpus ###

The language corpus that ships with this download, "freespeech.ref.txt" is likely to be very limited. Our excuse is that the small size saves memory while providing room to learn your spoken grammar. Don't be surprised if it does not work very well for you at first. Use the keyboard to manually edit the text in the box until it says what you intended to say. Then hit the "Learn" button. It will try to do better at understanding you next time! You may also train it new grammar by pasting in gobs of text from websites and documents. This works best when the documents are ones that you have created, so it can learn your manner of speaking**(Warning: See Security and privacy section).**

It seems that the PocketSphinx folks were trying to add support for capitalized words. If there is a word like "new" in the dictionary, freespeech.dic, which could also be capitalized, as in "New Mexico" it is enough to add a capitalized copy to the dictionary like so:
```
    new  N UW
    New  N UW
```
Now PocketSphinx will decide the capitalization depending on the context in which it appears in the text corpus. We tested it and it works! It capitalizes words like "New Mexico" and "The United States of America" but does not capitalize "altered states" nor "new pants". This is a wild idea, but maybe we could make a dictionary containing _both_ capitalized and un-capitalized words. That would save us the effort of going through and capitalizing all the proper names. The only question is would the resulting dictionary be too big? The solution is probably to propose a patch to make make PocketSphinx ignore case in the dictionary, using the word or acronym as it is found in the corpus, not the dictionary.

Don't worry if you inadvertently teach PocketSphinx bad grammar. It's not strictly necessary, but our corpus file, "lm/freespeech.ref.txt" may be manually corrected if it develops bad speech habits. Changes will apply next time you hit the "Learn" button.

The language model may be further [tweaked and improved](http://www.speech.cs.cmu.edu/SLM/toolkit_documentation.html#evallm).

### Dictionary ###

If there is a word that it stubbornly refuses to recognize, even after teaching it with several sentences, you may need to edit the dictionary: "freespeech.dic"

Sometimes the dictionary pronunciation can be little bit off. You will notice that some other words have alternate pronunciations denoted with (2). Go ahead and add an alternate and see if it doesn't improve immediately the next time the program starts.

This dictionary is based on Pocketsphinx's cmu07a.dic because it contains punctuation (Can you say ".full-stop" or "?question-mark") and some capitalized words. Open up "freespeech.dic" with a text editor to see the list of punctuation and their updated pronunciations. Adding new words to the dictionary may be done manually and customized to the way you wish to pronounce them, but we are working on incorporating a word trainer.

About the CMU Pronouncing Dictionary
http://www.speech.cs.cmu.edu/cgi-bin/cmudict

## Security and privacy ##

Learned speech patterns (from pressing the learn button) are stored in "plain text" format in "lm/freespeech.ref.txt". You probably do not want to teach FreeSpeech passwords, or private details of your life, especially if other people will have access to your PC. This file may be edited (whew)!