/*

	csbigimg.cpp - SBIG Image Class

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
#include "csbigimg.h"
#include <stdio.h>
#include <string.h>

/*

	Local Constants

*/
#define FILE_VERSION 	3		/* current header version written */
#define DATA_VERSION 	1		/* current data version written */
#define HEADER_LEN	2048
#define VERSION_STR		"1.0"	/* version of this class */
#ifndef PI
 #define PI 3.1415926535
#endif

/*

	CSBIGImg:

	Standard constructor.  Init member variables.

*/
CSBIGImg::CSBIGImg()
{
	Init();
}

/*

	CSBIGImg:

	Alternate constructor.  Try to allocate the image buffer.

*/
CSBIGImg::CSBIGImg(int height, int width)
{
	Init();
	AllocateImageBuffer(height, width);
}

/*

	~CSBIGImg:

	Deallocate the image buffer.

*/
CSBIGImg::~CSBIGImg()
{
	if ( m_pImage )
		delete m_pImage;
	m_pImage = NULL;
}

/*

	Init:

	Initialize the member variables with reasonable default values.

*/
void CSBIGImg::Init()
{
	string s1, s2;

	m_nHeight = m_nWidth = 0;
	m_pImage = NULL;
	m_imageStartTime = time(NULL);
	m_dCCDTemperature = 25.0;
	m_dExposureTime = m_dEachExposure = 1.0;
	m_dTrackExposure = 0.0;
	m_dFocalLength = 80.0;
	m_dApertureArea = PI * 4.0 * 4.0;
	m_dResponseFactor = 2000.0;
	m_dPixelHeight = m_dPixelWidth = 0.009;
	m_dEGain = 2.3;
	m_uBackground = 0;
	m_uRange = 65535;
	m_uNumberExposures = 1;
	m_uSaturationLevel = 65535;
	m_uPedestal = 0;
	m_uExposureState = ES_ABG_LOW | ES_ABG_RATE_FIXED |
		ES_DCS_ENABLED | ES_DCR_DISABLED | ES_AUTOBIAS_ENABLED;
	m_uReadoutMode = 0;
	m_cImageNote = "Image acquired with CSBIGImg";
	m_cObserver = "";
	m_cHistory = "0";
	m_cFilter = "None";
	s1 = "CSBIGImg Ver ";
	s2 = VERSION_STR;
	m_cSoftware = s1 + s2;
	m_cCameraModel = "ST-7";
}

/*

	SaveImage:

	Save the image in passed path and format.
	Returns any file errors that occur.

*/
SBIG_FILE_ERROR CSBIGImg::SaveImage(const char *pFullPath, SBIG_IMAGE_FORMAT fmt)
{
	char header[HEADER_LEN];
	FILE *fp;
	SBIG_FILE_ERROR res;
	int i, cmpWidth;
	unsigned char *pCmpData, *pRevData;
	unsigned short byteTest = 0x1234;
	MY_LOGICAL reverseBytes;

	switch ( fmt ) {
	case SBIF_COMPRESSED:
		/* SBIG Commpressed Format - create and write the image header
		   then compress and write each row of the image */
		CreateSBIGHeader(header, TRUE);
		res = SBFE_MEMORY_ERROR;
		pCmpData = new unsigned char[m_nWidth*2 + 2];
		if ( pCmpData )
		{
            res = SBFE_OPEN_ERROR;
    		if ( (fp = fopen(pFullPath, "wb")) != 0 )
			{
    			res = SBFE_WRITE_ERROR;
    			if ( fwrite(header, HEADER_LEN, 1, fp) == 1 )
				{
    				for (i=0; i<m_nHeight; i++){
						cmpWidth = CompressSBIGData(pCmpData, i);
						if ( fwrite(pCmpData, 1, cmpWidth, fp) != (size_t)cmpWidth )
							break;
    				}
    				if ( i == m_nHeight )
    					res = SBFE_NO_ERROR;
					 fclose(fp);
				}
		   }
		   delete pCmpData;
		}
		break;
	case SBIF_UNCOMPRESSED:
		/* SBIG Uncompressed Format - Create and write the header then
		   save the image data using the Intel byte order (ls them ms) */
        CreateSBIGHeader(header, FALSE);
        res = SBFE_OPEN_ERROR;
		if ( (fp = fopen(pFullPath, "wb")) != 0 )
		{
			res = SBFE_WRITE_ERROR;
			if ( fwrite(header, HEADER_LEN, 1, fp) == 1 )
			{
				reverseBytes = *((unsigned char*)&byteTest) != 0x34;
				if ( reverseBytes )
				{
					pRevData = new unsigned char[m_nWidth*2];
					if ( pRevData )
					{
						for (i=0; i<m_nHeight; i++ )
						{
							IntelCopyBytes(pRevData, i);
							if ( fwrite(pRevData, 2*m_nWidth, 1, fp) != 1 )
								break;
						}
						delete pRevData;
						if ( i == m_nHeight )
							res = SBFE_NO_ERROR;
					}
					else
						res = SBFE_MEMORY_ERROR;
				}
				else
				{
					if ( fwrite(m_pImage, 2*m_nWidth, m_nHeight, fp) == (size_t)m_nHeight )
						res = SBFE_NO_ERROR;
				}
			}
			fclose(fp);
		}
		break;
	default:
		res = SBFE_FORMAT_ERROR;
		break;
	}
	return res;
}

