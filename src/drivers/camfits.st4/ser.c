/* This file contains the functions for serial communication */

#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <signal.h>
#include <termios.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

#include "errors.h"
#include "ser.h"

static void rdtimeout(int signumber);
static ser_info *sertmp;

#ifdef COMMTEST

/* This example program writes a string in port `tty', and waits until
   timeout for a response. */


char teste[] = "Write test...";
unsigned char buf[25];
char tty[]   = "/dev/ttyS1";


int main(void)
{
	int result;
	ser_info porta;

	open_serial(&porta, tty);
	if (porta.err_code != ERR_OK) return(-1);
	puts("Communication test.\n\n");

	/* 9600,8e1 */
	porta.baudrate = B9600;
	porta.parity = PAR_EVEN;
	porta.stopbits = 1;
	porta.timeout = 10;
	porta.minchars = 25;
	porta.waitread = FALSE;
	set_serial(&porta);
	write_serial(&porta, teste, strlen(teste));

	if (read_serial(&porta, buf, 24))
	printf("Text received: %s\n\n", buf);
	else printf("Read timeout.\n\n");

	close_serial(&porta);
	return(0);
}
#endif /* COMMTEST */


int is_valid_serial(ser_info *serial)
{
	if ((serial == NULL)           ||
	    (serial->tty_name == NULL) ||
	    (serial->tio == NULL)      ||
	    (serial->oldtio == NULL))
		return(FALSE);
	return(TRUE);
}


void open_serial(ser_info *serial, char *ttyname)
{
	if (serial == NULL) return;

	serial->err_code = ERR_OK;
	signal(SIGALRM, rdtimeout);

/* Allocate memory for the structures */
	serial->tio = (struct termios *) malloc(sizeof(struct termios));
	if (serial->tio == NULL) {
		serial->err_code = ERR_MEM;
		return;
	}
	serial->oldtio = (struct termios *) malloc(sizeof(struct termios));
	if (serial->oldtio == NULL) {
		serial->err_code = ERR_MEM;
		return;
	}

	serial->tty_name = (char *) calloc(strlen(ttyname), sizeof(char));
	if (serial->tty_name == NULL) {
		serial->err_code = ERR_MEM;
		return;
	}
	strcpy(serial->tty_name, ttyname);


	serial->ttyfd = open(serial->tty_name, O_RDWR | O_NOCTTY);
	if (serial->ttyfd < 0) {
		serial->err_code = ERR_OPENTTY;
		close_serial(serial);
		return;
	}

/* Save current config */
	tcgetattr(serial->ttyfd, serial->oldtio);
	serial->isopen = TRUE;
}


int close_serial(ser_info *serial)
{
	if (!is_valid_serial(serial)) return(ERR_MEM);
	signal(SIGALRM, SIG_DFL);
/* Restore terminal to its previous state; free memory */ 
	if (serial->isopen) {
		tcsetattr(serial->ttyfd,TCSANOW,serial->tio);
		close(serial->ttyfd);
	}
	if (serial->tio != NULL) free(serial->tio);
	if (serial->oldtio != NULL) free(serial->oldtio);
	if (serial->tty_name != NULL) free(serial->tty_name);
	return(ERR_OK);
}


int set_serial(ser_info *serial)
{
	if (!is_valid_serial(serial)) return(ERR_MEM);
	if (!serial->isopen) {
		serial->err_code = ERR_SERIAL;
		return(ERR_SERIAL);
	}
	memset(serial->tio, 0, sizeof(struct termios));

	cfsetospeed(serial->tio, serial->baudrate);
	cfsetispeed(serial->tio, serial->baudrate);

/* Set byte size to 8bit, enable reading and set local mode */
	serial->tio->c_cflag |= CS8 | CLOCAL | CREAD;
	switch (serial->parity) {
	case PAR_NONE:
		serial->tio->c_iflag |= IGNPAR;
		serial->tio->c_cflag &= ~PARENB;
		break;

	case PAR_EVEN:
		serial->tio->c_iflag &= ~IGNPAR;
		serial->tio->c_cflag |= PARENB;
		serial->tio->c_cflag &= ~PARODD;
		break;

	case PAR_ODD:
		serial->tio->c_iflag &= ~IGNPAR;
		serial->tio->c_cflag |= PARENB;
		serial->tio->c_cflag &= PARODD;
		break;
	default:
		serial->err_code = ERR_PARITY;
		return;
	}

	if (serial->stopbits == 1)
		serial->tio->c_cflag &= ~CSTOPB;
	else if (serial->stopbits ==2)
		serial->tio->c_cflag |= CSTOPB;
	else {
		serial->err_code = ERR_STOPB;
		return;
	}

/* Raw input */
	serial-> tio->c_lflag = 0;

	serial->tio->c_cc[VTIME] = serial->timeout;
	if (serial->waitread)
		serial->tio->c_cc[VMIN] = serial->minchars;

	tcsetattr(serial->ttyfd,TCSANOW,serial->tio);
}


int write_serial(ser_info *serial, unsigned char *buf, unsigned int nbytes)
{
	int result;

	if (!is_valid_serial(serial)) return(ERR_MEM);
	if (!serial->isopen) {
		serial->err_code = ERR_SERIAL;
		return(0);
	}
	result = write(serial->ttyfd, buf, nbytes);
	if (result < nbytes) {
		serial->err_code = ERR_WRITE;
		return(result);
	}
	serial->err_code = ERR_OK;
	return(result);
}


int read_serial(ser_info *serial, unsigned char *buf, unsigned int nbytes)
{
	int result;

	if (!is_valid_serial(serial)) return(ERR_MEM);
	if (!serial->isopen) {
		serial->err_code = ERR_SERIAL;
		return(0);
	}
	serial->err_code = ERR_OK;

/* Set the minimum number of chars to read before returning */
	if (serial->waitread && (serial->minchars != nbytes)) {
		if (set_minchars(serial, nbytes) != ERR_OK) {
			serial->err_code = ERR_SERIAL;
			return(0);
		}
	}
/* save serial stuff for alarm() timeout. */
	sertmp = serial;
	alarm(serial->timeout);
	result = read(serial->ttyfd, buf, nbytes);
	alarm(0);
	serial->bytesread = result;
	if (result < nbytes)
		serial->err_code = ERR_READ;
	return(result);
}


static int set_minchars(ser_info *serial, int nbytes)
{
	if (!is_valid_serial(serial))
		return(ERR_MEM);
	if (!serial->waitread)
		return(ERR_READ);
	serial->minchars = nbytes;
	serial->tio->c_cc[VMIN] = nbytes;
	tcsetattr(serial->ttyfd,TCSANOW,serial->tio);
	return(ERR_OK);
}

static void rdtimeout(int signumber)
{
	fprintf(stderr, "Serial communication failed, exiting...\n");
	if (sertmp != NULL) close_serial(sertmp);
	exit(-1);
}

