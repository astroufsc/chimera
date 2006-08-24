/***************************************************************************
                          errors.h  -  description
                             -------------------
    begin                : Wed Jun 14 2000
    copyright            : (C) 2000 by Andre Luiz de Amorim
    email                : andre@astro.ufsc.br
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
#define TRUE	(1)
#define FALSE	(0)



#define ERR_OK			 (0)
#define ERR_OPENTTY		(-1)
#define ERR_SERIAL		(-2)
#define ERR_BAUDRATE		(-3)
#define ERR_PARITY		(-4)
#define ERR_STOPB		(-5)
#define ERR_WRITE		(-6)
#define ERR_READ		(-7)
#define ERR_MEM			(-8)
#define ERR_NOTRESPOND		(-9)

#define ERR_CAM			(-50)
#define ERR_CMD			(-51)
#define ERR_EXPOSE		(-52)
