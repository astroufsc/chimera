/*--------------------------------------------------------------------*/
/*;  Copyright (C) 1996                                               */
/*;  Associated Universities, Inc. Washington DC, USA.                */
/*;                                                                   */
/*;  This program is free software; you can redistribute it and/or    */
/*;  modify it under the terms of the GNU General Public License as   */
/*;  published by the Free Software Foundation; either version 2 of   */
/*;  the License, or (at your option) any later version.              */
/*;                                                                   */
/*;  This program is distributed in the hope that it will be useful,  */
/*;  but WITHOUT ANY WARRANTY; without even the implied warranty of   */
/*;  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the    */
/*;  GNU General Public License for more details.                     */
/*;                                                                   */
/*;  You should have received a copy of the GNU General Public        */
/*;  License along with this program; if not, write to the Free       */
/*;  Software Foundation, Inc., 675 Massachusetts Ave, Cambridge,     */
/*;  MA 02139, USA.                                                   */
/*;                                                                   */
/*;  Correspondence  should be addressed as follows:                  */
/*;         Internet email: bcotton@nrao.edu.                         */
/*;         Postal address: William Cotton                            */
/*;                         National Radio Astronomy Observatory      */
/*;                         520 Edgemont Road                         */
/*;                         Charlottesville, VA 22903-2475 USA        */
/*--------------------------------------------------------------------*/
#include "jpegsubs.h"

/*                      JPEG compress routines                        */

/* global values for jpeg I/O; allows 1 at a time */
int nx, ny;       /* size of image */
int nonlinear;    /* if true use nonlinear mapping */
float vmax, vmin; /* max and min unscaled values */
char *name=NULL;  /* name of output jpeg file */
JSAMPROW idata=NULL; /* buffer for scaled version of row */
FILE *outfile=NULL;  /* output jpeg stream pointer */
struct jpeg_compress_struct cinfo; /* jpeg compress structure */
struct jpeg_error_mgr jerr;        /* jpeg error handler structure */
JSAMPROW row_pointer[1];	   /* pointer to a single row */


void jpgini (char *iname, int inx, int iny, float ivmax,  float ivmin, 
	     int nonLin, int quality, int *ierr)
/*--------------------------------------------------------------------*/
/*  Initializes i/o to jpeg output routines                           */
/*  Inputs:                                                           */
/*     iname    Name of output file                                   */
/*     ilname   Length of name                                        */
/*     inx      number of columns in image                            */
/*     iny      Number of rows in image                               */
/*     ivmax    Maximum image value (values larger get this value)    */
/*     ivmin    Minimum image value (values smaller get this value)   */
/*     nonLin   if > 0.0 use non linear function                      */
/*     quality  jpeg quality factor [1-100]                           */
/*  Output:                                                           */
/*     ierr     0.0 => OK                                             */
/*--------------------------------------------------------------------*/
{
  int lname, i;

  /* get values */
  nx = inx;
  ny = iny;
  lname = strlen(iname);
  vmax = ivmax;
  vmin = ivmin;
  nonlinear = nonLin;

  /* file name */
  if (name) free(name);
  name = (char*)malloc(lname+1);
  if (name == NULL) {
    fprintf(stderr, "can't allocate file name");
    *ierr = 1; /* set error return */
    return; /* failed */
  }
  for (i=0;i<lname;i++) name[i] = iname[i]; name[i] = 0;

  /* row buffer */
  if (idata) free(idata);
  idata = (JSAMPROW)malloc(nx); /* allocate for gray scale */
  if (idata == NULL) {
    fprintf(stderr, "can't allocate row buffer");
    *ierr = 2; /* set error return */
    return; /* failed */
  }
  for (i=0;i<nx;i++) idata[i] = 0;

  /* open output file */
  if ((outfile = fopen(name, "wb")) == NULL) {
    fprintf(stderr, "can't open %s\n", name);
    *ierr = 3; /* set error return */
    return; /* failed */
  }

  /* create jpeg structures */
  cinfo.err = jpeg_std_error(&jerr);
  jpeg_create_compress(&cinfo);

  /* initialize jpeg output routines */
  jpeg_stdio_dest(&cinfo, outfile);

/* set image parameters */
  cinfo.image_width = nx; 	/* image width and height, in pixels */
  cinfo.image_height = ny;
  cinfo.input_components = 1;	/* # of color components per pixel */
  cinfo.in_color_space = JCS_GRAYSCALE; /* colorspace of input image */

  jpeg_set_defaults(&cinfo); /* get default settings */

  /* Make optional parameter settings here */
  if (quality<1) quality = 1;  /* constrain range of quality factors */
  if (quality>100) quality = 100;
  jpeg_set_quality (&cinfo, quality, TRUE); /* set quality factor */

  /* initialize compression */
  jpeg_start_compress(&cinfo, TRUE);

  *ierr = 0; /* OK */
} /* end of jpgini */

