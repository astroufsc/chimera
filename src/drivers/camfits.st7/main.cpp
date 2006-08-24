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
#include <math.h>

#include <getopt.h>

#include "fitsio.h"
#include "csbigcam.h"
#include "getindex.h"

using namespace std;


#define PROGRAM_NAME "SBIG CCD camera controller"

#define boolstring(x) (x?"true":"false")
#define shutterstate (openshutter?"OPEN":"CLOSED")
#define selectedccd  (ccd?"tracking":"imaging")


// filled by get_args()
int verbose;
char *exec_name;               // Name of executable file
static char *conffname;        // configuration file
static char *bfname;           // image base file name
static char imagefname[256];   // image file name
static double exptime;         // seconds
static int interval;           // seconds
static int nexp;               // number of exposures
static int openshutter;        // 1: open, 0: closed
static unsigned short binning;
static SBIG_DEVICE_TYPE device;// camera device
static CCD_REQUEST ccd;        // imaging=0, tracking=1
static ABG_STATE7 abg;         // abg state
static unsigned short filter;  // color filter.
static unsigned short top, left, width, height; // image window
static int tr;                 // set temperature regulation (if set to 1)
static double setpoint;        // target temperature for regulation

static void print_title(void);
static void print_help(void);
static void print_version(void);
static void print_usage(void);
static void get_args(int argc, char **argv);


/*-------------------------------------------------------------------------*/

