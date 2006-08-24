/***************************************************************************
                          messages.c  -  description
                             -------------------
    begin                : Thu Feb 1 2001
    copyright            : (C) 2001 by Andre Luiz de Amorim
    email                : andre@astro.ufsc.br
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

#include <stdio.h>

/* communication commands */
const char *fcomm[] = {
        "QUIT", "IDENT", "STATUS", "SETSTATUS", "NOTIFY", "UNOTIFY",
        "CONTROL", "ANSWER", "RESET", "SHUTDOWN", NULL
}; /* The null pointer terminator prevents getfield()
   to raise a `Segmentation fault' */

/* Responses */
const char *fresponses[] = {
        "HELLO", "OK", "ERROR", "ABORT","SERVER_FULL",
        "STATUS", "NOTIFY", "RESET", NULL
};

/* instrument states */
const char *finststatus[] = {
        "OFFLINE", "BUSY", "DISABLED", "IDLE", NULL
};

/* TRUE & FALSE */
#define S_TRUE  "TRUE"
#define S_FALSE "FALSE"
