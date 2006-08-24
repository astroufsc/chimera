#include <stdio.h>
#include "errors.h"
#include "ccd.h"


#undef CCDTEST
#ifdef CCDTEST

char minhatty[] = "/dev/ttyS1";

cam_info *camera;

int main()
{
	int i;

	puts("Programa para teste do CCD.");
	printf("tty = %s\n\n", minhatty);
	
	camera = alloc_camera(minhatty);
	if (camera == NULL) {
		puts("alloc_camera()");
		exit(1);
	}
	
	camera->ccd->baudrate = CAM_B57600;
	camera->ccd->rom_version = ROM_VERSION;
	if (init_camera(camera) != ERR_OK) {
		puts("init_camera()");
		exit(0);
	}

	camera->ccd->exptime = 5;
	camera->ccd->first_line = CAM_FIRST_LINE;
	camera->ccd->first_column = 0;
	camera->ccd->nlines = CAM_MAX_NLINES;
	camera->ccd->ncolumns = CAM_MAX_NCOLS;
	camera->ccd->offset = 0;
	camera->ccd->vref_plus = 255;
	camera->ccd->vref_minus = 0;
	camera->ccd->format_flag = 0;
	camera->ccd->mode_flag = (CAM_MODE_FEXP | CAM_MODE_LA);
	set_camera(camera);
	take_image(camera, camera->ccd->image);

	free_camera(camera);
}
#endif


int init_camera(cam_info *camera)
{
	int res;

	if (!is_valid_camera(camera))
		return(ERR_CAM);

	camera->serial->waitread = TRUE;
	camera->serial->baudrate = B9600;
	camera->serial->parity   = PAR_EVEN;
	camera->serial->stopbits = 1;
	camera->serial->minchars = 0;
	camera->serial->timeout  = 5;
	set_serial(camera->serial);
	if (camera->serial->err_code != ERR_OK)
		return(ERR_SERIAL);

	res = set_baudrate(camera, camera->ccd->baudrate);
	return(res);

}


int is_valid_camera(cam_info *camera)
{
	if (camera == NULL)
		return(FALSE);
	if (camera->ccd == NULL)
		return(FALSE);
	if (camera->serial == NULL)
		return(FALSE);
	return(TRUE);
}


cam_info *alloc_camera(char *ttyname)
{
	cam_info *camera;
	int i;

	camera = (cam_info *) calloc(sizeof(cam_info), 1);
	if (camera == NULL)
		return(NULL);
	camera->serial = (ser_info *) calloc(sizeof(ser_info), 1);
	if (camera->serial == NULL)
		return(NULL);
	camera->ccd = (ccd_info *) calloc(sizeof(ccd_info), 1);
	if (camera->ccd == NULL)
		return(NULL);
	open_serial(camera->serial, ttyname);
	return(camera);
}


void free_camera(cam_info *camera)
{
	if (camera == NULL)
		return;
	if (camera->serial != NULL) {
		if (camera->serial->ttyfd > 0) {
			set_baudrate(camera, CAM_B9600);
			close_serial(camera->serial);
		}
		free(camera->serial);
	}
	if (camera->ccd != NULL)
		free(camera->ccd);
	free(camera);
}


int set_camera(cam_info *camera)
{
	long int exptmp;
	int res;
	cmd_t cmd;

	if (!is_valid_camera(camera))
		return(ERR_CAM);
/* Set modes and format */
	cmd.nbytes = 2;
	cmd.address = CAM_MODE;
	cmd.ram = CAM_INT_RAM;
	camera->ccd->mode_flag &= ~CAM_MODE_STEXP;
	cmd.data[0] = camera->ccd->mode_flag;
	cmd.data[1] = camera->ccd->format_flag;
	res = write_mem(camera, &cmd);
	if (res != ERR_OK)
		return(ERR_WRITE);

/* Set exposure time */
/*	cmd.nbytes = 2;
	cmd.address = CAM_EXPTIME;
	exptmp = camera->ccd->exptime * 100;
	cmd.data[0] = exptmp & 0x00FF;
	cmd.data[1] = (exptmp >> 8) & 0x00FF;
	res = write_mem(camera, &cmd);
	if (res != ERR_OK)
		return(ERR_WRITE); */

/* Set first pixel and number of pixels per line */
	cmd.nbytes = 2;
	cmd.address = CAM_XPOINTER;
	cmd.data[0] = camera->ccd->first_column;
	cmd.data[1] = camera->ccd->ncolumns;
	res = write_mem(camera, &cmd);
	if (res != ERR_OK)
		return(ERR_WRITE);

/* Set additional offset and Vref+ */
	cmd.nbytes = 2;
	cmd.address = CAM_OFFSET;
	cmd.data[0] = camera->ccd->offset;
	cmd.data[1] = camera->ccd->vref_plus;
	res = write_mem(camera, &cmd);
	if (res != ERR_OK)
		return(ERR_WRITE);

/* Set Vref- */
	cmd.nbytes = 1;
	cmd.address = CAM_VREFMINUS;
	cmd.data[0] = camera->ccd->vref_minus;
	res = write_mem(camera, &cmd);
	if (res != ERR_OK)
		return(ERR_WRITE);

return(ERR_OK);
}