int main(int argc, char **argv)
{
	CSBIGCam *cam;
	PAR_ERROR err;
	unsigned short *data;

	char errmsg[255];
	char buffer[80];

	// get command line arguments
	get_args(argc, argv);

	if (verbose) {
	  print_version();
	  // list arguments
	  printf("\n*** Options:\n\n");
	  printf("Exptime : %'.2f seconds\n", exptime);
	  printf("Interval: %d seconds\n", interval);
	  printf("Nexp    : %d\n", nexp);
	  printf("Shutter : %s\n", shutterstate);
	  printf("Binning : %d\n", binning);
	  printf("Filter  : %d\n", filter);
	  printf("Device  : %x\n", device);
	  printf("CCD     : %s\n", selectedccd);
	  printf("Temperature regulation: %d\n", tr);
	  printf("Setpoint temperature  : %'.1f C\n", setpoint);
	  printf("ABG state: %d\n", abg);
	  printf("top   : %d\n", top);
	  printf("height: %d\n", height);
	  printf("left  : %d\n", left);
	  printf("width : %d\n", width);
	  printf("Output: %s-####.fits\n\n", bfname);
	  //printf("Config file: %s\n", conffname);
	}


	// start talking to camera
	cam = new CSBIGCam(device);

	if (verbose) {
	  printf("Establishing link... ");
	  fflush(stdout);
	}

	err = cam->EstablishLink();
	if (err != CE_NO_ERROR) {
	  printf("Error linking to camera.\n");
	  delete cam;
	  exit(1);
	}

	if (verbose) printf("OK.\nCamera type: %s\n",
			    (cam->GetCameraTypeString()).c_str());


	// Do temperature regulation stuff
	double ccd_temperature;
	MY_LOGICAL ccd_tr_enabled;
	double percentTE;
	double ccd_setpoint;

	if (verbose) printf("\nReading temperature regulation status...\n");
	cam->QueryTemperatureStatus(ccd_tr_enabled, ccd_temperature,
				    ccd_setpoint, percentTE);

	if (verbose) {
	        printf("Temperature regulation: %s\n",
		       boolstring(ccd_tr_enabled));
		printf("Chip temperature: %'.1f C\n",
		       ccd_temperature);
	        printf("Setpoint temperature: %'.1f\n",
		       ccd_setpoint);
	        printf("TE regulation power: %'.0f%%\n\n",
		       percentTE);
	}

	switch (tr) {
	case 2: // set regulation and wait stabilization
	        if (setpoint == 1000) setpoint = ccd_setpoint;
		printf("Activating temperature regulation.\n");
		printf("Target temperature: %'.1f C\n",
		       setpoint);
		cam->SetTemperatureRegulation(1, setpoint);

		printf("Waiting temperature stabilization...\n");

		// wait temperature regulation
		for (;;) {
		        cam->QueryTemperatureStatus(ccd_tr_enabled,
						    ccd_temperature,
						    ccd_setpoint, percentTE);
			if (verbose) printf("Current temperature is %'.1f C."
                                            " Target: %'.1f C."
					    " TE regulation power: %'.0f%%\n",
					    ccd_temperature, setpoint,
					    percentTE);
			if (fabs(ccd_temperature - setpoint) < 0.5) break;
			sleep(5);
		}
		printf("Temperature regulation completed.\n");
		delete cam;
		exit(0);
		break;

	}


	// allocate image buffer
	data = (unsigned short*)calloc(width*height, sizeof(unsigned short));
	if (data == NULL) {
		printf("Error malloc\'ing! :-/\n");
		delete cam;
		exit(1);
	}


	// set up camera
	cam->SetActiveCCD(ccd);
	cam->SetExposureTime(exptime);
	cam->SetReadoutMode(binning);
	cam->SetABGState(abg);


	// set filter
	if (filter != 0) {
		CFWResults cfwr;
		CFWParams cfwp = {CFWSEL_CFW8, CFWC_GOTO, filter,
				  0,0,NULL,0,NULL};

		printf("Moving filter wheel to position %d... ", filter);
		fflush(stdout);
		cam->CFWCommand(cfwp, cfwr);

		//wait GOTO command finish
		do {
			usleep(500000); // .5 sec
			cfwp.cfwCommand = CFWC_QUERY;
			cam->CFWCommand(cfwp, cfwr);
			//printf("status: %d\n", cfwr.cfwStatus);
		} while (cfwr.cfwStatus == CFWS_BUSY);
		printf("Done.\n");
	}


	// start taking images
	int i;
	int index;
	
	// find last image
	index = getindex(bfname) + 1;

	if (verbose)
	  printf("Taking %d images of %'.2f sec., with %d sec. interval.\n",
	       nexp, exptime, interval);

	for (i = 0; i < nexp; i++){
		int fitstatus = 0;
		long int naxes[2];		
		fitsfile *fptr = NULL;


		// initialize file and header
		naxes[0] = width;
		naxes[1] = height;


		// create file name
		sprintf(imagefname,"%s-%04d.fits", bfname, index + i);
		if(fits_create_file(&fptr, imagefname, &fitstatus)) {
		  fits_get_errstatus(fitstatus, errmsg);
		  printf("%s - criando arquivo\n", errmsg);
		}


		if(fits_create_img(fptr, USHORT_IMG, 2, naxes, &fitstatus)) {
		  fits_get_errstatus(fitstatus, errmsg);
		  printf("%s - criando imagem\n", errmsg);
		}


		// fill the header // FIXME add more header here
		fits_update_key(fptr, TDOUBLE, "EXPTIME", &exptime, "Exposure Time (secs.)", &fitstatus);

// 		// DETSIZE
// 		snprintf(buffer, 80, "[%d:%d,%d:%d]", 1, 2, 3, 4);
// 		fits_update_key(fptr, TSTRING, "DETSIZE", buffer, "Size of CCD detector", &fitstatus);

// 		// CCDSEC
// 		snprintf(buffer, 80, "[%d:%d,%d:%d]", top, width, left, height);
// 		fits_update_key(fptr, TSTRING, "CCDSEC", buffer, "Region of CCD read", &fitstatus);

// 		// DATASEC
// 		snprintf(buffer, 80, "[%d:%d,%d:%d]", top, width, left, height);
// 		fits_update_key(fptr, TSTRING, "DATASEC", buffer, "Region of CCD read", &fitstatus);

// 		// BIASSEC
// 		snprintf(buffer, 80, "[%d:%d,%d:%d]", 1, 2, 3, 4);
// 		fits_update_key(fptr, TSTRING, "BIASSEC", buffer, "Bias level section", &fitstatus);

// 		// TRIMSEC
// 		snprintf(buffer, 80, "[%d:%d,%d:%d]", 1, 2, 3, 4);
// 		fits_update_key(fptr, TSTRING, "TRIMSEC", buffer, "Useful section", &fitstatus);

// 		// CCDSUM (for binning)
// 		snprintf(buffer, 80, "%d %d", &binning, &binning);
// 		fits_update_key(fptr, TSTRING, "CCDSUM", buffer, "CCD on-chip summing", &fitstatus);

		fits_write_date(fptr, &fitstatus);


		// expose
		printf("\nFile: %s\n", imagefname);
		printf("Starting a %'.2f seconds exposure (shutter is %s)... ",
		       exptime, shutterstate); 
		fflush(stdout);
		if (openshutter)
		  cam->StartExposure(SC_OPEN_SHUTTER);
		else
		  cam->StartExposure(SC_CLOSE_SHUTTER);

		
		// wait exposure done
		MY_LOGICAL expcomplete;
		
		if (exptime < 0.5)
			usleep((unsigned long)exptime*1000000UL + 50000UL);
		else
			sleep((unsigned int)(exptime+1.0));

		cam->IsExposureComplete(expcomplete);
		if (!expcomplete) do {
			// check every 0.2 sec
			usleep(200000UL);
			cam->IsExposureComplete(expcomplete);
		} while (!expcomplete);
		cam->EndExposure();
		printf("Done.\n"); 

	
		// exposure complete, download data
		StartReadoutParams srp;
		ReadoutLineParams rlp;

		srp.ccd = ccd;
		srp.readoutMode = binning;
		srp.top = top;
		srp.left = left;
		srp.height = height;
		srp.width = width;

		rlp.ccd = ccd;
		rlp.readoutMode = binning;
		rlp.pixelStart = left;
		rlp.pixelLength = width;
				
		printf("Downloading image of size %dx%d... ", width, height);
		fflush(stdout);
		cam->StartReadout(srp);
		unsigned short *dest = data;
		int j;
		for (j = 0; j < height; j++) {
			dest = data + j*width;
			cam->ReadoutLine(rlp, FALSE, dest);
		}
		cam->EndReadout();
		printf("Done.\n");


		// save file
		//fitstatus = 0;
		if(fits_write_img(fptr, TUSHORT, 1, (naxes[0] * naxes[1]),
				  data, &fitstatus)) {
		  fits_get_errstatus(fitstatus, errmsg);
		  printf("%s\n", errmsg);
		}

		//fits_write_2d_usht(fptr, 0, naxes[0],
		//		   naxes[0], naxes[1], data, &fitstatus);

		fits_close_file(fptr, &fitstatus);


		// sleep until next image
		if (i == nexp) break;
		if (interval == 0) continue;
		printf("Sleeping %d seconds until next image... ", interval);
		fflush(stdout);
		sleep(interval);
		printf("Done.\n");


	} // imaging loop 
	printf("\nImaging complete.\n");


	// all done, clean up the mess
	free(data);
	delete cam;

	exit(0);
}


