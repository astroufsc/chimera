/***************************************************************************
                          tel.c  -  description
                             -------------------
    begin                : Wed Aug 1 2001
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
#include <unistd.h>
#include <fcntl.h>
#include <signal.h>
#include <math.h>
#include "fields.h"
#include "errors.h"
#include "ser.h"

/* enum { FALSE, TRUE };*/
typedef enum { BUSY, WAIT } stat_t;

/* mount types */
enum { LAND, POLAR, ALTAZ };

struct ras {
        int hh;
        int mm;
        int ss;
};

struct decs {
        int dd;
        int mm;
        int ss;
};

typedef struct {
        struct ras ra;
        float ra_range;
        struct decs dec;
        float dec_range;
        float lat;
        float lon;
        stat_t status;
        int moving;
        int mnt_type;
        ser_info *serial;
        char *outbuf;
} tel_info;


void wait_tel(tel_info *tel);
void usage(char *command);
void setup(void);
void status(tel_info *tel, stat_t stat);
void controlc(int signumber);


field f;
tel_info tel;
char *porta;
char linebuf[128];
char outbuf[128];
char fmask[20];
char imgfname[50];
int ram, rah, decm, decd;
float ras, decs;

enum {  QUIT, RA, DEC, ACTION };
char *fieldnames[] = { "QUIT", "RA", "DEC", "ACTION" };

int main(int argc, char ** argv)
{

        signal(SIGINT, controlc);
        signal(SIGABRT, controlc);

	fprintf(stderr, "LX-200 Fake Telescope controller ver. 0.01f.\n\n");
	if (argc < 4) {
		usage(argv[0]);
		exit(1);
	}

	porta = argv[1];

	sscanf(argv[2], "%d:%d:%d", &tel.ra.hh, &tel.ra.mm, &tel.ra.ss);
	sscanf(argv[3], "%d:%d:%d", &tel.dec.dd, &tel.dec.mm, &tel.dec.ss);

	printf("Moving to ra=%s dec=%s\n", argv[2], argv[3]);	
	//setup();

        /*** Write Coords. ***/

        tel.moving = TRUE;
        /*set RA */
/*        sprintf(tel.outbuf, ":Sr%02d:%4.1f#",
                tel.ra.hh, (double)tel.ra.mm + (double)tel.ra.ss / 60);
        //printf(tel.outbuf);
        //fflush(stdout);
        write_serial(tel.serial, tel.outbuf, strlen(outbuf));
        read_serial(tel.serial, tel.outbuf, 128);
        if (*(tel.outbuf) == '0') {
                sprintf(tel.outbuf, ":Sr%02d:%4.1f#",
                        tel.ra.hh, (double)(tel.ra.mm + (tel.ra.ss / 60)));
                write_serial(tel.serial, tel.outbuf, strlen(outbuf));
                read_serial(tel.serial, tel.outbuf, 128);
        } */
//        fprintf(stderr, "%c", *(tel.outbuf));

        /* set DEC */
/*        sprintf(tel.outbuf, ":Sd%02d*%02d#",
                tel.dec.dd, tel.dec.mm);
        write_serial(tel.serial, tel.outbuf, strlen(outbuf));
        read_serial(tel.serial, tel.outbuf, 128);
        if (*(tel.outbuf) == '0') {
                sprintf(tel.outbuf, ":Sd%02d*%02d#",
                        tel.dec.dd, tel.dec.mm);
                write_serial(tel.serial, tel.outbuf, strlen(outbuf));
                read_serial(tel.serial, tel.outbuf, 128);
        } */
//        fprintf(stderr, "%c", *(tel.outbuf));

        /* move telescope */
/*        sprintf(tel.outbuf, ":MS#");
        write_serial(tel.serial, tel.outbuf, strlen(outbuf));
        read_serial(tel.serial, tel.outbuf, 128);
//        fprintf(stderr, "%c", *(tel.outbuf));
//        fprintf(stderr, "\n%s\n", tel.outbuf);

        if (*(tel.outbuf) == '0') { 
        	wait_tel(&tel); */
		sleep(5);
        	fprintf(stderr, "\nDone\n");
/*        } */
        //else fprintf(stderr, "\nCould not move\n");
	
	
	exit(0);
}


void wait_tel(tel_info *tel)
{
        int rah;
        float ram;
        int decd, decm;
        float delta_dec;
        float delta_ra;
        char buf[64];

        while (tel->moving) {
                /* get current RA */
                strcpy(buf, ":GR#");
                write_serial(tel->serial, buf, strlen(buf));
                read_serial(tel->serial, buf, 64);
                sscanf(buf, "%d:%f#", &rah, &ram);


                /* get current DEC */
                strcpy(buf, ":GD#");
                write_serial(tel->serial, buf, strlen(buf));
                read_serial(tel->serial, buf, 64);
                sscanf(buf, "%d%*c%d#", &decd, &decm);


                /* are DEC and RA in range? */
                decd -= tel->dec.dd;
                decm -= tel->dec.mm;
                delta_dec = fabs(decd + (decm / 60));

                rah  -= tel->ra.hh;
                ram  -= tel->ra.mm;
                ram  -= ((double)tel->ra.ss / 60);
                delta_ra = fabs(rah + (ram / 60));
                /* limpa a linha e escreve os deltas */
                fprintf(stderr, "\r                                                       ");
                fprintf(stderr, "\rdelta-dec = %f; delta-ra = %f", delta_dec, delta_ra);
                fflush(stderr);
                if ((delta_dec < tel->dec_range) && (delta_ra < tel->ra_range))
                        tel->moving = FALSE;
                sleep(1);
        }
        sleep(1);
}


void usage(char *command)
{
	fprintf(stderr, "SYNTAX: %s terminal_device RA DEC\n\n", command);
	fprintf(stderr, "E.g.: %s /dev/ttyS1 12:12:12 13:12:14\n\n", command);
}


/* sets up telescope structs and initializes its parameters */
void setup(void)
{
        tel.serial = (ser_info*) calloc(sizeof(ser_info), 1);
        open_serial(tel.serial, porta);
        if (tel.serial->err_code != ERR_OK) {
                free(tel.serial);
                abort();
        }

        /* 9600,8n1 */
        tel.serial->baudrate = B9600;
        tel.serial->parity = PAR_NONE;
        tel.serial->stopbits = 1;
        tel.serial->timeout = 5;
        tel.serial->minchars = 20;
        tel.serial->waitread = TRUE;
        set_serial(tel.serial);

        tel.ra_range  = 0.007; /* 1min */
        tel.dec_range = 0.007; /* 1min */
        tel.moving = FALSE;
        tel.status = BUSY;
        tel.outbuf = outbuf;

}


void controlc(int signumber)
{
        if (signumber == SIGINT)
                fprintf(stderr, "\nControl-C signal caught, exiting.\n");
	else
                fprintf(stderr, "\nAborting...\n");
	exit(2);
}
