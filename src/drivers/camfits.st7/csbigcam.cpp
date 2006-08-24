/*

	csbigcam.cpp - Contains the code for the sbigcam class

	1. This software (c)2004 Santa Barbara Instrument Group.
	2. This free software is provided as an example of how 
	   to communicate with SBIG cameras.  It is provided AS-IS
	   without any guarantees by SBIG of suitability for a 
	   particular purpose and without any guarantee to be 
	   bug-free.  If you use it you agree to these terms and
	   agree to do so at your own risk.
    3. Any distribution of this source code to include these
	   terms.
	
	Revision History
	Date		Modification
	=========================================================
	1/26/04		Initial release

*/
#include "sbigudrv.h"
#include "csbigcam.h"
#include "csbigimg.h"
#include <string>
#include <math.h>

using namespace std;

#ifndef INVALID_HANDLE_VALUE
 #define INVALID_HANDLE_VALUE -1
#endif

/*

	Temperature Conversion Constants
	Defined in the SBIG Universal Driver Documentation

*/
#define T0      25.0
#define R0       3.0
#define DT_CCD  25.0
#define DT_AMB  45.0
#define RR_CCD   2.57
#define RR_AMB   7.791
#define RB_CCD  10.0
#define RB_AMB   3.0
#define MAX_AD  4096

/*

	hex2double:

	Convert the passed hex value to double.
	The hex value is assumed to be in the
	format: XXXXXX.XX

*/
static double hex2double(unsigned long ul)
{
	double res, mult;
	int i;

	res = 0.0;
	mult = 1.0;
	for (i=0; i<8; i++)
	{
		res += mult * (double)(ul & 0x0F);
		ul >>= 4;
		mult *= 10.0;
	}
	return res / 100.0;

}

/*

	Init:

	Initialize the base variables.

*/
void CSBIGCam::Init()
{
	m_eLastError = CE_NO_ERROR;
	m_eLastCommand = CC_NULL;
	m_nDrvHandle = INVALID_HANDLE_VALUE;
	m_eCameraType = NO_CAMERA;
	m_eActiveCCD = CCD_IMAGING;
	m_dExposureTime = 1.0;
	m_uReadoutMode = 0;
	m_eABGState = ABG_CLK_MED7;
}

/*

	GetCameraTypeString:

	Return a string describing the model camera
	that has been linked to.

*/
//typedef enum { ST7_CAMERA=4, ST8_CAMERA, ST5C_CAMERA, TCE_CONTROLLER,
//  ST237_CAMERA, STK_CAMERA, ST9_CAMERA, STV_CAMERA, ST10_CAMERA,
//  ST1K_CAMERA, ST2K_CAMERA, STL_CAMERA, STF_CAMERA, NEXT_CAMERA, NO_CAMERA=0xFFFF } CAMERA_TYPE;
static const char *CAM_NAMES[] = {
	"Type 0", "Type 1", "Type 2", "Type 3",
	"ST-7", "ST-8", "ST-5C", "TCE",
	"ST-237", "ST-K", "ST-9", "STV", "ST-10",
	"ST-1K", "ST-2K", "ST-L", "ST-F" };
string CSBIGCam::GetCameraTypeString(void)
{
	string s;
	GetCCDInfoParams gcip;
	GetCCDInfoResults0 gcir;
	char *p1, *p2;

    if ( m_eCameraType < (CAMERA_TYPE)(sizeof(CAM_NAMES)/sizeof(const char *)) ) {
		// default name
		s = CAM_NAMES[m_eCameraType];

		// see if ST-237A and if so indicate it in the name
		if ( m_eCameraType == ST237_CAMERA ) {
			gcip.request = CCD_INFO_IMAGING;
			if ( SBIGUnivDrvCommand(CC_GET_CCD_INFO, &gcip, &gcir) == CE_NO_ERROR )
				if ( gcir.readoutInfo[0].gain >= 0x100 )
					s += "A";
		}

 		// include the ST-L sub-models
    	if ( m_eCameraType == STL_CAMERA ) {
    		gcip.request = CCD_INFO_IMAGING;
    		if ( SBIGUnivDrvCommand(CC_GET_CCD_INFO, &gcip, &gcir) == CE_NO_ERROR ) {
				// driver reports name as "SBIG ST-L-XXX..."
    			p1 = gcir.name + 5;
    			if ( (p2 = strchr(p1,' ')) != NULL ) {
    				*p2 = 0;
    				s = p1;
    			}
    		}
    	}
	}
	else if ( m_eCameraType == NO_CAMERA )
		s = "No Camera";
	else
		s = "Unknown";
	return s;
}