/*-------------------------------------------------------------------------*/

static void print_title(void)
{
        printf("%s - version: %s\n", PROGRAM_NAME, VERSION);
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
               "                Use camera connected to DEVICE.\n"
               "                    0: USB (default)\n"
               "                    1: LPT1\n"
               "                    2: LPT2\n"
               "                    3: LPT3\n\n"

               "        -c / --CCD N\n"
               "                Use imaging (0) or tracking (1) ccd.\n"
               "                Default: imaging.\n\n"

               "        -r / --tregulation N\n"
               "                Control temperature regulation.\n"
	       "                   -1: Keep previous settings (default).\n"
	       "                    0: Disable.\n"
	       "                    1: Enable. If -T is present, change\n"
	       "                       setpoint temperature.\n"
	       "                    2: Enable and wait temperature\n"
	       "                       stabilization. If -T is present,\n"
	       "                       change setpoint temperature.\n"
	       "                       With this option no imaging will\n"
	       "                       take place.\n\n"

               "        -T / --temperature N\n"
               "                Setpoint temperature for regulation, in\n"
               "                degrees Celsius.\n\n"

               "        -a / --ABG ABG_STATE\n"
               "                Antiblooming gate state during integration.\n"
               "                    0: Low (default).\n"
               "                    1: Clocked low.\n"
               "                    2: Clocked medium.\n"
               "                    3: Clocked high.\n\n"

               "        -f / --filter N\n"
               "                Use Nth filter. N = 1 to 5\n"
	       "                N = 0 (default) keeps the current filter.\n\n"

               "        -t / --exptime TIME\n"
               "                Exposure time, in seconds.\n"
               "                Exposure times can be from 0.01 to 9999\n"
	       "                seconds, in 0.01 sec. steps.\n"
	       "                Default: 0 seconds.\n\n"

               "        -n / --nexp N\n"
               "                Number of images to take.\n"
               "                Default: 1 image.\n\n"

               "        -s / --openshutter 0/1\n"
               "                Open shutter? 0: No, 1: Yes.\n"
               "                Default: 0 - Shutter closed.\n\n"

               "        -i / --interval TIME\n"
               "                Time interval between images, in seconds.\n"
               "                Default: 0 seconds.\n\n"

               "        -w / --window X1:X2,Y1:Y2\n"
               "                Image window to be downloaded (zero-based).\n"
	       "                Default: 0:765,0:510.\n\n"

               "        -b / --binning N\n"
               "                Type of binning.\n"
	       "                    0: No binning (default)\n"
	       "                    1: 2x2\n"
	       "                    2: 3x3\n\n"

               "        -o / --output IMAGEFILE\n"
               "                Save image to IMAGEFILE.\n\n"
               );

        printf("\nFor more information visit the home page: %s\n", PROGRAM_URL);
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
               "       %s -t exptime -n nexp -d device -o imagefile\n\n"
               "       %s {-h|--help}\n\n", exec_name, exec_name);
}