/*

	AllocateImageBuffer:

	Delete any existing buffer then try to allocate one of the
	given size.  Returns TRUE if successful.

*/
MY_LOGICAL CSBIGImg::AllocateImageBuffer(int height, int width)
{
	if ( m_pImage )
		delete m_pImage;
	m_nHeight = m_nWidth = 0;
	if ( height > 0 && width > 0 ) {
		m_pImage = new unsigned short[(long)height * width * sizeof(unsigned short)];
		if ( m_pImage ) {
			m_nHeight = height;
			m_nWidth = width;
		}
		memset(m_pImage, 0, 2L * m_nHeight * m_nWidth);
	}
	return m_pImage != NULL;
}

void CSBIGImg::CreateSBIGHeader(char *pHeader, MY_LOGICAL isCompressed)
{
	char *p;
	struct tm *plt;

	memset(pHeader, 0, HEADER_LEN);
	plt = gmtime(&m_imageStartTime);
	p = pHeader;
    p += sprintf(p,"SBIG %sImage\n\r", isCompressed ? "Compressed " : "");
    p += sprintf(p,"File_version = %d\n\r",FILE_VERSION);
    p += sprintf(p,"Data_version = %d\n\r",DATA_VERSION);
    p += sprintf(p,"Exposure = %ld\n\r",m_dExposureTime < 0.01 ? 1 :
		(long)(m_dExposureTime * 100.0 + 0.5));
    p += sprintf(p,"Focal_length = %1.3lf\n\r", m_dFocalLength);
    p += sprintf(p,"Aperture = %1.4lf\n\r", m_dApertureArea);
    p += sprintf(p,"Response_factor = %1.3lf\n\r",m_dResponseFactor);
    p += sprintf(p,"Note = %s\n\r", m_cImageNote.length() == 0 ? "-" :
		m_cImageNote.c_str());
    p += sprintf(p,"Background = %u\n\r", m_uBackground);
    p += sprintf(p,"Range = %u\n\r", m_uRange);
    p += sprintf(p,"Height = %d\n\r", m_nHeight);
    p += sprintf(p,"Width = %d\n\r", m_nWidth);
    p += sprintf(p,"Date = %02d/%02d/%02d\n\r", plt->tm_mon+1, plt->tm_mday, plt->tm_year % 100);
    p += sprintf(p,"Time = %02d:%02d:%02d\n\r", plt->tm_hour, plt->tm_min, plt->tm_sec);
    p += sprintf(p,"Exposure_state = %u\n\r", m_uExposureState);
    p += sprintf(p,"Temperature = %1.2lf\n\r", m_dCCDTemperature);
    p += sprintf(p,"Number_exposures = %d\n\r", m_uNumberExposures);
	p += sprintf(p,"Each_exposure = %ld\n\r", m_dEachExposure < 0.01 ? 1 :
		(long)(m_dEachExposure * 100.0 + 0.5));
    p += sprintf(p,"History = %s\n\r", m_cHistory.c_str());
    p += sprintf(p,"Observer = %s\n\r", m_cObserver.length() == 0 ? "-" :
		m_cObserver.c_str());
    p += sprintf(p,"X_pixel_size = %1.4lf\n\r", m_dPixelWidth);
    p += sprintf(p,"Y_pixel_size = %1.4lf\n\r", m_dPixelHeight);
    p += sprintf(p,"Pedestal = %u\n\r", m_uPedestal);
    p += sprintf(p,"E_gain = %1.2lf\n\r", m_dEGain);

    /* create user parameters */
    p += sprintf(p,"User_1 = %s\n\r", m_cSoftware.length() == 0 ? "-" :
		m_cSoftware.c_str());
    p += sprintf(p,"User_2 = %s\n\r", m_cCameraModel.length() == 0 ? "-" :
		m_cCameraModel.c_str());
    p += sprintf(p,"User_3 = Exposure = %1.3lf, Each_exposure = %1.3lf\n\r",
		m_dExposureTime, m_dEachExposure);
    p += sprintf(p,"User_4 = %s%d\n\r", "Y2KYear = ", plt->tm_year + 1900);

    /* create filter string */
    p += sprintf(p,"Filter = %s\n\r", m_cFilter.length() == 0 ? "-" :
		m_cFilter.c_str());

    /* create readout mode */
    p += sprintf(p,"Readout_mode = %u\n\r", m_uReadoutMode);

    /* create track time */
    p += sprintf(p,"Track_time = %ld\n\r", m_dTrackExposure < 0.01 ? 0 :
		(long)(m_dTrackExposure * 100.0 + 0.5));

    /* create saturation level */
    p += sprintf(p,"Sat_level = %u\n\r", m_uSaturationLevel);
    p += sprintf(p,"End\n\r%c",0x1a);
}

