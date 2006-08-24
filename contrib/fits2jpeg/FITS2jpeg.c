/*-----------------------------------------------------------------------*/
/*  Copyright (C) 1996                                                   */
/*  Associated Universities, Inc. Washington DC, USA.                    */
/*  This program is free software; you can redistribute it and/or        */
/*  modify it under the terms of the GNU General Public License as       */
/*  published by the Free Software Foundation; either version 2 of       */
/*  the License, or (at your option) any later version.                  */
/*                                                                       */
/*  This program is distributed in the hope that it will be useful,      */
/*  but WITHOUT ANY WARRANTY; without even the implied warranty of       */
/*  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the        */
/*  GNU General Public License for more details.                         */
/*                                                                       */
/*  You should have received a copy of the GNU General Public            */
/*  License along with this program; if not, write to the Free           */
/*  Software Foundation, Inc., 675 Massachusetts Ave, Cambridge,         */
/*  MA 02139, USA.                                                       */
/*                                                                       */
/*  Correspondence concerning FITS2jpeg should be addressed as follows:  */
/*         Internet email: bcotton@nrao.edu.                             */
/*         Postal address: William Cotton                                */
/*                         National Radio Astronomy Observatory          */
/*                         520 Edgemont Road                             */
/*                         Charlottesville, VA 22903-2475 USA            */
/*-----------------------------------------------------------------------*/
#include "jpegsubs.h"
#include "fitsio.h"
#include <math.h>
#include <malloc.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

/* global variables */
char *infile;          /* input FITS file name */
char *outfile;         /* output jpeg file name */
float *DataArray=NULL; /* image data as 1-D array */
float fblank;          /* undefined pixel value */
float vmax,vmin;       /* Max. and Min. values to be displayed */
int  NonLinear;        /* if true then nonlinear transfer fn. */
int  quality;          /* jpeg quality factor [1-100] */
int  GotMaxMin;        /* if true then already have max/min to display */
int  naxis;            /* number of axes */
long inaxes[7];        /* dimensions of axes */
fitsfile *fptr;        /* cfitsio i/o file pointer */

/* internal prototypes */
void jpgfin (int argc, char **argv, int *ierr);
void Usage(void);
void jpegim (int *ierr);
void gethed (int *ierr);
void gtinfo (int *ierr);
void getdat (int *ierr);
int get_histogram_region(float* img, int size, float start, float end, int* startValue, int* endValue);
/*----------------------------------------------------------------------- */
/*   Program to convert a FITS image to a jpeg file */
/*----------------------------------------------------------------------- */
int main ( int argc, char **argv )
{
  int  iret;
/*                                       Startup */
  jpgfin (argc, argv, &iret);
  if (iret!=0) return iret;
/*                                       Convert to jpeg */
  jpegim(&iret);
  return iret;
} /* end of main */

void jpgfin (int argc, char **argv, int *ierr)
/*----------------------------------------------------------------------- */
/*  Parse control info from command line */
/*   Input: */
/*      argc   Number of arguments from command line */
/*      argv   Array of strings from command line */
/*   Output: */
/*      ierr       Error code: 0 => ok */
/*      infile     FITS file name */
/*      NonLinear  True if nonlinear function desired. */
/*      vmax, vmin Max and min values(image units) to be displayed */
/*----------------------------------------------------------------------- */
{
  int ax;
  char *arg;

/* copyright to get it into the executable */
char *copyright="Copyright 1996 NRAO/AUI";

  /*                                       Set undefined value */
  fblank = 1.234567e25;
  vmax = fblank;
  vmin = fblank;
  infile = NULL;
  outfile = NULL;
  NonLinear = 0;
  quality = 100;

  if (argc<=1) Usage(); /* must have arguments */
/* parse command line */
  for (ax=1; ax<argc; ax++) {
    arg = argv[ax];
    if (strcmp(arg, "-fits") == 0) {
      infile = argv[++ax];
    }
    else if (strcmp(arg, "-jpeg") == 0) {
      outfile = argv[++ax];
    }
    else if (strcmp(arg, "-nonLinear") == 0) {
      NonLinear = 1;
    }
    else if (strcmp(arg, "-max") == 0) {
      vmax = strtod(argv[++ax], (char **)NULL);
    }
    else if (strcmp(arg, "-min") == 0) {
      vmin = strtod(argv[++ax], (char **)NULL);
    }
    else if (strcmp(arg, "-quality") == 0) {
      quality = strtol(argv[++ax], (char **)NULL, 0);
    }
    else { /* unknown argument */
      Usage();
    }
  }

  /*  Max/min specified ? check defaults*/
  if ((vmax==fblank) && (vmin!=fblank)) vmax = 1.0e30;
  if ((vmin==fblank) && (vmax!=fblank)) vmin= -1.0e30;
  if ((vmax!=fblank) && (vmin!=fblank)) GotMaxMin = 1;

  /* must specify files */
  if (!infile) Usage();
  if (!outfile) Usage();
  *ierr = 0;
} /* end jpgfin */

