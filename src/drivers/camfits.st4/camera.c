#include <stdio.h>
#include <fcntl.h>
#include <signal.h>
#include <unistd.h>
#include <stdlib.h>

#include "errors.h"
#include "ccd.h"
#include "fitsio.h"

#define TRUE  (1)
#define FALSE (0)

void usage(char *command);
void setup(void);
void check_alloc_error(void);
void expose_error(int err);
void save_fits(void);
void print_image(unsigned char *image);
void controlc(int signumber);

cam_info *camera;
int output = FALSE;
char *porta;
char *imagefile;
float texp;
fitsfile *fptr;
int fitstatus;
unsigned char image[CAM_MAX_NLINES][CAM_MAX_NCOLS];
long naxes[2] = {CAM_MAX_NCOLS, CAM_MAX_NLINES};

int main(int argc, char ** argv)
{
	int res;

        signal(SIGINT, controlc);
        signal(SIGABRT, controlc);

	fprintf(stderr, "CCD dump, FITS file format support.\n");
	if (argc < 4) {
		usage(argv[0]);
		exit(1);
	}

/*	strcpy(porta, argv[1]);
	strcpy(imagefile, argv[3]); */
	porta = argv[1];
	imagefile = argv[3];
	if (*imagefile == '-') {
		if (*(++imagefile) == '\0') {
			output = TRUE;
			imagefile = NULL;
		} else {
			usage(argv[0]);
			exit(1);
		}
	}

/* get exposure time */
	res = sscanf(argv[2], "%f", &texp);
	if (res != 1) {
		fprintf(stderr, "\nError: \"%s\" is an invalid exposure time.\n\n", argv[2]);
		usage(argv[0]);
		exit(1);
	}

/* test if file already exists */
        if (!output && (res = open(imagefile, O_RDONLY)) != -1) {
        	close(res);
                fprintf(stderr, "Error: File \"%s\" already exists.\n\n", argv[3]);
		usage(argv[0]);
                exit(1);
        }

	setup();

	fprintf(stderr, "Exposing CCD...\n");
	if ((res = expose_ccd(camera, texp)) != ERR_OK) {
		expose_error(res);
                abort();
	}
	fprintf(stderr, "Exposure OK.\n\n");

	fprintf(stderr, "Downloading image...\n");
	if ((res = download_image(camera, camera->ccd->image)) != ERR_OK) {
		fprintf(stderr, "Error in download_image()\n");
                abort();
	}
	fprintf(stderr, "Download done.\n\n");

	if (output) {
		fprintf(stderr, "Printing image...\n");
		print_image(camera->ccd->image);
		fprintf(stderr, "\nDone.\n");
	} else {
		fprintf(stderr, "Saving image...\n");
		save_fits();
		fprintf(stderr, "Image taken successfully.\n\n");
	}

	free_camera(camera);
        return(0);
}


void usage(char *command)
{
	fprintf(stderr, "Specify terminal, exposure time (in seconds) and file name.\n");
	fprintf(stderr, "Use \"-\" instead of file name to output the image to stdout.\n\n");
	fprintf(stderr, "SYNTAX: %s terminal_device exposure_time { output_file | - }\n\n", command);
	fprintf(stderr, "E.g.: %s /dev/ttyS1 10.2 output.fit\n", command);
	fprintf(stderr, "E.g.: %s /dev/ttyS1 10.2 -\n\n\n", command);
}


/* sets up camera structs and initializes its parameters */
void setup(void)
{
	int tmp;

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
	}
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
}


void save_fits(void)
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

        if (fits_create_file(&fptr, imagefile, &fitstatus) ||
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
	exit(2);
}

