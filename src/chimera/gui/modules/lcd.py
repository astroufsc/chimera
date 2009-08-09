#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005 Gerome Fournier <jefke(at)free.fr>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"SLIMP3 player emulator written in python"

import gtk
import os
import sys
import signal
import struct
import socket
import random

_CHARS_FILENAME = os.path.join(os.path.dirname(__file__), "lcd_chars.txt")

_KEY_MAPPING = {
    "0": '0',
    "1": '1',
    "2": '2',
    "3": '3',
    "4": '4',
    "5": '5',
    "6": '6',
    "7": '7',
    "8": '8',
    "9": '9',
    "KP_0": '0',
    "KP_1": '1',
    "KP_2": '2',
    "KP_3": '3',
    "KP_4": '4',
    "KP_5": '5',
    "KP_6": '6',
    "KP_7": '7',
    "KP_8": '8',
    "KP_9": '9',
    "UP": 'UP',
    "RIGHT": 'RIGHT',
    "LEFT": 'LEFT',
    "DOWN": 'DOWN',
    "PAGE_UP": 'VOLUP',
    "PAGE_DOWN": 'VOLDOWN',
    "HOME": 'NOW_PLAYING',
    "RETURN": 'PLAY',
    "KP_ENTER": 'PLAY',
    "SPACE": 'PAUSE',
    "BRACKETLEFT": 'REW',
    "BRACKETRIGHT": 'FWD',
    "PLUS": 'ADD',
    "KP_ADD": 'ADD',
    "SLASH": 'SEARCH',
    "KP_DIVIDE": 'SEARCH',
    "A": 'SLEEP',
    "B": 'BRIGHTNESS',
    "F": 'SIZE',
    "R": 'REPEAT',
    "S": 'SHUFFLE',
}

class LCDWidget:
    "GTK+ LCD Widget"

    def __init__(self, widget, rows, cols):
        "Instantiate a LCD widget"
        self.rows = rows
        self.cols = cols
        self._area = widget
        self._pix = None
        self._table = {}
        self._area.connect("configure-event", self._configure_cb)
        self._area.connect("expose-event", self._expose_cb)
        self._lastString = None

    def set_zoom_factor(self, factor):
        "Set the zoom factor"
        self._factor = factor
        self._border = 5
        self._cborder = 3*factor
        self._cwidth = 9*factor
        self._cheight = 13*factor
        self._width = 2*self._border + \
                (self._cwidth+self._cborder)*self.cols + self._cborder
        self._height = 2*self._border + \
                (self._cheight+self._cborder)*self.rows + self._cborder
        self._area.set_size_request(self._width, self._height)
        
    def get_zoom_factor(self):
        return self._factor

    def refresh(self):
        "Refresh the LCD widget"
        self._area.queue_draw_area(0, 0, self._width, self._height)

    def draw_char(self, row, col, charindex):
        """Draw the character stored at position 'charindex' in the internal
           character definition table, on the LCD widget
        """
        if not self._pix:
            return
        x = col * (self._cwidth+self._cborder) + self._border + self._cborder
        y = row * (self._cheight+self._cborder) + self._border + self._cborder
        self._pix.draw_drawable(self._back, self._table[charindex], \
                0, 0, x, y, self._cwidth, self._cheight)

    def set_brightness_percentage(self, percentage):
        fg_colors = {
            100: "#00ff96",
            75: "#00d980",
            50: "#00b269",
            25: "#008c53",
            0: "#303030"
        }
        if percentage not in fg_colors.keys():
            return
        if hasattr(self, "_brightness_percentage") \
            and self._brightness_percentage == percentage:
            return
        self._brightness_percentage = percentage
        self._set_colors(["#000000", "#303030", fg_colors[percentage]])
        self._load_font_definition()
        
    def get_brightness_percentage(self):
        return self._brightness_percentage

    def clear(self):
        "Clear the LCD display"
        for row in range(self.rows):
            for col in range(self.cols):
                self.draw_char(row, col, 32)
        self.refresh()

    def set_button_press_event_cb(self, cb):
        "Setup a callback when a mouse button is pressed on the LCD display"
        self._area.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self._area.connect("button_press_event", cb)

    def set_scroll_event_cb(self, cb):
        "Setup a callback when wheel mouse is used on the LCD display"
        self._area.connect("scroll_event", cb)

    def create_char(self, charindex, shape):
        """Insert a new char in the character table definition,
           at position 'charindex', based on 'shape'
        """
        pix = gtk.gdk.Pixmap(self._area.window, self._cwidth, self._cheight)
        pix.draw_rectangle(self._back, True, 0, 0, self._cwidth, self._cheight)
        for x in range(5):
            for y in range(7):
                pix.draw_rectangle(self._charbg, True, \
                    x*2*self._factor, y*2*self._factor, \
                    self._factor, self._factor)
        for index in range(35):
            if shape[index] == "1":
                row = index / 5
                col = index - row*5
                pix.draw_rectangle(self._charfg, True, \
                    col*2*self._factor, row*2*self._factor, \
                    self._factor, self._factor)
        self._table[charindex] = pix

    def print_line(self, string):
        "Print a single line on the LCD display"
        self._lastString = string
        self.clear()
        for i in range(len(string[:self.cols])):
            self.draw_char(0, i, ord(string[i]))
        self.refresh()

    def _configure_cb(self, widget, event):
        x, y, width, height = widget.get_allocation()
        self._pix = gtk.gdk.Pixmap(widget.window, width, height)
        self.set_brightness_percentage(100)
        self._pix.draw_rectangle(self._back, True, 0, 0, width, height)
        self._load_font_definition()
        self.clear()
        if self._lastString:
            self.print_line(self._lastString)
        return True

    def _expose_cb(self, widget, event):
        if self._pix:
            widget.window.draw_drawable(self._back, self._pix, 0, 0, 0, 0, \
                    self._width, self._height)
        return False

    def _set_colors(self, colors):
        for widget, color in zip(["_back", "_charbg", "_charfg"], colors):
            exec "self.%s = gtk.gdk.GC(self._pix)" % widget
            exec "self.%s.set_rgb_fg_color(gtk.gdk.color_parse('%s'))" \
                % (widget, color)

    def _load_font_definition(self):
        try:
            file = open(_CHARS_FILENAME)
        except IOError:
            print >>sys.stderr, "Unable to open font characters definition '%s'" \
                    % _CHARS_FILENAME
            sys.exit(1)
        index = 1
        shape = ""
        for line in file.readlines():
            line = line.rstrip()
            if not line or line[0] == "#":
                continue
            if index == 1:
                char_index = int(line, 16)
            else:
                shape = ''.join([shape, line])
            index += 1
            if index == 9:
                self.create_char(char_index, shape)
                index = 1
                shape = ""

