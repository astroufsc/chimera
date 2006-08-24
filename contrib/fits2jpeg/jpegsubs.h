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
#include <math.h>
#include <malloc.h>
#include <string.h>
#include <stdio.h>
#include <sys/types.h>
#include "jpeglib.h"
#ifndef JPEGSUBS_H 
#define JPEGSUBS_H 

/*          includes for JPEG routines                                */

/* initialize jpeg output file */
void jpgini (char *name, int nx, int ny, float vmax,  float vmin, 
	     int nonLin, int quality, int *ierr);
/* write row in jpeg image */
void jpgwri (float *data, float blank, int *ierr);
/* close jpeg image */
void jpgclo (int *ierr);

#endif /* JPEGSUBS_H */ 
