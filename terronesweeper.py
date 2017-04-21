#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# TerronesWeeper Activity - terronesweeper.py
#
# Copyright 2011,2012 S. Daniel Francis <francis@sugarlabs.org>,
#                     Agustín Zubiaga <aguz@sugarlabs.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.
#

import os.path
import time
import random
import json

from gettext import gettext as _

import gtk
import pango
import gobject

from sugar.activity import activity
from sugar.graphics.toolbarbox import ToolbarBox
from sugar.activity.widgets import StopButton
from sugar.graphics.toolbutton import ToolButton
from sugar.graphics.menuitem import MenuItem
from sugar.graphics.alert import Alert

from timer import Timer
from dialogs import ScoreDialog

NUM_COLORS = {1: gtk.gdk.Color("#0092D0"),
              2: gtk.gdk.Color("#00C51C"),
              3: gtk.gdk.Color("#FF0000"),
              4: gtk.gdk.Color("#0000BA"),
              5: gtk.gdk.Color("#AA0800"),
              6: gtk.gdk.Color("#A020F0"),
              7: gtk.gdk.Color("#FF6600"),
              8: gtk.gdk.Color("#D42AFF")}

BUTTON_COLOR = gtk.gdk.Color("#E3E39D")
ANIMATION_DIR = "icons/anim"


class TerronAnimation(gtk.Image):

    def __init__(self, w, h):
        gtk.Image.__init__(self)

        self._current_image = 1
        self._timeout = None

        self._size = w, h

    def run(self):
        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(
                           os.path.join(ANIMATION_DIR,
                           str(self._current_image) + ".svg"),
                           self._size[0] - 10, self._size[1] - 20)

        self.set_from_pixbuf(pixbuf)

        self._timeout = gobject.timeout_add(500, self._next_image)

    def stop(self):
        gobject.source_remove(self._timeout)

    def _next_image(self):
        if self._current_image != 3:
            self._current_image += 1

        else:
            self._current_image = 1

        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(
                           os.path.join(ANIMATION_DIR,
                           str(self._current_image) + ".svg"),
                           self._size[0] - 10, self._size[1] - 20)

        self.set_from_pixbuf(pixbuf)

        return True


