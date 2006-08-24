#include <termios.h>

#define RD_TIMEOUT (2)
#define TRUE (1)
#define FALSE (0)

#define MAX_BUF_LEN (255)
#define PAR_NONE 'n'
#define PAR_EVEN 'e'
#define PAR_ODD  'o'

typedef struct {
	int isopen;
	int waitread;
	int err_code;
	char *tty_name;
	int ttyfd;
	cc_t minchars; /* not used if waitread == FALSE */
	int bytesread;
	int baudrate;
	char parity;
	int stopbits;
	cc_t timeout; /* interchar time (1/10 secs), and read timeout (secs) */
	struct termios *tio;    /* |- don't mess with these structs, */
	struct termios *oldtio; /* |  the routines will handle it.   */
} ser_info;

int is_valid_serial(ser_info *serial);
void open_serial(ser_info *serial, char *ttyname);
int close_serial(ser_info *serial);
int set_serial(ser_info *serial);
//static int set_minchars(ser_info *serial, int nbytes);
int read_serial(ser_info *serial, unsigned char *buf, unsigned int nbytes);
int write_serial(ser_info *serial, unsigned char *buf, unsigned int nbytes);