void Usage()
/*----------------------------------------------------------------------- */
/*   Tells about usage of program and bails out */
/*----------------------------------------------------------------------- */
{
    fprintf(stderr, "Usage: fits2jpeg -fits input_file -jpeg output_file [options]\n");
    fprintf(stderr, "Options:\n");
    fprintf(stderr, "       -nonLinear\n");
    fprintf(stderr, "       -max max_image_value\n");
    fprintf(stderr, "       -min min_image_value\n");
    fprintf(stderr, "       -quality image_quality [1-100]\n");
    
    exit(1); /* bail out */
  }/* end Usage */

void jpegim (int *ierr)
/*----------------------------------------------------------------------- */
/*   Copy FITS file  to jpeg */
/*   Inputs in common: */
/*      infile    Input FITS file name */
/*      outfil    Output jpeg file name */
/*   Output: */
/*      ierr      Error code: 0 => ok */
/*----------------------------------------------------------------------- */
{
  int   iptr, nrow, lrow, irow, i, iln, nx, ny, donon, lname;

  *ierr = 0;
/*                                       Open */
  if ( fits_open_file(&fptr, infile, READONLY, ierr) ) {
    fprintf(stderr,"ERROR  opening input FITS file %s \n", infile);
    *ierr = 1;
    return;
  }
/*                                       Get header information */
  gethed (ierr);
  if (*ierr!=0) {
    fprintf(stderr,"ERROR getting FITS file header info \n");
    return;
  }
/*                                       Read FITS image */
  getdat (ierr);
  if (*ierr!=0) {
    fprintf(stderr,"ERROR getting image pixel values \n");
    return;
  }
/*                                       Close FITS file */
  fits_close_file (fptr, ierr);
/*                                       Initialize output */
  nx = inaxes[0];
  ny = inaxes[1];
  jpgini (outfile, nx, ny, vmax, vmin, NonLinear, quality, ierr);
  if (*ierr!=0) {
    fprintf(stderr,"error %d initializing jpeg output \n", 
	    *ierr);
    return;
  }

/*                                       Write, loop over image */
/*                             write backwards to get right side up */
  lrow = inaxes[0];
  nrow = inaxes[1];
  iptr = (nrow-1) * lrow;
  irow = nrow;
  for (i=0;i<nrow;i++) {
    jpgwri(&DataArray[iptr], fblank, ierr);
    if (*ierr!=0) {
      fprintf(stderr,"ERROR %d compressing/writing row %d \n", 
	      *ierr, irow);
      return;
    }
    iptr = iptr - lrow;
    irow = irow - 1;
  } /* end loop writing rows */
/*                                       Close output */
  jpgclo (ierr);
    if (*ierr!=0) {
      fprintf(stderr,"ERROR %d closing output \n", *ierr);
      return;
    }
} /* end jpegim */

void gethed (int *ierr)
/*----------------------------------------------------------------------- */
/*   Get information from fits header */
/*   Inputs in common: */
/*      fptr     Input FITS fitsio unit number */
/*   Output: */
/*      ierr     Error code: 0 => ok */
/*----------------------------------------------------------------------- */
{
  int bitpix, simple, extend, maxdim=7;
  long pcount, gcount;

  fits_read_imghdr (fptr, maxdim, &simple, &bitpix, &naxis, inaxes,
	  &pcount, &gcount, &extend, ierr);
  if (*ierr!=0) {
    fprintf(stderr,"fits_read_imghdr error %d reading FITS header \n", *ierr);
    return;
  }
/*                                      Max/min if necessary */
  gtinfo (ierr);
  if (*ierr!=0) {
    fprintf(stderr,"gtinfo error %d reading FITS header \n", *ierr);
    return;
  }
} /* end gethed */

