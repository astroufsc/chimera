/***************************************************************************
                          messages.h  -  description
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

#ifndef MESSAGES_H
#define MESSAGES_H

/* TRUE & FALSE */
#define S_TRUE  "TRUE"
#define S_FALSE "FALSE"


/* communication commands */
extern const char *fcomm[];
enum { C_QUIT, C_IDENT, C_STATUS, C_SETSTATUS, C_NOTIFY, C_UNOTIFY,
       C_CONTROL, C_ANSWER, C_RESET, C_SHUTDOWN };

/* Responses */
extern const char *fresponses[];
enum { RES_HELLO, RES_OK, RES_ERROR, RES_ABORT, RES_SERVER_FULL, RES_STATUS,
       RES_NOTIFY, RES_RESET };

/* instrument states */
extern const char *finststatus[];
enum { IST_OFFLINE, IST_BUSY, IST_DISABLED, IST_IDLE };

#endif /* MESSAGES_H */
