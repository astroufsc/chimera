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
#include <fcntl.h>
#include <signal.h>
#include <string.h>
#include "errors.h"
#include "ccd.h"
#include "fitsio.h"

#define TRUE  (1)
#define FALSE (0)

int getimage(cam_info *camera, float texp, char *bfname, int imindex);
int fileexists(char *fname);
void usage(void);
void setup(void);
void check_alloc_error(void);
void expose_error(int err);
void save_fits(char *fname);
void print_image(unsigned char *image);
void controlc(int signumber);
void hangup(int signumber);


cam_info *camera;
char command[128];
int output = FALSE; /* Enable output to terminal */
int nexp = 0;       /* Number of images to take */
char *porta;        /* Serial port */
char *bfname;       /* Image base-file-name */
int imindex;        /* index to bfname */
float texp;         /* Exposure time */
fitsfile *fptr;     /* Image file */
int fitstatus;      /* Status returned by fits library */

int nimg;           /* Number of images taken */
int stop_imaging = FALSE; /* if TRUE stop imaging */

unsigned char image[CAM_MAX_NLINES][CAM_MAX_NCOLS];
long naxes[2] = {CAM_MAX_NCOLS, CAM_MAX_NLINES};

int main(int argc, char ** argv)
{
	int res;

        signal(SIGINT, controlc);
        signal(SIGHUP, hangup);
        signal(SIGABRT, controlc);

	strcpy(command, argv[0]);
	fprintf(stderr, "CCD faker, FITS file format support.\n"
                        "Ver0.6f - Image sequence enabled.\n\n");
	if (argc < 8) {
		usage();
		exit(1);
	}

/*	strcpy(porta, argv[1]);
	strcpy(bfname, argv[4]); */
	porta = argv[1];
	bfname = argv[6];
	if (*bfname == '-') {
		if (*(++bfname) == '\0') {
			output = TRUE;
			bfname = NULL;
		} else {
			usage();
			exit(1);
		}
	}


/* get index */
	if (!output) {
		res = sscanf(argv[7], "%d", &imindex);
		if (res != 1) {
			fprintf(stderr, "\nError: \"%s\" is an invalid index.\n\n", argv[2]);
			usage();
			exit(1);
		}
	}

/* get exposure time */
	res = sscanf(argv[2], "%f", &texp);
	if (res != 1) {
		fprintf(stderr, "\nError: \"%s\" is an invalid exposure time.\n\n", argv[2]);
		usage();
		exit(1);
	}

/* get number of exposures */
	res = sscanf(argv[3], "%d", &nexp);
	if (res != 1) {
		fprintf(stderr, "\nError: \"%s\" is an invalid number of exposures.\n\n", argv[2]);
		usage();
		exit(1);
	}

	setup();

	for (nimg = 0; nimg < nexp; nimg++) {
		fprintf(stderr, "\nTaking image #%d.\n", nimg);
		getimage(camera, texp, bfname, (nimg + imindex));
		if (stop_imaging) break;
	}

	free_camera(camera);
        exit(nimg++);
}


int getimage(cam_info *camera, float texp, char *bfname, int imindex)
{
	char fname[128];
	char tmp[128];
	int res;
 
	fprintf(stderr, "Exposing CCD...");
/*	if ((res = expose_ccd(camera, texp)) != ERR_OK) {
		expose_error(res);
                abort();
	} */
	sleep((int) texp);
	fprintf(stderr, "OK.\n");

	fprintf(stderr, "Downloading image...");
/*	if ((res = download_image(camera, camera->ccd->image)) != ERR_OK) {
		fprintf(stderr, "Error in download_image()\n");
                abort();
	} */
	sleep(5);
	fprintf(stderr, "OK.\n");

	if (output) {
/*		fprintf(stderr, "Printing image...\n");
		print_image(camera->ccd->image);
		fprintf(stderr, "\nDone.\n"); */
	} else {
		sprintf(fname, "%s%04d.fits", bfname, imindex);
		fprintf(stderr, "Saving image %s...", fname);
		if (fileexists(fname))
			fprintf(stderr, " file already exists.\n");
		else {
			snprintf(tmp,128, "touch %s", fname);
			system(tmp);
		/*	save_fits(fname); */
			fprintf(stderr, "OK\n");
		}
	}
}



void usage(void)
{
	fprintf(stderr, "Specify terminal, exposure time (in seconds), # of exposures, base-file-name and indexer.\n");
	fprintf(stderr, "Use \"-\" instead of file name to output the image to stdout.\n\n");
	fprintf(stderr, "SYNTAX: %s terminal_device exposure_time nexposures x1:x2 y1:y2 { output_file indexer | - }\n\n", command);
	fprintf(stderr, "E.g.: %s /dev/ttyS1 10.2 25 0:192 0:165 junk 0000\n", command);
	fprintf(stderr, "E.g.: %s /dev/ttyS1 10.2 1 50:100 46:120 -\n\n\n", command);
}