class Slimp3LCD(LCDWidget):
    "An LCD display abble to parse Slimp3 LCD display packets"
    _CODE_DELAY = 0
    _CODE_CMD = 2
    _CODE_DATA = 3

    _CMD_CLEAR = 0
    _CMD_HOME = 1
    _CMD_MODE = 2
    _CMD_DISPLAY = 3
    _CMD_SHIFT = 4
    _CMD_FUNC_SET = 5
    _CMD_CG_ADDR = 6
    _CMD_DD_ADDR = 7
    
    def parse_lcd_packet(self, lcd_packet):
        "Parse a SLIMP3 LCD packet"
        self.addr = 0
        self.shift = 1
        i = 0
        while i < len(lcd_packet)/2:
            chunk = socket.ntohs(struct.unpack("H", lcd_packet[i*2:i*2+2])[0])
            code = (chunk & 0xFF00) >> 8
            cmd = chunk & 0x00FF
            if code == self._CODE_DELAY:
                pass
            elif code == self._CODE_CMD:
                i += self._handle_command(cmd, lcd_packet[i*2:])
            elif code == self._CODE_DATA:
                row = self.addr / self.cols
                col = self.addr - self.cols*row
                self.draw_char(row, col, cmd)
                self._move_cursor(self.shift)
            i += 1
        self.refresh()

    def _handle_command(self, cmd, string):
        "Handle LCD commands"
        if cmd >> self._CMD_CLEAR == 1:
            self.clear()
            self.addr = 0
            self.shift = 1
        elif cmd >> self._CMD_HOME == 1:
            self.addr = 0
        elif cmd >> self._CMD_MODE == 1:
            if cmd & 2 != 0:
                self.shift = 1
            else:
                self.shift = -1
        elif cmd >> self._CMD_DISPLAY == 1:
            pass
        elif cmd >> self._CMD_SHIFT == 1:
            if cmd & 0x04:
                self.move_cursor(-1)
            else:
                self.move_cursor(1)
        elif cmd >> self._CMD_FUNC_SET == 1:
            return self._handle_function_set(cmd, string[2:4])
        elif cmd >> self._CMD_CG_ADDR == 1:
            return self._handle_char_definition(cmd, string[2:16])
        elif cmd >> self._CMD_DD_ADDR == 1:
            pass
        return 0

    def _handle_function_set(self, cmd, string):
        "Handle Brightness stuff"
        if ord(string[0]) == 3:
            self.set_brightness_percentage(100 - 25 * ord(string[1]))
            return 1
        else:
            return 0
        
    def _handle_char_definition(self, char, string):
        "Create a char as defined by 'string'"
        if len(string) != 14:
            print >>sys.stderr, "Character definition has a wrong size!"
            return 0
        shape = [' '] * 35
        index = (0x3f & char) >> 3;
        for i in range(7):
            line = ord(string[2*i + 1])
            for j in range(5):
                if 1 & (line >> (4 - j)):
                    shape[i*5+j] = "1"
        self.create_char(index, shape)
        # defining a new char consume 7 extra command codes
        return 7

    def _move_cursor(self, shift):
        self.addr += shift
        if self.addr < 0:
            self.addr = 0
        elif self.addr > self.rows * self.cols - 1:
            self.addr = self.rows * self.cols - 1


