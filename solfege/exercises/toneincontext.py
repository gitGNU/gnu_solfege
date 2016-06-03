# vim: set fileencoding=utf-8:
# GNU Solfege - free ear training software
# Copyright (C) 2011, 2016  Tom Cato Amundsen
#
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


import logging
import random
import time
import inspect

from gi.repository import Gtk

import solfege
from solfege import abstract
from solfege import cfg
from solfege import gu
from solfege import lessonfile
from solfege import mpd
from solfege import soundcard
from solfege import statistics
from solfege import statisticsviewer
from solfege.mpd import elems

labels = ['1', '♯1/♭2', '2', '♯2/♭3', '3', '4', '♯4/♭5',
          '5', '♯5/6♭', '6', '♯6/♭7', '7', '1']


class ToneInKeyStatistics(statistics.LessonStatistics):

    def add_correct(self, answer):
        fileid = solfege.db.get_fileid(self.m_t.m_P.m_filename)
        cursor = solfege.db.conn.cursor()
        cursor.execute(
            "insert into toneincontext "
            "(fileid, timestamp, answerkey, guessedkey) "
            "values (?, ?, ?, ?)",
            (fileid, int(time.time()), answer, answer))
        solfege.db.conn.commit()

    def add_wrong(self, question, answer):
        if question == 12:
            question = 0
        if answer == 12:
            answer = 0
        fileid = solfege.db.get_fileid(self.m_t.m_P.m_filename)
        cursor = solfege.db.conn.cursor()
        cursor.execute(
            "insert into toneincontext "
            "(fileid, timestamp, answerkey, guessedkey) "
            "values (?, ?, ?, ?)",
            (fileid, int(time.time()), question, answer))
        solfege.db.conn.commit()

    def key_to_pretty_name(self, key):
        return labels[int(key)]

    def num_asked(self, key):
        row = solfege.db.conn.execute(
            "select count(guessedkey) from toneincontext "
            "where answerkey=? and fileid=?",
            (key, solfege.db.get_fileid(self.m_t.m_P.m_filename)))
        for r in row:
            return r[0]
        return 0

    def num_correct(self, key):
        row = solfege.db.conn.execute(
            "select count(guessedkey) from toneincontext "
            "where answerkey=? and guessedkey=? and fileid=?",
            (key, key, solfege.db.get_fileid(self.m_t.m_P.m_filename)))
        for r in row:
            return r[0]
        return 0

    @staticmethod
    def get_percentage_of_file(filename):
        """
        raise solfege.statistics.DB.FileNotInDB if the lesson file never
        has been practised.
        """
        # how many answered correct
        row = solfege.db.conn.execute(
            "select count(guessedkey) from toneincontext "
            "where answerkey=guessedkey and fileid=?",
            (solfege.db.get_fileid(filename),))
        correct = row.fetchone()
        correct = correct[0] if correct else 0
        # how many asked
        row = solfege.db.conn.execute(
            "select count(guessedkey) from toneincontext "
            "where fileid=?",
            (solfege.db.get_fileid(filename),))
        asked = row.fetchone()
        asked = asked[0] if correct else 1
        return correct / asked


class StatisticsViewer(Gtk.Grid):

    def __init__(self, teacher):
        Gtk.Grid.__init__(self)
        self.set_column_spacing(gu.hig.SPACE_SMALL)
        self.set_row_spacing(gu.hig.SPACE_SMALL)
        self.props.margin = gu.hig.SPACE_SMALL
        self.m_t = teacher
        self.set_column_homogeneous(True)
        self.labels = fill_grid(Gtk.Label, self)
        self.show_all()

    def update(self, *w):
        for n in range(13):
            c = self.m_t.m_statistics.num_correct(n if n < 12 else 0)
            a = self.m_t.m_statistics.num_asked(n if n < 12 else 0)
            p = 0 if a == 0 else c / a
            if n not in self.m_t.get_list("tones"):
                self.labels[n].set_name("labelgreyout")
            elif p < 0.5:
                self.labels[n].set_name("labelred")
            elif p < 0.9:
                self.labels[n].set_name("labelyellow")
            else:
                self.labels[n].set_name("labelgreen")
            self.labels[n].set_text("{}%\n{}/{}".format(int(p * 100), c, a))