/* test if file already exists */
int fileexists(char *fname)
{
	int res;

	if ((res = open(fname, O_RDONLY)) != -1) {
        	close(res);
                return (TRUE); /* File exists! */
        }
	return (FALSE); /* File does not exist */
}



/* sets up camera structs and initializes its parameters */
void setup(void)
{
/*	int tmp;

	camera = alloc_camera(porta);
	check_alloc_error();

	camera->ccd->image = &(image[0][0]);

	camera->ccd->baudrate = CAM_B57600;
	camera->ccd->rom_version = ROM_VERSION;
	if ((tmp = init_camera(camera)) != ERR_OK) {
		fprintf(stderr, "Error in init_camera(): %d\n", tmp);
                abort();
	}
	camera->ccd->first_line = CAM_FIRST_LINE;
	camera->ccd->first_column = 0;
	camera->ccd->nlines = CAM_MAX_NLINES;
	camera->ccd->ncolumns = CAM_MAX_NCOLS;
	camera->ccd->offset = 0;
	camera->ccd->vref_plus = 255;
	camera->ccd->vref_minus = 0;
	camera->ccd->format_flag = 0;
	camera->ccd->mode_flag = (CAM_MODE_FEXP | CAM_MODE_LA);
	if ((tmp = set_camera(camera)) != ERR_OK) {
		fprintf(stderr, "Error in set_camera()\n");
                abort();
	} */
}


void print_image(unsigned char *image)
{
	int i, j, lastline, lastcol;

	lastline = camera->ccd->nlines;
	lastcol = camera->ccd->ncolumns;
	for (i = 0; i < lastline; i++) {
		for (j = 0; j < lastcol; j++)
			printf("%d\n", *(image++));
	}
	printf("$"); /* image terminator */
}


void save_fits(char *fname)
{
        int x, y, i, j, lastline, lastcol;
        unsigned char ** imgptr;

/* Gradient fill
	for (i = 0; i < 165; i++) 
		for (j = 0; j < 192; j++)
			image[i][j] = (i+j)/2;
*/

	naxes[0] = camera->ccd->ncolumns;
	naxes[1] = camera->ccd->nlines;

/*
        imgptr = camera->ccd->image;
	lastline = camera->ccd->nlines + camera->ccd->first_line;
	lastcol = camera->ccd->first_column + camera->ccd->ncolumns;

	for (i = camera->ccd->first_line, x = 0; i < lastline; i++, x++, imgptr++) {
		for (j = camera->ccd->first_column, y = 0; j < lastcol; j++, y++)
			rawimage[x][y] = (*imgptr)[y];
	}
*/

/* open file for writing a FITS image */

        if (fits_create_file(&fptr, fname, &fitstatus) ||
            fits_create_img(fptr, BYTE_IMG, 2, naxes, &fitstatus) ||
            fits_write_img(fptr, TBYTE, 1, (naxes[0] * naxes[1]), image, &fitstatus) ||
            fits_update_key(fptr, TFLOAT, "EXPTIME", &texp, "Exposure Time (secs.)", &fitstatus) ||
            fits_close_file(fptr, &fitstatus)) {
                 fits_report_error(stderr, fitstatus);
                 abort();
         }
}


void check_alloc_error(void)
{
	if (!is_valid_camera(camera)) {
		fprintf(stderr, "Error allocating camera structures.\n");
		abort();
	}
	if (camera->serial->err_code == ERR_OK) return;

	fprintf(stderr, "Error setting up camera, ");
	if (camera->serial->err_code == ERR_READ)
		fprintf(stderr, "could not read serial port.\n");
	else if (camera->serial->err_code == ERR_WRITE)
		fprintf(stderr, "could not write serial port.\n");
	else if (camera->serial->err_code == ERR_OPENTTY)
		fprintf(stderr, "could not open serial port.\n");
	else if (camera->serial->err_code == ERR_MEM)
		fprintf(stderr, "serial structures could not be created.\n");
	else fprintf(stderr, "unexpected error.\n");
	abort();
}


void expose_error(int err)
{
	fprintf(stderr, "Problem exposing CCD, ");
	if (err == ERR_CAM) fprintf(stderr, "camera not allocated.\n");
	else if (err == ERR_WRITE) fprintf(stderr, "error writing camera.\n");
	else if (err == ERR_READ) fprintf(stderr, "error reading camera.\n");
	else fprintf(stderr, "unexpected error.\n");
	abort();
}


void controlc(int signumber)
{
        if (signumber == SIGINT)
                fprintf(stderr, "Control-C signal caught, exiting.\n");
	else
                fprintf(stderr, "Aborting...\n");
        if (is_valid_camera(camera)) 
                tcflush(camera->serial->ttyfd, TCOFLUSH);
	free_camera(camera);
	exit(nimg++);
}

void hangup(int signumber)
{
  fprintf(stderr, "\nHangup signal received, stopping imaging.\n");
        stop_imaging = TRUE;
}