/*

	CSBIGCam:

	Stamdard constructor.  Initialize appropriate member variables.

*/
CSBIGCam::CSBIGCam()
{
	Init();
}

/*

	CSBIGCam:

	Alternate constructor.  Init the vars, Open the driver and then
	try to open the passed device.

	If you want to use the Ethernet connection this is the best
	constructor.  If you're using the LPT or USB connections
	the alternate constructor below may make more sense.

*/
CSBIGCam::CSBIGCam(OpenDeviceParams odp)
{
	Init();
	if ( OpenDriver() == CE_NO_ERROR )
		m_eLastError = OpenDevice(odp);
}

/*

	CSBIGCam:

	Alternate constructor.  Init the vars, Open the driver and then
	try to open the passed device.

	This won't work the Ethernet port because no IP address
	is specified.  Use the constructor above where you can
	pass the OpenDeviceParams struct.

*/
CSBIGCam::CSBIGCam(SBIG_DEVICE_TYPE dev)
{
	OpenDeviceParams odp;

	Init();
	if ( dev == DEV_ETH )
		m_eLastError = CE_BAD_PARAMETER;
	else {
		odp.deviceType = dev;
		if ( OpenDriver() == CE_NO_ERROR )
			m_eLastError = OpenDevice(odp);
	}
}


/*

	~CSBIGCam:

	Standard destructor.  Close the device then the driver.

*/
CSBIGCam::~CSBIGCam()
{
	CloseDevice();
	CloseDriver();
}

/*

	GetError:

	Return the error generated in the previous driver call.

*/
PAR_ERROR CSBIGCam::GetError()
{
	return m_eLastError;
}

/*

	GetCommand:

	Return the command last passed to the driver.

*/
PAR_COMMAND CSBIGCam::GetCommand()
{
	return m_eLastCommand;
}

/*

	SBIGUnivDrvCommand:

	Bottleneck function for all calls to the driver that logs
	the command and error. First it activates our handle and
	then it calls the driver.  Activating the handle first
	allows having multiple instances of this class dealing
	with multiple cameras on different communications port.

	Also allows direct access to the SBIG Universal Driver after
	the driver has been opened.

*/
PAR_ERROR CSBIGCam::SBIGUnivDrvCommand(short command, void *Params, void *Results)
{
	SetDriverHandleParams sdhp;

	// make sure we have a valid handle to the driver
	m_eLastCommand = (PAR_COMMAND)command;
	if ( m_nDrvHandle == INVALID_HANDLE_VALUE )
		m_eLastError = CE_DRIVER_NOT_OPEN;
	else
	{
		// handle is valid so install it in the driver
		sdhp.handle = m_nDrvHandle;
		if ( (m_eLastError = (PAR_ERROR)::SBIGUnivDrvCommand(CC_SET_DRIVER_HANDLE, &sdhp, NULL)) == CE_NO_ERROR )
			// call the desired command
			m_eLastError = (PAR_ERROR)::SBIGUnivDrvCommand(command, Params, Results);
	}
	return m_eLastError;
}

