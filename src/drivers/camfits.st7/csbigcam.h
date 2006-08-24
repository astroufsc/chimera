/*

	csbigcam.h - Contains the interface to the csbigcam
				 camera class

	1. This software (c)2004 Santa Barbara Instrument Group.
	2. This free software is provided as an example of how 
	   to communicate with SBIG cameras.  It is provided AS-IS
	   without any guarantees by SBIG of suitability for a 
	   particular purpose and without any guarantee to be 
	   bug-free.  If you use it you agree to these terms and
	   agree to do so at your own risk.
    3. Any distribution of this source code to include these
	   terms.
	
*/
#ifndef _CSBIGCAM_
#define _CSBIGCAM_

#ifndef _PARDRV_
 #include "sbigudrv.h"
#endif

#ifndef _CSBIGIMG_
 #include "csbigimg.h"
#endif

#include <string>
using namespace std;

typedef enum {RELAY_XPLUS, RELAY_XMINUS, RELAY_YPLUS, RELAY_YMINUS } CAMERA_RELAY;
typedef enum {SBDF_LIGHT_ONLY, SBDF_DARK_ONLY, SBDF_DARK_ALSO } SBIG_DARK_FRAME;

class CSBIGCam {
private:
	PAR_ERROR m_eLastError;
	PAR_COMMAND m_eLastCommand;
	short m_nDrvHandle;
	CAMERA_TYPE m_eCameraType;
	CCD_REQUEST m_eActiveCCD;
	double m_dExposureTime;
	unsigned short m_uReadoutMode;
	ABG_STATE7 m_eABGState;

public:
	// Constructors/Destructors
	CSBIGCam();
	CSBIGCam(OpenDeviceParams odp);
	CSBIGCam(SBIG_DEVICE_TYPE dev);
	~CSBIGCam();
	void Init();

	// Error Reporting Routines
	PAR_ERROR GetError();
	string GetErrorString();
	string GetErrorString(PAR_ERROR err);
	PAR_COMMAND GetCommand();

	// Accessor Functions
	double GetExposureTime(void) { return m_dExposureTime; }
	void SetExposureTime(double exp) { m_dExposureTime = exp; }
	CCD_REQUEST GetActiveCCD(void) { return m_eActiveCCD; }
	void SetActiveCCD(CCD_REQUEST ccd) { m_eActiveCCD = ccd; }
	unsigned short GetReadoutMode(void) { return m_uReadoutMode; }
	void SetReadoutMode(unsigned short rm) { m_uReadoutMode = rm; }
	CAMERA_TYPE GetCameraType(void) { return m_eCameraType; }
	ABG_STATE7 GetABGState(void) { return m_eABGState; }
	void SetABGState(ABG_STATE7 abgState) { m_eABGState = abgState; }

	// Driver/Device Routines
	PAR_ERROR OpenDriver();
	PAR_ERROR CloseDriver();
	PAR_ERROR OpenDevice(OpenDeviceParams odp);
	PAR_ERROR CloseDevice();
	PAR_ERROR GetDriverInfo(DRIVER_REQUEST request, GetDriverInfoResults0 &gdir);

	// High-Level Exposure Related Commands
	PAR_ERROR GrabImage(CSBIGImg *pImg, SBIG_DARK_FRAME dark);

	// Low-Level Exposure Related Commands
	PAR_ERROR StartExposure(SHUTTER_COMMAND shutterState);
	PAR_ERROR EndExposure(void);
	PAR_ERROR IsExposureComplete(MY_LOGICAL &complete);
	PAR_ERROR StartReadout(StartReadoutParams srp);
	PAR_ERROR EndReadout(void);
	PAR_ERROR ReadoutLine(ReadoutLineParams rlp, MY_LOGICAL darkSubtract, unsigned short *dest);
	PAR_ERROR DumpLines(unsigned short noLines);

	//Temperature Related Commands
	PAR_ERROR GetCCDTemperature(double &ccdTemp);
	PAR_ERROR SetTemperatureRegulation(MY_LOGICAL enable, double setpoint);
	PAR_ERROR QueryTemperatureStatus(MY_LOGICAL &enabled, double &ccdTemp,
		double &setpointTemp, double &percentTE);

	// Control Related Commands
	PAR_ERROR ActivateRelay(CAMERA_RELAY relay, double time);
	PAR_ERROR AOTipTilt(AOTipTiltParams attp);
	PAR_ERROR CFWCommand(CFWParams cfwp, CFWResults &cfwr);

	// General Purpose Commands
	PAR_ERROR EstablishLink(void);
	string GetCameraTypeString(void);

	// Utility functions
	MY_LOGICAL CheckLink(void);
	unsigned short DegreesCToAD(double degC, MY_LOGICAL ccd = TRUE);
	double ADToDegreesC(unsigned short ad, MY_LOGICAL ccd = TRUE);

	// Allows access directly to driver
	PAR_ERROR SBIGUnivDrvCommand(short command, void *Params, void *Results);
};

#endif /* #ifndef _CSBIGCAM_ */
