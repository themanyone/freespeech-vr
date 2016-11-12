#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# FreeSpeech
# Copyright (C) 2016 Henry Kroll III, http://www.TheNerdShow.com
# Continuous realtime speech recognition and control

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

# ATTN: This version requires Gstreamer-1.0 and python3-gobject
# Compile sphinxbase and pocketsphinx from source
# since Gstreamer-1.0 packages are probably not available yet.
# See https://sourceforge.net/p/cmusphinx/discussion/help/thread/6a286ad1/

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, Gtk, Gdk
GObject.threads_init()
Gst.init(None)

import subprocess, time
import platform, os, shutil, sys, codecs
import re
import json
from send_key import *

""" global variables """
appname = 'FreeSpeech'
refdir = 'lm'

# hmmm, where to put files? How about XDG_CONFIG_HOME?
# This will work on most Linux
if 'XDG_CONFIG_HOME' in os.environ:
    confhome = os.environ['XDG_CONFIG_HOME']
    confdir  = os.path.join(confhome, appname)
else:
    if 'HOME' in os.environ:
        confhome = os.path.join(os.environ['HOME'],".config")
        confdir  = os.path.join(confhome, appname)
    else:
        confdir = refdir

# reference files written by this application
lang_ref= os.path.join(confdir, 'freespeech.ref.txt')
vocab   = os.path.join(confdir, 'freespeech.vocab')
idngram = os.path.join(confdir, 'freespeech.idngram')
arpa    = os.path.join(confdir, 'freespeech.arpa')
dmp     = os.path.join(confdir, 'freespeech.dmp')
cmdtext = os.path.join(confdir, 'freespeech.cmd.txt')
cmdjson = os.path.join(confdir, 'freespeech.cmd.json')
dic     = os.path.join(confdir, 'custom.dic')

