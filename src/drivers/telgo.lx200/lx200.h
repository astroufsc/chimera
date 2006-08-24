#ifndef LX200_H
#define LX200_H

#include "ser.h"
#include "lx200.h"


#define LX_BUFSIZE 128
#define LX_SLEW_TIMEOUT 30 // ~seconds
#define LX_DEFAULT_DEVICE "/dev/ttyS0"

/* precision */
#define LX_HIPRECISION_RESP 9
#define LX_LOPRECISION_RESP 8
enum { LX_PRECISION_LOW, LX_PRECISION_HIGH };

#define LX_FOCUS_GAIN 10000    /* 1/100 seconds */
enum {LX_FOCUS_MINUS, LX_FOCUS_PLUS, LX_FOCUS_STOP}; // direction
enum {LX_FOCUS_SLOW, LX_FOCUS_FAST};  // speed



struct ras {
        int hh;
        int mm;
        int ss;
};


struct decs {
        int he;  // celestial hesmisphere. +1 = N, -1 = S.
        int dd;
        int mm;
        int ss;
};


typedef struct {
        struct ras pra;        //pointed RA
        struct ras cra;        //current RA
        struct ras ra_range;   //maximum displacement allowed in RA

        struct decs pdec;      //pointed DEC
        struct decs cdec;      //current DEC
        struct decs dec_range; //maximum displacement allowed in DEC

        float lat;
        float lon;
        int moving;
	int focus;
        int mnt_type;
        ser_info *serial;
        char *outbuf;
} tel_info;




int lx200_set_coords(tel_info *tel, struct ras ra, struct decs dec);
int lx200_slew(tel_info *tel);
int lx200_update_coords(tel_info *tel);
int lx200_wait_slew(tel_info *tel);
int lx200_match_coords(tel_info *tel);

int lx200_point(tel_info *tel, struct ras ra, struct decs dec);

tel_info *lx200_open(char *device);
void lx200_close(tel_info *tel);

int lx200_change_focus(tel_info *tel, int steps, int speed);
int lx200_focus_control(tel_info *tel, int direction, int speed);

int lx200_ra_drive_on(tel_info *tel);
int lx200_ra_drive_off(tel_info *tel);


#endif /* LX200_H */
