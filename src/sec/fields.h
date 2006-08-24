/***************************************************************************
                          fields.h  -  command identification
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

#define MAX_FIELD_SIZE    (50)
#define MAX_FIELD_CONTENTS (255)
#define FCOMMENT_CHAR '#'



#define FNO_MATCH    (-10)
#define FEMPTY_FIELD (-11)

typedef struct {
	int index;      /* position of field in list */
	char *contents; /* points to field contents in command */
} field;


/* getfield() breaks ``command'' in a field, contained in ``flist'',
   and its contents. It ignores whitespace before and after field
   (see example). Also, a `#' beginning character could be used as
   ``comment character''.

   Field and contents are stored in a ``field'' structure; ``index''
   is the position of the field in ``flist''. The return value is index,
   if successfull, FNO_MATCH if the command isn't in ``flist'' and
   FEMPTY_FIELD if command is an empty command.
   If ``f'' is NULL, getfield just gets the index and returns.

   Example:

        #include "getfield.h"

        (...)

        cmd = "  FIELD2    CONTENTS";
        char *fl[] = { "FIELD1", "FIELD2", "FIELD3" };
        field f;
        int i;

        (...)

        i = getfield(cmd, &f, fl);            // i == 1
        printf("Index: %d\n", f.index);       // Index: 1
        printf("Contents: %s\n", f.contents); // Contents: CONTENTS

   */

int getfield(char *command, field *f, const char *flist[]);

#endif /* FIELDS_H */