/*

	OpenDriver:

	Open the driver.  Must be made before any other calls and
	should be called only once per instance of the camera class.
	Based on the results of the open call to the driver this can
	open a new handle to the driver.

	The alternate constructors do this for you when you specify
	the communications port to use.

*/
PAR_ERROR CSBIGCam::OpenDriver()
{
	short res;
	GetDriverHandleResults gdhr;
	SetDriverHandleParams sdhp;

	// call the driver directly so doesn't install our handle
	res = ::SBIGUnivDrvCommand(m_eLastCommand = CC_OPEN_DRIVER, NULL, NULL);
	if ( res == CE_DRIVER_NOT_CLOSED )
	{
		/*
			the driver is open already which we interpret
			as having been opened by another instance of
			the class so get the driver to allocate a new
			handle and then record it
		*/
		sdhp.handle = INVALID_HANDLE_VALUE;
		res = ::SBIGUnivDrvCommand(CC_SET_DRIVER_HANDLE, &sdhp, NULL);
		if ( res == CE_NO_ERROR ) {
			res = ::SBIGUnivDrvCommand(CC_OPEN_DRIVER, NULL, NULL);
			if ( res == CE_NO_ERROR ) {
				res = ::SBIGUnivDrvCommand(CC_GET_DRIVER_HANDLE, NULL, &gdhr);
				if ( res == CE_NO_ERROR )
					m_nDrvHandle = gdhr.handle;
			}
		}
	}
	else if ( res == CE_NO_ERROR )
	{
		/*
			the driver was not open so record the driver handle
			so we can support multiple instances of this class
			talking to multiple cameras
		*/
		res = ::SBIGUnivDrvCommand(CC_GET_DRIVER_HANDLE, NULL, &gdhr);
		if ( res == CE_NO_ERROR )
			m_nDrvHandle = gdhr.handle;
	}
	return m_eLastError = (PAR_ERROR)res;
}

/*

	CloseDriver:

	Should be called for every call to OpenDriver.
	Standard destructor does this for you as well.
	Closing the Drriver multiple times won't hurt
	but will return an error.

	The destructor will do this for you if you
	don't do it explicitly.

*/
PAR_ERROR CSBIGCam::CloseDriver()
{
	PAR_ERROR res;

	res = SBIGUnivDrvCommand(CC_CLOSE_DRIVER, NULL, NULL);
	if ( res == CE_NO_ERROR )
		m_nDrvHandle = INVALID_HANDLE_VALUE;
	return res;
}

/*

	OpenDevice:

	Call once to open a particular port (USB, LPT,
	Ethernet, etc).  Must be balanced with a call
	to CloseDevice.

	Note that the alternate constructors will make
	this call for you so you don't have to do it
	explicitly.

*/
PAR_ERROR CSBIGCam::OpenDevice(OpenDeviceParams odp)
{
	return SBIGUnivDrvCommand(CC_OPEN_DEVICE, &odp, NULL);
}

/*

	CloseDevice:

	Closes which ever device was opened by OpenDriver.

	The destructor does this for you so you don't have
	to call it explicitly.

*/
PAR_ERROR CSBIGCam::CloseDevice()
{
	return SBIGUnivDrvCommand(CC_CLOSE_DEVICE, NULL, NULL);
}

/*

	GetErrorString:

	Return a string object describing the passed error code.

*/
string CSBIGCam::GetErrorString(PAR_ERROR err)
{
	GetErrorStringParams gesp;
	GetErrorStringResults gesr;
	string s;

	gesp.errorNo = err;
	SBIGUnivDrvCommand(CC_GET_ERROR_STRING, &gesp, &gesr);
	s = gesr.errorString;
	return s;
}

/*

	GetDriverInfo:

	Get the requested driver info for the passed request.
	This call only works with the DRIVER_STANDARD and
	DRIVER_EXTENDED requests as you pass it a result
	reference that only works with those 2 requests.
	For other requests simply call the
	SBIGUnivDrvCommand class function.

*/
PAR_ERROR CSBIGCam::GetDriverInfo(DRIVER_REQUEST request, GetDriverInfoResults0 &gdir)
{
	GetDriverInfoParams gdip;

	gdip.request = request;
	m_eLastCommand = CC_GET_DRIVER_INFO;
	if ( request > DRIVER_EXTENDED )
		return m_eLastError = CE_BAD_PARAMETER;
	else
		return SBIGUnivDrvCommand(CC_GET_DRIVER_INFO, &gdip, &gdir);
}

