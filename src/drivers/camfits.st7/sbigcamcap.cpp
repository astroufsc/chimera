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

/* $Id: sbigcamcap.cpp,v 1.1.2.1 2006/05/17 16:32:34 henrique Exp $ */

#include "sbigcamcap.h"
#include "csbigcam.h"

using namespace std;

int SBIGCamCap::loadData() {

  if(ccd == CCD_IMAGING) {
    infoPars.request = 0;
  } else if(ccd == CCD_TRACKING) {
    infoPars.request = 1;
  }

  if(cam->SBIGUnivDrvCommand(CC_GET_CCD_INFO, &infoPars, &infoRes0) == CE_NO_ERROR) {

    _ccdModel = infoRes0.name;
    _ccdMaker = "SBIG";
    _ccdSubModel = "";

    _nReadoutModes = infoRes0.readoutModes;

    for(int i = 0; i < _nReadoutModes; i++) {
      ReadoutMode* m = new ReadoutMode;
      m->width = infoRes0.readoutInfo[i].width;
      m->height = infoRes0.readoutInfo[i].height;
      m->pixelWidth = infoRes0.readoutInfo[i].pixelWidth;
      m->pixelHeight = infoRes0.readoutInfo[i].pixelHeight;
      m->gain = infoRes0.readoutInfo[i].gain;
      m->modeFlag = infoRes0.readoutInfo[i].mode;

      _readoutModes.push_back(m);

    }

    _firmwareVersion = infoRes0.firmwareVersion;

  } else {
    return 1;
  }

  infoPars.request = 2;

  if(cam->SBIGUnivDrvCommand(CC_GET_CCD_INFO, &infoPars, &infoRes2) == CE_NO_ERROR) {

    _antiBlooming = infoRes2.imagingABG;

  } else {
    return 1;
  }

  if(ccd == CCD_IMAGING) {
    infoPars.request = 4;
  } else if(ccd == CCD_TRACKING) {
    infoPars.request = 5;
  }

  if(cam->SBIGUnivDrvCommand(CC_GET_CCD_INFO, &infoPars, &infoRes4) == CE_NO_ERROR) {

    unsigned short capbits;

    capbits = infoRes4.capabilitiesBits & CB_CCD_TYPE_MASK;

    _fullFrame = (((capbits) & (CB_CCD_TYPE_FULL_FRAME)) != 0);
    _frameTransfer = (((capbits) & (CB_CCD_TYPE_FRAME_TRANSFER)) != 0);

    capbits = infoRes4.capabilitiesBits & CB_CCD_ESHUTTER_MASK;

    _interline = (((capbits) & (CB_CCD_ESHUTTER_YES)) != 0);
    _shutter = (((capbits) & (CB_CCD_ESHUTTER_NO)) != 0);

  } else {
    return 1;
  }

}
