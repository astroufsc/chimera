/***************************************************************************
                          skterror.h  -  description
                             -------------------
    begin                : Wed Oct 4 2000
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

#ifndef SKTERROR_H
#define SKTERROR_H

#include "sockets.h"

/* ask if there were some error while writing to socket */
int skterror(void);
/* Tell sigpipe() who is trying to write to socket */
void watch(Socket *skt);

void pipe_error(int sig);

#endif /* STKERROR_H */