/*

	GrabImage:

	Grab an image into the passed image of the passed type.
	This does the whole processing for you: Starts
	and Ends the Exposure then Readsout the data.

*/
PAR_ERROR CSBIGCam::GrabImage(CSBIGImg *pImg, SBIG_DARK_FRAME dark)
{
	int height, width;
	GetCCDInfoResults0 gcir;
	GetCCDInfoParams gcip;
	double ccdTemp;
	unsigned short vertNBinning;
	unsigned short rm;
	string s;
	unsigned short es;
	MY_LOGICAL expComp;
	PAR_ERROR err;
	StartReadoutParams srp;
	int i;
	ReadoutLineParams rlp;

	// Get the image dimensions
	vertNBinning = m_uReadoutMode >> 8;
	if ( vertNBinning == 0 )
		vertNBinning = 1;
	rm = m_uReadoutMode & 0xFF;
	gcip.request = (m_eActiveCCD == CCD_IMAGING ? CCD_INFO_IMAGING : CCD_INFO_TRACKING);
	if ( SBIGUnivDrvCommand(CC_GET_CCD_INFO, &gcip, &gcir) != CE_NO_ERROR )
		return m_eLastError;
	if ( rm >= gcir.readoutModes )
		return CE_BAD_PARAMETER;
	width = gcir.readoutInfo[rm].width;
	height = gcir.readoutInfo[rm].height / vertNBinning;

	// try to allocate the image buffer
	if ( !pImg->AllocateImageBuffer(height, width) )
		return CE_MEMORY_ERROR;

	// initialize some image header params
	if ( GetCCDTemperature(ccdTemp) != CE_NO_ERROR )
		return m_eLastError;
	pImg->SetCCDTemperature(ccdTemp);
	pImg->SetEachExposure(m_dExposureTime);
	pImg->SetEGain(hex2double(gcir.readoutInfo[rm].gain));
	pImg->SetPixelHeight(hex2double(gcir.readoutInfo[rm].pixelHeight) *
		vertNBinning / 1000.0);
	pImg->SetPixelWidth(hex2double(gcir.readoutInfo[rm].pixelWidth) / 1000.0);
	es = ES_DCS_ENABLED | ES_DCR_DISABLED | ES_AUTOBIAS_ENABLED;
	if ( m_eCameraType == ST5C_CAMERA )
		es |= (ES_ABG_CLOCKED | ES_ABG_RATE_MED);
	else if ( m_eCameraType == ST237_CAMERA )
		es |= (ES_ABG_CLOCKED | ES_ABG_RATE_FIXED);
	else if ( m_eActiveCCD == CCD_TRACKING )
		es |= (ES_ABG_CLOCKED | ES_ABG_RATE_MED);
	else
		es |= ES_ABG_LOW;
	pImg->SetExposureState(es);
	pImg->SetExposureTime(m_dExposureTime);
	pImg->SetNumberExposures(1);
	pImg->SetReadoutMode(m_uReadoutMode);
	s = GetCameraTypeString();
	if ( m_eCameraType == ST5C_CAMERA || ( m_eCameraType == ST237_CAMERA &&
	  s.find("ST-237A", 0) == string::npos) )
		pImg->SetSaturationLevel(4095);
	else
		pImg->SetSaturationLevel(65535);
	s = gcir.name;
	pImg->SetCameraModel(s);

	// end any exposure in case one in progress
	EndExposure();
	if ( m_eLastError != CE_NO_ERROR && m_eLastError != CE_NO_EXPOSURE_IN_PROGRESS )
		return m_eLastError;

	// start the exposure
	if ( StartExposure(dark == SBDF_LIGHT_ONLY ? SC_OPEN_SHUTTER : SC_CLOSE_SHUTTER) != CE_NO_ERROR )
		return m_eLastError;
	pImg->SetImageStartTime(time(NULL));

	// wait for exposure to complete
	do {
	} while ((err = IsExposureComplete(expComp)) == CE_NO_ERROR && !expComp );
	EndExposure();
	if ( err != CE_NO_ERROR )
		return err;
	if ( m_eLastError != CE_NO_ERROR )
		return m_eLastError;

	// readout the CCD
	srp.ccd = m_eActiveCCD;
	srp.left = srp.top = 0;
	srp.height = height;
	srp.width = width;
	srp.readoutMode = m_uReadoutMode;
	if ( (err = StartReadout(srp)) == CE_NO_ERROR ) {
		rlp.ccd = m_eActiveCCD;
		rlp.pixelStart = 0;
		rlp.pixelLength = width;
		rlp.readoutMode = m_uReadoutMode;
		for (i=0; i<height && err==CE_NO_ERROR; i++ )
			err = ReadoutLine(rlp, FALSE, pImg->GetImagePointer() + (long)i * width);
	}
	EndReadout();
	if ( err != CE_NO_ERROR )
		return err;
	if ( m_eLastError != CE_NO_ERROR )
		return err;

	// we're done unless we wanted a dark also image
	if ( dark != SBDF_DARK_ALSO )
		return CE_NO_ERROR;

	// start the light exposure
	if ( StartExposure(SC_OPEN_SHUTTER) != CE_NO_ERROR )
		return m_eLastError;
	pImg->SetImageStartTime(time(NULL));

	// wait for exposure to complete
	do {
	} while ((err = IsExposureComplete(expComp)) == CE_NO_ERROR && !expComp );
	EndExposure();
	if ( err != CE_NO_ERROR )
		return err;
	if ( m_eLastError != CE_NO_ERROR )
		return m_eLastError;

	// readout the CCD
	srp.ccd = m_eActiveCCD;
	srp.left = srp.top = 0;
	srp.height = height;
	srp.width = width;
	srp.readoutMode = m_uReadoutMode;
	if ( (err = StartReadout(srp)) == CE_NO_ERROR ) {
		rlp.ccd = m_eActiveCCD;
		rlp.pixelStart = 0;
		rlp.pixelLength = width;
		rlp.readoutMode = m_uReadoutMode;
		for (i=0; i<height && err==CE_NO_ERROR; i++ )
			err = ReadoutLine(rlp, TRUE, pImg->GetImagePointer() + (long)i * width);
	}
	EndReadout();
	if ( err != CE_NO_ERROR )
		return err;
	if ( m_eLastError != CE_NO_ERROR )
		return err;

	// record dark subtraction in history
	if ( m_eCameraType == ST5C_CAMERA || m_eCameraType == ST237_CAMERA )
		pImg->SetHistory("f");
	else
		pImg->SetHistory("R");

	return CE_NO_ERROR;	
}