class Slimp3Gui:
    "Main GUI"

    def __init__(self):
        "Instantiate the application"
        self._setup_widgets()
        self._set_zoom_factor(1)

    def run(self):
        "Start the application"
        try:
            signal.signal(signal.SIGINT, self._quit)
            signal.signal(signal.SIGTERM, self._quit)
            self._window.show_all()
            self.print_bollocks()
            gtk.main()
        except KeyboardInterrupt:
            self._quit()
        except:
            raise

    def _quit(self, *args):
        gtk.main_quit()

    def _setup_widgets(self):
        self._window = gtk.Window()
        self._window.hide()
        self._window.connect("destroy", self._quit)
        widget = gtk.DrawingArea()
        self._window.add(widget)
        self.lcd_display = Slimp3LCD(widget, 2, 40)
        self.lcd_display.set_button_press_event_cb(self.button_press_cb)
        self.lcd_display.set_scroll_event_cb(self.scroll_event_cb)
        
    def button_press_cb(self, widget, event):
        self.print_bollocks(start=random.randint(16,30))
        return True

    def scroll_event_cb(self, widget, event):
        change = 0
        
        if (event.state & gtk.gdk.CONTROL_MASK) == gtk.gdk.CONTROL_MASK:
            if event.direction == gtk.gdk.SCROLL_UP:
                change = 25
            elif event.direction == gtk.gdk.SCROLL_DOWN:
                change = -25

            p = self.lcd_display.get_brightness_percentage()
            self._set_brightness_percentage(p+change)
                

        else:
            if event.direction == gtk.gdk.SCROLL_UP:
                change = 1
            elif event.direction == gtk.gdk.SCROLL_DOWN:
                change = -1
            
            z = self.lcd_display.get_zoom_factor()
            self._set_zoom_factor(z+change)

        self.print_bollocks()
        return True

    def _set_zoom_factor(self, factor):
        if factor < 1:
            factor = 1
        if factor > 2:
            factor = 2
        self.lcd_display.set_zoom_factor(factor)
        
    def _set_brightness_percentage(self, percent):
        if percent < 0:
            percent = 0
        if percent > 100:
            percent = 100
        self.lcd_display.set_brightness_percentage(percent)
        
    def print_bollocks(self, start=16):
        self.lcd_display.clear()
        self.lcd_display.print_line("ABCDEFGHIJKLMNOPabcdefghij")
        for i in range(0,40):
            self.lcd_display.draw_char(1,i,start+i)
        self.lcd_display.refresh()
        
if __name__ == "__main__":
    if len(sys.argv) > 1:
        print >>sys.stderr, "Usage: %s\nSlimp3 client written in python." \
                % sys.argv[0]
        sys.exit(1)
    app = Slimp3Gui()
    app.run()

# vim: ts=4 sw=4 noet