class freespeech(object):
    """GStreamer/PocketSphinx Continuous Speech Recognition"""
    def __init__(self):
        """Initialize a freespeech object"""
        # place to store the currently open file name, if any
        self.open_filename=''
        # create confdir if not exists
        if not os.access(confdir, os.R_OK):
            os.mkdir(confdir)
        # copy lang_ref to confdir if not exists
        if not os.access(lang_ref, os.R_OK):
            lang_ref_orig = os.path.join(refdir, 'freespeech.ref.txt')
            shutil.copy(lang_ref_orig, lang_ref)
        # copy dictionary to confdir if not exists
        if not os.access(dic, os.R_OK):
            shutil.copy('custom.dic', dic)
        # initialize components
        self.init_gui()
        self.init_errmsg()
        self.init_prefs()
        self.init_file_chooser()
        self.init_gst()

    def init_gui(self):
        self.undo = [] # Say "Scratch that" or "Undo that"
        """Initialize the GUI components"""
        self.window = Gtk.Window()
        # Change to executable's dir
        if os.path.dirname(sys.argv[0]):
            os.chdir(os.path.dirname(sys.argv[0]))     
        #self.icon = Gdk.pixbuf_new_from_file(appname+".png")
        self.window.connect("delete-event", Gtk.main_quit)
        self.window.set_default_size(400, 200)
        self.window.set_border_width(10)
        #self.window.set_icon(self.icon)
        self.window.set_title(appname)
        vbox = Gtk.VBox()
        hbox = Gtk.HBox(homogeneous=True)
        self.text = Gtk.TextView()
        self.textbuf = self.text.get_buffer()
        self.text.set_wrap_mode(Gtk.WrapMode.WORD)
        self.scroller = Gtk.ScrolledWindow(None, None)
        self.scroller.set_policy(Gtk.ScrollablePolicy.NATURAL, Gtk.ScrollablePolicy.NATURAL)
        self.scroller.add(self.text)
        vbox.pack_start(self.scroller, True, True, 5)
        vbox.pack_end(hbox, False, False, False)
        self.button0 = Gtk.Button("Learn")
        self.button0.connect('clicked', self.learn_new_words)
        self.button1 = Gtk.ToggleButton("Send keys")
        self.button1.connect('clicked', self.toggle_echo)
        self.button2 = Gtk.Button("Show commands")
        self.button2.connect('clicked', self.show_commands)
        self.button3 = Gtk.ToggleButton("Mute")
        self.button3.connect('clicked', self.mute)
        hbox.pack_start(self.button0, True, False, 0)
        hbox.pack_start(self.button1, True, False, 0)
        hbox.pack_start(self.button2, True, False, 0)
        hbox.pack_start(self.button3, True, False, 0)
        self.window.add(vbox)
        self.window.show_all()

    def init_file_chooser(self):
        self.file_chooser = Gtk.FileChooserDialog(title="File Chooser",
        parent=self.window, action=Gtk.FileChooserAction.OPEN,
        buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OK, Gtk.ResponseType.OK))
    
    def init_commands(self):
            self.commands = {'file quit': 'Gtk.main_quit',
                'file open': 'self.file_open',
                'file save': 'self.file_save',
                'file save as': 'self.file_save_as',
                'show commands': 'self.show_commands',
                'editor clear': 'self.clear_edits',
                'clear edits': 'self.clear_edits',
                'file close': 'self.clear_edits',
                'delete': 'self.delete',
                'select': 'self.select',
                'send keys' : 'self.toggle_keys',
                'insert': 'self.insert',
                'go to the end': 'self.done_editing',
                'done editing': 'self.done_editing',
                'scratch that': 'self.scratch_that',
                'back space': 'self.backspace',
                'new paragraph':  'self.new_paragraph',
            }
            self.write_prefs()
            try:
                self.prefsdialog.checkbox.set_active(False)
            except:
                pass

    def init_prefs(self):
        """Initialize new GUI components"""
        me = self.prefsdialog = Gtk.Dialog("Command Preferences", self.window,
            Gtk.DialogFlags.DESTROY_WITH_PARENT,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OK, Gtk.ResponseType.OK))
        me.set_default_size(200, 300)
        if not os.access(cmdjson, os.R_OK):
            #~ write some default commands to a file if it doesn't exist
            self.init_commands()
        else:
            self.read_prefs()
        
        me.label = Gtk.Label( \
"Double-click to change command wording.\n\
If new commands don't work click the learn button to train them.")
        me.vbox.pack_start(me.label, False, False, False)
        me.checkbox=Gtk.CheckButton("Restore Defaults")
        me.checkbox.show()
        me.action_area.pack_start(me.checkbox, False, False, 0)
        me.liststore=Gtk.ListStore(str, str)
        me.liststore.set_sort_column_id(0, 0)
        me.tree=Gtk.TreeView(me.liststore)
        editable = Gtk.CellRendererText()
        fixed = Gtk.CellRendererText()
        editable.set_property('editable', True)
        editable.connect('edited', self.edited_cb)
        # me.connect("draw", self.prefs_expose)
        me.liststore.clear()
        gtk = Gtk
        for x,y in list(self.commands.items()):
            me.liststore.append([x,eval(y).__doc__])
        me.connect("response", self.prefs_response)
        me.connect("delete_event", self.prefs_response)
        column = Gtk.TreeViewColumn("Spoken command",editable,text=0)
        column.set_fixed_width(200)
        me.tree.append_column(column)
        column = Gtk.TreeViewColumn("What it does",fixed,text=1)
        me.tree.append_column(column)
        me.vbox.pack_end(me.tree, False, False, 0)
        me.label.show()
        me.tree.show()
        self.commands_old = self.commands
        me.show_all()

    def prefs_expose(self, me, event):
        """ callback when prefs window is shown """
        # populate commands list with documentation
        me.liststore.clear()
        for x,y in list(self.commands.items()):
            me.liststore.append([x,y])
            print([x,y])
        
    def write_prefs(self):
        """ write command list to file """
        with codecs.open(cmdjson, encoding='utf-8', mode='w') as f:
            f.write(json.dumps(self.commands))
        # write commands text, so we don't have to train each time
        with codecs.open(cmdtext, encoding='utf-8', mode='w') as f:
            for j in list(self.commands.keys()):
                f.write('<s> '+j+' </s>\n')

    def read_prefs(self):
        """ read command list from file """
        with codecs.open(cmdjson, encoding='utf-8', mode='r') as f:
            self.commands=json.loads(f.read())
            
    def prefs_response(self, me, event):
        """ make prefs dialog non-modal by using response event
            instead of run() method, which waited for input """
        if me.checkbox.get_active():
            self.init_commands()
        else:
            if event!=Gtk.ResponseType.OK:
                self.commands = self.commands_old
            else:
                self.write_prefs()
        me.hide()
        return True
        
    def edited_cb(self, cellrenderertext, path, new_text):
        """ callback activated when treeview text edited """
        #~ self.prefsdialog.tree.path=new_text
        liststore=self.prefsdialog.liststore
        treeiter = liststore.get_iter(path)
        old_text = liststore.get_value(treeiter,0)
        if new_text not in self.commands:
            liststore.set_value(treeiter,0,new_text)
            self.commands[new_text]=self.commands[old_text]
            del(self.commands[old_text])
            #~ print(old_text, new_text)
        
    def init_errmsg(self):
        me = self.errmsg = Gtk.Dialog("Error", None,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OK, Gtk.ResponseType.OK))
        me.set_default_size(400, 200)
        me.label = Gtk.Label("Nice label")
        me.vbox.pack_start(me.label, False, False, False)
        me.label.show()
        
    def element_message(self, bus, msg):
        """Receive element messages from the bus."""
        msgtype = msg.get_structure().get_name()
        if msgtype != 'pocketsphinx':
            return

        if msg.get_structure().get_value('final'):
            self.final_result(msg.get_structure().get_value('hypothesis'), msg.get_structure().get_value('confidence'))
            # self.pipeline.set_state(Gst.State.PAUSED)
            # self.button1.set_active(False)
        elif msg.get_structure().get_value('hypothesis'):
            self.partial_result(msg.get_structure().get_value('hypothesis'))
        
    def init_gst(self):
        """Initialize the speech components"""
        self.pipeline = Gst.parse_launch('autoaudiosrc ! ladspa-gate-1410-so-gate threshold=200.0 decay=2.0 hold=2.0 attack=0.01 ! audioconvert ! audioresample ! pocketsphinx name=asr ! fakesink')
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message::element', self.element_message)
        self.pipeline.set_state(Gst.State.PAUSED)

        asr = self.pipeline.get_by_name('asr')
        
        """Load custom dictionary and language model"""
        asr.set_property('dict', dic)
        
        # The language model that came with pocketsphinx works OK...
        # asr.set_property('lm', '/usr/share/pocketsphinx/model/lm/en_US/wsj0vp.5000.DMP')
        # but it does not contain editing commands, so we make our own
        if not os.access(dmp, os.R_OK): # create if not exists
                self.learn_new_words(None)
        asr.set_property('lm', dmp)
        
        # Adapt pocketsphinx to your voice for better accuracy.
        # See http://cmusphinx.sourceforge.net/wiki/tutorialadapt_
        
        # asr.set_property('hmm', '../sphinx/hub4wsj_sc_8kadapt')
        
        #fixme: write an acoustic model trainer
        
        self.pipeline.set_state(Gst.State.PLAYING)

    def learn_new_words(self, button):
        """ Learn new words, jargon, or other language
        
          1. Add the word(s) to the dictionary, if necessary.
          2. Type or paste sentences containing the word(s).
          2. Use the word(s) differently in at least 3 sentences.
          3. Click the "Learn" button. """
        
        # prepare a text corpus from the textbox
        corpus = self.prepare_corpus(self.textbuf)
        
        # append it to the language reference
        with codecs.open(lang_ref, encoding='utf-8', mode='a+') as f:
            for line in corpus:
                if line:
                    f.write(line + '\n')
        
        # cat command
        if platform.system()=='Windows':
            catcmd = 'type '
        else:
            catcmd = 'cat '
        
        # compile a vocabulary
        # http://www.speech.cs.cmu.edu/SLM/toolkit_documentation.html#text2wfreq
        if subprocess.call(catcmd + cmdtext + ' ' + cmdtext + ' ' + cmdtext + ' ' + cmdtext + ' ' + lang_ref + '|text2wfreq -verbosity 2' \
        + ' |wfreq2vocab -top 20000 -records 100000 > ' + vocab, shell=True):
            self.err('Trouble writing ' + vocab)
        # update the idngram\
        # http://www.speech.cs.cmu.edu/SLM/toolkit_documentation.html#text2idngram
        if subprocess.call('text2idngram -vocab ' + vocab + \
            ' -n 3 < ' + lang_ref + ' > ' + idngram, shell=True):
            self.err('Trouble writing ' + idngram)
        
        # (re)build arpa language model
        # http://drupal.cs.grinnell.edu/~stone/courses/computational-linguistics/ngram-lab.html
        if subprocess.call('idngram2lm -idngram -n 3 -verbosity 2 ' + idngram + \
            ' -vocab ' + vocab + ' -arpa ' + arpa + ' -vocab_type 1' \
            ' -good_turing', shell=True):
            self.err('Trouble writing ' + arpa)

        # convert to dmp
        if subprocess.call('sphinx_lm_convert -i ' + arpa + \
            ' -o ' + dmp + ' -ofmt dmp', shell=True):
            self.err('Trouble writing ' + dmp)
        
        # fixme: reload the dmp
        self.pipeline.set_state(Gst.State.PAUSED)
        #asr = self.pipeline.get_by_name('asr')
        #asr.set_property('lm', dmp)
        if not self.button3.get_active():
            self.pipeline.set_state(Gst.State.PLAYING)
        
    def mute(self, button):
        """Handle button presses."""
        if not button.get_active():
            button.set_label("Mute")
            self.pipeline.set_state(Gst.State.PLAYING)
        else:
            button.set_label("Speak")
            self.pipeline.set_state(Gst.State.PAUSED)
    
    def toggle_echo(self, button):
        """ echo keystrokes to the desktop """
        if not button.get_active():
            button.set_label("Send keys")
            button.set_active(False)
        else:
            button.set_label("Stop sending")
            button.set_active(True)

    def toggle_keys(self):
        """ echo keystrokes to the desktop """
        self.button1.set_active(True - self.button1.get_active())
        return True

    def collapse_punctuation(self, txt, starting):
        index = 0
        insert = self.textbuf.get_iter_at_mark(self.textbuf.get_insert())
        prior = self.textbuf.get_iter_at_offset(insert.get_offset() - 2)
        next = self.textbuf.get_iter_at_offset(insert.get_offset() + 1)
        nextchar = self.textbuf.get_text(insert, next, False)
        lastchars = self.textbuf.get_text(prior, insert, False)
        words = txt.split()
        # remove the extra text to the right of the punctuation mark
        while True:
            if (index >= len(words)):
                break
            word = words[index]
            if (re.match("^\W\w", word)):
                words[index] = word[0]
            index += 1
        txt = " ".join(words)
        txt = txt.replace(" ...ellipsis", " ...")
        # move space before punctuation to after
        txt = re.sub(r" ([^\w\s]+)\s*", r"\1 ", txt)
        # remove space after opening bracket
        txt = re.sub(r"([({[]) ", r" \1", txt).strip()
        # capitalize if necessary
        if (starting or re.match(".*[.?!:]",lastchars)) and len(txt) > 1:
            txt = txt[0].capitalize() + txt[1:]
        # add space to beginning if necessary
        if txt and re.match("[^.?!:,\-\"';^@]",txt[0]) and len(lastchars) and lastchars[-1] != " " and not starting:
            txt = " " + txt
        # add space to end if necessary
        # abort if text selected
        if not self.textbuf.get_selection_bounds():
            if len(nextchar) and (nextchar != " "):
                txt = txt + " "
        return txt
        
    def expand_punctuation(self, corpus):
        # tweak punctuation to match dictionary utterances
        for ind, line in enumerate(corpus):
            line = re.sub(r'--',          r'--dash',                  line)
            line = re.sub(r'- ',          r'-hyphen ',                line)
            line = re.sub(r'`',           r'`agrave',                 line)
            line = re.sub(r'=',           r'=equals-sign',            line)
            line = re.sub(r'>',           r'>greater-than-symbol',    line)
            line = re.sub(r'<',           r'<less-than-symbol',       line)
            line = re.sub(r'\|',          r'\|pipe-symbol',           line)
            line = re.sub(r'\. \. \.',    r'...ellipsis',             line)
            line = re.sub(r' \. ',        r' .dot ',                  line)
            line = re.sub(r'\.$',         r'.period',                 line)
            line = re.sub(r',',           r',comma',                  line)
            line = re.sub(r':',           r':colon',                  line)
            line = re.sub(r'\?',          r'?question-mark',          line)
            line = re.sub(r'"',           r'"quote',                  line)
            line = re.sub(r'([\w]) \' s', r"\1's",                    line)
            line = re.sub(r" '",          r" 'single-quote",          line)
            line = re.sub(r'\(',          r'(left-paren',             line)
            line = re.sub(r'\)',          r')right-paren',            line)
            line = re.sub(r'\[',          r'[left-bracket',           line)
            line = re.sub(r'\]',          r']right-bracket',          line)
            line = re.sub(r'{',           r'{left-brace',             line)
            line = re.sub(r'}',           r'}right-brace',            line)
            line = re.sub(r'!',           r'!exclamation-point',      line)
            line = re.sub(r';',           r';semi-colon',             line)
            line = re.sub(r'/',           r'/slash',                  line)
            line = re.sub(r'%',           r'%percent',                line)
            line = re.sub(r'#',           r'#sharp-sign',             line)
            line = re.sub(r'@',           r'@at-symbol',              line)
            line = re.sub(r'\*',          r'*asterisk',               line)
            line = re.sub(r'\^',          r'^circumflex',             line)
            line = re.sub(r'&',           r'&ampersand',              line)
            line = re.sub(r'\$',          r'$dollar-sign',            line)
            line = re.sub(r'\+',          r'+plus-symbol',            line)
            line = re.sub(r'§',           r'§section-sign',           line)
            line = re.sub(r'¶',           r'¶paragraph-sign',         line)
            line = re.sub(r'¼',           r'¼and-a-quarter',          line)
            line = re.sub(r'½',           r'½and-a-half',             line)
            line = re.sub(r'¾',           r'¾and-three-quarters',     line)
            line = re.sub(r'¿',           r'¿inverted-question-mark', line)
            line = re.sub(r'×',           r'×multiplication-sign',    line)
            line = re.sub(r'÷',           r'÷division-sign',          line)
            line = re.sub(r'° ',          r'°degree-sign ',           line)
            line = re.sub(r'©',           r'©copyright-sign',         line)
            line = re.sub(r'™',           r'™trademark-sign',         line)            
            line = re.sub(r'®',           r'®registered-sign',      line)
            line = re.sub(r'_',           r'_underscore',             line)
            line = re.sub(r'\\',          r'\backslash',              line)
            line = re.sub(r'^(.)',        r'<s> \1',                  line)
            line = re.sub(r'(.)$',        r'\1 </s>',                 line)
            corpus[ind] = line
        return corpus

    def prepare_corpus(self, txt):
        txt.begin_user_action()
        self.bounds = self.textbuf.get_bounds()
        text = txt.get_text(self.bounds[0], self.bounds[1], True)
        # break on end of sentence
        text = re.sub(r'(\w[.:;?!])\s+(\w)', r'\1\n\2', text)
        text = re.sub(r'\n+', r'\n', text)
        corpus= re.split(r'\n', text)       
        for ind, tex in enumerate(corpus):
            # try to remove blank lines
            tex = tex.strip()
            if not re.match(r".*\w.*", tex):
                try:
                    corpus.remove(ind)
                except:
                    pass
                continue
            # lower case maybe
            if len(tex) > 1 and tex[1] > 'Z':
                tex = tex[0].lower() + tex[1:]
            # separate punctuation marks into 'words'
            # by adding spaces between them
            tex = re.sub(r'\s*([^\w\s]|[_])\s*', r' \1 ', tex)
            # except apostrophe followed by lower-case letter
            tex = re.sub(r"(\w) ' ([a-z])", r"\1'\2", tex)
            tex = re.sub(r'\s+', ' ', tex)
            tex = tex.strip()
            # fix the ʼunicode charactersʼ
            tex = tex.encode('ascii', 'ignore').decode()
            corpus[ind] = tex
        return self.expand_punctuation(corpus)

    def partial_result(self, hyp):
        """Show partial result on tooltip."""
        self.text.set_tooltip_text(hyp)

    def final_result(self, hyp, uttid):
        """Insert the final result into the textbox."""
        # All this stuff appears as one single action
        self.textbuf.begin_user_action()
        self.text.set_tooltip_text(hyp)
        # get bounds of text buffer
        self.bounds = self.textbuf.get_bounds()
        # Fix punctuation
        hyp = self.collapse_punctuation(hyp, \
        self.bounds[1].starts_line())
        # handle commands
        if not self.do_command(hyp):
            self.undo.append(hyp)
            self.textbuf.delete_selection(True, self.text.get_editable())
            self.textbuf.insert_at_cursor(hyp)
            # send keystrokes to the desktop?
            if self.button1.get_active():
                send_string(hyp)
                display.sync()
            print(hyp)
        ins = self.textbuf.get_insert()
        iter = self.textbuf.get_iter_at_mark(ins)
        self.text.scroll_to_iter(iter, 0, False, 0.5, 0.5)
        self.textbuf.end_user_action()

    """Process spoken commands"""
    def err(self, errormsg):
        self.errmsg.label.set_text(errormsg)
        self.errmsg.run()
        self.errmsg.hide()
    def show_commands(self, argument=None):
        """ show these command preferences """
        me=self.prefsdialog
        self.commands_old = self.commands
        me.show_all()
        me.present()
        return True # command completed successfully!
    def clear_edits(self):
        """ close file and start over without saving """
        self.textbuf.set_text('')
        self.open_filename=''
        self.window.set_title("FreeSpeech")
        self.undo = []
        return True # command completed successfully!
    def backspace(self):
        """ delete one character """
        start = self.textbuf.get_iter_at_mark(self.textbuf.get_insert())
        self.textbuf.backspace(start, False, True)
        return True # command completed successfully!
    def select(self,argument=None):
        """ select [text/all/to end] """
        if argument:
            if re.match("^to end", argument):
                start = self.textbuf.get_iter_at_mark(self.textbuf.get_insert())
                end = self.bounds[1]
                self.textbuf.select_range(start, end)
                return True # success
            search_back = self.searchback(self.bounds[1], argument)
            if re.match("^all", argument):
                self.textbuf.select_range(self.bounds[0], self.bounds[1])
                return True # success
            search_back = self.searchback(self.bounds[1], argument)
            if None == search_back:
                return True
            # also select the space before it
            search_back[0].backward_char()
            self.textbuf.select_range(search_back[0], search_back[1])
            return True # command completed successfully!
        return False
    def delete(self,argument=None):
        """ delete [text] or erase selection """
        if argument:
            # print("del "+argument)
            if re.match("^to end", argument):
                start = self.textbuf.get_iter_at_mark(self.textbuf.get_insert())
                end = self.bounds[1]
                self.textbuf.delete(start, end)
                return True # success
            search_back = self.searchback(self.bounds[1], argument)
            if None == search_back:
                return True
            # also select the space before it
            search_back[0].backward_char()
            self.textbuf.delete(search_back[0], search_back[1])
            return True # command completed successfully!
        self.textbuf.delete_selection(True, self.text.get_editable())
        return True # command completed successfully!
    def insert(self,argument=None):
        """ insert after [text] """      
        #~ return True # command completed successfully!
        arg = re.match('\w+(.*)', argument).group(1)
        search_back = self.searchback(self.bounds[1], arg)
        if None == search_back:
            return True
        if re.match("^after", argument):
            self.textbuf.place_cursor(search_back[1])
        elif re.match("^before", argument):
            self.textbuf.place_cursor(search_back[0])
        return True # command completed successfully!
    def done_editing(self):
        """ place cursor at end """
        self.textbuf.place_cursor(self.bounds[1])
        return True # command completed successfully!
    def scratch_that(self,argument=None):
        """ erase recent text """
        if self.undo:
            scratch = self.undo.pop(-1)
            search_back = self.bounds[1].backward_search( \
                scratch, Gtk.TextSearchFlags.TEXT_ONLY)
            if search_back:
                self.textbuf.select_range(search_back[0], search_back[1])
                self.textbuf.delete_selection(True, self.text.get_editable())
                if self.button1.get_active():
                    b="".join(["\b" for x in range(0,len(scratch))])
                    send_string(b)
                    display.sync()
                return True # command completed successfully!
        return False
    def new_paragraph(self):
        """ start a new paragraph """
        self.textbuf.insert_at_cursor('\n')
        if self.button1.get_active():
            send_string("\n")
            display.sync()
        return True # command completed successfully!
    def file_open(self):
        """ open file dialog """
        response=self.file_chooser.run()
        if response==Gtk.ResponseType.OK:
            self.open_filename=self.file_chooser.get_filename()
            with codecs.open(self.open_filename, encoding='utf-8', mode='r') as f:
                self.textbuf.set_text(f.read())
        self.file_chooser.hide()
        self.window.set_title("FreeSpeech | "+ os.path.basename(self.open_filename))
        return True # command completed successfully!
    def file_save(self):
        """ save text buffer to disk """
        if not self.open_filename:
            response=self.file_chooser.run()
            if response==Gtk.ResponseType.OK:
                self.open_filename=self.file_chooser.get_filename()
            self.file_chooser.hide()
            self.window.set_title("FreeSpeech | "+ os.path.basename(self.open_filename))
        if self.open_filename:
            with codecs.open(self.open_filename, encoding='utf-8', mode='w') as f:
                f.write(self.textbuf.get_text(self.bounds[0],self.bounds[1]))
        return True # command completed successfully!
    def file_save_as(self):
        """ save under a different name """
        self.open_filename=''
        return self.file_save()

    def do_command(self, hyp):
        """decode spoken commands"""
        h = hyp.strip()
        h = h.lower()
        # editable commands
        commands=self.commands
        # process commands with no arguments
        if h in commands:
            return eval(commands[h])()
        elif h.find(' ')>0:
            #~ reg = re.match(u'(\w+) (.*)', hyp)
            #~ command = reg.group(1)
            #~ argument = reg.group(2)
            cmd = h.partition(' ')
            if cmd[0] in commands:
                return eval(commands[cmd[0]])(cmd[2])
                
        return False

    def searchback(self, iter, argument):
        """helper function to search backwards in text buffer"""
        search_back = iter.backward_search(argument, Gtk.TextSearchFlags.TEXT_ONLY)
        if None == search_back:
            argument = argument.capitalize()
            search_back = iter.backward_search(argument, Gtk.TextSearchFlags.TEXT_ONLY)
        if None == search_back:
            argument = argument.strip()
            search_back = iter.backward_search(argument, Gtk.TextSearchFlags.TEXT_ONLY)
        return search_back

if __name__ == "__main__":
    app = freespeech()
    Gtk.main()
