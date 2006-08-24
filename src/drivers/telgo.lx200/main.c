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
#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <signal.h>
#include <getopt.h>

#include "lx200.h"

/*-------------------------------------------------------------------------*/

#define PROGRAM_NAME "LX200/Compatible Telescope Controller"

/*-------------------------------------------------------------------------*/

// filled by get_args()
int verbose;
char *exec_name;               // Name of executable file
char *conffname;               // configuration file
char *device;                  // serial device to connect


// Modes of operation
//  TEL_POINT - Point to given coordinates
//  TEL_MATCH - Perform coordinates match
//  TEL_STOP  - Stop RA drive / stop tracking

#define TEL_POINT 0
#define TEL_MATCH 1
#define TEL_STOP  2
#define TEL_FOCUS 3
int mode;

int focsteps;                  // how much?
int focspeed;                  // how fast?

int paranoia;                  // level of paranoia while pointing.
                               //   actually # of pointing iterations.

int coords_present;            // coordinates were given?
struct ras ra;                 // RA to point at.
struct decs dec;               // DEC to point at.

/*-------------------------------------------------------------------------*/

static void print_title(void);
static void print_help(void);
static void print_version(void);
static void print_usage(void);
static void show_options(void);
static void get_args(int argc, char **argv);

int match_coords(tel_info *tel);
int point_telescope(tel_info *tel);
int change_focus(tel_info *tel);


/*-------------------------------------------------------------------------*/


int main(int argc, char ** argv)
{
        tel_info *tel;

	// get command line arguments
	get_args(argc, argv);

	if (verbose) {
	        print_version();
		show_options();
	}


	if (verbose) printf("Opening device %s.\n", device);
	tel = lx200_open(device);

	// match coords is exclusive
	switch (mode) {
	case TEL_POINT:
	        point_telescope(tel);
		break;

	case TEL_MATCH:
	        match_coords(tel);
		break;

	case TEL_FOCUS:
	        change_focus(tel);
		break;

	case TEL_STOP:
		printf("Stopping RA drive.\n");
		lx200_ra_drive_off(tel);
		if (verbose) printf("Done.\n");
		break;
	}

	lx200_close(tel);
	exit (0);
}


/*-------------------------------------------------------------------------*/


int point_telescope(tel_info *tel)
{
        int i;

	printf("Pointing Telescope.\n");

	if (verbose)
	        printf("Current position:\n"
		       "    RA   %02d:%02d:%02d\n"
		       "    DEC  %02d:%02d:%02d\n",
		       tel->cra.hh, tel->cra.mm, tel->cra.ss,
		       tel->cdec.dd, tel->cdec.mm, tel->cdec.ss);
		 

	if (verbose) printf("Setting destination coordinates:\n"
			    "    RA   %02d:%02d:%02d\n"
			    "    DEC  %02d:%02d:%02d\n",
			    ra.hh, ra.mm, ra.ss,
			    dec.dd, dec.mm, dec.ss);

        lx200_set_coords(tel, ra, dec);


	for(i = 1; i <= paranoia; i++) {
	        if (verbose) printf("Sending GOTO command, pass #%d\n", i);
                lx200_slew(tel);

		if (verbose) printf("Waiting telescope movement.\n");
		lx200_wait_slew(tel);

		if (verbose)
		        printf("New position:\n"
			       "    RA   %02d:%02d:%02d\n"
			       "    DEC  %02d:%02d:%02d\n",
			       tel->cra.hh, tel->cra.mm, tel->cra.ss,
			       tel->cdec.dd, tel->cdec.mm, tel->cdec.ss);
	}

	printf("Pointing completed.\n");
	return (0);
}
	

/*-------------------------------------------------------------------------*/


int change_focus(tel_info *tel)
{
	if (verbose)
	        printf("Changing focus.\n"
		       "Amount: %d\n", focsteps);

	lx200_change_focus(tel, focsteps, focspeed);

	if (verbose) printf("Focus changed.\n");
	return (0);
}
	

/*-------------------------------------------------------------------------*/


int match_coords(tel_info *tel)
{
        printf("Performing coordinates match.\n");

	lx200_update_coords(tel);
	lx200_match_coords(tel);

	if (verbose) printf("Coordinates matched:\n"
			    "    RA   %02d:%02d:%02d\n"
			    "    DEC  %02d:%02d:%02d\n",
			    tel->cra.hh, tel->cra.mm, tel->cra.ss,
			    tel->cdec.dd, tel->cdec.mm, tel->cdec.ss);

	printf("Coordinates match completed.\n");
	return (0);
}
	

/*-------------------------------------------------------------------------*/


static void print_title(void)
{
        printf("%s - version: %s\n", PROGRAM_NAME, VERSION);
}


/*-------------------------------------------------------------------------*/


void show_options(void)
{
        // list arguments
        // default values
        printf("\n*** Options:\n\n");
	printf("Device   : %s\n", device);
	printf("Paranoia : %d\n\n", paranoia);

	switch (mode) {

	case TEL_POINT:
	        printf("Mode: POINT\n");
		printf("\n*** Coordinates:\n\n");
		printf("RA  : %02d:%02d:%02d\n",
		       ra.hh, ra.mm, ra.ss);
		printf("DEC : %02d:%02d:%02d\n\n",
		       dec.dd, dec.mm, dec.ss);
		break;
		
	case TEL_MATCH:
		printf("Mode: MATCH\n");
		break;
		
		
	case TEL_STOP:
		printf("Mode: STOP\n");
		break;

	case TEL_FOCUS:
                printf("Mode: FOCUS\n");
		printf("Speed    : %d\n", focspeed);
		printf("Steps    : %d\n\n", focsteps);
		break;
	}
}


