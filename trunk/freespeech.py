#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
# FreeSpeech
# Continuous realtime speech recognition and control via pocketsphinx
# Copyright (c) Henry Kroll III, http://www.TheNerdShow.com

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pygtk
pygtk.require('2.0')
import gtk

import gobject
import pygst
pygst.require('0.10')
gobject.threads_init()
import gst
import subprocess
import os
import re

lang_ref= 'lm/freespeech.ref.txt'
vocab   = 'lm/freespeech.vocab'
idngram = 'lm/freespeech.idngram'
arpa    = 'lm/freespeech.arpa'
dmp     = 'lm/freespeech.dmp'

def collapse_punctuation(hyp, started):
    index = 0
    words = hyp.split()
    words[0] = words[0].capitalize()
    # remove the extra text to the right of the punctuation mark
    while True:
        if (index >= len(words)):
            break
        word = words[index]
        if (re.match("^\W\w", word)):
            words[index] = word[0]
        index += 1
    hyp = " ".join(words)
    hyp = hyp.replace(" ...ellipsis"," ...")
    hyp = re.sub(r" ([^\w\s]{1,3})\s*",r"\1 ",hyp)
    hyp = re.sub(r"([({[]) ",r" \1",hyp)
    if re.match(r"\w",hyp[0]) and started:
        space = " "
    else:
        space = ""
    return space + hyp.strip()
    
def expand_punctuation(corpus):
    # tweak punctuation to match dictionary utterances
    for ind,line in enumerate(corpus):
        line = re.sub(r'--',          r'--dash',               line)
        line = re.sub(r'- ',          r'-hyphen ',             line)
        line = re.sub(r'`',           r'`agrave',              line)
        line = re.sub(r'=',           r'=equals-sign',         line)
        line = re.sub(r'>',           r'>greater-than-symbol', line)
        line = re.sub(r'<',           r'<less-than-symbol',    line)
        line = re.sub(r'\|',          r'\|pipe-symbol',        line)
        line = re.sub(r'\. \. \.',    r'...ellipsis',          line)
        line = re.sub(r' \. ',        r' .dot ',               line)
        line = re.sub(r'\.$',         r'.period',              line)
        line = re.sub(r',',           r',comma',               line)
        line = re.sub(r':',           r':colon',               line)
        line = re.sub(r'\?',          r'?question-mark',       line)
        line = re.sub(r'"',           r'"quote',               line)
        line = re.sub(r'([\w]) \' s', r"\1's",                 line)
        line = re.sub(r' \'',         r' \'single-quote',      line)
        line = re.sub(r'\(',          r'(left-paren',          line)
        line = re.sub(r'\)',          r')right-paren',         line)
        line = re.sub(r'\[',          r'[left-bracket',        line)
        line = re.sub(r'\]',          r']right-bracket',       line)
        line = re.sub(r'{',           r'{left-brace',          line)
        line = re.sub(r'}',           r'}right-brace',         line)
        line = re.sub(r'!',           r'!exclamation-point',   line)
        line = re.sub(r';',           r';semi-colon',          line)
        line = re.sub(r'/',           r'/slash',               line)
        line = re.sub(r'%',           r'%percent',             line)
        line = re.sub(r'#',           r'#sharp-sign',          line)
        line = re.sub(r'@',           r'@at-symbol',           line)
        line = re.sub(r'\*',          r'*asterisk',            line)
        line = re.sub(r'\^',          r'^carrat',              line)
        line = re.sub(r'&',           r'&ampersand',           line)
        line = re.sub(r'\$',          r'$dollar-sign',         line)
        line = re.sub(r'\+',          r'+plus-symbol',         line)
        line = re.sub(r'®',           r'®registered-symbol',   line)
        line = re.sub(r'_',           r'_underscore',          line)
        line = re.sub(r'\\',          r'\backslash',           line)
        line = re.sub(r'^',           r'<s> ',                 line)
        line = re.sub(r'$',           r' </s>',                line)
        if line.strip():
            corpus[ind] = line
    return corpus

def prepare_corpus(txt):
    txt.begin_user_action()
    txt_bounds = txt.get_bounds()
    text = txt.get_text(txt_bounds[0],txt_bounds[1])
    # break on end of sentence
    text = re.sub(r'(\w[.:;!])\s+(\w)',r'\1\n\2',text)
    text = re.sub(r'\n+',r'\n',text)
    corpus= re.split(r'\n', text)       
    for ind,tex in enumerate(corpus):
        # try to remove blank lines
        tex = tex.strip()
        if len(tex) == 0:
            try:
                corpus.remove(ind)
            except:
                pass
            continue;
        # lower case maybe
        if len(tex) > 1 and tex[1] > 'Z':
            tex = tex[0].lower() + tex[1:]
        # separate punctuation marks into 'words'
        # by adding spaces between them
        tex = re.sub(r'\s*([^\w\s]|[_])\s*', r' \1 ',tex)
        tex = re.sub(r'\s+',' ',tex)
        # fixme: needs more unicode -> dictionary replacements
        tex = tex.replace("’","'apostrophe")
        tex = tex.strip()
        corpus[ind] = tex
    return expand_punctuation(corpus)

