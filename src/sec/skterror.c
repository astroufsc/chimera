/***************************************************************************
                          skterror.c  -  description
                             -------------------
    begin                : Tue Oct 3 2000
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
#include "sockets.h"

#include "skterror.h"

#define TRUE  (1)
#define FALSE (0)

static Socket *watch_socket;
static int s_error;

/* prepare to write to Status socket */
void watch(Socket *skt)
{
        watch_socket = skt;
        s_error = FALSE;
}


int skterror(void)
{
        if (s_error) return (1);
        return (0);
}


void pipe_error(int sig)
{
        /* Error writing to a socket */
        printf("\n\n*** Error: Attempt to write to a broken socket.\n");

        s_error = TRUE;

}