/*

	StartExposure:

	Start an exposure in the camera.  Should be matched
	with an EndExposure call.

*/
PAR_ERROR CSBIGCam::StartExposure(SHUTTER_COMMAND shutterState)
{
	StartExposureParams sep;

	sep.ccd = m_eActiveCCD;
	sep.exposureTime = (unsigned long)(m_dExposureTime * 100.0 + 0.5);
	if ( sep.exposureTime < 1 )
		sep.exposureTime = 1;
	sep.abgState = m_eABGState;
	sep.openShutter = shutterState;
	if ( CheckLink() )
		return SBIGUnivDrvCommand(CC_START_EXPOSURE, &sep, NULL);
	else
		return m_eLastError;
}

/*

	EndExposure:

	End or abort an exposure in the camera.  Should be
	matched to a StartExposure but no damage is done
	by calling it by itself if you don't know if an
	exposure was started for example.

*/
PAR_ERROR CSBIGCam::EndExposure(void)
{
	EndExposureParams eep;

	eep.ccd = m_eActiveCCD;
	if ( CheckLink() )
		return SBIGUnivDrvCommand(CC_END_EXPOSURE, &eep, NULL);
	else
		return m_eLastError;
}

/*

	IsExposueComplete:

	Query the camera to see if the exposure in progress is complete.
	This returns TRUE if the CCD is idle (an exposure was never
	started) or if the CCD exposure is complete.

*/
PAR_ERROR CSBIGCam::IsExposureComplete(MY_LOGICAL &complete)
{
	QueryCommandStatusParams qcsp;
	QueryCommandStatusResults qcsr;

	complete = FALSE;
	if ( CheckLink() ) {
    	qcsp.command = CC_START_EXPOSURE;
    	if ( SBIGUnivDrvCommand(CC_QUERY_COMMAND_STATUS, &qcsp, &qcsr) == CE_NO_ERROR ) {
    		if ( m_eActiveCCD == CCD_IMAGING )
    			complete = (qcsr.status & 0x03) != 0x02;
    		else
    			complete = (qcsr.status & 0x0C) != 0x08;
    	}
	}
   	return m_eLastError;
}

/*

	StartReadout:

	Start the readout process.  This should be called
	after EndExposure and should be matched with an
	EndExposure call.

*/
PAR_ERROR CSBIGCam::StartReadout(StartReadoutParams srp)
{
	if ( CheckLink() )
		return SBIGUnivDrvCommand(CC_START_READOUT, &srp, NULL);
	else
		return m_eLastError;
}

