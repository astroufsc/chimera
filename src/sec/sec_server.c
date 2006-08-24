/***************************************************************************
                          comm.c  -  description
                             -------------------
    begin                : Thu Sep 28 2000
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
#include <signal.h>
#include <string.h>
#include <assert.h>

#include "sockets.h"

#include "skterror.h"
#include "sktlist.h"
#include "server.h"
#include "fields.h"
#include "messages.h"

#include "sec_config.h"
#include "sec_server.h"

#define FALSE (0)
#define TRUE  (1)

#define CONTROL_STR "control"
#define STATUS_STR "status"

#define INST_CLIENT_NAME "INSTRUMENT"

#define DEF_STATUS_CONTENT "EMPTY"
#define DEF_INSTSTATUS_CONTENT "OFFLINE"

#define SKT_CTRLSERVER (SKT_SERVER +1)
#define SKT_STATSERVER (SKT_SERVER +2)

typedef struct {
        char contents[MAX_STATUS_CONTENTS];
        SktList *notify_table;
}statcontents_t;

static char *fstatus[MAX_STATUS_FIELDS];
static statcontents_t *status_contents[MAX_STATUS_FIELDS];

static int statcounter = 0;


static void notify_internal(int i);
static void free_notify_table(SktList *list);


static void 	controlc(int sig);
void		ping_sockets(SecServer *sec);

static Server	*run_status_server(SecServer* );
static Server	*run_control_server(SecServer* );

/* Servers, for emergency use (aborting) */
static SecServer *sec_ptr;

/* status server connection handlers */
static int accept_client(SktListItem *client);
static int statsrv_answer(SktListItem *client);
static int close_client_handler(SktListItem *client);

/* control server connection handlers */
static int instsrv_answer(SktListItem *client);
static int close_instclient_handler(SktListItem *client);

/* protocol handler */
static int request_status(SktListItem *client, char *name);
static int change_status(SktListItem *client, char *statstr);
static int client_notify(SktListItem *client, char *statname);
static int client_unotify(SktListItem *client, char *statname);
static int client_ident(SktListItem *client, char *name);
static int check_ident(SktListItem *client);


SecServer *sec_server_new(void) {

  SecServer* sec = (SecServer *)calloc(1, sizeof(SecServer));
  assert(sec != NULL);

/*   sec->status = s_dict_new(); */
/*   sec->notify = s_dict_new(); */

  return sec;

}

void sec_server_free(SecServer* sec) {

  if(sec->config != NULL)
    sec_config_free(sec->config);

  if(sec->instname != NULL)
    free(sec->instname);

/*   if(sec->status != NULL) */
/*     s_dict_free(sec->status) */

/*   if(sec->notify != NULL) */
/*     s_dict_free(sec->notify) */

  free(sec);

}

int sec_server_configure(SecServer* sec, const char *cfile)
{

        /* signal handlers */
        signal(SIGINT, controlc);
        signal(SIGTERM, controlc);
        signal(SIGABRT, controlc);
        signal(SIGPIPE, pipe_error);

        /* ignored signals */
        signal(SIGHUP, SIG_IGN);
        signal(SIGQUIT, SIG_IGN);
        signal(SIGUSR1, SIG_IGN);
        signal(SIGUSR2, SIG_IGN);

        /*** Get custom configuration (server names and status fields) ***/

	sec->config = sec_config_new_from_file(cfile);

        if (sec->config == NULL) {
                /* Use default values */
                printf("*** Config file does not exist, using defaults.\n");
                sec->config = sec_config_new();
                strcpy(sec->config->instname, DEF_INSTNAME);
                sec->config->maxclnt = DEF_MAXCLNT;
        }

	return TRUE;
}

int sec_server_run(SecServer* sec)
{

        if(sec->config == NULL) return FALSE;
        
        /*  Save instname */
        sec->instname = (char *) calloc(strlen(sec->config->instname) + 1,
                                    sizeof(char));
        strcpy(sec->instname, sec->config->instname);

        /*** Status server ***/
        sec->statsrv = run_status_server(sec);
        if (sec->statsrv == NULL) abort();

        /* Configure Status Fields */
        fill_statlist(sec->config->instname, sec->config->fstatus,
                      sec->config->nstatus);

        /*** Instrument control server ***/
        sec->instsrv = run_control_server(sec);
        if (sec->instsrv == NULL) abort();

        /* save ``sec'' for signal handling */
        sec_ptr = sec;

        return TRUE;
}

