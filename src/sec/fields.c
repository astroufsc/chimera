/***************************************************************************
                          fields.c  -  description
                             -------------------
    begin                : Wed Jun 7 2000
    copyright            : (C) 2000 by Andre Luiz de Amorim
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
#include <ctype.h>
#include <string.h>
#include "fields.h"

int getfield(char *command, field *f, const char *flist[])
{
        int i;
        char tmp[MAX_FIELD_SIZE];
        char *ptr;

        if (command == NULL || *command == '\0') return(FEMPTY_FIELD);
        if (flist == NULL) return (EOF);

        /* find field type */
        ptr = tmp;
        while (isspace(*command)) command++;
        if (*command == FCOMMENT_CHAR || *command == '\0')
                /* Comment or empty line */
                return(FEMPTY_FIELD);

        i = 0;
        while (!isspace(*command) && *command != '\0' && i++ < MAX_FIELD_SIZE)
                *ptr++ = *command++;
        *ptr = '\0';

        i = -1;
        /* Look for the field index, */
        /* exit if reached the end of list */
        do
	  if (flist[++i] == NULL) return (FNO_MATCH);
        while (strncmp(tmp, flist[i], MAX_FIELD_SIZE) != 0);

        /* do not care with field contents */
        if (f == NULL) return (i);

        /* store field content */
        f->index = i;
        while (isspace(*command)) command++;
        /* while (*ptr++ = *command++); */
        f->contents = command;

        return(i);
}

