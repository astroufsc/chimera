#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <fcntl.h>
#include <signal.h>
#include "errors.h"
#include "ser.h"

#include "lx200.h"


static void controlc(int signumber);


/*-------------------------------------------------------------------------*/


int lx200_point(tel_info *tel, struct ras ra, struct decs dec)
{
        lx200_set_coords(tel, ra, dec);
	lx200_slew(tel);
	lx200_wait_slew(tel);

	return (0);
}


/*-------------------------------------------------------------------------*/


int lx200_wait_slew(tel_info *tel)
{
        struct ras Dra;   //delta RA
	struct decs Ddec; //delta DEC
	int i = LX_SLEW_TIMEOUT;



	while (i--) {
	        lx200_update_coords(tel);

	        // evaluate displacement.
	        Ddec.dd = tel->pdec.dd - tel->cdec.dd;
		Ddec.mm = tel->pdec.mm - tel->cdec.mm;
		Ddec.ss = tel->pdec.ss - tel->cdec.ss;
		
		Dra.hh = tel->pra.hh - tel->cra.hh;
		Dra.mm = tel->pra.mm - tel->cra.mm;
		Dra.ss = tel->pra.ss - tel->cra.ss;
		
		if (abs(Dra.hh) <= tel->ra_range.hh &&
		    abs(Dra.mm) <= tel->ra_range.mm &&
		    abs(Dra.ss) <= tel->ra_range.ss &&

		    abs(Ddec.dd) <= tel->dec_range.dd &&
		    abs(Ddec.mm) <= tel->dec_range.mm &&
		    abs(Ddec.ss) <= tel->dec_range.ss) {
		        //Close enough
		        sleep(10);
		        return (0);
		}
		sleep(1);
	}
	// bad, timeout :(
	return (-1);
}


/*-------------------------------------------------------------------------*/


int lx200_update_coords(tel_info *tel)
{
        char cmd1[] = ":GR#";
        char cmd2[] = ":GD#";

        /* get current RA */
	write_serial(tel->serial, cmd1, strlen(cmd1));
	read_serial(tel->serial, tel->outbuf, LX_BUFSIZE);

	sscanf(tel->outbuf, "%d:%d:%d#",
	       &(tel->cra.hh),
	       &(tel->cra.mm),
	       &(tel->cra.ss));
	
	
	/* get current DEC */
	write_serial(tel->serial, cmd2, strlen(cmd2));
	read_serial(tel->serial, tel->outbuf, LX_BUFSIZE);

	sscanf(tel->outbuf, "%d%*c%d:%d#",
	       &(tel->cdec.dd),
	       &(tel->cdec.mm),
	       &(tel->cdec.ss));
	return(0);
}


/*-------------------------------------------------------------------------*/


int lx200_slew(tel_info *tel)
{
        char cmd[] = ":MS#";

	// make sure tracking is ON
	lx200_ra_drive_on(tel);

        write_serial(tel->serial, cmd, strlen(cmd));
        read_serial(tel->serial, tel->outbuf, LX_BUFSIZE);

        if (*(tel->outbuf) != '0') // can not slew
                return (-1);

	return (0);
}


/*-------------------------------------------------------------------------*/


int lx200_match_coords(tel_info *tel)
{
        char cmd[] = ":CM#";

        write_serial(tel->serial, cmd, strlen(cmd));
        read_serial(tel->serial, tel->outbuf, LX_BUFSIZE);

	// Finda way to check the success of this operation

	return (0);
}


/*-------------------------------------------------------------------------*/


int lx200_set_coords(tel_info *tel, struct ras ra, struct decs dec)
{
        /*set RA */
        sprintf(tel->outbuf, ":Sr %02d:%02d:%02d#",
                ra.hh, ra.mm, ra.ss);

        write_serial(tel->serial, tel->outbuf, strlen(tel->outbuf));
        read_serial(tel->serial, tel->outbuf, LX_BUFSIZE);

        /* set DEC */
        sprintf(tel->outbuf, ":Sd %02d*%02d:%02d#",
                dec.dd, dec.mm, dec.ss);

        write_serial(tel->serial, tel->outbuf, strlen(tel->outbuf));
        read_serial(tel->serial, tel->outbuf, LX_BUFSIZE);

	tel->pra = ra;
	tel->pdec = dec;
	return (0);
}


/*-------------------------------------------------------------------------*/