int sec_server_wait(SecServer *sec)
{
        int i;

        /* _MUST_ set Smasktime before Smaskwaiting */
        Smasktime(WAIT_TIME, 0);
        i = Smaskwait();
        if (i > 0) {
                /* Someone has new data, check it */
                server_verify(sec->statsrv);
                server_verify(sec->instsrv);
        }
        else if (i < 0) {
                /* Smaskwait crashed... fix it in the future; */
                /* by now, abort the program. */
                printf("*** Critical error: Smaskwait() failed!\n\n");
                abort();
        }
        return (i);
}


int sec_server_check(SecServer *sec)
{
        ping_sockets(sec);
        return(0);
}

static void controlc(int sig)
{
        if (sig == SIGINT) printf("\n*** Control-C caught.\n");

        /* Close all connections and exit. */
        printf("*** Closing servers...\n");
        if (sec_ptr != NULL) {
                server_close(sec_ptr->statsrv);
                server_close(sec_ptr->instsrv);
        }

	sec_server_free(sec_ptr);

        exit(1);
}



/* Open status server */
Server* run_status_server(SecServer* sec)
{
        char sname[MAX_SERVER_NAME];
        Server *stsrv;

        /* build status server name based on instname */
        strcpy(sname, sec->instname);
        strcat(sname, STATUS_STR);
                /* e.g: instname == INST  =>  buf == INSTstatus */

        stsrv = server_init(sname, SKT_STATSERVER);
        if (stsrv == NULL) return (NULL);

        stsrv->accept_handler = accept_client;
        stsrv->answer_handler = statsrv_answer;
        stsrv->close_handler = close_client_handler;
        stsrv->maxclients = sec->config->maxclnt;
        return (stsrv);
}


/* Open instrument control server */
Server *run_control_server(SecServer* sec)
{
        char sname[MAX_SERVER_NAME];
        Server *isrv;

        /* build server name based on instname */
        strcpy(sname, sec->instname);
        strcat(sname, CONTROL_STR);
                /* e.g: instname == INST  =>  buf == INSTcontrol */

        isrv = server_init(sname, SKT_CTRLSERVER);
        if (isrv == NULL) return (NULL);

        isrv->accept_handler = accept_client;
        isrv->answer_handler = instsrv_answer;
        isrv->close_handler = close_instclient_handler;
        isrv->maxclients = 1;
        return (isrv);
}



/* Client will be able to ask server after identifying itself */
static int client_ident(SktListItem *client, char *name)
{
        int i;
        Server *server;

        if (client == NULL) return (EOF);
        server = client->server;
        if (!server_is_valid(server)) return(EOF);

        i = server_set_client_name(client, name);
        if (i == EOF) {
                server_write_client(fresponses[RES_ERROR], client);
                server_close_client(client);
                return (EOF);
        }
        i = server_write_client(fresponses[RES_OK], client);
        if (i == EOF) return (EOF);
        printf(" -> <%s> Identification: %s@%s\n",
                server->name, client->name, Speername(client->skt));
        client->state = CST_IDLE;

        return (0);
}


static int instrument_ident(SktListItem *client, char *name)
{
        int i;
        Server *server;

        if (client == NULL || name == NULL) return (EOF);
        server = client->server;
        if (!server_is_valid(server)) return(EOF);

        /* Verify instrument identification */
        i = strncmp(name, INST_CLIENT_NAME, MAX_CLIENT_NAME);
        if (i != 0) {
                /* bad identification string. */
        printf("*** <%s> Bad identification from %s, client closed\n",
                server->name, Speername(client->skt));
                server_write_client(fresponses[RES_ERROR], client);
                server_close_client(client);
                return (EOF);
        }

        /* Proceed as in client_ident() */

        i = server_set_client_name(client, name);
        if (i == EOF) {
                server_write_client(fresponses[RES_ERROR], client);
                server_close_client(client);
                return (EOF);
        }
        i = server_write_client(fresponses[RES_OK], client);
        if (i == EOF) return (EOF);
        printf(" -> <%s> Identification: %s@%s\n",
                server->name, client->name, Speername(client->skt));
        client->state = CST_IDLE;

        return (0);
}


static int check_ident(SktListItem *client)
{
        Server *server;

        if (client == NULL) return (EOF);
        server = client->server;
        if (!server_is_valid(server)) return (EOF);

        /* Only answer clients who have already identified */
        if (client->state == CST_IDENT_PENDING) {
                if (server_write_client(fresponses[RES_ERROR], client) == EOF)
                        return (EOF);
                printf("*** <%s> %s: Unidentified client, "
                        "access denied.\n",
                        server->name, Speername(client->skt));
                return (EOF);
        }
        return (0);
}


