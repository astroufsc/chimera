#ifndef _SEC_SERVER_H_
#define _SEC_SERVER_H_ 1

// #include "sdict.h"
#include "server.h"
#include "sec_config.h"

#define WAIT_TIME    (1) /* seconds */
#define DEF_STATUS_CONTENT "EMPTY"
#define DEF_INSTSTATUS_CONTENT "OFFLINE"

/* Field name for connection monitoring */
#define STPING "PING"

#define STATUS_INSTNAME (0)
#define STATUS_PING (1)

typedef struct _SecServer SecServer;

struct _SecServer {
  char *instname;

  SecConfig *config;

//   SDict *status;
//   SDict* notify;

  Server *statsrv;
  Server *instsrv;

};

SecServer	*sec_server_new(void);

void	 sec_server_free(SecServer* sec);
int	 sec_server_configure(SecServer* sec, const char *cfile);
int	 sec_server_run(SecServer* sec);
int 	 sec_server_wait(SecServer* sec);
int	 sec_server_check(SecServer* sec);

// int		 sec_server_add_status(SecServer* sec, const char* status);
// int		 sec_server_free_status(SecServer* sec, const char* status);
// int		 sec_server_set_status(SecServer* sec, const char* status, const char* contents);
// const char*	 sec_server_get_status(SecServer* sec, const char* status);

// int	 sec_server_set_notify(SecServer* sec, SktListItem* client, const char* status);
// int	 sec_server_remove_notify(SecServer* sec, SktListItem* client, const char* status););

/* from status.c */

int fill_statlist(char *instname,
                  char fstatus[][MAX_FIELD_SIZE], int nst);
int   add_status(char *name);
void  free_status(void);
int   set_istatus(int i, char *contents);
int   set_status(char *name, char *contents);
int   set_status_str(char *statstr);
char *get_istatus(int i);
char *get_status(char *name);

int set_notify(SktListItem *client, char *statfield);
int set_inotify(SktListItem *client, int i);
int rmv_notify(SktListItem *client, char *statfield);
int rmv_inotify(SktListItem *client, int i);


#endif /* !_SEC_SERVER_H_ */
