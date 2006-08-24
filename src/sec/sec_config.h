/***************************************************************************
                          getconf.h  -  description
                             -------------------
    begin                : Fri Sep 29 2000
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
#ifndef _SEC_CONFIG_H_
#define _SEC_CONFIG_H_ 1

#include "fields.h"

/*** Default values ***/
#define DEF_INSTNAME "SEC"
#define DEF_MAXCLNT     (10)

#define MAXBUFLEN      (128)
#define MAX_SERVERNAME  (32)

#define MAX_STATUS_FIELDS  (200)
#define MAX_STATUS_CONTENTS (256)


typedef struct _SecConfig SecConfig;

struct _SecConfig {
        char instname[MAX_SERVERNAME];
        int maxclnt; /* maximum number of clients for status server */
        char fstatus[MAX_STATUS_FIELDS][MAX_FIELD_SIZE];
        int nstatus;
};

SecConfig *sec_config_new(void);
void	   sec_config_free(SecConfig* config);
SecConfig *sec_config_new_from_file(char *conffile);

#endif /* !_SEC_CONFIG_H */