static int request_status(SktListItem *client, char *name)
{
        char buf[MAXBUFLEN];
        char *ptr;
        int i;

        if (check_ident(client) == EOF) return (EOF);
        ptr = get_status(name);
        if (ptr == NULL) {
                i = server_write_client(fresponses[RES_ERROR], client);
                return (i);
        }
        snprintf(buf, MAXBUFLEN, "%s %s", fresponses[RES_STATUS], ptr);
        i = server_write_client(buf, client);
        return (i);
}


static int change_status(SktListItem *client, char *statstr)
{
        int i;

        i = set_status_str(statstr);
        if (i == EOF) {
                i = server_write_client(fresponses[RES_ERROR], client);
                return (i);
        }
        i = server_write_client(fresponses[RES_OK], client);
        return (i);
}


/* add client to "status"'s notification list */
static int client_notify(SktListItem *client, char *statname)
{
        int i;

        if (check_ident(client) == EOF) return (EOF);
        i = set_notify(client, statname);
        if (i == EOF) {
                i = server_write_client(fresponses[RES_ERROR], client);
                return (i);
        }
        i = server_write_client(fresponses[RES_OK], client);
        return (i);
}


/* remove client from "status"'s notification list */
static int client_unotify(SktListItem *client, char *statname)
{
        int i;

        if (check_ident(client) == EOF) return (EOF);
        i = rmv_notify(client, statname);
        if (i == EOF) {
                i = server_write_client(fresponses[RES_ERROR], client);
                return (i);
        }
        i = server_write_client(fresponses[RES_OK], client);
        return (i);
}


void ping_sockets(SecServer *sec)
{
        static int tc;

        /* Notify the special field PING every WAIT_TIME * 3 */
        if (tc % 3) return;

        /* SETSTATUS PING INSTNAME */
        set_status(STPING, sec->instname);
}


/* Additional proceedings after client connection */
static int accept_client(SktListItem *client)
{
        int i;

        if (client == NULL) return (EOF);
        if (!server_is_valid(client->server)) return(EOF);

        /* Tell client we accepted */
        i = server_write_client(fresponses[RES_HELLO], client);
        if (i == EOF) return (EOF);

        client->state = CST_IDENT_PENDING;
        return (0);
}


static int statsrv_answer(SktListItem *client)
{
        char buf[MAXBUFLEN];
        int fi;
        field f;
        Server *server;

        if (client == NULL) return (EOF);
        server = client->server;
        if (!server_is_valid(server)) return(EOF);

        /* Determine which command we received */
        Sgets(buf, MAXBUFLEN, client->skt);
        fi = getfield(buf, &f, fcomm);
        switch (fi) {

        case C_QUIT:
                server_close_client(client);
                return(1);
                break;

        case C_IDENT:
                client_ident(client, f.contents);
                break;

        case C_STATUS:
                if (check_ident(client) != EOF)
                        request_status(client, f.contents);
                break;


        case C_NOTIFY:
                if (check_ident(client) != EOF)
                        client_notify(client, f.contents);
                break;

        case C_UNOTIFY:
                if (check_ident(client) != EOF)
                        client_unotify(client, f.contents);
                break;

        case C_CONTROL:
        case C_SETSTATUS:
        case EOF:
        default:
                /* Invalid command or command unavailable */
                if (server_write_client(fresponses[RES_ERROR], client) == EOF)
                        return (EOF);
                printf(" -> <%s> %s@%s: Invalid command - %s\n",
                        server->name, client->name,
                        Speername(client->skt), buf);
                break;
        }
        return (0);
}



static int instsrv_answer(SktListItem *client)
{
        char buf[MAXBUFLEN];
        int fi;
        field f;
        Server *server;

        if (client == NULL) return (EOF);
        server = client->server;
        if (!server_is_valid(server)) return(EOF);

        /* Determine which command we received */
        Sgets(buf, MAXBUFLEN, client->skt);
        fi = getfield(buf, &f, fcomm);
        switch (fi) {

        case C_QUIT:
                server_close_client(client);
                return(1);
                break;

        case C_IDENT:
                if (instrument_ident(client, f.contents) != 0)
                        return (1);

                break;

        case C_STATUS:
                if (check_ident(client) != EOF)
                        request_status(client, f.contents);
                break;

        case C_SETSTATUS:
                change_status(client, f.contents);
                break;

        case C_NOTIFY:
        case C_UNOTIFY:
        case EOF:
        default:
                /* Invalid command or command unavailable */
                if (server_write_client(fresponses[RES_ERROR], client) == EOF)
                        return (EOF);
                printf(" -> <%s> %s@%s: Invalid command - %s\n",
                        server->name, client->name,
                        Speername(client->skt), buf);
                break;
        }
        return (0);
}



