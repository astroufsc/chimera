# Copyright 1998-2004 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id: output.py,v 1.1 2006/03/06 18:13:31 henrique Exp $


import os
import sys
import re

have_color = 1
do_titles = 1

spin_pos = 0
spinner = "/-\\|/-\\|/-\\|/-\\|\\-/|\\-/|\\-/|\\-/|"

esc_seq = "\x1b["

g_attr = {}
g_attr["normal"] = 0

g_attr["bold"] = 1
g_attr["faint"] = 2
g_attr["standout"] = 3
g_attr["underline"] = 4
g_attr["blink"] = 5
g_attr["overline"] = 6  # Why is overline actually useful?
g_attr["reverse"] = 7
g_attr["invisible"] = 8

g_attr["no-attr"] = 22
g_attr["no-standout"] = 23
g_attr["no-underline"] = 24
g_attr["no-blink"] = 25
g_attr["no-overline"] = 26
g_attr["no-reverse"] = 27
# 28 isn't defined?
# 29 isn't defined?
g_attr["black"] = 30
g_attr["red"] = 31
g_attr["green"] = 32
g_attr["yellow"] = 33
g_attr["blue"] = 34
g_attr["magenta"] = 35
g_attr["cyan"] = 36
g_attr["white"] = 37
# 38 isn't defined?
g_attr["default"] = 39
g_attr["bg_black"] = 40
g_attr["bg_red"] = 41
g_attr["bg_green"] = 42
g_attr["bg_yellow"] = 43
g_attr["bg_blue"] = 44
g_attr["bg_magenta"] = 45
g_attr["bg_cyan"] = 46
g_attr["bg_white"] = 47
g_attr["bg_default"] = 49


# make_seq("blue", "black", "normal")
def color(fg, bg="default", attr=["normal"]):
    my_str = f"{esc_seq}{g_attr[fg]:02d}"
    for x in [bg] + attr:
        my_str += f";{g_attr[x]:02d}"
    return f"{my_str}m"


codes = {}
codes["reset"] = esc_seq + "39;49;00m"

codes["bold"] = esc_seq + "01m"
codes["faint"] = esc_seq + "02m"
codes["standout"] = esc_seq + "03m"
codes["underline"] = esc_seq + "04m"
codes["blink"] = esc_seq + "05m"
codes["overline"] = esc_seq + "06m"  # Who made this up? Seriously.

codes["teal"] = esc_seq + "36m"
codes["turquoise"] = esc_seq + "36;01m"

codes["fuchsia"] = esc_seq + "35;01m"
codes["purple"] = esc_seq + "35m"

codes["blue"] = esc_seq + "34;01m"
codes["darkblue"] = esc_seq + "34m"

codes["green"] = esc_seq + "32;01m"
codes["darkgreen"] = esc_seq + "32m"

codes["yellow"] = esc_seq + "33;01m"
codes["brown"] = esc_seq + "33m"

codes["red"] = esc_seq + "31;01m"
codes["darkred"] = esc_seq + "31m"


def nc_len(my_str):
    tmp = re.sub(esc_seq + "^m]+m", "", my_str)
    return len(tmp)


def xterm_title(my_str):
    if have_color and do_titles and "TERM" in os.environ and sys.stderr.isatty():
        my_t = os.environ["TERM"]
        legal_terms = [
            "xterm",
            "Eterm",
            "aterm",
            "rxvt",
            "screen",
            "kterm",
            "rxvt-unicode",
        ]
        for term in legal_terms:
            if my_t.startswith(term):
                sys.stderr.write("\x1b]2;" + str(my_str) + "\x07")
                sys.stderr.flush()
                break


def xterm_title_reset():
    if have_color and do_titles and "TERM" in os.environ:
        xterm_title(os.environ["TERM"])


def no_titles():
    "turn off title setting"


def no_color():
    "turn off colorization"
    for x in list(codes.keys()):
        codes[x] = ""


def reset_color():
    return codes["reset"]


def ctext(color, text):
    return codes[ctext] + text + codes["reset"]


def bold(text):
    return codes["bold"] + text + codes["reset"]


def faint(text):
    return codes["faint"] + text + codes["reset"]


def white(text):
    return bold(text)


def teal(text):
    return codes["teal"] + text + codes["reset"]


def turquoise(text):
    return codes["turquoise"] + text + codes["reset"]


def dark_teal(text):
    return turquoise(text)


def fuscia(text):  # Don't use this one. It's spelled wrong!
    return codes["fuchsia"] + text + codes["reset"]


def fuchsia(text):
    return codes["fuchsia"] + text + codes["reset"]


def purple(text):
    return codes["purple"] + text + codes["reset"]


def blue(text):
    return codes["blue"] + text + codes["reset"]


def dark_blue(text):
    return codes["darkblue"] + text + codes["reset"]


def green(text):
    return codes["green"] + text + codes["reset"]


def dark_green(text):
    return codes["darkgreen"] + text + codes["reset"]


def yellow(text):
    return codes["yellow"] + text + codes["reset"]


def brown(text):
    return codes["brown"] + text + codes["reset"]


def dark_yellow(text):
    return brown(text)


def red(text):
    return codes["red"] + text + codes["reset"]


def dark_red(text):
    return codes["darkred"] + text + codes["reset"]


def update_basic_spinner():
    global spinner, spin_pos
    spin_pos = (spin_pos + 1) % 500
    if (spin_pos % 100) == 0:
        if spin_pos == 0:
            sys.stdout.write(". ")
        else:
            sys.stdout.write(".")
    sys.stdout.flush()


def update_scroll_spinner():
    global spinner, spin_pos
    if spin_pos >= len(spinner):
        sys.stdout.write(
            dark_green(
                " \b\b\b" + spinner[len(spinner) - 1 - (spin_pos % len(spinner))]
            )
        )
    else:
        sys.stdout.write(green("\b " + spinner[spin_pos]))
    sys.stdout.flush()
    spin_pos = (spin_pos + 1) % (2 * len(spinner))


def update_spinner():
    global spinner, spin_pos
    spin_pos = (spin_pos + 1) % len(spinner)
    sys.stdout.write("\b\b " + spinner[spin_pos])
    sys.stdout.flush()
