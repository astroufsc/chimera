/***************************************************************************
                          sktlist.h  -  description
                             -------------------
    begin                : Tue Sep 12 2000
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

#ifndef SKTLIST_H
#define SKTLIST_H

#include "sockets.h"

/* socket types */
#define SKT_SENTINEL (0)
#define SKT_CLIENT   (1)
#define SKT_SERVER   (2)

/* to use static id's, start them at (MAX_ID + 1) */
#define MAX_ID (1000000L)
#define MAXBUFLEN  (128)

/* Client states */
/* CST_IDENT_PENDING  - Server is waiting response from client,
                        don't send anything */
/* CST_NOTIFY         - Notify the client when an event occurs */
/* CST_IDLE           - Client is idle */
/* CST_WAITING_NOTIFY - Client is waiting notification from server */
enum { CST_IDENT_PENDING, CST_NOTIFY, CST_IDLE, CST_WAITING };

/* item of sockets linked list */
typedef struct _SktListItem SktListItem;

struct _SktListItem {
        int id;
        char *name;
        void *server; /*  pointer to Server structure */
        int type;
        int state;
	Socket *skt;
        
	SktListItem *next, *previous;
};

/* Socket linked list */
typedef struct {
        SktListItem *head;
        SktListItem *first;
        SktListItem *tail;
} SktList;


/* Socket list utilities */
SktList     *sktlist_new(void);
int          sktlist_free(SktList *list);
SktListItem *sktlist_add(SktList *list, Socket *skt, int type);
void         sktlist_remove(SktList *list, SktListItem *item);


#endif /* SKTLIST_H */