void jpgwri (float *data, float blank, int *ierr)
/*--------------------------------------------------------------------*/
/*  Write row of a jpeg image, floating values scaled and converted   */
/*  as specified to jpgini.  Grayscale only.                          */
/*  Only does gray scale at present                                   */
/*  Pure black reserved for blanked pixels.                           */
/*  Inputs:                                                           */
/*     data    floating values                                        */
/*     blank   value of undefined pixel                               */
/*  Output:                                                           */
/*     ierr     0.0 => OK                                             */
/*--------------------------------------------------------------------*/
{
  int i, icol, maxcolor=255;
  float val, irange, c1, c2;
  double arg;

  /* scaling parameters */
  /*
   irange = vmax - vmin;
   if (fabs(irange)<1.0e-25)
   	  irange = 1.0;
   else
      irange = 1.0 / irange;

   c1 = (maxcolor - 1.0) * irange;
   c2 = vmin * c1 - 0.5;
  */

  // get vmax and vmin from image histogram

  if(nonlinear) {
    c1 = maxcolor / log10(vmax - vmin + 1.0);
  } else {
    c1 = maxcolor / (vmax - vmin + 1.0);
  }

  /* convert row */
  for (i=0;i<nx;i++) {
    val = data[i];
    if (val==blank) { /* blanked */
      idata[i] = 0;
    }
    else
      { /* non blanked */
	if (val<vmin) val=vmin;
	if (val>vmax) val=vmax;
	if (nonlinear)  {/* nonlinear */
	  icol = log10(val - vmin + 1) * c1;
	  //arg = ((val-vmin) * irange);
	  //icol =  0.5 + ((maxcolor-1.0) * log10(arg));
	}
	else  /* Linear */
	  icol = (val - vmin + 1) * c1;
	  //icol = c1 * val - c2;

	if (icol<1) icol = 1;  /* minimum color = 1 */
	if (icol>=maxcolor) icol = maxcolor-1;
	idata[i] = GETJSAMPLE(icol);
      }
  } /* end loop over row pixels */

  row_pointer[0] = (JSAMPROW)idata; /* set row pointer */

  /* compress/write row */
  jpeg_write_scanlines(&cinfo, row_pointer, 1);

  *ierr = 0; /* OK */
} /* end of jpgwri */

void jpgclo (int *ierr)
/*--------------------------------------------------------------------*/
/*  Close/flush i/o to jpeg image file                                */
/*  Output:                                                           */
/*     ierr     0.0 => OK                                             */
/*--------------------------------------------------------------------*/
{
  /* finish compression/ flush output */
  jpeg_finish_compress(&cinfo);

  /* close output file */
  if (outfile) fclose(outfile);
  outfile = NULL;

  jpeg_destroy_compress(&cinfo); /* delete jpeg structures */

  /* delete file structures: file name */
  if (name) free(name);
  /* row buffer */
  if (idata) free(idata);

  *ierr = 0; /* OK */
} /* end of jpgclo */

