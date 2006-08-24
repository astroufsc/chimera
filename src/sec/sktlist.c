/***************************************************************************
                          sktlist.c  -  description
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

#include <stdio.h>
#include <stdlib.h>
#include "sockets.h"
#include "sktlist.h"

static int id_counter = 0;

SktList *sktlist_new(void)
{
        SktList *list;

        list = (SktList *) calloc(1, sizeof(SktList));
        if (list == NULL) return (NULL);

        /* create ``sentinels'' */
        /* Null SocketList entries, just to mark the end/beginning of the list. */
        list->head = (SktListItem *) calloc(1, sizeof(SktListItem));
        if (list->head == NULL) return (NULL);
        list->tail = (SktListItem *) calloc(1, sizeof(SktListItem));
        if (list->tail == NULL) return (NULL);

        /* head points to tail */
        list->head->previous = NULL;
        list->head->next = list->tail;
        list->head->skt = NULL;
        list->head->type = SKT_SENTINEL;

        /* tail points to head */
        list->tail->previous = list->head;
        list->tail->next = NULL;
        list->tail->skt = NULL;
        list->tail->type = SKT_SENTINEL;

        /* `first' == `head->next' */
        list->first = list->head->next;

        return (list);
}


int sktlist_free(SktList *list)
{
        if (list == NULL) return (0);

        /* List must be empty */
        if (list->head->next != NULL) return (-1);
        free(list->head);
        free(list->tail);
        free(list);
        return (0);
}


SktListItem *sktlist_add(SktList *list, Socket *skt, int type)
{
        SktListItem *new;

        /* Add a _connected_ socket only */
        if (skt == NULL || list == NULL) return (NULL);
        new = (SktListItem *) calloc(1, sizeof(SktListItem));
        if (new == NULL) return (NULL);

        /* append new item to the tail */
        list->tail->previous->next = new;
        new->previous = list->tail->previous;
        list->tail->previous = new;
        new->next = list->tail;
        new->type = type;

        /* Increment id_counter, if reached MAX_ID, restart counting */
        /* I don't know what to do when this happen, hope it won't   */
        /*   bring any trouble. */
        new->id = id_counter++ % MAX_ID;

        /* Point the first item to the right place */
        list->first = list->head->next;

        new->skt = skt;

        return (new);
}


/* this does NOT disconnect the socket! */
void sktlist_remove(SktList *list, SktListItem *item)
{
        if (item == NULL  || list == NULL) return;

        /* keep the sentinels */
        if (item->type == SKT_SENTINEL) return;

        /* link neighbors together */
        item->previous->next = item->next;
        if (item->next != NULL) item->next->previous = item->previous;

        /* Point the first item to the right place */
        list->first = list->head->next;

        free(item);
}