class freespeech(object):
    """GStreamer/PocketSphinx Demo Application"""
    def __init__(self):
        """Initialize a freespeech object"""
        self.init_gui()
        self.init_prefs()
        self.init_errmsg()
        self.init_gst()

    def init_gui(self):
        self.undo = [] # Say "Scratch that" or "Undo that"
        """Initialize the GUI components"""
        self.window = gtk.Window()
        self.icon = gtk.gdk.pixbuf_new_from_file("icon.png")
        self.window.connect("delete-event", gtk.main_quit)
        self.window.set_default_size(400,200)
        self.window.set_border_width(10)
        self.window.set_icon(self.icon)
        vbox = gtk.VBox()
        hbox = gtk.HBox(homogeneous=True)
        self.textbuf = gtk.TextBuffer()
        self.text = gtk.TextView(self.textbuf)
        self.text.set_wrap_mode(gtk.WRAP_WORD)
        vbox.pack_start(self.text, True, True, 5)
        vbox.pack_end(hbox, False, False)
        self.button = gtk.Button("Learn")
        self.button.connect('clicked', self.learn_new_words)
        self.button2 = gtk.ToggleButton("Mute")
        self.button2.connect('clicked', self.mute)
        self.button2.set_active(True)
        hbox.pack_start(self.button, True, False, 5)
        hbox.pack_start(self.button2, True, False, 5)
        self.window.add(vbox)
        self.window.add(hbox)
        self.window.show_all()

    def init_prefs(self):
        """Initialize new GUI components"""
        # self.prefswindow = gtk.Window()
        # self.prefswindow.connect("delete-event", gtk.Widget.hide_on_delete)
        # self.prefswindow.set_default_size(400,200)
        # self.prefswindow.set_border_width(10)
        # vbox = gtk.VBox()
        # self.textbuf2 = gtk.TextBuffer()
        # self.text2 = gtk.TextView(self.textbuf2)
        # self.text2.set_wrap_mode(gtk.WRAP_WORD)
        # vbox.pack_start(self.text2)
        # self.textbuf2.begin_user_action()
        # self.textbuf2.insert_at_cursor(str(dir(self.prefswindow)))
        # self.prefswindow.add(vbox)
        me = self.prefsdialog = gtk.Dialog("Preferences", None,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
            gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        me.set_default_size(400,300)
        me.label = gtk.Label("Nice label")
        me.vbox.pack_start(me.label)
        me.label.show()
        me.checkbox = gtk.CheckButton("Useless checkbox")
        me.action_area.pack_end(me.checkbox)
        me.checkbox.show()
        
    def init_errmsg(self):
        me = self.errmsg = gtk.Dialog("Error", None,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
            gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        me.set_default_size(400,200)
        me.label = gtk.Label("Nice label")
        me.vbox.pack_start(me.label)
        me.label.show()
        
    def init_gst(self):
        """Initialize the speech components"""
        self.pipeline = gst.parse_launch('gconfaudiosrc ! audioconvert ! audioresample '
                                         + '! vader name=vad auto-threshold=true '
                                         + '! pocketsphinx name=asr ! fakesink')
        asr = self.pipeline.get_by_name('asr')
        
        """Load custom dictionary and language model"""
        asr.set_property('dict', 'custom.dic')
        
        # The language model dmp that came with pocketsphinx works OK...
        # asr.set_property('lm', '/usr/share/pocketsphinx/model/lm/en_US/wsj0vp.5000.DMP')
        # but it is too large and lacks accuracy so we use our own
        asr.set_property('lm', os.getcwd() + '/' + dmp)
        
        # Adapt pocketsphinx to your voice for better accuracy.
        # See http://cmusphinx.sourceforge.net/wiki/tutorialadapt
        
        # The tutorial contains broken download links!
        # Hit me up for the missing files
        # asr.set_property('hmm', '../sphinx/hub4wsj_sc_8kadapt')
        
        asr.connect('partial_result', self.asr_partial_result)
        asr.connect('result', self.asr_result)
        asr.set_property('configured', True)

        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message::application', self.application_message)

        #self.pipeline.set_state(gst.STATE_PAUSED)
        self.pipeline.set_state(gst.STATE_PLAYING)

    def asr_partial_result(self, asr, text, uttid):
        """Forward partial result signals on the bus to the main thread."""
        struct = gst.Structure('partial_result')
        struct.set_value('hyp', text)
        struct.set_value('uttid', uttid)
        asr.post_message(gst.message_new_application(asr, struct))

    def asr_result(self, asr, text, uttid):
        """Forward result signals on the bus to the main thread."""
        struct = gst.Structure('result')
        struct.set_value('hyp', text)
        struct.set_value('uttid', uttid)
        asr.post_message(gst.message_new_application(asr, struct))

    def application_message(self, bus, msg):
        """Receive application messages from the bus."""
        msgtype = msg.structure.get_name()
        if msgtype == 'partial_result':
            self.partial_result(msg.structure['hyp'], 
            msg.structure['uttid'])
        elif msgtype == 'result':
            self.final_result(msg.structure['hyp'], 
            msg.structure['uttid'])
            #self.pipeline.set_state(gst.STATE_PAUSED)
            #self.button.set_active(False)

    def partial_result(self, hyp, uttid):
        """Delete any previous selection, insert text and select it."""
        # All this stuff appears as one single action
        self.textbuf.begin_user_action()
        self.textbuf.delete_selection(True, self.text.get_editable())
        self.textbuf.insert_at_cursor(hyp)
        ins = self.textbuf.get_insert()
        iter = self.textbuf.get_iter_at_mark(ins)
        iter.backward_chars(len(hyp))
        self.textbuf.move_mark(ins, iter)
        self.textbuf.end_user_action()

    def final_result(self, hyp, uttid):
        """Insert the final result."""
        # All this stuff appears as one single action
        txt = self.textbuf
        self.textbuf.begin_user_action()
        txt.delete_selection(True, self.text.get_editable())
        txt_bounds = txt.get_bounds()
        # Fix punctuation
        if not self.do_command(hyp):
            hyp = collapse_punctuation(hyp, not txt_bounds[1].is_start())
            txt.insert_at_cursor(hyp)
        txt.end_user_action()

    def learn_new_words(self, button):
        """ Learn new words, jargon, or other language
        
          1. Add the word(s) to the dictionary, if necessary.
          2. Type or paste sentences containing the word(s).
          2. Use the word(s) differently in at least 3 sentences.
          3. Click the "Learn" button. """
        
        # prepare a text corpus from the textbox
        corpus = prepare_corpus(self.textbuf)
        
        # append it to the language reference
        with open(lang_ref,'a+') as f:
            for line in corpus:
                f.write(line + '\n')
        
        # compile a vocabulary
        if subprocess.call('text2wfreq -verbosity 2 -hash 1000000 < ' \
            + lang_ref + ' | wfreq2vocab -records 10000 > ' + vocab, \
            shell=True):
            self.err('Trouble writing ' + vocab)
        
        # update the idngram
        if subprocess.call('text2idngram -vocab ' + vocab + \
            ' -n 3 < ' + lang_ref + ' > ' + idngram, shell=True):
            self.err('Trouble writing ' + idngram)
        
        # (re)build arpa language model
        if subprocess.call('idngram2lm -idngram ' + idngram + \
            ' -vocab ' + vocab + ' -arpa ' + arpa + ' -vocab_type 1' \
            ' -linear', shell=True):
            self.err('Trouble writing ' + arpa)
        
        # convert to dmp
        if subprocess.call('sphinx_lm_convert -i ' + arpa + \
            ' -o ' + dmp + ' -ofmt arpa', shell=True):
            self.err('Trouble writing ' + dmp)
        
        # load the dmp
        asr = self.pipeline.get_by_name('asr')
        self.pipeline.set_state(gst.STATE_PAUSED)
        asr.set_property('configured', False)
        asr.set_property('lm', os.getcwd() + '/' + dmp)
        asr.set_property('configured', True)
        self.pipeline.set_state(gst.STATE_PLAYING)
        
    def mute(self, button):
        """Handle button presses."""
        if button.get_active():
            button.set_label("Mute")
            self.pipeline.set_state(gst.STATE_PLAYING)
        else:
            button.set_label("Speak")
            vader = self.pipeline.get_by_name('vad')
            vader.set_property('silent', True)
            self.pipeline.set_state(gst.STATE_PAUSED)

    def err(self, errormsg):
        self.errmsg.label.set_text(errormsg)
        self.errmsg.run()
        self.errmsg.hide()
    
    def do_command(self, hyp):
        # todo: load command list from file?
        commands = {'file quit': gtk.main_quit, \
                    'file preferences': self.launch_preferences, \
                    'editor clear': self.clear_edits}
        if commands.has_key(hyp):
            commands[hyp]()
            return True
        return False

    def launch_preferences(self):
        self.prefsdialog.run()
        self.prefsdialog.hide()
    def clear_edits(self):
        txt = self.textbuf
        txt.set_text('')
        print('cleared')


app = freespeech()
gtk.main()
