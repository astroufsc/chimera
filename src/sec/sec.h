/***************************************************************************
                          sec.h  -  secretary control
                             -------------------
    begin                : Mon May 7 2001
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

#ifndef SEC_H
#define SEC_H


#include "sockets.h"
// #include "server.h"
#include "fields.h"
#include "sec_config.h"

#define MAXBUFLEN  (128)

#define SEC_READ_TIMEOUT     (0)  /* seconds */
 #define SEC_READ_BLKTIMEOUT (10)  /* seconds */

#define SEC_CTRLSERVER_STR ("control")    /* String to append InstName
                                             to form control servername */
#define SEC_STATSERVER_STR ("status")     /* String to append InstName
                                             to form status servername */
#define SEC_INSTCLNT_IDENT ("INSTRUMENT") /* Identification String */
#define SEC_CLIENT_CHAR   ('r')
#define SEC_INST_CHAR     ('w')
#define SEC_DEF_FVALUE    ("EMPTY")       /* Default field value */

/* Error codes */
#define SEC_ERROK        (0)
#define SEC_ERRSOCKET  (-10)
#define SEC_ERRMODE    (-11)


/* --Type definitions----------------------------------------------------- */

/* Event handler */
typedef int (*notify_handler)(const int, const char *);

/* Status fields data structure */
typedef struct {
        int nstat;
        char *fields[MAX_STATUS_FIELDS];
        char *contents[MAX_STATUS_FIELDS];
        /* Notification event handlers */
        notify_handler handler[MAX_STATUS_FIELDS];
        int notify[MAX_STATUS_FIELDS]; /* TRUE = notification enabled */
        int notified[MAX_STATUS_FIELDS];
} status_t;

/* Secretary main structure */
typedef struct {
        int enable;
        Socket *skt;
        status_t *status;

//   /* merged from comm.h */
//   char *instname;
//   Server *statsrv;
//   Server *instsrv;

} sec_t;


/* --Function Prototypes-------------------------------------------------- */

/* secconnect() - connect to a secretary.
   With `mode' == "r" (read), secconnect() connects to the Status port -
   i.e "SERVERNAMEstatus" port, where "SERVERNAME" is specified by `sname'.
   In this case, it is also necessary to specify `ident'. With
   `mode' == "w" (write), secconcets() connects to Control port. In this case
   it is possible to use the functions:
        setstatus()
        setnstatus() */
sec_t *secconnect(char *sname, char *mode, char *ident);

/* Closes an open secretary */
void secclose(sec_t *sec);

/* Add a staus field with name `statname' to sec. Returns status index. */
int addstatus(sec_t *sec, const char *statname);

/* Fill status field indexed by stat with contents. */
int setstatus(sec_t *sec, int stat, const char *content);

/* The same as above, but use a numeric content. */
int setnstatus(sec_t *sec, int stat, float content);

/* Gets the value of status field indexed by stat */
char *getstatus(sec_t *sec, int stat);
float getnstatus(sec_t *sec, int stat);
char *status(sec_t *sec, int stat);
float nstatus(sec_t *sec, int stat);

/* Request notification of field stat to secretary, execute
   the handler function hndl() */
int notify(sec_t *sec, int stat, notify_handler hndl);

/* Removes notification request */
int unotify(sec_t *sec, int stat);

/* Wait notification fot `time' seconds */
int wait_notify(int time);

/* Execute pending notifications */
int process_notifies(sec_t *sec);

#endif /* SEC_H */
