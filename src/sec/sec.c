/***************************************************************************
                          sec.c  -  secretary control
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

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "sockets.h"
#include "skterror.h"
#include "fields.h"
#include "messages.h"

#include "sec.h"

#define TRUE  (1)
#define FALSE (0)


/* Read socket `skt' and put data in `buf'; wait for `timeout' seconds.
   Return value: 0 if did not read anything, EOF at error, and some positive
   number if there is data available. */
static int sktread(Socket *skt, char *buf, int timeout);

/* Read Scretary's socket to `buf'; block for SEC_READ_BLKTIMEOUT seconds.
   Return value: If successfull, returns the index of the command sent by
   Secretary. Returns 0 if did not read anything, EOF at error, FNO_MATCH if
   the secretary sent an invalid command, FEMPTY_FIELD if th secretary sent
   an empty field (see fields.h fot more details in these two). */
static int secreadb(Socket *sec, char *buf);

/* The same as above, but don't block. */
static int secread(Socket *sec, char *buf);

/* Write buf to secretary's socket. */
static int secwrite(Socket *sec, const char *buf);

/* Removes all status fields entries */
static void clearstatfields(sec_t *sec);

/* Open connetion to secretary. Mode = "r" opens sec's status port,
   "w" opens control port */
sec_t *secconnect(char *sname, char *mode, char *ident);

/* Synchronous status reading */
char *getstatus(sec_t *sec, int stat);

/* Asynchronous status reading */
int notify(sec_t *sec, int stat, notify_handler hndl);


/* ----------------------------------------------------------------------- */

static int sktread(Socket *skt, char *buf, int timeout)
{
        int res;

        if (skt == NULL || buf == NULL || timeout < 0) return (EOF);

        res = Stimeoutwait(skt, timeout, 0);
        if (res == -2) return (0); /* No data */
        else if (res == -1) return (EOF); /* error */

        /* We have data */
        if (Sgets(buf, MAXBUFLEN, skt) == NULL) return (EOF);

        return (res);
}

/* ----------------------------------------------------------------------- */

static int secreadb(Socket *sec, char *buf)
{
        char tmpbuf[MAXBUFLEN];
        field f;
        int res;

        if (sec == NULL || buf == NULL) return (EOF);

        res = sktread(sec, tmpbuf, SEC_READ_BLKTIMEOUT);
        if (res <= 0) return (res);

        /* Identify the response */
        res = getfield(tmpbuf, &f, fresponses);
        if (res < 0) return (res);
        strncpy(buf, f.contents, MAXBUFLEN);
        return (res);
}

/* ----------------------------------------------------------------------- */

static int secread(Socket *sec, char *buf)
{
        char tmpbuf[MAXBUFLEN];
        field f;
        int res;

        if (sec == NULL || buf == NULL) return (EOF);

        res = sktread(sec, tmpbuf, SEC_READ_TIMEOUT);
        if (res <= 0) return (res);

        /* Identify the response */
        res = getfield(tmpbuf, &f, fresponses);
        if (res < 0) return (res);
        strncpy(buf, f.contents, MAXBUFLEN);
        return (res);
}

/* ----------------------------------------------------------------------- */

static int secwrite(Socket *sec, const char *buf)
{
        if (sec == NULL) return (SEC_ERRSOCKET);
        if (buf == NULL) return (EOF);

        /* write and verify error */
        watch(sec);
        Sputs(buf, sec);
        if (skterror()) { /* pipe error */
                Sclose(sec);
                return (SEC_ERRSOCKET);
        }
        return (SEC_ERROK);
}

/* ----------------------------------------------------------------------- */

static void clearstatfields(sec_t *sec)
{
        int i = 0;

        if (sec == NULL || sec->status == NULL) return;
        for (i = 0; i < sec->status->nstat; i++) {
                unotify(sec, i);
                free(sec->status->fields[i]);
                free(sec->status->contents[i]);
        }
        free(sec->status);
}

/* ----------------------------------------------------------------------- */

