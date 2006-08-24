/* xstdlib.h: has standard library function prototypes */
#ifndef XSTDLIB_H
#define XSTDLIB_H

#include <sys/types.h>

/* Prototypes for standard library functions */
extern char *calloc();
extern void  exit();
extern char *getenv();
extern char *index();
extern char *malloc();
extern char *strchr();
extern char *strrchr();
#define remove unlink


#endif