class TerronesTable(gtk.Table):

    __gsignals__ = {"game-over": (gobject.SIGNAL_RUN_LAST,
                                  gobject.TYPE_NONE,
                                  (gobject.TYPE_BOOLEAN,)),
                    "flag-added": (gobject.SIGNAL_RUN_LAST,
                                  gobject.TYPE_NONE,
                                  ()),
                    "flag-removed": (gobject.SIGNAL_RUN_LAST,
                                     gobject.TYPE_NONE,
                                     ()),
                     }

    def __init__(self, size, icon_size):
        rows, columns = size, size
        terrones = (size ** 2) / 4
        gtk.Table.__init__(self, rows, columns, True)
        self.icon_size = icon_size
        self.array = []
        self.void_buttons = size ** 2
        self.finded_void_buttons = 0
        for row in range(0, rows):
            new_row = []
            for column in range(0, columns):
                button = gtk.ToggleButton()
                button.flag = False
                button.connect('button-press-event',
                               self.button_event,
                               row,
                               column)
                button.connect("toggled", self.button_activated, row, column)
                button.modify_bg(gtk.STATE_NORMAL, BUTTON_COLOR)
                button.modify_bg(gtk.STATE_PRELIGHT, BUTTON_COLOR)
                button.show()
                self.attach(button,
                            row,
                            row + 1,
                            column,
                            column + 1,
                            xoptions=gtk.EXPAND | gtk.FILL,
                            yoptions=gtk.EXPAND | gtk.FILL)
                random.seed()
                new_row.append([button, False, False, False])
            self.array.append(new_row)
        for i in range(0, terrones):
            ready = False
            while not ready:
                row = random.randrange(0, len(self.array))
                ready2 = False
                attemps = 0
                while not ready2:
                    col = random.randrange(0, len(self.array[row]))
                    if not self.array[row][col][1]:
                        self.array[row][col][1] = True
                        self.void_buttons -= 1
                        ready2 = True
                    else:
                        attemps += 1
                        if attemps > len(self.array[row]):
                            break

                if ready2:
                    ready = True

    def button_event(self, widget, event, row, column):
        if event.button == 3:
            if not self.array[row][column][2]:
                if not self.array[row][column][3]:
                    image = gtk.Image()
                    pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(
                                             "icons/terron-flag.svg",
                                             widget.get_allocation()[-2] - 10,
                                             widget.get_allocation()[-1] - 10)
                    image.set_from_pixbuf(pixbuf)
                    image.show()
                    widget.flag = True
                    widget.add(image)
                    widget.set_property("inconsistent", True)
                    self.array[row][column][3] = True
                    self.emit("flag-added")
                else:
                    widget.flag = False
                    widget.set_property("inconsistent", False)
                    widget.remove(widget.get_children()[0])
                    self.array[row][column][3] = False
                    self.emit("flag-removed")

    def button_activated(self, widget, row, column):
        widget.connect("toggled", self.activate_button)
        if self.array[row][column][3]:
            return
        if not self.array[row][column][2]:
            if self.array[row][column][1]:
                anim = TerronAnimation(widget.get_allocation()[-2],
                                       widget.get_allocation()[-1])
                widget.set_image(anim)
                anim.run()
                anim.show()
                self.lose()
            else:
                terrones = []
                voids = []
                if row > 0:
                    if self.array[row - 1][column][1]:
                        terrones.append(self.array[row - 1][column])
                    else:
                        voids.append(self.array[row - 1][column])
                    if column > 0:
                        if self.array[row - 1][column - 1][1]:
                            terrones.append(self.array[row - 1][column - 1])
                        else:
                            voids.append(self.array[row - 1][column - 1])
                    if column < len(self.array[0]) - 1:
                        if self.array[row - 1][column + 1][1]:
                            terrones.append(self.array[row - 1][column + 1])
                        else:
                            voids.append(self.array[row - 1][column + 1])
                if column > 0:
                    if self.array[row][column - 1][1]:
                        terrones.append(self.array[row][column - 1])
                    else:
                        voids.append(self.array[row][column - 1])
                if column < len(self.array[0]) - 1:
                    if self.array[row][column + 1][1]:
                        terrones.append(self.array[row][column + 1])
                    else:
                        voids.append(self.array[row][column + 1])
                if row < len(self.array) - 1:
                    if self.array[row + 1][column][1]:
                        terrones.append(self.array[row + 1][column])
                    else:
                        voids.append(self.array[row + 1][column])
                    if column > 0:
                        if self.array[row + 1][column - 1][1]:
                            terrones.append(self.array[row + 1][column - 1])
                        else:
                            voids.append(self.array[row + 1][column - 1])
                    if column < len(self.array[0]) - 1:
                        if self.array[row + 1][column + 1][1]:
                            terrones.append(self.array[row + 1][column + 1])
                        else:
                            voids.append(self.array[row + 1][column + 1])
                if len(terrones):
                    label = gtk.Label(str(len(terrones)))
                    label.modify_fg(gtk.STATE_ACTIVE,
                                    NUM_COLORS[len(terrones)])
                    label.modify_font(pango.FontDescription("bold"))
                    widget.add(label)
                    label.show_all()
                else:
                    for i in voids:
                        i[0].set_active(True)
                self.finded_void_buttons += 1
                if self.finded_void_buttons == self.void_buttons:
                    self.win()
            self.array[row][column][2] = True

    def desactivate_button(self, widget):
        widget.set_active(False)

    def activate_button(self, widget):
        widget.set_active(True)

    def lose(self):
        self.emit("game-over", False)
        gobject.idle_add(self._after_lose)  # Time for the system

    def _after_lose(self):
        for b in self.array:
            for bb in b:

                try:
                    bb[0].disconnect_by_func(self.button_event)
                    bb[0].disconnect_by_func(self.button_activated)
                except:
                    pass

                if bb[0].get_active():
                    bb[0].set_active(True)
                    bb[0].connect("toggled", self.activate_button)

                elif not bb[0].get_active():
                    bb[0].set_active(False)
                    bb[0].connect("toggled", self.desactivate_button)

                if bb[1]:
                    image = gtk.Image()
                    pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(
                                             "icons/terron-mine.svg",
                                             bb[0].get_allocation()[-2] - 10,
                                             bb[0].get_allocation()[-1] - 10)
                    image.set_from_pixbuf(pixbuf)
                    image.show()
                    bb[0].add(image)

                if bb[0].flag:
                    image = gtk.Image()
                    pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(
          "icons/terron-flag-ok.svg" if bb[1] else "icons/terron-flag-bad.svg",
                                             bb[0].get_allocation()[-2] - 10,
                                             bb[0].get_allocation()[-1] - 10)
                    image.set_from_pixbuf(pixbuf)
                    image.show()
                    bb[0].remove(bb[0].get_children()[0])
                    bb[0].add(image)

    def win(self):
        self.emit('game-over', True)
        for b in self.array:
            for bb in b:

                bb[0].disconnect_by_func(self.button_event)
                bb[0].disconnect_by_func(self.button_activated)

                if bb[0].get_active():
                    bb[0].set_active(True)
                    bb[0].connect("toggled", self.activate_button)

                elif not bb[0].get_active():
                    bb[0].set_active(False)
                    bb[0].connect("toggled", self.desactivate_button)