sec_t *secconnect(char *sname, char *mode, char *ident)
{
        char buf[MAXBUFLEN];
        sec_t *sec;
        int res;

        if (sname == NULL || mode == NULL) return (NULL);
        if (*mode != SEC_CLIENT_CHAR && *mode != SEC_INST_CHAR)
                return (NULL);

        sec = (sec_t *) calloc(1, sizeof(sec_t));
        if (sec == NULL) return (NULL);
        sec->status = (status_t *) calloc(1, sizeof(status_t));
        if (sec->status == NULL) {
                free(sec);
                return (NULL);
        }


        sec->skt = Sopen(sname, "c");
        if (sec->skt == NULL) {
                secclose(sec);
                return (NULL);
        }

        /* Get initial "HELLO" */
        res = secreadb(sec->skt, buf);
        if (res < 0) {
                fprintf(stderr, "Read timeout or socket error\n\n");
                secclose(sec);
                return (NULL);
        }
        if (res != RES_HELLO) {
                fprintf(stderr, "Expected \"%s\", but got \"%s\"\n",
                        fresponses[RES_HELLO], fresponses[res]);
                secclose(sec);
                return (NULL);
        }

        /* Send identification string */
        if (*mode == SEC_CLIENT_CHAR) { /* client connection */
                snprintf(buf, MAXBUFLEN, "%s %s", fcomm[C_IDENT], ident);
                secwrite(sec->skt, buf);
        }
        else if (*mode == SEC_INST_CHAR) { /* instrument connection */
                snprintf(buf, MAXBUFLEN, "%s %s",
                         fcomm[C_IDENT], SEC_INSTCLNT_IDENT);
                secwrite(sec->skt, buf);
        }

        res = secreadb(sec->skt, buf);
        if (res < 0) {
                fprintf(stderr, "Read timeout or socket error\n\n");
                secclose(sec);
                return (NULL);
        }
        if (res != RES_OK) {
                fprintf(stderr, "Unexpected response on IDENT: \"%s\"\n",
                        fresponses[res]);
                secclose(sec);
                return (NULL);
        }

        sec->enable = TRUE;
        Smaskset(sec->skt);
        return (sec);
}

/* ----------------------------------------------------------------------- */

void secclose(sec_t *sec)
{
        if (sec == NULL) return;

        clearstatfields(sec);
        if (sec->skt != NULL) {
                secwrite(sec->skt, fcomm[C_QUIT]);
                Smaskunset(sec->skt);
                Sclose(sec->skt);
        }

        free(sec);
        return;
}

/* ----------------------------------------------------------------------- */

int addstatus(sec_t *sec, const char *statname)
{
        char *stf, *stc;
        status_t *stp;
        int sz;

        if (sec == NULL || statname == NULL) return (EOF);
        stp = sec->status;
        sz = strlen(statname);
        if (sz > MAX_FIELD_SIZE) sz = MAX_FIELD_SIZE;
        stc = (char *) calloc(MAX_FIELD_CONTENTS + 1, sizeof(char));
        if (stc == NULL) return (EOF);
        stf = (char *) calloc(sz + 1, sizeof(char));
        if (stf == NULL) {
                free(stc);
                return (EOF);
        }
        strncpy(stf, statname, sz);

        stp->fields[stp->nstat] = stf;
        stp->contents[stp->nstat] = stc;
        return (stp->nstat++);
}

/* ----------------------------------------------------------------------- */

int setnstatus(sec_t *sec, int stat, float content)
{
        char buf[MAXBUFLEN];
        int res;

        res = snprintf(buf, MAXBUFLEN, "%-5.3f", content);
        if (res == 0) return (EOF);

        res = setstatus(sec, stat, buf);
        return (res);
}

/* ----------------------------------------------------------------------- */

int setstatus(sec_t *sec, int stat, const char *content)
{
        int res;
        char buf[MAXBUFLEN];

        if (sec == NULL || content == NULL) return (EOF);
        if (stat < 0 || stat > sec->status->nstat) return (EOF);

        sprintf(buf, "%s %s %s",
                      fcomm[C_SETSTATUS], sec->status->fields[stat], content);
	// FIXME
	//                      fcomm[C_SETSTATUS], fsyncstat[stat], content);
        res = secwrite(sec->skt, buf);

	//printf("\n%s\n", buf);
        if (res < 0) return (EOF);

        res = secreadb(sec->skt, buf);
        if (res < 0) {
                fprintf(stderr, "Read timeout or socket error\n\n");
                Sclose(sec);
                return (EOF);
        }
        if (res != RES_OK) {
                fprintf(stderr, "Error setting status %d = %s\n",
                        stat, content);
        }
        return (res);
}