/*

	EndReadout:

	End a readout started with StartReadout.
	Don't forget to make this call to prepare the
	CCD for idling.

*/
PAR_ERROR CSBIGCam::EndReadout(void)
{
	EndReadoutParams erp;

	erp.ccd = m_eActiveCCD;
	if ( CheckLink() )
		return SBIGUnivDrvCommand(CC_END_READOUT, &erp, NULL);
	else
		return m_eLastError;
}

/*

	ReadoutLine:

	Readout a line of data from the camera, optionally
	performing a dark subtraction, placing the data
	at dest.

*/
PAR_ERROR CSBIGCam::ReadoutLine(ReadoutLineParams rlp, MY_LOGICAL darkSubtract,
	unsigned short *dest)
{
	if ( CheckLink() ) {
    	if ( darkSubtract )
    		return SBIGUnivDrvCommand(CC_READ_SUBTRACT_LINE, &rlp, dest);
    	else
    		return SBIGUnivDrvCommand(CC_READOUT_LINE, &rlp, dest);
	}
	else
		return m_eLastError;

}

/*

	DumpLines:

	Discard data from one or more lines in the camera.

*/
PAR_ERROR CSBIGCam::DumpLines(unsigned short noLines)
{
	DumpLinesParams dlp;

	dlp.ccd = m_eActiveCCD;
	dlp.lineLength = noLines;
	dlp.readoutMode = m_uReadoutMode;
	if ( CheckLink() )
		return SBIGUnivDrvCommand(CC_DUMP_LINES, &dlp, NULL);
	else
		return m_eLastError;
}

/*

	SetTemperatureRegulation:

	Enable or disable the temperatre controll at
	the passed setpoint which is the absolute
	(not delta) temperature in degrees C.

*/
PAR_ERROR CSBIGCam::SetTemperatureRegulation(MY_LOGICAL enable, double setpoint)
{
        PAR_ERROR e;

	SetTemperatureRegulationParams strp;

	if ( CheckLink() ) {
	strp.regulation = enable ? REGULATION_ON : REGULATION_OFF;
    	strp.ccdSetpoint = DegreesCToAD(setpoint, TRUE);
    	e = SBIGUnivDrvCommand(CC_SET_TEMPERATURE_REGULATION, &strp, NULL);
	if (e != CE_NO_ERROR) return e;
	// enable autofreeze, by Andre
	strp.regulation = REGULATION_ENABLE_AUTOFREEZE;
    	return SBIGUnivDrvCommand(CC_SET_TEMPERATURE_REGULATION, &strp, NULL);
    }
	else
		return m_eLastError;
}

/*

	QueryTemperatureStatus:

	Get whether the cooling is enabled, the CCD temp
	and setpoint in degrees C and the percent power
	applied to the TE cooler.

*/
PAR_ERROR CSBIGCam::QueryTemperatureStatus(MY_LOGICAL &enabled, double &ccdTemp,
	double &setpointTemp, double &percentTE)
{
	QueryTemperatureStatusResults qtsr;

	if ( CheckLink() ) {
    	if ( SBIGUnivDrvCommand(CC_QUERY_TEMPERATURE_STATUS, NULL, &qtsr) == CE_NO_ERROR )
    	{
    		enabled = qtsr.enabled;
    		ccdTemp = ADToDegreesC(qtsr.ccdThermistor, TRUE);
    		setpointTemp = ADToDegreesC(qtsr.ccdSetpoint, TRUE);
    		percentTE = qtsr.power/255.0 * 100;
    	}
    }
	return m_eLastError;
}

/*

	GetCCDTemperature:

	Read and return the current CCD temperature.

*/
PAR_ERROR CSBIGCam::GetCCDTemperature(double &ccdTemp)
{
	double setpointTemp, percentTE;
	MY_LOGICAL teEnabled;

	return QueryTemperatureStatus(teEnabled, ccdTemp, setpointTemp, percentTE);
}


