#!/usr/bin/env python
# -*- coding: utf-8 -*-
# FreeSpeech
# Continuous realtime speech recognition and control via pocketsphinx
# Copyright (c) 2013 Henry Kroll III, http://www.TheNerdShow.com

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
import pygst
pygst.require('0.10')

import gobject
gobject.threads_init()
import gst
import subprocess
import platform, os, shutil, sys, codecs
import re
import json

""" global variables """
appname = 'FreeSpeech'
refdir = 'lm'

# hmmm, where to put files? How about XDG_CONFIG_HOME?
# This will work on most Linux
if os.environ.has_key('XDG_CONFIG_HOME'):
    confhome = os.environ['XDG_CONFIG_HOME']
    confdir  = os.path.join(confhome, appname)
else:
    # todo: determine suitable writable location for other os
    confdir = refdir

# reference files written by this application
lang_ref= os.path.join(confdir, 'freespeech.ref.txt')
vocab   = os.path.join(confdir, 'freespeech.vocab')
idngram = os.path.join(confdir, 'freespeech.idngram')
arpa    = os.path.join(confdir, 'freespeech.arpa')
dmp     = os.path.join(confdir, 'freespeech.dmp')
cmdtext = os.path.join(confdir, 'freespeech.cmd.txt')
cmdjson = os.path.join(confdir, 'freespeech.cmd.json')

