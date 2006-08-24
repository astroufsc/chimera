/***************************************************************************
                          ser.h  -  description
                             -------------------
    begin                : Wed Jun 7 2000
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

#ifndef SER_H
#define SER_H

#include <termios.h>

#define RD_TIMEOUT (2)
#define TRUE (1)
#define FALSE (0)

#define MAX_BUF_LEN (255)
#define PAR_NONE 'n'
#define PAR_EVEN 'e'
#define PAR_ODD  'o'

typedef struct {
	int isopen;
	int waitread;
	int err_code;
	char *tty_name;
	int ttyfd;
	cc_t minchars; /* not used if waitread == FALSE */
	int bytesread;
	int baudrate;
	char parity;
	int stopbits;
	cc_t timeout; /* interchar time (1/10 secs), and read timeout (secs) */
	struct termios *tio;    /* |- don't mess with these structs, */
	struct termios *oldtio; /* |  the routines will handle it.   */
} ser_info;

int is_valid_serial(ser_info *serial);
ser_info *open_serial(char *ttyname);
int close_serial(ser_info *serial);
int set_serial(ser_info *serial);
int read_serial(ser_info *serial, unsigned char *buf, unsigned int nbytes);
int write_serial(ser_info *serial, unsigned char *buf, unsigned int nbytes);


#endif /* SER_H */
