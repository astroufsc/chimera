#include "ser.h"

#define ROM_VERSION (3)

#define CAM_MAX_NLINES (165)
#define CAM_MAX_NCOLS  (192)

#define CAM_FIRST_LINE  (64)
#define CAM_LAST_LINE  (228)

/* Commands */
#define CAM_WRITE_MEM (1)
#define CAM_READ_MEM  (2)
#define CAM_EXT_RAM   (0)
#define CAM_INT_RAM   (1)

/* Responses */
#define CAM_ACK (0x06)
#define CAM_NAK (0x15)

/* Mode flags (46) */
#define CAM_MODE_FEXP     (0x80) /* Full exposure            */
#define CAM_MODE_LA       (0x40) /* Light array              */
#define CAM_MODE_STEXP    (0x20) /* Start exposure           */
#define CAM_MODE_EXPDONE  (0x10) /* Exposure done            */
#define CAM_MODE_CMPRSIMG (0x08) /* Compress image in memory */
#define CAM_MODE_SUBDARKF (0x04) /* Subtract dark frame      */
#define CAM_MODE_CMPRSDAT (0x02) /* Enable data compression  */
#define CAM_MODE_SMTH     (0x01) /* Smooth image in memory   */

/* Format flags (47) */
#define CAM_FMT_FFOCUS    (0x80) /* Find and focus mode                  */
#define CAM_FMT_ANTIBLOOM (0x40) /* Anti-blooming gate enable            */
#define CAM_FMT_INTERRUPT (0x20) /* Interrupt from Find and focus, Track */
                                 /*   and Calibrate modes.               */
#define CAM_FMT_TRACK     (0x10) /* Track mode                           */
#define CAM_FMT_CALIBRATE (0x08) /* Calibrate mode                       */
#define CAM_FMT_CLOSE_R0  (0x04) /* Close `left' relay                   */
#define CAM_FMT_CLOSE_R1  (0x05) /* Close `right' relay                  */
#define CAM_FMT_CLOSE_R2  (0x06) /* Close `up' relay                     */
#define CAM_FMT_CLOSE_R3  (0x07) /* Close `down' relay                   */

/* Baud rates */
#define CAM_B57600 (255)
#define CAM_B19200 (253)
#define CAM_B9600  (250)
#define CAM_B4800  (244)
#define CAM_B2400  (232)
#define CAM_B1200  (208)
#define CAM_B600   (160)
#define CAM_B300    (64)

/* Addresses */
#define CAM_LAST_KEY  (45)
#define CAM_MODE      (46)
#define CAM_FORMAT    (47)
#define CAM_EXPTIME   (48)
#define CAM_XPOINTER  (50)
#define CAM_NBYTES    (51)
#define CAM_OFFSET    (52)
#define CAM_VREFPLUS  (53)
#define CAM_VREFMINUS (54)
#define CAM_ROMVER    (55)
#define CAM_BAUDRATE  (56)
#define CAM_INSTRUCT  (58)


#define CAM_MAX_DATA                (4)
#define CAM_MAX_CMD  (CAM_MAX_DATA + 6)


typedef struct {
	float exptime; /* seconds */
	unsigned char mode_flag;
	unsigned char format_flag;
	unsigned char first_line;
	unsigned char first_column;
	unsigned char nlines;
	unsigned char ncolumns;
	unsigned char offset;
	unsigned char vref_plus;
	unsigned char vref_minus;
	unsigned char rom_version;
	unsigned char baudrate;  /* note: this is the constant specified */
                                 /* above, e.g. CAM_BXXXXX.              */
	unsigned char  *image;
} ccd_info;

typedef struct { 
	ccd_info *ccd;
	ser_info *serial;
} cam_info;

typedef struct {
	int nbytes;
	int ram;
	int address;
	unsigned char data[CAM_MAX_DATA];
} cmd_t;


/* Camera structure management */
int is_valid_camera(cam_info *camera);
cam_info *alloc_camera(char *ttyname);
void free_camera(cam_info *camera);

/* Low level functions */
int set_baudrate(cam_info *camera, unsigned char baudrate);
	/* values of baud rates are defined in camera.h */
int init_camera(cam_info *camera);
int write_mem(cam_info *camera, cmd_t *command);
int read_mem(cam_info *camera, cmd_t *command);
unsigned char wait_response(cam_info *camera);

/* user functions */
int expose_ccd(cam_info *camera, float time); /* seconds */
int read_line(cam_info *camera, int line, unsigned char *buf);
int download_image(cam_info *camera, unsigned char *image);
int set_camera(cam_info *camera);
int take_image(cam_info *camera, unsigned char *image);