class Teacher(abstract.Teacher):
    OK = 0
    ERR_NO_TONES = 1
    resolve = {
        'major': {
            0: "c2",
            1: "cis c2",
            2: "d c2",
            3: "dis4 d8 c2",
            4: "e4 d8 c2",
            5: "f4 e8 d c2",
            6: "fis4 g8 a b c'2",
            7: "g4 a8 b c'2",
            8: "gis4 a8 b c'2",
            9: "a4 b8 c'2",
            10: "ais4 b8 c'2",
            11: "b4 c'2",
            12: "c'2"},
        'minor': {
            0: "c2",
            1: "des c2",
            2: "d c2",
            3: "es4 d8 c2",
            4: "e4 es8 d c2",
            5: "f4 es8 d c2",
            6: "fis4 g8 as bes c'2",
            7: "g4 as8 bes c'2",
            8: "as4 bes8 c'2",
            9: "a4 bes8 c'2",
            10: "bes4 c'2",
            11: "b4 c'2",
            12: "c'2"}
    }
    cadence = {
        'major': {
            'music': lessonfile.Music(r"\staff\relative g'{ \time 3/4 <g e c> <a f c> <g f d b> <g2 e c> }"),
            'name': _("Major"),
            'key': 'major',
        },
        'minor': {
            'music': lessonfile.Music(r"\staff\relative g'{ \time 3/4 <g es c> <as f c> <g f d b> <g2 es c> }"),
            'name': _("Minor"),
            'key': 'minor',
        }
    }

    def __init__(self, exname):
        abstract.Teacher.__init__(self, exname)
        self.lessonfileclass = lessonfile.HeaderLessonfile
        self.m_lessonfile_header_defaults['random_tonic'] = False
        self.m_lessonfile_header_defaults['cadence'] = 'major'
        self.m_lessonfile_defs['other'] = 'other'
        self.m_transpose = mpd.MusicalPitch()
        """To which key the question should be transposed.
        Will be set in :func:`~new_question`
        """
        self.m_statistics = ToneInKeyStatistics(self)

    def new_question(self):
        """
        Return OK or ERR_NO_TONES
        Will set the following variables defining the question.

            self.m_tone
            self.m_octave
            self.m_transpose
        """
        if not self.get_list("tones"):
            return self.ERR_NO_TONES
        self.m_tone = random.choice(
            [i for i in self.get_list("tones") if i != 12])
        if self.get_bool('many_octaves'):
            self.m_octave = random.choice((-1, 0, 1, 2))
        else:
            self.m_octave = 0
        self.q_status = self.QSTATUS_NEW
        if self.get_string('random_tonic') == 'True':
            self.m_transpose.randomize("c'", "b'")
        if self.m_custom_mode:
            # In m_custom_mode, we will choose one of the cadences selected
            # on the config page.
            cadence_list = [k for k in list(self.m_cadences.keys()) if self.m_cadences[k]]
            if not cadence_list:
                return self.ERR_NO_CADENCES
            self.m_chosen_cadence = c = random.choice(cadence_list)
            if isinstance(c, str):
                self.m_cadence = self.cadence[c]
            else:
                self.m_cadence = self.m_P.blocklists['cadence'][c]
        else:
            # In normal mode (not m_custom_mode), if there are cadences
            # defined in the lesson file, we choose one of them by random.
            if 'cadence' in self.m_P.blocklists:
                self.m_cadence = random.choice(self.m_P.blocklists['cadence'])
            else:
                # If no cadences are defined in the lesson file, the header
                # variable cadence should select one of the builtin cadences.
                self.m_cadence = self.cadence[self.m_P.header.cadence]
        return self.OK

    def play_answer(self):
        soundcard.synth.play_track(self.get_track_of_answer())

    def play_question(self):
        """
        Play the resolution of the previous question, if any, and then
        the cadence and the new question.
        """
        t = self.get_track_of_question()
        soundcard.synth.play_track(t)

    def guess_answer(self, answer):
        if answer == 12:
            answer = 0
        assert self.q_status not in (self.QSTATUS_NO, self.QSTATUS_GIVE_UP)
        if self.m_tone == answer or (answer == 0 and self.m_tone == 12):
            if self.q_status == self.QSTATUS_NEW:
                self.m_statistics.add_correct(answer)
            answer_track = self.get_track_of_answer()
            self.new_question()
            question_track = self.get_track_of_question()
            soundcard.synth.play_track(answer_track + question_track)
            self.q_status = self.QSTATUS_NEW
            return 1
        else:
            if self.q_status == self.QSTATUS_NEW:
                self.m_statistics.add_wrong(self.m_tone, answer)
                self.q_status = self.QSTATUS_WRONG

    def get_track_of_answer(self):
        """
        If the lessonfile have defined a resolve block with the same key
        as the cadense that is selected, it will use that. If not it will
        use the builtin.
        """
        # First see if we have a matching resolve block in the lesson file
        try:
            resolve = [r for r in self.m_P.blocklists['resolve']
                       if r['key'] == self.m_cadence['key']][0]['list'][self.m_tone]
        except (IndexError, KeyError):
            # If not found, we use the builtin definition
            resolve = self.resolve[self.m_cadence['key']][self.m_tone]

        tr = self.m_transpose.clone()
        tr.m_octave_i += self.m_octave - 1
        t = mpd.music_to_track(r"\staff\transpose %s'{ \time 100/4 %s }" % (
            tr.get_octave_notename(), resolve))
        t.prepend_bpm(90)
        return t

    def get_track_of_question(self):
        c = self.m_cadence['music'].get_mpd_music_string(self.m_P)
        c = c.replace(r"\transpose c'",
                      r"\transpose %s" % self.m_transpose.get_octave_notename())
        cadence_track = mpd.music_to_track(c)
        cadence_track.prepend_bpm(90)

        p = mpd.MusicalPitch.new_from_notename("c'") + self.m_tone
        p.m_octave_i = self.m_octave
        s = r"\staff{ %s }" % p.transpose_by_musicalpitch(self.m_transpose).get_octave_notename()
        track = mpd.music_to_track(s)
        return cadence_track + track

    def give_up(self):
        self.m_qstatus = self.QSTATUS_GIVE_UP

    def start_practise(self):
        self.m_custom_mode = bool(not self.m_P.header.tones)
        if self.m_custom_mode:
            self.m_statistics.reset_custom_mode_session(self.m_P.m_filename)
        else:
            self.m_statistics.reset_session()
        if self.m_P.header.tones:
            self.set_list("tones", self.m_P.header.tones)
        # FIXME in preparation for 'configure yourself mode'
        self.set_string('random_tonic', str(self.m_P.header.random_tonic))
        if self.get_string('random_tonic') == 'other':
            self.m_transpose.randomize("cis'", "b'")
        elif self.get_string('random_tonic') == 'False':
            self.m_transpose.set_from_notename("c'")


