#include <stdio.h>
#include <dirent.h>
#include <fnmatch.h>
#include <libgen.h>
#include <string.h>

static int matchfits(const struct dirent *d);

static char pattern[256];


// returns last index of bfname-####.fits
int getindex(char *bfname)
{
  struct dirent **namelist;
  int nd;
  char scanfmt[256];
  char dirc[256];
  char basec[256];
  char *dir, *base;
  char *lastent;
  int lastindex;

  strncpy(dirc, bfname, 255);
  strncpy(basec, bfname, 255);
  dir = dirname(dirc);
  base = basename(basec);

  snprintf(pattern, 255, "%s-[0-9][0-9][0-9][0-9].fits", base);

  //find files that match pattern, see matchfits() below
  nd = scandir(dir, &namelist, matchfits, alphasort);
  if (nd == 0) // no file with this base name
    return -1;

  // extract index from filename
  snprintf(scanfmt, 255, "%s-%%d.fits", base);
  lastent = namelist[nd-1]->d_name;
  sscanf(lastent, scanfmt, &lastindex);

  /* TODO: must somehow free the space allocated by scandir()
  for (i = 0; i < nd; i++) {
    free(namelist[i]->d_name);
  } 
  free(namelist);
  */

  return lastindex;

}



int matchfits(const struct dirent *d)
{
  //printf("pattern: %s\nfname  : %s\n\n", pattern, d->d_name);
  return !fnmatch(pattern, d->d_name, FNM_PATHNAME);
}