void gtinfo (int *ierr)
/*----------------------------------------------------------------------- */
/*   Read FITS header info from INUNIT and save in common */
/*   Inputs in common: */
/*      fptr      Input FITS fitsio unit number */
/*      GotMaxMin   If true already have Max and Min values */
/*   Output: */
/*      ierr        Error code: 0 => ok */
/*   Output in common: */
/*      vmax        Maximum image value */
/*      vmin        Minimum image value */
/*      GotMaxMin   If true already have Max and Min values */
/*----------------------------------------------------------------------- */
{
  char commnt[81];
  float tmax=0.0, tmin=0.0;
  int GotMax=0, GotMin=0;
/*                                          Read keyword values */
  fits_read_key_flt (fptr, "DATAMAX", &tmax, commnt, ierr);
  GotMax = (*ierr==0);
  if (*ierr==202) *ierr = 0;
  fits_read_key_flt (fptr, "DATAMIN", &tmin, commnt, ierr);
  GotMin = (*ierr==0);
  if (*ierr==202) *ierr = 0;
  if (*ierr!=0) {
    fprintf(stderr,"ERROR reading input FITS header \n");
    return;
  }
  if (GotMaxMin) {
/*                                          Don't put vmax,vmin outside */
/*                                          of actual range */
    if (GotMin && (vmin<tmin)) vmin = tmin;
    if (GotMin && (vmax>tmax)) vmax = tmax;
  }
  else if (GotMin && GotMax) {
    GotMaxMin = 1;
    vmax = tmax;
    vmin = tmin;
  }
*ierr = 0; /* OK */
} /* end gtinfo */

void getdat (int *ierr)
/*----------------------------------------------------------------------- */
/*   Read FITS file and determine max. and min. values */
/*   Inputs in common: */
/*      fptr    Input FITS fitsio unit number */
/*   Output: */
/*      ierr  I    Error code: 0 => ok */
/*   Output in common: */
/*      vmax    Maximum image value */
/*      vmin    Minimum image value */
/*      GotMaxMin    If true already have Max and Min values */
/*----------------------------------------------------------------------- */
{
  long size,incs[7]={1,1,1,1,1,1,1},blc[7]={1,1,1,1,1,1,1},trc[7];
  int group=0, i, anyf;
  float tmax,tmin;
  int s_max, s_min;

/* How big is the array? */
  size = inaxes[0];
  size = size * inaxes[1];
/* allocate floating array */
  if (DataArray) free(DataArray); /* free any old allocations */
  DataArray = (float*)malloc(sizeof(float)*size);
  if (!DataArray) { /* cannot allocate */
    fprintf(stderr,"Cannot allocate memory for image array \n");
    *ierr = 1;
    return;
  }
/*                                       Take all of image */
  trc[0] = inaxes[0];
  trc[1] = inaxes[1];
/*                                       but only first plane */
  for (i=2;i<naxis;i++) trc[i] = 1;
/*                                       Read selected portion of input */
  fits_read_subset_flt (fptr, group, naxis, inaxes, blc, trc, incs,
	fblank, DataArray, &anyf, ierr);
  if (*ierr!=0) {
    fprintf(stderr,"fits_read_subset_flt error reading input file \n");
    return;
  }

  get_histogram_region(DataArray, size, 10, 98, &s_min, &s_max);

  vmin = s_min;
  vmax = s_max;
  GotMaxMin = 1;

/*                                      Update data max, min */
/*   tmin = 1.0e20; */
/*   tmax = -1.0e20; */
/*   for (i=0;i<size;i++) { */
/*     if ((!anyf) || (DataArray[i]!=fblank)) { */
/*       if (DataArray[i]>tmax) tmax = DataArray[i]; */
/*       if (DataArray[i]<tmin) tmin = DataArray[i]; */
/*     } */
/*   } */
/*   if (GotMaxMin) { */
/* /\*                                          Don't put vmax,vmin outside *\/ */
/* /\*                                          of actual range *\/ */
/*     if (vmin<tmin) vmin = tmin; */
/*     if (vmax>tmax) vmax = tmax; */
/*   } */
/*   else { /\* set to full range *\/ */
/*     GotMaxMin = 1; */
/*     vmax = tmax; */
/*     vmin = tmin; */
/*   } */
} /* end getdat */

int get_histogram_region(float* img, int size, float start, float end, int* startValue, int* endValue) {

  int startTarget, endTarget;
  int default_max = (2<<15) -1;
  int sum = 0;
  int i;
  int* histo = (int *)calloc(default_max, sizeof(int));

  startTarget = (start/100) * size;
  endTarget = (end/100) * size;

  for (i = 0; i < size; i++) {
      histo[(int)truncf(img[i])]++;
  }

/*   printf("%d %f %f %d %d\n", size, start, end, startTarget, endTarget); */

/*   for (i = 0; i < default_max; i++) { */
/*       printf("%d\n", histo[i]); */
/*   } */

  for (i = 0; i < default_max; i++) {

    sum += histo[i];

    if ( (sum < startTarget) && (startTarget < (sum + histo[i+1])) )
      *startValue = i;

    if ( (sum < endTarget) && (endTarget < (sum + histo[i+1])) )
      *endValue = i;

  }

  return 1;

}