class DifficultyButton(ToolButton):
    __gtype_name__ = 'TerronesWeeperDifficultyOptions'

    __gsignals__ = {
        'difficulty-changed': (gobject.SIGNAL_RUN_FIRST,
                               gobject.TYPE_NONE,
                               ([])),
                    }

    _SORT_OPTIONS = [('easy', 'insert-table', _('Easy')),
                     ('medium', 'insert-table', _('Medium')),
                     ('difficult', 'insert-table', _('Difficult'))]

    def __init__(self):
        ToolButton.__init__(self)
        self.connect("clicked", lambda w: w.props.palette.popup())

        self._property = 'medium'
        self._order = gtk.SORT_ASCENDING

        self.props.tooltip = _('Difficulty')
        self.props.icon_name = 'insert-table'

        for property_, icon, label in self._SORT_OPTIONS:
            button = MenuItem(icon_name=icon, text_label=label)
            button.connect('activate',
                           self.__difficulty_changed_cb,
                           property_,
                           icon)
            button.show()
            self.props.palette.menu.insert(button, -1)

    def __difficulty_changed_cb(self, widget, property_, icon_name):
        self._property = property_
        #FIXME: Implement sorting order
        self._order = gtk.SORT_ASCENDING
        self.emit('difficulty-changed')

        self.props.icon_name = icon_name

    def get_current_difficulty(self):
        return (self._property, self._order)