int write_mem(cam_info *camera, cmd_t *cmd)
{
	unsigned char buf[CAM_MAX_CMD], *pbuf, chksum, tmp;
	int i, res;

	if (!is_valid_camera(camera))
		return(ERR_CAM);
	if (cmd == NULL)
		return(ERR_CMD);

	pbuf = buf;
	*pbuf++ = CAM_WRITE_MEM;
	chksum = CAM_WRITE_MEM;
	tmp = cmd->nbytes + 3;
	*pbuf++ = tmp;
	chksum += tmp;
	*pbuf++ = cmd->ram;
	chksum += cmd->ram;
	tmp = cmd->address & 0x00FF;
	*pbuf++ = tmp;
	chksum += tmp;
	tmp = (cmd->address >> 8) & 0x00FF;
	*pbuf++ = tmp;
	chksum += tmp;

	for (i = 0; i < (cmd->nbytes); i++) {
		*pbuf++ = cmd->data[i];
		chksum += cmd->data[i];
	}
	*pbuf = chksum;
	if (write_serial(camera->serial, buf, (6 + cmd->nbytes)) == ERR_WRITE)
		return(ERR_WRITE);
	res = wait_response(camera);
	if (res == CAM_NAK)
		return(ERR_READ);
	return(ERR_OK);
}


unsigned char wait_response(cam_info *camera)
{
	unsigned char c;
	int res;

	if (!is_valid_camera(camera))
		return;

	if (read_serial(camera->serial, &c, 1) == ERR_READ)
		return(CAM_NAK);
	if (c != CAM_ACK)
		return(CAM_NAK);
	return(CAM_ACK);
}


int read_mem(cam_info *camera, cmd_t *cmd)
{
	unsigned char buf[CAM_MAX_CMD], *pbuf, tmp, chksum;
	int res, i;

	if (!is_valid_camera(camera))
		return(ERR_CAM);
	if (cmd == NULL)
		return(ERR_CMD);
/* Set command in buffer */
	pbuf = buf;
	*pbuf++ = CAM_READ_MEM;
	chksum = CAM_READ_MEM;
	*pbuf++ = cmd->nbytes;
	chksum += cmd->nbytes;
	*pbuf++ = cmd->ram;
	chksum += cmd->ram;
	tmp = cmd->address & 0x00FF;
	*pbuf++ = tmp;
	chksum += tmp;
	tmp = (cmd->address >> 8) & 0x00FF;
	*pbuf++ = tmp;
	chksum += tmp;
	*pbuf = chksum;
	res = write_serial(camera->serial, buf, 6);
	if (res < 6)
		return(ERR_WRITE);
/* Read header */
	res = read_serial(camera->serial, buf, 2);
	if ((res < 2) || (buf[0] != 2) || (buf[1] != cmd->nbytes))
		return(ERR_READ);
/* Read data */
	res = read_serial(camera->serial, buf, cmd->nbytes);
	if (res < cmd->nbytes)
		return(ERR_READ);
	pbuf = buf;
	for (i = 0; i < cmd->nbytes;)
		cmd->data[i++] = *pbuf++;
/* Checksum */
	res = read_serial(camera->serial, buf, 1);
	if (res < 1)
		return(ERR_READ);
/* Evaluate checksum in the futute */
	return(ERR_OK);
}