/*-------------------------------------------------------------------------*/


static void print_help(void)
{
        print_title();
        print_usage();
        printf("Command line options:\n\n"
               "        -h / --help\n"
               "                This help screen.\n\n"

               "        -v / --version\n"
               "                Display version and copyright information.\n\n"

               "        -V / --verbose\n"
               "                Display more progress stuff.\n\n"

               "        -C / --config-file CONFFILE\n"
               "                Read options from CONFFILE.\n\n"

               "        -d / --device DEVICE\n"
               "                Use given serial port.\n"
               "                Default: /dev/ttyS0\n\n"

               "        -m / --match-coords\n"
               "                Match the position of the telescope in the\n"
	       "                sky to the last pointed coordinates.\n\n"

               "        -S / --stop-ra-drive\n"
               "                Stops RA drive, no tracking will occur.\n\n"

               "        -f / --focus N\n"
               "                Move focus N \"steps\", where N is a\n"
	       "                positive or negative integer.\n\n"

               "        -s / --focus-speed N\n"
               "                Speed of focus motor.\n"
	       "                  0: Slow.\n"
	       "                  1: Fast. (default)\n\n"

               "        -P / --paranoia N\n"
               "                Paranoid pointing checking.\n\n"
               "                Perform N pointing iterations.\n"
	       "                Default: 1 iteration.\n\n"
               );

        printf("\nFor more information visit our home page: %s\n", PROGRAM_URL);
        exit(0);
}

/*-------------------------------------------------------------------------*/

static void print_version(void)
{
        print_title();
        printf("Copyright (C) 2004 Andre Luiz de Amorim\n");
        printf("%s comes with NO WARRANTY,\n"
               "to the extent permitted by law.\n", PROGRAM_NAME);
        printf("You may redistribute copies of %s\n"
               "under the terms of the GNU General Public License.\n"
               "For more information about these matters,\n"
               "see the files named COPYING.\n", PROGRAM_NAME);

        //exit(0);
}

/*-------------------------------------------------------------------------*/

static void print_usage(void)
{
        printf("SYNTAX:\n"
               "       %s [options] <R.A.> <DEC.>\n\n"
               "       %s {-h|--help}\n\n"
	       "<R.A.> in the form  HH:MM:SS.S\n"
	       "<DEC.> in the form +DD:MM:SS.S\n\n", exec_name, exec_name);
}

/*-------------------------------------------------------------------------*/

static void get_args(int argc, char **argv)
{
        int next_opt;
        const char *short_options = "hvVC:d:mSf:s:P:";
        const struct option long_options [] = {
                { "help", 0, NULL, 'h' },
                { "version", 0, NULL, 'v' },
                { "verbose", 0, NULL, 'V' },
                { "config-file", 1, NULL, 'C' },
                { "device", 1, NULL, 'd' },
                { "match-coords", 0, NULL, 'm' },
                { "stop-ra-drive", 0, NULL, 'S' },
                { "focus", 1, NULL, 'f' },
                { "focus-speed", 1, NULL, 's' },
                { "paranoia", 1, NULL, 'P' },
                { NULL, 0, NULL, 0 }
        };

	// default values
	exec_name = argv[0];
	verbose = 0;
        conffname = NULL;
	device = LX_DEFAULT_DEVICE;
	mode = TEL_POINT;
	focsteps = 0;
	focspeed = 1;
	paranoia = 1;



       do {
                next_opt = getopt_long(argc, argv, short_options,
                                       long_options, NULL);
                switch (next_opt) {
                case 'h':
                        print_help();
                        break;

                case 'v':
                        print_version();
			exit(0);
                        break;

                case 'V':
                        verbose = 1;
                        break;

                case 'C':
			/* config file */
			conffname = optarg;
                        break;

                case 'd':
			/* device */
		        device = optarg;
                        break;

                case 'm':
			/* device */
		        mode = TEL_MATCH;
			return; // do nothing else when matching
                        break;

                case 'S':
			/* stop RA drive */
		        mode = TEL_STOP;
			return;
                        break;


                case 'f':
			/* focus control */
			sscanf(optarg, "%d", &focsteps);
			mode = TEL_FOCUS;
                        break;

                case 's':
			/* focus speed */
			sscanf(optarg, "%d", &focspeed);
			if (focspeed == 0) focspeed = LX_FOCUS_SLOW;
			else focspeed = LX_FOCUS_FAST;
                        break;

                case 'P':
			/* level of paranoia */
			sscanf(optarg, "%d", &paranoia);
                        break;



                case '?':
                        /* Invalid option */
			print_usage();
                        exit(1);
                        break;

                case -1:
                        /* end of options */
                        break;

                default:
                        printf("Tell author he should read the getopt_long man page.\n");
			exit(1);
                        break;
                }
        } while (next_opt != -1);

       if (mode == TEL_FOCUS) {
	 return;
       }


       // extra argument mandatory if in point mode
       if(optind != argc-1 && mode == TEL_POINT)  {
	        print_usage();
                exit(1);
       }

       // read RA and DEC
       coords_present = 1;
       sscanf(argv[optind], "%d:%d:%d,%d:%d:%d",
	      &ra.hh, &ra.mm, &ra.ss, &dec.dd, &dec.mm, &dec.ss);

}

/*-------------------------------------------------------------------------*/