/*

	CompressSBIGData:

	Compress the imgRow row of pixel data into the pCmpData buffer,
	returning the length of the combressed data in bytes.

*/	
int CSBIGImg::CompressSBIGData(unsigned char *pCmpData, int imgRow)
{
	unsigned short us, *pImg;
	unsigned char *puc;
	int cmpLen, i;
	long delta;

	pImg = m_pImage + (long)imgRow * m_nWidth;
	puc = pCmpData + 2;		// offset passed length
	cmpLen = 0;

	// encode first pixel as is
	us = *pImg++;
	*puc++ = (unsigned char)(us & 0xFF);	// ls byte first
	*puc++ = (unsigned char)(us >> 8);
	cmpLen += 2;

	// compress remaining pixels
	for (i=1; i<m_nWidth; i++ )
	{
		delta = (long)(*pImg) - us;
		us = *pImg++;
		if ( delta >= -127 && delta <= 127 )
		{
			// encode pixel as delta;
			*puc++ = (unsigned char)delta;
			cmpLen++;
			if ( cmpLen >= 2*m_nWidth )	// make syre don't overwrite buffer
				break;
		}
		else
		{
			// encode pixel directly
			if ( cmpLen+3 >= 2*m_nWidth )
				break;
			*puc++ = 0x80;
			*puc++ = (unsigned char)(us & 0xFF);	// ls byte first
			*puc++ = (unsigned char)(us >> 8);
			cmpLen += 3;
		}
	}
	if ( i < m_nWidth )
	{
		// compressed data is longer, simply copy uncompressed data
		// note we don't use memcpy here because the the byte order
		// in memory may be different that ls then ms required by
		// the file
		IntelCopyBytes(pCmpData + 2, imgRow);
		cmpLen = 2 * m_nWidth;
	}
	// encode length at start of buffer
	pCmpData[0] = (unsigned char)(cmpLen & 0xFF); // ls byte of len
	pCmpData[1] = (unsigned char)(cmpLen >> 8);
	return cmpLen + 2;
}

/*

	IntelCopyBytes:

	Copy the imgRow row of pixels to the passed buffer
	preserving the Intel byte order (ls them ms).

*/
void CSBIGImg::IntelCopyBytes(unsigned char *pRevData, int imgRow)
{
	int i;
	unsigned short us, *pImg;
	unsigned char *puc;

	pImg = m_pImage + (long)imgRow * m_nWidth;
	puc = pRevData;
	for (i=0; i<m_nWidth; i++) {
		us = *pImg++;
		*puc++ = (unsigned char)(us & 0xFF);	// ls byte first
		*puc++ = (unsigned char)(us >> 8);
	}
}
