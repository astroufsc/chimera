/*

	csbigimg.h - Contains the definition of the interface to
				 the SBIG Image Class

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
#ifndef _CSBIGIMG_
#define _CSBIGIMG_

#ifndef _PARDRV_
 #include "sbigudrv.h"
#endif

#include <time.h>
#include <string>
using namespace std;

/*

	Exposure State Field Defines

*/
#define ES_ABG_MASK 0x0003
#define ES_ABG_UNKNOWN 0x0000
#define ES_ABG_LOW 0x0001
#define ES_ABG_CLOCKED 0x0002
#define ES_ABG_MID 0x0003

#define ES_ABG_RATE_MASK 0x00C0
#define ES_ABG_RATE_FIXED 0x0000
#define ES_ABG_RATE_LOW 0x0040
#define ES_ABG_RATE_MED 0x0080
#define ES_ABG_RATE_HI 0x00C0

#define ES_DCS_MASK 0x000c
#define ES_DCS_UNKNOWN 0x0000
#define ES_DCS_ENABLED 0x0004
#define ES_DCS_DISABLED 0x0008

#define ES_DCR_MASK 0x0030
#define ES_DCR_UNKNOWN 0x0000
#define ES_DCR_ENABLED 0x0010
#define ES_DCR_DISABLED 0x0020

#define ES_AUTOBIAS_MASK 0x0100
#define ES_AUTOBIAS_ENABLED 0x0100
#define ES_AUTOBIAS_DISABLED 0x0000


typedef enum { SBIF_COMPRESSED, SBIF_UNCOMPRESSED } SBIG_IMAGE_FORMAT;
typedef enum {SBFE_NO_ERROR, SBFE_OPEN_ERROR, SBRE_CLOSE_ERROR, SBFE_READ_ERROR, SBFE_WRITE_ERROR,
	SBFE_FORMAT_ERROR, SBFE_MEMORY_ERROR } SBIG_FILE_ERROR;

class CSBIGImg {
private:
	int m_nHeight, m_nWidth;					// image size in pixels
	unsigned short *m_pImage;					// pointer to image data
	time_t m_imageStartTime;					// time that light exposure started
	double m_dCCDTemperature;					// CCD Temp at start of exposure
	double m_dExposureTime;						// Exposure time in seconds
	double m_dTrackExposure;					// Exposure when tracking
	double m_dEachExposure;						// Snapshot time in seconds
	double m_dFocalLength;						// Lens/Telescope Focal Length in inches
	double m_dApertureArea;						// Lens/Telescope Aperture Are in Sq-Inches
	double m_dResponseFactor;					// Magnitude Calibration Factor
	double m_dPixelHeight, m_dPixelWidth;		// Pixel Dimensions in mm
	double m_dEGain;							// Electronic Gain, e-/ADU
	unsigned short m_uBackground, m_uRange;		// Display Background and Range
	unsigned short m_uNumberExposures;			// Number of exposures co-added
	unsigned short m_uSaturationLevel;			// Pixels at this level are saturated
	unsigned short m_uPedestal;					// Image Pedestal
	unsigned short m_uExposureState;			// Exposure State
	unsigned short m_uReadoutMode;				// Camera Readout Mode use to acquire image
	string m_cImageNote;						// Note attached to image
	string m_cObserver;							// Observer name
	string m_cHistory;							// Image History string of modification chars
	string m_cFilter;							// Filter name imaged through
	string m_cSoftware;							// Software App Name and Version
	string m_cCameraModel;						// Model of camera used to acquire image

public:
	/* Constructors/Destructor */
	CSBIGImg();
	CSBIGImg(int height, int width);
	~CSBIGImg();
	void Init();

	/* Accessor Functions */
	int GetHeight() {return m_nHeight;}
	int GetWidth() {return m_nWidth;}
	unsigned short *GetImagePointer() {return m_pImage;}
	void SetImageStartTime(time_t startTime){m_imageStartTime = startTime;}
	time_t GetImageStartTime(void) {return m_imageStartTime;}
	void SetCCDTemperature(double temp) {m_dCCDTemperature = temp;}
	double GetCCDTemperature(void) {return m_dCCDTemperature;}
	void SetExposureTime(double exp) {m_dExposureTime = exp;}
	double GetExposureTime(void) {return m_dExposureTime;}
	void SetEachExposure(double exp) {m_dEachExposure = exp;}
	double GetEachExposure(void) {return m_dEachExposure;}
	void SetFocalLength(double fl) {m_dFocalLength = fl;}
	double GetFocalLength(void) {return m_dFocalLength;}
	void SetApertureArea(double ap) {m_dApertureArea = ap;}
	double GetApertureArea(void) {return m_dApertureArea;}
	void SetResponseFactor(double resp) {m_dResponseFactor = resp;}
	double GetResponseFactor(void) {return m_dResponseFactor;}
	void SetPixelHeight(double ht) {m_dPixelHeight = ht;}
	double GetPixelHeight(void) {return m_dPixelHeight;}
	void SetPixelWidth(double wd) {m_dPixelWidth = wd;}
	double GetPixelWidth(void) {return m_dPixelWidth;}
	void SetEGain(double gn) {m_dEGain = gn;}
	double GetEGain(void) {return m_dEGain;}
	void SetBackground(unsigned short back) {m_uBackground = back;}
	unsigned short GetBackground(void) {return m_uBackground;}
	void SetRange(unsigned short range) {m_uRange = range;}
	unsigned short GetRange(void) {return m_uRange;}
	void SetSaturationLevel(unsigned short sat) {m_uSaturationLevel = sat;}
	unsigned short GetSaturationLevel(void) {return m_uSaturationLevel;}
	void SetNumberExposures(unsigned short no) {m_uNumberExposures = no;}
	unsigned short GetNumberExposures(void) {return m_uNumberExposures;}
	void SetTrackExposure(double exp) {m_dTrackExposure = exp;}
	double GetTrackExposure(void) {return m_dTrackExposure;}
	void SetReadoutMode(unsigned short rm) {m_uReadoutMode = rm;}
	unsigned short GetReadoutMode(void) {return m_uReadoutMode;}
	void SetPedestal(unsigned short ped) {m_uPedestal = ped;}
	unsigned short GetPedestal(void) {return m_uPedestal;}
	void SetExposureState(unsigned short es) {m_uExposureState = es;}
	unsigned short GetExposureState(void) {return m_uExposureState;}
	void SetImageNote(string str) {m_cImageNote = str;}
	string GetImageNote(void) {return m_cImageNote;}
	void SetObserver(string str) {m_cObserver = str;}
	string GetObserver(void) {return m_cObserver;}
	void SetHistory(string str) {m_cHistory = str;}
	string GetHistory(void) {return m_cHistory;}
	void SetCameraModel(string str) {m_cCameraModel = str;}
	string GetCameraModel(void) {return m_cCameraModel;}

	/* File IO Routines */
	SBIG_FILE_ERROR SaveImage(const char *pFullPath, SBIG_IMAGE_FORMAT fmt);

	/* Utility Functions */
	MY_LOGICAL AllocateImageBuffer(int height, int width);
	void CreateSBIGHeader(char *pHeader, MY_LOGICAL isCompressed);
	int CompressSBIGData(unsigned char *pCmpData, int imgRow);
	void IntelCopyBytes(unsigned char *pRevData, int imgRow);
};

#endif /* #ifndef _CSBIGIMG_ */