/* Things to do before closing the client */
static int close_client_handler(SktListItem *client)
{
        clear_client_notifies(client);
        return (0);
}


static int close_instclient_handler(SktListItem *client)
{
        clear_client_notifies(client);

        /* SETSTATUS INSTNAME OFFLINE */
        set_istatus(STATUS_INSTNAME, DEF_INSTSTATUS_CONTENT);
        return (0);
}

/* int	 sec_server_add_status(SecServer* sec, const char* status) { */

/*   assert(sec != NULL); */
/*   assert(status != NULL); */

/*   return (s_dict_add(sec->status, status, DEF_STATUS_CONTENS) && */
/* 	  s_dict_add(sec->notify, status, skt_list_new())); */

/* } */

/* int	 sec_server_free_status(SecServer* sec, const char* status) { */

/*   assert(sec != NULL); */
/*   assert(status != NULL); */

/*   return (s_dict_remove(sec->status, status) && */
/* 	  s_dict_remove(sec->notify, status)); */

/* } */

/* int	 sec_server_set_status(SecServer* sec, const char* status, const char* contents) { */

/*   assert(sec != NULL); */
/*   assert(status != NULL); */
/*   assert(contents != NULL); */

/*   return (s_dict_set(sec->status, status, contents)); */

/* } */

/* const char* sec_server_get_status(SecServer* sec, const char* status) { */

/*   assert(sec != NULL); */
/*   assert(status != NULL); */

/*   return (s_dict_get(sec->status, status); */


/* } */

/* int	 sec_server_set_notify(SecServer* sec, SktListItem* client, const char* status) { */

/*   assert(sec != NULL); */
/*   assert(client != NULL); */
/*   assert(status != NULL); */

/*   SktList* list = s_dict_get(sec->notify, status); */

/*   sktlist_add(list, client->skt); */

/*   return RUE; */

/* } */

/* int	 sec_server_remove_notify(SecServer* sec, SktListItem* client, const char* status) { */

/*   assert(sec != NULL); */
/*   assert(client != NULL); */
/*   assert(status != NULL); */

/*   SktList* list = s_dict_get(sec->notify, status); */

/*   sktlist_remove(list, client); */

/*   return RUE; */

/* } */

/* Status field table */

/* This creates the status fields; should be avoided while runing */
int fill_statlist(char *instname,
                  char fstatus[][MAX_FIELD_SIZE], int nst)
{
        int i;

	if ( instname == NULL || fstatus == NULL || nst <= 0 ||
	     nst > MAX_STATUS_FIELDS )
	return (EOF);
	
	/* add a status field for instrument state */
        if (add_status(instname) < 0) return (EOF);

        /* add a status field for connection monitoring */
        if (add_status(STPING) < 0) return (EOF);


        for (i = 0; i < nst; i++)
                if (add_status((char *) fstatus[i]) < 0) return (EOF);

        return (0);
}


int add_status(char *name)
{
        char *status_ptr;
        statcontents_t *contents_ptr;

        /* Do not allocate more than MAX_STATUS_FIELDS fields */
        if (statcounter >= MAX_STATUS_FIELDS) return (EOF);
        if (name == NULL) return(EOF);
        if (strlen(name) > MAX_FIELD_SIZE) return (EOF);

        /* Get memory for field stuff & notify list */
        status_ptr = (char *) calloc(strlen(name) + 1, sizeof(char));
        if (status_ptr == NULL) return(EOF);
        contents_ptr = (statcontents_t *) calloc(1, sizeof(statcontents_t));
        if (contents_ptr == NULL) {
                free(status_ptr);
                return(EOF);
        }
        /* Fill the structures */
        strcpy(status_ptr, name);
        if (statcounter == 0) /* INSTNAME Status field */
                strcpy(contents_ptr->contents, DEF_INSTSTATUS_CONTENT);
        else
                strcpy(contents_ptr->contents, DEF_STATUS_CONTENT);

        /* Create notification list */
        contents_ptr->notify_table = sktlist_new();
        if (contents_ptr->notify_table == NULL) {
                free(status_ptr);
                free(contents_ptr);
                return (EOF);
        }

        fstatus[statcounter] = status_ptr;
        status_contents[statcounter] = contents_ptr;

        return(statcounter++);
}


/* Free _ALL_ status fields */
void free_status(void)
{
        char **ptr1;
        statcontents_t *ptr2;

        ptr1 = fstatus;
        ptr2 = *status_contents;
        while (statcounter > 0) {
                if (ptr1 != NULL) free(ptr1++);
                if (ptr2 != NULL) {
                        free_notify_table(ptr2->notify_table);
                        free(ptr2++);
                }
                statcounter--;
        }

}


