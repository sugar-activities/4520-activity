#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
#       TerronesWeeper Activity - timer.py
#
#       Copyright 2011 Daniel Francis <santiago.danielfrancis@gmail.com>,
#                      Agustín Zubiaga <aguzubiaga97@gmail.com>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 3 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
#
#

import gobject


class Timer(gobject.GObject):

    __gsignals__ = {"time-changed": (gobject.SIGNAL_RUN_LAST,
                                     gobject.TYPE_NONE,
                                     (gobject.TYPE_STRING,))}

    def __init__(self):

        gobject.GObject.__init__(self)

        self.time = "00:00:00"
        self.seconds = 0
        self.minutes = 0

        self.timeout = None

    def start(self):
        self.timeout = gobject.timeout_add(1000, self.update_time)

    def stop(self):
        if self.timeout:
            gobject.source_remove(self.timeout)

    def update_time(self):
        self.seconds += 1

        if int(str(float(self.seconds / 60)).split(".")[-1]) > 0:
            self.minutes += 1
            self.seconds = 0

        else:
            if self.seconds / 60 >= 1:
                self.minutes += 1
                self.seconds = 0

        minutes = str(self.minutes)
        seconds = str(self.seconds)

        if self.minutes < 10:
            minutes = "0" + str(self.minutes)

        if self.seconds < 10:
            seconds = "0" + str(self.seconds)

        self.time = "%s:%s" % (minutes, seconds)

        self.emit("time-changed", self.time)

        return True

    def reset_timer(self, start=False):
        self.stop()
        self.minutes = 0
        self.seconds = 0
        self.time = "00:00:00"

        if start:
            self.start()