class TerronesWeeper(activity.Activity):
    difficulty_levels = {'easy': (5, gtk.ICON_SIZE_DIALOG),
                         'medium': (10, gtk.ICON_SIZE_LARGE_TOOLBAR),
                         'difficult': (20, gtk.ICON_SIZE_MENU)}

    def change_difficulty(self, widget):
        _property, order = widget.get_current_difficulty()
        self.size, self.icon = self.difficulty_levels[_property]
        if not type(self.current_widget) == gtk.Image:
            self.refresh_game(None)

    def _alert_user(self, title, msg):
        alert = Alert()
        alert.props.title = title
        alert.props.msg = msg
        self.add_alert(alert)
        alert.show()
        return alert

    def refresh_game(self, widget):
        self._flags = 0
        if self.alerting != None:
            self.remove_alert(self.alerting)
            self.alerting.destroy()
            self.alerting = None
        self._terrones = (self.size ** 2) / 4
        self.terron_button.set_icon("terron")
        self.label.set_text("%s: 00:00" % _("Time"))
        self.flags_label.set_text("%s: %s/%s" % (_("Flags"),
                                                    "0", self._terrones))
        self.timer.reset_timer(start=True)
        self.notebook.remove_page(0)
        self.current_widget = TerronesTable(self.size, self.icon)
        self.current_widget.show()
        self.current_widget.connect("game-over", self.game_over)
        self.current_widget.connect("flag-added", self._flag_added)
        self.current_widget.connect("flag-removed", self._flag_removed)
        self.notebook.append_page(self.current_widget)

    def time_changed(self, timer, time):
        self.label.set_text(("%s: " % _("Time")) + time)
        self.time = time

    def game_over(self, table, winner):
        self._flags = 0
        if winner:
            self.terron_button.set_icon("terron-glasses")
            self.timer.stop()
            self.label.set_text(self.label.get_text())

            # Save score:
            self.score.append("%s, %s" % (self.time,
                                    time.strftime("%d/%m/%y - %H:%M")))

            self.alerting = self._alert_user(_("CONGRATULATIONS"),
                                             _("You won"))
        else:
            self.terron_button.set_icon("terron-sad")
            self.alerting = self._alert_user(_("GAME OVER"), _("You lost"))
            self.timer.stop()

    def _flag_added(self, table):
        self._flags += 1
        self.flags_label.set_label("%s: %s/%s" % (_("Flags"),
                                                  self._flags,
                                                  self._terrones))

    def _flag_removed(self, table):
        self._flags -= 1
        self.flags_label.set_label("%s: %s/%s" % (_("Flags"),
                                                  self._flags,
                                                  self._terrones))

    def _show_score_dialog(self, button):
        score_dialog = ScoreDialog(self.score)
        score_dialog.show_all()

    def __init__(self, handle):
        activity.Activity.__init__(self, handle, True)
        self.alerting = None

        self.set_title(_("TerronesWeeper"))
        self.size = 10
        self.icon = gtk.ICON_SIZE_LARGE_TOOLBAR
        self.toolbarbox = ToolbarBox()

        self.score = []
        self.time = None

        self.timer = Timer()
        self.timer.connect("time-changed", self.time_changed)

        self.difficulty_button = DifficultyButton()
        self.difficulty_button.connect("difficulty-changed",
                                        self.change_difficulty)
        self.toolbarbox.toolbar.insert(self.difficulty_button, 0)
        self.difficulty_button.show()

        separator = gtk.SeparatorToolItem()
        separator.set_draw(False)
        separator.set_expand(True)
        self.toolbarbox.toolbar.insert(separator, -1)

        self.terron_button = ToolButton("terron")
        self.terron_button.connect("clicked", self.refresh_game)
        self.toolbarbox.toolbar.insert(self.terron_button, -1)
        self.terron_button.show()

        separator = gtk.SeparatorToolItem()
        separator.set_draw(False)
        separator.set_expand(True)
        self.toolbarbox.toolbar.insert(separator, -1)

        score_btn = ToolButton("score")
        score_btn.connect("clicked", self._show_score_dialog)
        self.toolbarbox.toolbar.insert(score_btn, -1)

        exit = StopButton(self)
        self.toolbarbox.toolbar.insert(exit, -1)

        self.set_toolbar_box(self.toolbarbox)
        self.toolbarbox.show_all()
        self.notebook = gtk.Notebook()
        white_box = gtk.EventBox()
        white_box.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
        self.current_widget = gtk.image_new_from_file(_("presentation.png"))
        self.current_widget.show()
        white_box.add(self.current_widget)
        self.notebook.set_show_tabs(False)
        self.notebook.append_page(white_box)
        self.notebook.show()
        self.statusbar = gtk.Statusbar()
        self.label = gtk.Label(_("Click on the terron of the toolbar to start."
                                 ))
        self.label.show()

        self._flags = 0
        self._terrones = (self.size ** 2) / 4

        self.flags_label = gtk.Label()

        self.statusbar.pack_start(self.flags_label, False, True, 2)
        self.statusbar.pack_end(self.label, True, True, 2)
        self.statusbar.show()
        self.vbox = gtk.VBox()
        self.vbox.pack_start(self.notebook, True, True, 0)
        self.vbox.pack_end(self.statusbar, False, True, 0)
        self.vbox.show()
        self.set_canvas(self.vbox)

        self.show_all()

    def read_file(self, file_path):
        jfile = open(file_path)
        try:
            self.score = json.load(jfile)
        except:
            jfile.close()

        # To list
        self.score = list(self.score)

    def write_file(self, file_path):
        jfile = open(file_path, "w")

        try:
            json.dump(tuple(self.score), jfile)
        finally:
            jfile.close()
