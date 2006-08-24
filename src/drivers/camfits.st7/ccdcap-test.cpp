/*
 * camfits.st7 - SBIG ST 7/8 Controller
 * Copyright (C) 2005 Paulo Henrique Silva
 *
 * This file is part of camfits.st7
 * camfits.st7 is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * camfits.st7 is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA
 *
 */

/* $Id: ccdcap-test.cpp,v 1.1.2.1 2006/05/17 16:32:41 henrique Exp $ */

#include "sbigudrv.h"
#include "sbigcamcap.h"

#include <stdio.h>

void cameraDump(const CCDCap& cap) {

  printf("%s\n===\n", cap.ccdModel().c_str());

  int n = cap.nReadoutModes();
  const vector<ReadoutMode*> rmodes = cap.readoutModes();
  
  for(int i = 0; i < n; i++) {
    printf("%20s : %hd\n"
	   "%20s : %hd pixel\n"
	   "%20s : %hd pixel\n"
	   "%20s : %0x um\n"
	   "%20s : %0x um\n"
	   "%20s : %0x e-/ADU\n\n", "Mode", rmodes[i]->modeFlag, "Width", rmodes[i]->width, "Height", rmodes[i]->height,
	   "Pixel Width", rmodes[i]->pixelWidth, "Pixel Height", rmodes[i]->pixelHeight, "Gain", rmodes[i]->gain);
  }	

  printf("%20s : %d\n"
	 "%20s : %d\n"
	 "%20s : %d\n"
	 "%20s : %d\n\n", "Full Frame", cap.fullFrame(), "Fraame Transfer", cap.frameTransfer(),
	 "Interline", cap.interline(), "Shutter", cap.shutter());

  printf("%20s : %0x\n", "Firmware Version", cap.firmwareVersion());

}

int main() {

  CSBIGCam *cam = new CSBIGCam(DEV_LPT1);

  PAR_ERROR err;

  err = cam->EstablishLink();
  if (err != CE_NO_ERROR) {
    printf("Error linking to camera.\n");
    delete cam;
    exit(1);
  }

  CCDCap img = SBIGCamCap(cam, CCD_IMAGING);
  CCDCap track= SBIGCamCap(cam, CCD_TRACKING);

  cameraDump(img);

  printf("\n");

  cameraDump(track);

  return 0;


}
