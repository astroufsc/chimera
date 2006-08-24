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

/* $Id: ccdcap.h,v 1.1.2.1 2006/05/17 16:32:33 henrique Exp $ */

#ifndef _CCD_CAP_H_
#define _CCD_CAP_H_ 1

#include <string>
#include <vector>

struct ReadoutMode {
  unsigned short width;
  unsigned short height;
  unsigned long pixelWidth;
  unsigned long pixelHeight;
  unsigned short gain;
  unsigned short modeFlag;
};

class CCDCap {

 public:

  CCDCap() { loadData(); };
  virtual ~CCDCap() { };

  virtual int loadData() { return 1; };

  std::string ccdModel() const { return _ccdModel; }
  std::string ccdSubModel() const { return _ccdSubModel; }
  std::string ccdMaker() const { return _ccdMaker; }

  bool fullFrame() const { return _fullFrame; }
  bool frameTransfer() const { return _frameTransfer; }
  bool interline() const { return _interline; }
  bool shutter() const { return _shutter; }
  bool antiBlooming() const { return _antiBlooming; }

  unsigned short firmwareVersion() const { return _firmwareVersion; } 

  int nReadoutModes() const { return _nReadoutModes; }

  const std::vector<ReadoutMode*>& readoutModes() const { return _readoutModes; }

 
protected:

  std::string _ccdModel;
  std::string _ccdSubModel;
  std::string _ccdMaker;

  bool _fullFrame;
  bool _frameTransfer;
  bool _interline;
  bool _shutter;
  bool _antiBlooming;

  unsigned short _firmwareVersion;

  int _nReadoutModes;

  std::vector<ReadoutMode*> _readoutModes;

};

#endif // !_CAM_CAP_H_
