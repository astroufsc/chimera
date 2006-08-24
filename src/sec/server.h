/***************************************************************************
                          multisrv.h  -  description
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

#ifndef MULTISKT_H
#define MULTISKT_H

#include "sockets.h"

#include "sktlist.h"

#define ABORT_MESSAGE "ABORT"
#define ERROR_MESSAGE "ERROR"
#define SERVER_FULL_MESSAGE "SERVER_FULL"

#define MAX_CLIENT_NAME (32)
#define MAX_SERVER_NAME (32)

typedef struct _Server Server;

/* pointer to handler functions */
typedef int (*accept_hndl) (SktListItem *);
typedef int (*answer_hndl) (SktListItem *);
typedef int (*close_hndl) (SktListItem *);

struct _Server {
        char *name;
        int type;

        Socket *skt;
        int nconn;
        int nclients;
        int maxclients;
        SktList *clientlist;

	/* pointer to `accept' handler */
	accept_hndl accept_handler;
	/* pointer to `answer' handler */
	answer_hndl answer_handler;
	/* pointer to `server_close_client' handler */
	close_hndl close_handler;
	/* pointer to any useful thing */
};


Server *server_init(char *sname, int type);
void 	server_close(Server *srv);

int 	server_is_valid(Server *srv);
int 	server_verify(Server *srv);

int 	server_write_client(const char *buf, SktListItem *clnt);
int 	server_set_client_name(SktListItem *clnt, char *name);
void 	server_close_client(SktListItem *clnt);

/* default accept routine */
SktListItem	*server_accept(Server *srv);
int 		server_answer(SktListItem *clnt);

#endif /* MULTISKT_H */