/* ----------------------------------------------------------------------- */

char *getstatus(sec_t *sec, int stat)
{
        int res;
        char buf[MAXBUFLEN];

        if (sec == NULL || sec->status == NULL ||
            stat < 0 || stat > sec->status->nstat)
                return (NULL);

	// FIXME (por que nao usar?)
/*         /\* If notification handling is enabled, use saved value *\/ */
/*         if (sec->status->notify[stat]) */
/*                 return (sec->status->contents[stat]); */

	// ALWAYS ASK
        /* else, ask secretary */

        sprintf(buf, "%s %s", fcomm[C_STATUS], (sec->status->fields[stat]));

        res = secwrite(sec->skt, buf);
        if (res != SEC_ERROK) return (NULL);

        res = secreadb(sec->skt, sec->status->contents[stat]);
        if (res != RES_STATUS) return (NULL);

	printf("%s -> %s\n", buf, sec->status->contents[stat]);

        return (sec->status->contents[stat]);
}

/* ----------------------------------------------------------------------- */

float getnstatus(sec_t *sec, int stat)
{
        char *buf;

        buf = getstatus(sec, stat);
        if (buf == NULL) return (HUGE_VAL);

        return(atof(buf));
}

/* ----------------------------------------------------------------------- */

int notify(sec_t *sec, int stat, notify_handler hndl)
{
        int res;
        char buf[MAXBUFLEN];

        if (sec == NULL || sec->status == NULL ||
            stat < 0 || stat > sec->status->nstat)
                return (EOF);

        /* Exit if notification handling is already enabled */
        if (sec->status->notify[stat]) {
                sec->status->handler[stat] = hndl;
                return (SEC_ERROK);
        }

        /* else, ask secretary */
        sprintf(buf, "%s %s", fcomm[C_NOTIFY], sec->status->fields[stat]);
        res = secwrite(sec->skt, buf);
        if (res != SEC_ERROK) return (EOF);

        res = secreadb(sec->skt, buf);
        if (res == RES_OK) {
                sec->status->notify[stat] = TRUE;
                sec->status->handler[stat] = hndl;
        }

        return (res);
}

/* ----------------------------------------------------------------------- */

int unotify(sec_t *sec, int stat)
{
        int res;
        char buf[MAXBUFLEN];

        if (sec == NULL || sec->status == NULL ||
            stat < 0 || stat > sec->status->nstat)
                return (EOF);

        /* Exit if notification handling is already disabled */
        if (!sec->status->notify[stat])
                return (SEC_ERROK);

        /* else, ask secretary */
        sprintf(buf, "%s %s", fcomm[C_UNOTIFY], sec->status->fields[stat]);
        res = secwrite(sec->skt, buf);
        if (res != SEC_ERROK) return (EOF);

        res = secreadb(sec->skt, buf);
        if (res == RES_OK) sec->status->notify[stat] = FALSE;
        return (res);
}

/* ----------------------------------------------------------------------- */

int wait_notify(int time)
{
        Smasktime(time, 0);
        return Smaskwait();
}

/* ----------------------------------------------------------------------- */

int process_notifies(sec_t *sec)
{
        int res;
        field f;
        status_t *st;
        char buf[MAXBUFLEN];

        if (sec == NULL || sec->status == NULL) return(EOF);
        st = sec->status;
        res = Stest(sec->skt);

        if (res <= 0) return (res);

        /* Data received */
        res = secread(sec->skt, buf);
        if (res < 0) return (EOF);
        switch (res) {
        case RES_STATUS:
        case RES_NOTIFY:
                res = getfield(buf, &f, (const char **)st->fields);
                if (res < 0) return (EOF);
                strncpy(st->contents[res], f.contents, MAX_FIELD_CONTENTS);
                if (!st->notify[res]) return (SEC_ERROK);
                /* Call status notification handler */
                (*st->handler[res])(res, st->contents[res]);
                break;

        case RES_ERROR:
        case RES_OK:
                return (res);
                break;

        case RES_ABORT:
                secclose(sec);
                return (res);
                break;

        default:
                break;
        }

        return (SEC_ERROK);
}

/* ----------------------------------------------------------------------- */
