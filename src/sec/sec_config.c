/***************************************************************************
                          getconf.c  -  description
                             -------------------
    begin                : Thu Sep 28 2000
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

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#include "fields.h"

#include "sec_config.h"

/* used to scan config file */
static const char *foptions[]  = {
        "NSTATCLIENTS", "INSTNAME", "STATUS", NULL
};
enum { NSTATCLIENTS, INSTNAME, STATUS };

SecConfig *sec_config_new(void) {

  SecConfig* config = (SecConfig *)calloc(1, sizeof(SecConfig));
  if (config == NULL) return (NULL);

  return config;

}

void sec_config_free(SecConfig* config) {

  free(config);

}

SecConfig *sec_config_new_from_file(char *conffile)
{
        SecConfig *opts;
        FILE *cfile;
        char buf[MAXBUFLEN];
        char *ptr;
        field f;
        int i, tmp;
        int line = 0;

        if (conffile == NULL) return (NULL);

	opts = sec_config_new();

	if(opts == NULL) return NULL;

        /* Number of status fields */
        opts->nstatus = 0;
        opts->maxclnt = -1;

        cfile = fopen(conffile, "r");
        if (cfile == NULL) {
                free(opts);
                return (NULL);
        }

        while (fgets(buf, MAXBUFLEN, cfile) != NULL) {
                line++;
                i = getfield(buf, &f, foptions);
                switch (i) {
                case NSTATCLIENTS:
                        /* Get max. clients */
                        if (sscanf(f.contents,"%d",&tmp) == EOF)
                                tmp = DEF_MAXCLNT;
                        opts->maxclnt = tmp;
                        break;

                case INSTNAME:
                        ptr = opts->instname;
                        /* Get instrument name */
                        while (!isspace(*f.contents) && *f.contents != '\0')
                                *ptr++ = *f.contents++;
                        break;

                case STATUS:
                        ptr = opts->fstatus[opts->nstatus];
                        tmp = 0;
                        /* Store in status field table */
                        while (!isspace(*f.contents) && *f.contents != '\0') {
                                *ptr++ = *f.contents++;
                                if (++tmp == MAX_FIELD_SIZE) break;
                        }
                        ptr = opts->fstatus[opts->nstatus];
                        /* Avoid having an empty fieldname */
                        if (*ptr != '\0') opts->nstatus++;
                        break;

                case FEMPTY_FIELD:
                        /* Comment or empty line */
                        break;

                case FNO_MATCH:
                case EOF:
                default:
                        fprintf(stderr,
                                "*** Config file: Error in line %d.\n", line);
                        abort();
                        break;
                }
        }
	if (*opts->instname == '\0') strcpy(opts->instname, DEF_INSTNAME);
	if (opts->maxclnt == -1) opts->maxclnt = DEF_MAXCLNT;

        fclose(cfile);
        return (opts);
}