/*-------------------------------------------------------------------------*/

static void get_args(int argc, char **argv)
{
        int next_opt;
        const char *short_options = "hvVC:d:c:r:T:a:f:t:n:s:i:w:b:o:";
        const struct option long_options [] = {
                { "help", 0, NULL, 'h' },
                { "version", 0, NULL, 'v' },
                { "verbose", 0, NULL, 'V' },

                { "config-file", 1, NULL, 'C' },
                { "device", 1, NULL, 'd' },
                { "CCD", 1, NULL, 'c' },
                { "tregulation", 1, NULL, 'r' },
                { "temperature", 1, NULL, 'T' },
                { "ABG", 1, NULL, 'a' },
                { "filter", 1, NULL, 'f' },
                { "exptime", 1, NULL, 't' },
                { "nexp", 1, NULL, 'n' },
                { "openshutter", 1, NULL, 's' },
                { "interval", 1, NULL, 'i' },
                { "window", 1, NULL, 'w' },
                { "binning", 1, NULL, 'b' },
                { "output", 1, NULL, 'o' },
                { NULL, 0, NULL, 0 }
        };

	// default values
        exec_name = argv[0];
	verbose = 0;
        conffname = NULL;
        bfname  = "img";
	filter = 0;      // keep the same
	device = DEV_USB;
	ccd = CCD_IMAGING;
	tr = -1;         // keep the same
	setpoint = 1000; // default value will be read from camera
	abg = ABG_LOW7;
	exptime = 0;
	nexp = 1;
	openshutter = 0; // dont open shutter
	interval = 0;
	binning = 0;     // no binning

 	top = 0;         // full frame
	left = 0;
	width = 765;
	height = 510;

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
		        int temp;
		        sscanf(optarg, "%d", &temp);
			switch (temp) {
			  case 0:
			    device = DEV_USB;
			    break;

			  case 1:
			    device = DEV_LPT1;
			    break;

			  case 2:
			    device = DEV_LPT2;
			    break;

			  case 3:
			    device = DEV_LPT3;
			    break;
			} // temp
                        break;

                case 'c':
			/* ccd */
			sscanf(optarg, "%hu", &ccd);
                        break;

                case 'r':
			/* temperature regulation */
			sscanf(optarg, "%d", &tr);
                        break;

                case 'T':
			/* target temperature */
			sscanf(optarg, "%lf", &setpoint);
                        break;

                case 'a':
			/* abg state */
			sscanf(optarg, "%hu", &abg);
                        break;

                case 'f':
			/* filter */
			sscanf(optarg, "%hu", &filter);
                        break;

                case 't':
                        /* exposure time */
			sscanf(optarg, "%lf", &exptime);
                        break;

                case 'n':
                        /* number of images */
			sscanf(optarg, "%d", &nexp);
                        break;

                case 's':
                        /* open shutter? */
			sscanf(optarg, "%d", &openshutter);
                        break;

                case 'i':
                        /* time interval between images */
			sscanf(optarg, "%d", &interval);
                        break;

                case 'w':
                        /* set image window */
			sscanf(optarg, "%hu:%hu,%hu:%hu",
			       &left, &width, &top, &height);
			// optarg comes as X1:X2,Y1:Y2, fix width and height
			width -= left;
			height -= top;
                        break;

                case 'b':
                        /* set readout mode */
			sscanf(optarg, "%hu", &binning);
                        break;

                case 'o':
                        /* base image file name */
			//imagefname = optarg;
			bfname = optarg;
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

}

/*-------------------------------------------------------------------------*/

