/***************************************************************************
                          fields.c  -  description
                             -------------------
    begin                : Wed Jun 7 2000
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
#include <ctype.h>
#include <string.h>
#include "fields.h"

/* char *fieldnames[] = { "EXPTIME", "START", "NEXP", "BFNAME", "INDEX", "BEGPIXX", "BEGPIXY", "ENDPIXX", "ENDPIXY" }; */
extern char *fieldnames[];

#ifdef FIELDTEST
int main(void)
{
	field f;
	char texto[] = " # EXPTIME  1.3 ";

	if (get_field(texto, &f) == EOF) {
		puts("Comment line");
		return(1);
	}
	printf("The field is %s. Contents: %s\n\n", fieldnames[f.index], f.contents);
	return(0);
}
#endif /* FIELDTEST */



int get_field(char *command, field *f)
{
	int i;
	char tmp[MAX_FIELD_SIZE];
	char *ptr;

	if (command == NULL || *command == '\0') return(EOF);
	/* find field type */
	ptr = tmp;
	while (isspace(*command)) command++;
	if (*command == COMMENT_CHAR) return(EOF);
	while (!isspace(*command)) *ptr++ = *command++;
	*ptr = '\0';
	for (i = 0; (i < 6) && strncmp(tmp, fieldnames[i], MAX_FIELD_SIZE); i++);
	f->index = i;

	/* store field content */
	ptr = f->contents;
	while (isspace(*command)) command++;
	while (*ptr++ = *command++);
	*(ptr -= 2) = '\0';
	
/*	strcpy(f->contents, command); */
	return(i);
}