/* Set status by index */
int set_istatus(int i, char *contents)
{
        if (contents == NULL) return (EOF);
        if (i < 0 || i > statcounter) return (EOF);
        if (strlen(contents) > MAX_STATUS_CONTENTS) return (EOF);


#ifdef NOTIFY_ON_CHANGE
        /* Notify clients only if status changed */
        if (strncmp(status_contents[i]->contents,
                   contents, MAX_STATUS_CONTENTS) != 0) {
                strcpy(status_contents[i]->contents, contents);
                notify_internal(i); /* FIXME */
        }
#else
        /* Notify always */
        strcpy(status_contents[i]->contents, contents);
        notify_internal(i); /* FIXME */
#endif

        return (0);
}


/* Set status by name */
int set_status(char *name, char *contents)
{
        int i, res;

        if (name == NULL) return (EOF);
        if (contents == NULL) return (EOF);
        if (strlen(contents) > MAX_STATUS_CONTENTS) return (EOF);

        i = getfield(name, NULL, (const char **) fstatus);
        res = set_istatus(i, contents);

        return(res);
}


/* set status by string: "STATUS VALUE" */
int set_status_str(char *statstr)
{
        int i, res;
        field f;

        if (statstr == NULL) return (EOF);

        i = getfield(statstr, &f, (const char **) fstatus);
        res = set_istatus(i, f.contents);

        return (res);

}


/* Get status by index */
char *get_istatus(int i)
{
        if (i < 0 || i > statcounter) return (NULL);

        return (status_contents[i]->contents);
}


/* Get status by name */
char *get_status(char *name)
{
        int i;

        if (name == NULL) return (NULL);

        i = getfield(name, NULL, (const char **) fstatus);
        if (i < 0 || i > statcounter) return (NULL);

        return (status_contents[i]->contents);
}


int set_notify(SktListItem *client, char *statfield)
{
        int i, res;

        if (client == NULL) return (EOF);
        i = getfield(statfield, NULL, (const char **) fstatus);
        res = set_inotify(client, i);
        return (res);
}


int set_inotify(SktListItem *client, int i)
{
        SktListItem *item;

        if (client == NULL) return (EOF);
        if (i < 0 || i > statcounter) return (EOF);

        /* Check if this client already requested notification */
        for (item = status_contents[i]->notify_table->first;
             item != NULL; item = item->next) {
                if (item->type == SKT_SENTINEL) continue;
                if (item->id == client->id)
                        /* This client is already registered */
                        return (0);
        }

        /* Else, add client to list */
        item = sktlist_add(status_contents[i]->notify_table,
                           client->skt, client->type);
        if (item == NULL) return (EOF);
        /* Save id for future removal */
        item->id = client->id;
        /* Save server for future writing */
        item->server = client->server;
        return (0);

}


int rmv_notify(SktListItem *client, char *statfield)
{
        int i, res;

        if (client == NULL) return (EOF);
        i = getfield(statfield, NULL, (const char **) fstatus);
        res = rmv_inotify(client, i);
        return (res);
}


int rmv_inotify(SktListItem *client, int i)
{
        SktListItem *item, *tmp;

        if (client == NULL) return (EOF);
        if (i < 0 || i > statcounter) return (EOF);

        /* Find who has this id */
        for (item = status_contents[i]->notify_table->first;
             item != NULL; item = item->next) {
                if (item->type == SKT_SENTINEL) continue;
                if (item->id == client->id) {
                        /* id found, remove it */
                        tmp = item;
                        item = item->previous;
                        sktlist_remove(status_contents[i]->notify_table, tmp);
                        return (0);
                }
        }
        /* id not found */
        return (EOF);
}

void clear_client_notifies(SktListItem *client)
{
        int i;

        /* Clear notifies for each Status entry */
        for (i = 0; i < statcounter; i++)
                rmv_inotify(client, i);
}


static void notify_internal(int i)
{
        char buf[MAXBUFLEN];
        SktListItem *client;

        /* Notify everyone in list */
        for (client = status_contents[i]->notify_table->first;
             client != NULL; client = client->next) {
                if (client->type == SKT_SENTINEL) continue;
                snprintf(buf, MAXBUFLEN, "NOTIFY %s %s",
                         fstatus[i], status_contents[i]->contents);
                server_write_client(buf, client);
        }
}


static void free_notify_table(SktList *list)
{
        if (list == NULL) return;

        while (list->first->type == SKT_CLIENT) sktlist_remove(list, list->first);
        sktlist_free(list);
}