int lx200_set_precision(tel_info *tel, int precision)
{
        char cmd1[] = ":GR#";
        char cmd2[] = ":U#";
	int nb;
	int rdprec;

        write_serial(tel->serial, cmd1, strlen(cmd1));
        nb = read_serial(tel->serial, tel->outbuf, LX_BUFSIZE);

	//depending on precision, "get RA returns:
	// :NN:NN:NN#  == 10 char, or
	// :NN:NN.N#   ==  9 char.

        rdprec = (nb==LX_HIPRECISION_RESP)?LX_PRECISION_HIGH:LX_PRECISION_LOW;
        if (rdprec != precision) write_serial(tel->serial, cmd2, strlen(cmd2));

	return (0);
 }


/*-------------------------------------------------------------------------*/


/* sets up telescope structs and initializes its parameters */
tel_info *lx200_open(char *device)
{
        tel_info *tel;
	ser_info *ser;

	tel = calloc(sizeof(tel_info), 1);
	tel->outbuf = calloc(sizeof(char), LX_BUFSIZE);
	if(device == NULL) device = LX_DEFAULT_DEVICE;
        ser = open_serial(device);
        if (ser == NULL) {
	        free(tel->outbuf);
                free(tel);
		return (NULL);
        }
        /* 9600,8n1 */
        ser->baudrate = B9600;
        ser->parity = PAR_NONE;
        ser->stopbits = 1;
        ser->timeout = 5;
        ser->minchars = 20;
        ser->waitread = TRUE;
        set_serial(ser);

        tel->ra_range.hh = 0;
        tel->ra_range.mm = 0;
        tel->ra_range.ss =  1;

        tel->dec_range.dd = 0;
        tel->dec_range.mm = 0;
        tel->dec_range.ss = 3;

        tel->moving = FALSE;
	tel->serial = ser;

        signal(SIGINT, controlc);
        signal(SIGABRT, controlc);

	lx200_set_precision(tel, LX_PRECISION_HIGH);
	lx200_update_coords(tel);
	return (tel);
}


/*-------------------------------------------------------------------------*/


void lx200_close(tel_info *tel)
{
  // stop/wait slewing and focus?
  
  close_serial(tel->serial);
  free(tel);
}


/*-------------------------------------------------------------------------*/


static void controlc(int signumber)
{
        if (signumber == SIGINT)
                fprintf(stderr, "\nInterrupt signal caught, exiting.\n");
	else
                fprintf(stderr, "\nAborting...\n");

	/*	if (tel.focus)
        	write_serial(tel.serial, ":FQ#", 4);*/
	exit(2);
}


/*-------------------------------------------------------------------------*/


int lx200_change_focus(tel_info *tel, int steps, int speed)
{
        if (steps == 0) {
                lx200_focus_control(tel, LX_FOCUS_STOP, speed);
		return (0);
	}

	// start motor in which direction?
        if (steps < 0)
	        lx200_focus_control(tel, LX_FOCUS_MINUS, speed);

	else
	        lx200_focus_control(tel, LX_FOCUS_PLUS, speed);
	
	// this kind of focuser really s****
	// sleep then stop motor
	usleep(abs(steps) * LX_FOCUS_GAIN);

	lx200_focus_control(tel, LX_FOCUS_STOP, speed);

	return(0);
}


/*-------------------------------------------------------------------------*/


int lx200_focus_control(tel_info *tel, int direction, int speed)
{
        char cmdSlow[] = ":FS#";
	char cmdFast[] = ":FF#";
	char cmdMinus[] = ":F-#";
	char cmdPlus[] = ":F+#";
	char cmdStop[] = ":FQ#";


	if (speed == LX_FOCUS_FAST) 
	        write_serial(tel->serial, cmdFast, strlen(cmdFast));
	else 
	        write_serial(tel->serial, cmdSlow, strlen(cmdFast));

	switch (direction) {
	case LX_FOCUS_MINUS:
	        write_serial(tel->serial, cmdMinus, strlen(cmdMinus));
		break;
	case LX_FOCUS_PLUS:
	        write_serial(tel->serial, cmdPlus, strlen(cmdPlus));
		break;
	case LX_FOCUS_STOP:
	        write_serial(tel->serial, cmdStop, strlen(cmdStop));
		break;
	}

	return (0);
}


/*-------------------------------------------------------------------------*/


int lx200_ra_drive_off(tel_info *tel)
{
        char cmdGuideRate[] = ":RG#";
	char cmdMoveEast[] = ":Me#";

	write_serial(tel->serial, cmdGuideRate, strlen(cmdGuideRate));
	write_serial(tel->serial, cmdMoveEast, strlen(cmdMoveEast));
	return (0);
}


/*-------------------------------------------------------------------------*/


int lx200_ra_drive_on(tel_info *tel)
{
	char cmdStop[] = ":Qe#";

	write_serial(tel->serial, cmdStop, strlen(cmdStop));
	return (0);
}


/*-------------------------------------------------------------------------*/