class freespeech(object):
    """GStreamer/PocketSphinx Demo Application"""
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
        # initialize components
        self.init_gui()
        self.init_errmsg()
        self.init_prefs()
        self.init_file_chooser()
        self.init_gst()

    def init_gui(self):
        self.undo = [] # Say "Scratch that" or "Undo that"
        """Initialize the GUI components"""
        self.window = gtk.Window()
        # Change to executable's dir
        if os.path.dirname(sys.argv[0]):
            os.chdir(os.path.dirname(sys.argv[0]))     
        self.icon = gtk.gdk.pixbuf_new_from_file(appname+".png")
        self.window.connect("delete-event", gtk.main_quit)
        self.window.set_default_size(400, 200)
        self.window.set_border_width(10)
        self.window.set_icon(self.icon)
        self.window.set_title(appname)
        vbox = gtk.VBox()
        hbox = gtk.HBox(homogeneous=True)
        self.textbuf = gtk.TextBuffer()
        self.text = gtk.TextView(self.textbuf)
        self.text.set_wrap_mode(gtk.WRAP_WORD)
        self.scroller = gtk.ScrolledWindow(None, None)
        self.scroller.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scroller.add(self.text)
        vbox.pack_start(self.scroller, True, True, 5)
        vbox.pack_end(hbox, False, False)
        self.button = gtk.Button("Learn")
        self.button.connect('clicked', self.learn_new_words)
        self.button2 = gtk.ToggleButton("Mute")
        self.button2.connect('clicked', self.mute)
        hbox.pack_start(self.button, True, False, 5)
        hbox.pack_start(self.button2, True, False, 5)
        self.window.add(vbox)
        self.window.show_all()

    def init_file_chooser(self):
        self.file_chooser = gtk.FileChooserDialog(title="File Chooser",
        parent=self.window, action=gtk.FILE_CHOOSER_ACTION_OPEN,
        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
            gtk.STOCK_OK, gtk.RESPONSE_ACCEPT), backend=None)
    
    def init_commands(self):
            self.commands = {'file quit': 'gtk.main_quit',
                'file open': 'self.file_open',
                'file save': 'self.file_save',
                'file save as': 'self.file_save_as',
                'show commands': 'self.show_commands',
                'editor clear': 'self.clear_edits',
                'clear edits': 'self.clear_edits',
                'file close': 'self.clear_edits',
                'delete': 'self.delete',
                'select': 'self.select',
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
        me = self.prefsdialog = gtk.Dialog("Command Preferences", None,
            gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
            gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        me.set_default_size(400, 300)
        if not os.access(cmdjson, os.R_OK):
            #~ write some default commands to a file if it doesn't exist
            self.init_commands()
        else:
            self.read_prefs()
        
        me.label = gtk.Label( \
"Double-click to change command wording.\n\
If new commands don't work click the learn button to train them.")
        me.vbox.pack_start(me.label)
        me.checkbox=gtk.CheckButton("Restore Defaults")
        me.checkbox.show()
        me.action_area.pack_start(me.checkbox)
        me.liststore=gtk.ListStore(str, str)
        me.liststore.set_sort_column_id(0, gtk.SORT_ASCENDING)
        me.tree=gtk.TreeView(me.liststore)
        editable = gtk.CellRendererText()
        fixed = gtk.CellRendererText()
        editable.set_property('editable', True)
        editable.connect('edited', self.edited_cb)
        me.connect("expose-event", self.prefs_expose)
        column = gtk.TreeViewColumn("Spoken command",editable,text=0)
        me.tree.append_column(column)
        column = gtk.TreeViewColumn("What it does",fixed,text=1)
        me.tree.append_column(column)
        me.vbox.pack_end(me.tree)
        me.label.show()
        me.tree.show()
        self.commands_old = self.commands
        ret = me.run()
        if me.checkbox.get_active():
            self.init_commands()
        else:
            if ret!=gtk.RESPONSE_ACCEPT:
                self.commands = self.commands_old
            else:
                self.write_prefs()
        me.hide()

    def prefs_expose(self, me, event):
        """ callback when prefs window is shown """
        # populate commands list with documentation
        me.liststore.clear()
        for x,y in self.commands.items():
            me.liststore.append([x,eval(y).__doc__])        
        
    def write_prefs(self):
        # write command list to file
        with codecs.open(cmdjson, encoding='utf-8', mode='w') as f:
            f.write(json.dumps(self.commands))
        # write commands text, so we don't have to train each time
        with codecs.open(cmdtext, encoding='utf-8', mode='w') as f:
            for j in self.commands.keys():
                f.write('<s> '+j+' </s>\n')
        

    def read_prefs(self):
        with codecs.open(cmdjson, encoding='utf-8', mode='r') as f:
            self.commands=json.loads(f.read())
        
    def edited_cb(self, cellrenderertext, path, new_text):
        """ callback activated when treeview text edited """
        #~ self.prefsdialog.tree.path=new_text
        liststore=self.prefsdialog.liststore
        treeiter = liststore.get_iter(path)
        old_text = liststore.get_value(treeiter,0)
        if not self.commands.has_key(new_text):
            liststore.set_value(treeiter,0,new_text)
            self.commands[new_text]=self.commands[old_text]
            del(self.commands[old_text])
            #~ print(old_text, new_text)
        
    def init_errmsg(self):
        me = self.errmsg = gtk.Dialog("Error", None,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
            gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        me.set_default_size(400, 200)
        me.label = gtk.Label("Nice label")
        me.vbox.pack_start(me.label)
        me.label.show()
        
    def init_gst(self):
        """Initialize the speech components"""
        self.pipeline = gst.parse_launch('autoaudiosrc ! audioconvert ! audioresample '
                                         + '! vader name=vad auto-threshold=true '
                                         + '! pocketsphinx name=asr ! fakesink')
        asr = self.pipeline.get_by_name('asr')
        
        """Load custom dictionary and language model"""
        asr.set_property('dict', 'custom.dic')
        
        # The language model that came with pocketsphinx works OK...
        # asr.set_property('lm', '/usr/share/pocketsphinx/model/lm/en_US/wsj0vp.5000.DMP')
        # but it does not contain editing commands, so we make our own
        if not os.access(dmp, os.R_OK): # create if not exists
                self.learn_new_words(None)
        asr.set_property('lm', dmp)
        
        # Adapt pocketsphinx to your voice for better accuracy.
        # See http://cmusphinx.sourceforge.net/wiki/tutorialadapt
        
        # asr.set_property('hmm', '../sphinx/hub4wsj_sc_8kadapt')
        
        #fixme: write an acoustic model trainer
        
        asr.connect('partial_result', self.asr_partial_result)
        asr.connect('result', self.asr_result)
        asr.set_property('configured', True)

        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message::application', self.application_message)

        #self.pipeline.set_state(gst.STATE_PAUSED)
        self.pipeline.set_state(gst.STATE_PLAYING)

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
        if subprocess.call(catcmd + cmdtext + ' ' + lang_ref + '|text2wfreq -verbosity 2' \
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
        
        # load the dmp
        asr = self.pipeline.get_by_name('asr')
        self.pipeline.set_state(gst.STATE_PAUSED)
        asr.set_property('configured', False)
        asr.set_property('lm', dmp)
        asr.set_property('configured', True)
        self.pipeline.set_state(gst.STATE_PLAYING)
        
    def mute(self, button):
        """Handle button presses."""
        if not button.get_active():
            button.set_label("Mute")
            self.pipeline.set_state(gst.STATE_PLAYING)
        else:
            button.set_label("Speak")
            vader = self.pipeline.get_by_name('vad')
            vader.set_property('silent', True)
            self.pipeline.set_state(gst.STATE_PAUSED)

    def collapse_punctuation(self, hyp, started):
        index = 0
        start = self.textbuf.get_iter_at_mark(self.textbuf.get_insert())
        words = hyp.split()
        # remove the extra text to the right of the punctuation mark
        while True:
            if (index >= len(words)):
                break
            word = words[index]
            if (re.match("^\W\w", word)):
                words[index] = word[0]
            index += 1
        hyp = " ".join(words)
        hyp = hyp.replace(" ...ellipsis", " ...")
        hyp = re.sub(r" ([^\w\s]+)\s*", r"\1 ", hyp)
        hyp = re.sub(r"([({[]) ", r" \1", hyp).strip()
        if not start.inside_sentence():
            hyp = hyp[0].capitalize() + hyp[1:]
        print(hyp)
        if re.match(r"\w", hyp[0]) and started:
            space = " "
        else:
            space = ""
        return space + hyp
        
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
            line = re.sub(u'§',           u'§section-sign',           line)
            line = re.sub(u'¶',           u'¶paragraph-sign',         line)
            line = re.sub(u'¼',           u'¼and-a-quarter',          line)
            line = re.sub(u'½',           u'½and-a-half',             line)
            line = re.sub(u'¾',           u'¾and-three-quarters',     line)
            line = re.sub(u'¿',           u'¿inverted-question-mark', line)
            line = re.sub(u'×',           u'×multiplication-sign',    line)
            line = re.sub(u'÷',           u'÷division-sign',          line)
            line = re.sub(u'° ',          u'°degree-sign ',           line)
            line = re.sub(u'©',           u'©copyright-sign',         line)
            line = re.sub(u'™',           u'™trademark-sign',         line)            
            line = re.sub(u'®',           u'®registered-symbol',      line)
            line = re.sub(r'_',           r'_underscore',             line)
            line = re.sub(r'\\',          r'\backslash',              line)
            line = re.sub(r'^(.)',        r'<s> \1',                  line)
            line = re.sub(r'(.)$',        r'\1 </s>',                 line)
            corpus[ind] = line
        return corpus

    def prepare_corpus(self, txt):
        txt.begin_user_action()
        self.bounds = self.textbuf.get_bounds()
        text = txt.get_text(self.bounds[0], self.bounds[1])
        # break on end of sentence
        text = re.sub(r'(\w[.:;?!])\s+(\w)', r'\1\n\2', text)
        text = re.sub(r'\n+', r'\n', text)
        corpus= re.split(r'\n', text)       
        for ind, tex in enumerate(corpus):
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
            tex = re.sub(r'\s*([^\w\s]|[_])\s*', r' \1 ', tex)
            # except apostrophe followed by lower-case letter
            tex = re.sub(r"(\w) ' ([a-z])", r"\1'\2", tex)
            tex = re.sub(r'\s+', ' ', tex)
            # fixme: needs more unicode -> dictionary replacements
            # or we could convert the rest of the dictionary to utf-8
            # and use the ʼunicode charactersʼ
            tex = tex.replace(u"ʼ", "'apostrophe")
            tex = tex.strip()
            corpus[ind] = tex
        return self.expand_punctuation(corpus)

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
        not self.bounds[1].is_start())
        # handle commands
        if not self.do_command(hyp):
            self.undo.append(hyp)
            self.textbuf.delete_selection(True, self.text.get_editable())
            self.textbuf.insert_at_cursor(hyp)
        ins = self.textbuf.get_insert()
        iter = self.textbuf.get_iter_at_mark(ins)
        self.text.scroll_to_iter(iter, 0, False)
        self.textbuf.end_user_action()

    """Process spoken commands"""
    def err(self, errormsg):
        self.errmsg.label.set_text(errormsg)
        self.errmsg.run()
        self.errmsg.hide()
    def show_commands(self):
        """ show these command preferences """
        me=self.prefsdialog
        self.commands_old = self.commands
        ret = me.run()
        if me.checkbox.get_active():
            self.init_commands()
        else:
            if ret!=gtk.RESPONSE_ACCEPT:
                self.commands = self.commands_old
            else:
                self.write_prefs()
        me.hide()
        return True # command completed successfully!
    def clear_edits(self):
        """ erase text buffer, close files """
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
            print("del "+argument)
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
        if re.match("^after", argument):
            argument = re.match(r'\w+(.*)', argument).group(1)
            search_back = self.searchback(self.bounds[1], argument)
            if None == search_back:
                return True
            self.textbuf.place_cursor(search_back[1])        
            return True # command completed successfully!
    def done_editing(self):
        """ place cursor at end """
        self.textbuf.place_cursor(self.bounds[1])
        return True # command completed successfully!
    def scratch_that(self):
        """ erase recent text """
        scratch = self.undo.pop(-1)
        search_back = self.bounds[1].backward_search( \
            scratch, gtk.TEXT_SEARCH_TEXT_ONLY)
        self.textbuf.select_range(search_back[0], search_back[1])
        self.textbuf.delete_selection(True, self.text.get_editable())
        return True # command completed successfully!
    def new_paragraph(self):
        """ start a new paragraph """
        self.textbuf.insert_at_cursor('\n')
        return True # command completed successfully!
    def file_open(self):
        """ open file dialog """
        response=self.file_chooser.run()
        if response==gtk.RESPONSE_ACCEPT:
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
            if response==gtk.RESPONSE_ACCEPT:
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
        hyp = hyp.strip()
        hyp = hyp[0].lower() + hyp[1:]
        # editable commands
        commands=self.commands
        # process editable commands
        if commands.has_key(hyp):
            return eval(commands[hyp])()
        try:# separate command and arguments
            reg = re.match(r'(\w+) (.*)', hyp)
            command = reg.group(1)
            argument = reg.group(2)
            return eval(commands[command])(argument)
        except:
            pass # didn't work; not a command
        return False

    def searchback(self, iter, argument):
        """helper function to search backwards in text buffer"""
        search_back = iter.backward_search( \
        argument, gtk.TEXT_SEARCH_TEXT_ONLY)
        if None == search_back:
            search_back = iter.backward_search( \
            argument.capitalize(), gtk.TEXT_SEARCH_TEXT_ONLY)
            if None == search_back:
                return None
        return search_back

app = freespeech()
gtk.main()