int set_baudrate(cam_info *camera, unsigned char baudrate)
{
	cmd_t cmd;
	int tmp;

	if (!is_valid_camera(camera))
		return(ERR_CAM);

/* Write ROM version */
	cmd.nbytes = 1;
	cmd.ram = CAM_INT_RAM;
	cmd.address = CAM_ROMVER;
	cmd.data[0] = camera->ccd->rom_version;
	if (write_mem(camera, &cmd) != ERR_OK)
		return(ERR_WRITE);

/* Set baud rate */
	cmd.nbytes = 1;
	cmd.address = CAM_BAUDRATE;
	cmd.data[0] = baudrate;
	if (write_mem(camera, &cmd) != ERR_OK)
		return(ERR_WRITE);

	camera->ccd->baudrate = baudrate;
	switch (baudrate) {
	case CAM_B57600:
		camera->serial->baudrate = B57600;
		break;
	case CAM_B19200:
		camera->serial->baudrate = B19200;
		break;
	case CAM_B9600:
		camera->serial->baudrate = B9600;
		break;
	case CAM_B4800:
		camera->serial->baudrate = B4800;
		break;
	case CAM_B2400:
		camera->serial->baudrate = B2400;
		break;
	case CAM_B1200:
		camera->serial->baudrate = B1200;
		break;
	case CAM_B600:
		camera->serial->baudrate = B600;
		break;
	case CAM_B300:
		camera->serial->baudrate = B300;
		break;
	default:
		return(ERR_BAUDRATE);
	}
	set_serial(camera->serial);
	if (camera->serial->err_code != ERR_OK)
		return(ERR_SERIAL);

	/* Read ROM version for testing */
	cmd.nbytes = 1;
	cmd.address = CAM_ROMVER;
	tmp = read_mem(camera, &cmd);
	if (tmp != ERR_OK)
		return(ERR_READ);
	if (cmd.data[0] != camera->ccd->rom_version)
		return(ERR_SERIAL);

	return(ERR_OK);
}


int expose_ccd(cam_info *camera, float time)
{
cmd_t cmd;
int tmp, res;

if (!is_valid_camera(camera))
	return(ERR_CAM);

/* Set exposure time */
	cmd.nbytes = 2;
	cmd.address = CAM_EXPTIME;
	cmd.ram = CAM_INT_RAM;
	camera->ccd->exptime = time;
	tmp = time * 100;
	cmd.data[0] = tmp & 0x00FF;
	cmd.data[1] = (tmp >> 8) & 0x00FF;
	res = write_mem(camera, &cmd);
	if (res != ERR_OK)
		return(res);

/* Start exposure */
	cmd.nbytes = 1;
	cmd.address = CAM_MODE;
	camera->ccd->mode_flag &= ~CAM_MODE_STEXP;
	cmd.data[0] = camera->ccd->mode_flag | CAM_MODE_STEXP;
	res = write_mem(camera, &cmd);
	if (res != ERR_OK)
		return(res);

/* Wait until exposure is done */
	cmd.nbytes = 1;
	cmd.address = CAM_MODE;
	sleep((int)time);
	do {
		if ((res = read_mem(camera, &cmd)) != ERR_OK)
			return(res);
		sleep(1);
	} while((cmd.data[0] & CAM_MODE_EXPDONE) == CAM_MODE_EXPDONE);

return(ERR_OK);
}


int read_line(cam_info *camera, int line, unsigned char *buf)
{
	unsigned char chksum;
	int res;

	if (!is_valid_camera(camera))
		return(ERR_CAM);
	if ((line < CAM_FIRST_LINE ) || (line > CAM_LAST_LINE))
		return;
	buf[0] = line;
	buf[1] = line;
	res = write_serial(camera->serial, buf, 2);
	if (res < 2)
		return(ERR_WRITE);
	res = read_serial(camera->serial, buf, 2);
	if (res < 2)
		return(ERR_READ);
	if ((buf[0] != line) || (buf[1] != camera->ccd->ncolumns))
		return(ERR_READ);

	res = read_serial(camera->serial, buf, camera->ccd->ncolumns);
	if (res < camera->ccd->ncolumns)
		return(ERR_READ);

	res = read_serial(camera->serial, &chksum, 1);
	if (res < 1)
		return(ERR_READ);
/* Evaluate checksum in future */

	return(ERR_OK);
}


int take_image(cam_info *camera, unsigned char *image)
{
	int res;
	if (!is_valid_camera(camera))
		return(ERR_CAM);
	if (camera->ccd->image == NULL)
		return(ERR_MEM);

	if ((res = expose_ccd(camera, camera->ccd->exptime)) != ERR_OK)
		return(res);

	if ((res = download_image(camera, image)) != ERR_OK)
		return(res);

	return(ERR_OK);

}


int download_image(cam_info *camera, unsigned char *image)
{
	int i, l;

	if (!is_valid_camera(camera))
		return(ERR_CAM);
	if (image == NULL)
		return(ERR_MEM);

	l = camera->ccd->first_line;
	for (i = 0; i < camera->ccd->nlines; i++, l++) {
		if (read_line(camera, l , image) != ERR_OK)
			return(ERR_READ);
/* Pad to next line */
		image += CAM_MAX_NCOLS;
	}

	return(ERR_OK);
}