def fill_grid(button_class, grid):
    grid.set_column_homogeneous(True)
    buttons = {}
    for p, x in ((0, 1), (1, 3), (3, 6), (4, 8), (5, 10)):
        b = button_class(labels[x])
        buttons[x] = b
        grid.attach(b, p * 2 + 1, 0, 2, 1)
    for p, x in enumerate((0, 2, 4, 5, 7, 9, 11, 12)):
        b = button_class(labels[x])
        buttons[x] = b
        grid.attach(b, p * 2, 1, 2, 1)
    return buttons


class nConfigButtons(Gtk.Grid, cfg.ConfigUtils):

    def __init__(self, exname, name):
        Gtk.Grid.__init__(self)
        cfg.ConfigUtils.__init__(self, exname)
        self.m_varname = name
        self.g_buttons = fill_grid(Gtk.CheckButton, self)
        for key, button in list(self.g_buttons.items()):
            button.connect('toggled', self.on_toggled)
        for key in self.get_list('tones'):
            self.g_buttons[key].set_active(True)

    def on_toggled(self, *w):
        self.set_list(self.m_varname,
            [k for k in list(self.g_buttons.keys()) if self.g_buttons[k].get_active()])


class Gui(abstract.Gui):
    lesson_heading = _("Tone in context")

    def __init__(self, teacher):
        abstract.Gui.__init__(self, teacher)
        grid = Gtk.Grid()
        grid.set_row_spacing(gu.hig.SPACE_SMALL)
        grid.set_column_spacing(gu.hig.SPACE_SMALL)
        self.g_buttons = fill_grid(Gtk.Button, grid)
        for key, button in list(self.g_buttons.items()):
            button.connect('clicked', self.on_left_click, key)
        self.practise_box.pack_start(grid, False, False, gu.hig.SPACE_SMALL)
        self.g_flashbar = gu.FlashBar()
        self.g_flashbar.show()
        self.practise_box.pack_start(self.g_flashbar, False, False, 0)
        self.std_buttons_add(
            ('new', self.new_question),
            ('repeat', lambda _o, self=self: self.m_t.play_question()),
            ('give_up', self.give_up))
        self.practise_box.show_all()
        ###############
        # config_grid #
        ###############
        # FIXME we need a ComboBox
        # self.g_random = gu.nCheckButton(self.m_exname, 'random_tonic', _("Random transpose"))
        # self.g_config_grid.attach(self.g_random, 0, 0, 1, 1)
        #
        self.g_tones_category, box = gu.hig_category_vbox(_("Tones"))
        self.g_config_grid.attach(self.g_tones_category, 0, 2, 3, 1)
        self.g_tone_selector = nConfigButtons(self.m_exname, 'tones')
        self.g_tone_selector.show_all()
        box.pack_start(self.g_tone_selector, False, False, 0)
        self.g_many_octaves = b = gu.nCheckButton('toneincontext', 'many_octaves',
            _("Many octaves"))
        self.g_config_grid.attach(b, 0, 3, 1, 1)
        # Cadences
        self.g_cadences_category, self.g_cadences = gu.hig_category_vbox(_("Cadences"))
        self.g_cadences.show()
        self.g_config_grid.attach(self.g_cadences_category, 0, 4, 1, 1)
        #

        def _ff(var):
            if self.m_t.m_custom_mode:
                # If we are running in custom mode, then the user can
                # select himself what intervals to practise. And then
                # we have to reset the exercise.
                # self.on_end_practise()
                # self.on_start_practise()
                self.cancel_question()
        self.add_watch('tones', _ff)
        ##############
        # Statistics #
        ##############
        self.setup_statisticsviewer(statisticsviewer.StatisticsViewer,
                                   _("Tone in cadence"))
        #
        self.g_statview = StatisticsViewer(self.m_t)
        self.g_statview.show()
        self.g_notebook.append_page(self.g_statview, Gtk.Label(label=_("Statistics")))
        self.g_notebook.connect(
            'switch_page', self.g_statview.update)

    def cancel_question(self):
        self.m_t.end_practise()
        self.std_buttons_end_practise()

    def new_question(self, *w):
        i = self.m_t.new_question()
        if i == Teacher.OK:
            self.std_buttons_new_question()
            self.m_t.play_question()
            for key, button in list(self.g_buttons.items()):
                button.set_sensitive(key in self.get_list("tones"))
        elif i == Teacher.ERR_NO_CADENCES:
            self.g_flashbar.flash(_("No cadences selected"))

    def give_up(self, *w):
        if self.m_t.q_status == self.QSTATUS_WRONG:
            self.g_flashbar.push(_("The answer is: %s")
                 % labels[self.m_t.m_tone])
            self.m_t.give_up()
            self.std_buttons_give_up()

    def on_left_click(self, button, tone_int):
        if self.m_t.q_status == self.QSTATUS_SOLVED:
            if self.m_t.guess_answer(tone_int):
                self.g_flashbar.flash(_("Correct, but you have already solved this question"))
            else:
                self.g_flashbar.flash(_("Wrong, but you have already solved this question"))
        elif self.m_t.q_status in (self.QSTATUS_NEW, self.QSTATUS_WRONG):
            if self.m_t.guess_answer(tone_int):
                self.g_flashbar.flash(_("Correct"))
                self.std_buttons_new_question()
            else:
                self.g_flashbar.flash(("Wrong"))
                self.std_buttons_answer_wrong()
                if self.get_bool("config/auto_repeat_question_if_wrong_answer"):
                    self.m_t.play_question()

    def on_start_practise(self):
        self.m_t.start_practise()
        super(Gui, self).on_start_practise()
        if self.m_t.m_custom_mode:
            self.g_tone_selector.show()
            # self.g_random.show()
            self.g_tones_category.show()
            self.g_many_octaves.show()
            for w in self.g_cadences.get_children():
                w.destroy()
            # We let the user select between all available cadences, both
            # the builtin cadences and any defined in the lesson file.
            # First we add gui for the builtin cadences
            self.g_cadences_category.show()
            self.g_cadences.show()
            self.m_t.m_cadences = {}
            self.m_t.m_cadences['minor'] = False
            self.m_t.m_cadences['major'] = False
            b = _(" (builtin)") if 'cadence' in self.m_t.m_P.blocklists \
               else ""
            for k in Teacher.cadence:
                btn = Gtk.CheckButton(Teacher.cadence[k]['name'] + b)
                btn.show()
                btn.set_active(True)
                self.m_t.m_cadences[k] = True
                btn.connect('toggled', self.on_cadences_toggled, k)
                self.g_cadences.pack_start(btn, False, False, 0)
            # Then for the one supplied with the lesson file
            if 'cadence' in self.m_t.m_P.blocklists:
                for idx, c in enumerate(self.m_t.m_P.blocklists['cadence']):
                    name = c.get('name', _("Unnamed"))
                    btn = Gtk.CheckButton(name)
                    btn.show()
                    btn.set_active(True)
                    self.m_t.m_cadences[idx] = True
                    btn.connect('toggled', self.on_cadences_toggled, idx)
                    self.g_cadences.pack_start(btn, False, False, 0)
        else:
            self.g_tone_selector.hide()
            self.g_tones_category.hide()
            self.g_many_octaves.hide()
            self.g_cadences_category.hide()
            # self.g_random.hide()
        for key, button in list(self.g_buttons.items()):
            button.set_sensitive(False)
        self.set_bool('tone_in_cadence', self.m_t.m_P.header.tone_in_cadence)
        self.std_buttons_start_practise()
        self.g_flashbar.delayed_flash(self.short_delay,
            _("Click 'New' to begin."))
        self.g_flashbar.require_size([
            _("Correct, but you have already solved this question"),
            _("Wrong, but you have already solved this question")])

    def on_cadences_toggled(self, btn, key):
        self.cancel_question()
        self.m_t.m_cadences[key] = btn.get_active()
