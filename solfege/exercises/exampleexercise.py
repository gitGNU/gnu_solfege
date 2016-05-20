# GNU Solfege - free ear training software
# Copyright (C) 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2011, 2016  Tom Cato Amundsen
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


from gi.repository import GObject
from gi.repository import Gtk

from solfege import abstract
from solfege import gu
from solfege import lessonfile
from solfege import mpd
from solfege import soundcard
from solfege import statistics, statisticsviewer
from solfege import utils

import solfege


class Teacher(abstract.Teacher):
    OK = 0
    ERR_PICKY = 1
    ERR_NO_INTERVALLS = 2
    ERR_NOTERANGE = 3

    def __init__(self, exname):
        abstract.Teacher.__init__(self, exname)
        self.lessonfileclass = lessonfile.IntervalsLessonfile
        self.m_statistics = statistics.HarmonicIntervalStatistics(self)
        self.m_tonika = None

    def enter_test_mode(self):
        self.m_custom_mode = False
        self.m_statistics.enter_test_mode()
        self.m_P.enter_test_mode()

    def new_question(self, L, H):
        self.q_status = self.QSTATUS_NEW
        return Teacher.OK

    def guess_answer(self, answer):
        """
        Return: 1 if correct, None if wrong
        """
        assert self.q_status not in (self.QSTATUS_NO, self.QSTATUS_GIVE_UP)
        if 1:  # add test
            # if self.q_status == self.QSTATUS_NEW \
            #        and not self.m_custom_mode:
            #    #self.m_statistics.add_correct(some value)
            self.maybe_auto_new_question()
            self.q_status = self.QSTATUS_SOLVED
            return 1
        else:
            if self.q_status == self.QSTATUS_NEW:
                # if not self.m_custom_mode:
                #    self.m_statistics.add_wrong(some value, some value)
                self.q_status = self.QSTATUS_WRONG
            if solfege.app.m_test_mode:
                self.maybe_auto_new_question()

    def give_up(self):
        """This function is only called *after* the user already has
        answered wrong once, so the statistics are already updated.
        """
        self.q_status = self.QSTATUS_GIVE_UP

    def play_question(self):
        return

    def start_practise(self):
        return


class Gui(abstract.Gui):
    lesson_heading = _("Identify the interval")

    def __init__(self, teacher):
        abstract.Gui.__init__(self, teacher)
        ################
        # practice_box #
        ################
        self.std_buttons_add(
            ('new', None),  # add callback
            ('give_up', self.give_up),
        )
        self.g_flashbar = gu.FlashBar()
        self.g_flashbar.show()
        self.practise_box.pack_start(self.g_flashbar, False, False, 0)
        self.practise_box.set_spacing(gu.PAD)
        ###############
        # config_grid #
        ###############
        self._add_auto_new_question_gui(row=0)
        # ----------------------------------------------
        self.config_grid.show_all()
        ##############
        # statistics #
        ##############
        self.setup_statisticsviewer(statisticsviewer.StatisticsViewer,
                                   _("Statistics for this example exercise"))

    def give_up(self, _o=None):
        if self.m_t.q_status == self.QSTATUS_WRONG:
            self.g_flashbar.push(_("The answer is: xxx"))
            self.m_t.give_up()
            self.std_buttons_give_up()

    def new_question(self, _o=None):
        """This function is called when you click on the 'New'
        button, or when you use the key bindings. So it can be called even
        if the 'New' button is insensitive.
        """
        self.std_buttons_new_question()
        print("New question")

    def on_start_practise(self):
        self.m_t.start_practise()
        super(Gui, self).on_start_practise()
        if not self.m_t.m_custom_mode:
            self.m_t.m_statistics.reset_session()
        self.g_statview.g_heading.set_text("%s - %s" % (_("Example"), self.m_t.m_P.header.title))
        self.std_buttons_start_practise()
        if solfege.app.m_test_mode:
            self.g_flashbar.delayed_flash(self.short_delay,
                _("Click 'Start test' to begin."))
        else:
            self.g_flashbar.delayed_flash(self.short_delay,
                _("Click 'New' to begin."))

    def on_end_practise(self):
        self.m_t.end_practise()
        self.g_flashbar.clear()

    def enter_test_mode(self):
        self.m_saved_q_auto = self.get_bool('new_question_automatically')
        self.m_saved_s_new = self.get_float('seconds_before_new_question')
        self.set_bool('new_question_automatically', True)
        self.set_float('seconds_before_new_question', 0.5)
        self.m_t.enter_test_mode()
        self.g_new.set_label(_("_Start test"))
        self.g_cancel_test.show()
        self.g_give_up.hide()

    def exit_test_mode(self):
        self.set_bool('new_question_automatically', self.m_saved_q_auto)
        self.set_float('seconds_before_new_question', self.m_saved_s_new)
        self.m_t.exit_test_mode()
        self.g_new.show()
        self.g_new.set_label(_("_New something"))
        self.g_give_up.show()