/*

	ActivateRelay:

	Activate one of the four relays for the passed
	period of time.  Cancel a relay by passing
	zero for the time.

*/
PAR_ERROR CSBIGCam::ActivateRelay(CAMERA_RELAY relay, double time)
{
	ActivateRelayParams arp;
	unsigned short ut;

	if ( CheckLink() ) {
    	arp.tXMinus = arp.tXPlus = arp.tYMinus = arp.tYPlus = 0;
    	if ( time >= 655.35 )
    		ut = 65535;
    	else
    		ut = (unsigned short)(time/0.01);
    	switch ( relay ){
    	case RELAY_XPLUS:  arp.tXPlus = ut; break;
    	case RELAY_XMINUS: arp.tXPlus = ut; break;
    	case RELAY_YPLUS:  arp.tXPlus = ut; break;
    	case RELAY_YMINUS: arp.tXPlus = ut; break;
    	}
    	return SBIGUnivDrvCommand(CC_ACTIVATE_RELAY, &arp, NULL);
    }
	else
		return m_eLastError;
}

/*

	AOTipTilt:

	Send a tip/tilt command to the AO-7.

*/
PAR_ERROR CSBIGCam::AOTipTilt(AOTipTiltParams attp)
{
	if ( CheckLink() )
		return SBIGUnivDrvCommand(CC_AO_TIP_TILT, &attp, NULL);
	else
		return m_eLastError;
}

/*

	CFWCommand:

	Send a command to the Color Filter Wheel.

*/
PAR_ERROR CSBIGCam::CFWCommand(CFWParams cfwp, CFWResults &cfwr)
{
	if ( CheckLink() )
		return SBIGUnivDrvCommand(CC_CFW, &cfwp, &cfwr);
	else
		return m_eLastError;
}

/*

	EstablishLink:

	Once the driver and device are open call this to
	establish a communications link with the camera.
	May be called multiple times without problem.

	If there's no error and you want to find out what
	model of camera was found use the GetCameraType()
	function.

*/
PAR_ERROR CSBIGCam::EstablishLink(void)
{
	PAR_ERROR res;
	EstablishLinkResults elr;
	EstablishLinkParams elp;

	res = SBIGUnivDrvCommand(CC_ESTABLISH_LINK, &elp, &elr);
	if ( res == CE_NO_ERROR )
		m_eCameraType = (CAMERA_TYPE)elr.cameraType;
	return res;
}

/*

	GetErrorString:

	Returns a ANSI C++ standard string object describing
	the error code returned from the lass call to the driver.

*/
string CSBIGCam::GetErrorString()
{
	return GetErrorString(m_eLastError);
}

/*

	CheckLink:

	If a link has been established to a camera return TRUE.
    Otherwise try to establish a link and if successful
	return TRUE.  If fails return FALSE.

*/
MY_LOGICAL CSBIGCam::CheckLink(void)
{
	if ( m_eCameraType != NO_CAMERA || EstablishLink() == CE_NO_ERROR )
		return TRUE;
	else
		return FALSE;
}

/*

	DegreesCToAD:

	Convert temperatures in degrees C to
	camera AD setpoints.

*/
unsigned short CSBIGCam::DegreesCToAD(double degC, MY_LOGICAL ccd /* = TRUE */)
{
	double r;
	unsigned short setpoint;

	if ( degC < -50.0 )
		degC = -50.0;
	else if ( degC > 35.0 )
		degC = 35.0;
	if ( ccd ) {
		r = R0 * exp(log(RR_CCD)*(T0 - degC)/DT_CCD);
		setpoint = (unsigned short)(MAX_AD/((RB_CCD/r) + 1.0) + 0.5);
	} else {
		r = R0 * exp(log(RR_AMB)*(T0 - degC)/DT_AMB);
		setpoint = (unsigned short)(MAX_AD/((RB_AMB/r) + 1.0) + 0.5);
	}
	return setpoint;
}

/*

	ADToDegreesC:

	Convert camera AD temperatures to
	degrees C

*/
double CSBIGCam::ADToDegreesC(unsigned short ad, MY_LOGICAL ccd /* = TRUE */)
{
	double r, degC;

	if ( ad < 1 )
		ad = 1;
	else if ( ad >= MAX_AD - 1 )
		ad = MAX_AD - 1;
	if ( ccd ) {
		r = RB_CCD/(((double)MAX_AD/ad) - 1.0);
		degC = T0 - DT_CCD*(log(r/R0)/log(RR_CCD));
	} else {
		r = RB_AMB/(((double)MAX_AD/ad) - 1.0);
		degC = T0 - DT_AMB*(log(r/R0)/log(RR_AMB));
	}
	return degC;
}
