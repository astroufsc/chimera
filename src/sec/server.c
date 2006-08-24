/***************************************************************************
                          multiskt.c  -  description
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
#include <string.h>
#include <ctype.h>
#include <stdlib.h>

#include "sockets.h"

#include "skterror.h"
#include "sktlist.h"

#include "server.h"

int server_is_valid(Server *srv)
{
        if (srv == NULL) return (0);
        if (srv->name == NULL) return (0);
        if (srv->clientlist == NULL) return (0);
        if (srv->skt == NULL) return (0);
        return (1);
}


Server *server_init(char *sname, int type)
{
        Server *srv;

        if (sname == NULL) return (NULL);
        srv = (Server *) calloc(1, sizeof(Server));
        if (srv == NULL) return (NULL);

        srv->name = (char *) calloc(strlen(sname) + 1, sizeof(char));
        if (srv->name == NULL) {
                free(srv);
                return (NULL);
        }
        strcpy(srv->name, sname);
        srv->skt = Sopen(sname, "s");
        if (srv->skt == NULL) {
                /* force opening, remove existing server */
                Srmsrvr(sname);
                srv->skt = Sopen(sname, "s");
        }
        if (srv->skt == NULL) {
                /* could not open server */
                printf("*** Error opening \"%s\" server.\n", sname);
                printf("*** The PortMaster could be down.\n");
                free(srv);
                return (NULL);
        }
        srv->clientlist = sktlist_new();
        if (srv->clientlist == NULL) {
                printf("*** Error allocating client list.\n");
                Sclose(srv->skt);
                free(srv);
                return(NULL);
        }
        Smaskset(srv->skt);

        printf(" -> Server \"%s\" open.\n", sname);

        return (srv);
}


void server_close(Server *srv)
{
        SktList *tmp;

        if (srv == NULL) return;

        if (srv->name != NULL) free(srv->name);
        if (srv->clientlist != NULL) {
                /* disconnect all clients... */
                tmp = srv->clientlist;
                while (tmp->first->type == SKT_CLIENT) {
                        Sputs(ABORT_MESSAGE, tmp->first->skt);
                        server_close_client(tmp->first);
                }
                sktlist_free(srv->clientlist);
        }
        if (srv->skt != NULL) {
                Smaskunset(srv->skt);
                Sclose(srv->skt);
        }
        free(srv);
}


SktListItem *server_accept(Server *srv)
{
        Socket *skt;
        SktListItem *item;

        if (!server_is_valid(srv)) return(NULL);

        skt = Saccept(srv->skt);
        if (skt == NULL) return (NULL);
/*         if (srv->nclients >= srv->maxclients) { */
/*                 /\* Deny access, server full *\/ */
/*                 printf("*** <%s> %s: Connection denied.\n", */
/*                         srv->name, Speername(skt)); */
/*                 Sputs(SERVER_FULL_MESSAGE, skt); */
/*                 Sclose(skt); */
/*                 return (NULL); */
/*         } */
        item = sktlist_add(srv->clientlist, skt, SKT_CLIENT);
        if (item == NULL) {
                printf("*** <%s> %s: Error allocating Socket List \
                                 entry. Connection denied.\n",
                                 srv->name, Speername(skt));
                Sputs(ERROR_MESSAGE, skt);
                Sclose(skt);
                return (NULL);
        }

        Smaskset(skt);
        srv->nclients++;
        srv->nconn++;

        /* Save pointer to server in client */
        item->server = srv; /* e.g: srv->clientlist->last->server = srv; */

        printf(" -> <%s> %s Connected.\n",
                srv->name, Speername(skt));

        return (item);
}


void server_close_client(SktListItem *clnt)
{
        Server *srv;

        if (clnt == NULL) return;
        srv = clnt->server;
        if (!server_is_valid(srv)) return;

        /* Execute close handler */
        if (srv->close_handler != NULL)
                (*srv->close_handler) (clnt);

        if (clnt->name != NULL) free(clnt->name);

        if (clnt->skt != NULL) {
                Smaskunset(clnt->skt);
                Sclose(clnt->skt);
        }
        sktlist_remove(srv->clientlist, clnt);

        srv->nclients--;
}


int server_write_client(const char *buf, SktListItem *clnt)
{
        Server *srv;

        if (buf == NULL || clnt == NULL) return (EOF);
        srv = clnt->server;
        if (!server_is_valid(srv)) return (EOF);

        watch(clnt->skt);
        Sputs((char *)buf, clnt->skt);
        if (skterror()) {
                server_close_client(clnt);
                return (EOF);
        }
        return (0);
}


int server_set_client_name(SktListItem *clnt, char *name)
{
        char buf[MAX_CLIENT_NAME];
        char *ptr;
	int i = 0;

        if (clnt == NULL) return (EOF);
        if (clnt->name != NULL) free(clnt->name);

	/* Remove white space, and keep 1 char for '\0' */
        ptr = buf;
        while (!isspace(*name) && (*name != '\0') && (++i < MAX_CLIENT_NAME))
                *ptr++ = *name++;
        *ptr = '\0';

	/* String size already checked, safe calling strlen and stcpy */
        clnt->name = (char *) calloc(strlen(buf) + 1, sizeof(char));
        if (clnt->name == NULL) return (EOF);
        strcpy(clnt->name, buf);
        return (0);
}


int server_answer(SktListItem *clnt)
{
        /* Dummy routine */
        return (1);
}


/* Look for sockets that have changed and process them */
int server_verify(Server *srv)
{
        SktListItem *client, *tmp;
        int res;

        if (!server_is_valid(srv)) return(EOF);
        /*** Do not even dream calling a NULL function pointer ***/
        if (srv->accept_handler == NULL || srv->answer_handler == NULL)
                return (EOF);

        /*** Process server ***/
        res = Stest(srv->skt);
        if (res > 0) {
                /* Accept connection (ATTENTION: call to function pointer) */
                tmp = server_accept(srv);
                (*srv->accept_handler) (tmp);
        }
        else if (res == EOF) {
                /* Socket error, must restart server */
                return (EOF);
        }

        /*** Process Clients ***/
        /* seek client list */
        for (client = srv->clientlist->first;
             client != NULL; client = client->next) {
                if (client->type == SKT_SENTINEL) continue;
                res = Stest(client->skt);
                if (res > 0) {
                        /* Save next pointer */
                        tmp = client->previous;
                        /* Answer the request */
                        /* (ATTENTION: call to function pointer) */
                        res = (*srv->answer_handler) (client);
                        if (res == 1) client = tmp;
                }
                else if (res == EOF) {
                        /* Socket error, close the client */
                        printf("*** <%s> %s@%s - Connection broken.\n",
                            srv->name, client->name, Speername(client->skt));

                        tmp = client;
                        client = client->previous;
                        server_close_client(tmp);
                }
        }
        return (0);
}
