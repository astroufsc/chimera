/***************************************************************************
                          fields.h  -  description
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
#ifndef FIELDS_H
#define FIELDS_H
#define MAX_FIELD_SIZE 20
#define MAX_FIELD_CONTENT 64
#define COMMENT_CHAR '#'

//extern char **fieldnames;

typedef struct {
	int index;
	char contents[MAX_FIELD_CONTENT];
} field;

int get_field(char *command, field *f);

#endif /* FIELDS_H */
