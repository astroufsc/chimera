/***************************************************************************
                          main.c  -  description
                             -------------------
    begin                : Tue Jul 11 14:18:57 BRT 2000
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

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <getopt.h>

#include "sec_server.h"

#define FALSE (0)
#define TRUE  (1)

#define PROGRAM_NAME "Socket Secretary"
#define URL "http://www.astro.ufsc.br/~andre/"
#ifndef VERSION
#define VERSION "Beta"
#endif

#define ROOT_DIR_ENV_VAR "UTS_DIR"
#define DEF_ROOT_DIR "/usr/local/uts"
#define DEF_CONF_FILE_NAME "/etc/sec.conf"


/*** Global variables filled by get_args() ***/
char *exec_name;        /* Name of executable file */
static char *conffname; /* configuration file */
static char *logfname;  /* log file */
static int detach = FALSE; /* should the program detach from terminal? */


static void print_title(void);
static void print_help(void);
static void print_version(void);
static void print_usage(void);
static void get_args(int argc, char **argv);
static void goto_bg(void);


/*-------------------------------------------------------------------------*/

int main(int argc, char **argv)
{

        SecServer *sec;

        /* Parse arguments */
        get_args(argc, argv);

        /* Open log file and redirect stdout, if required */
        if (logfname != NULL) {
                fprintf(stderr, " -> Logging to file \"%s\".\n", logfname);
                stdout = freopen(logfname, "a", stdout);
                if (stdout == NULL) {
                        fprintf(stderr, "*** Error opening file \"%s\".\n",
                                logfname);
                        exit(1);
                }
        }

        /*** The function exit() is not recommended hereafter. ***/
        /*** Use abort() instead.                              ***/

	sec = sec_server_new();
	if(sec == NULL) abort();

        /* Set signal handlers and get configuration */
        fprintf(stderr, " -> Getting configuration from file \"%s\".\n", conffname);

        if(sec_server_configure(sec, conffname) == FALSE)
	  abort();

        /* Open the servers */
        fprintf(stderr, " -> Opening servers for instrument %s.\n", sec->config->instname);

        sec_server_run(sec);

        fprintf(stderr, " -> OK, working.\n");

        if (detach) {
                /* Detach from terminal (daemon mode) */
                fprintf(stderr, " -> Jumping into background...\n\n");
                goto_bg();
                /* close stdout if no logfile specified */
                if (logfname == NULL) fclose(stdout);
        }


        /*** Main loop ***/
        while (sec_server_wait(sec) >= 0) {
                /* Do any periodic stuff here, but don't overload. */
                /* -> check inactive sockets every */
                sec_server_check(sec);
        }

        /* waitsockets failed! */
        printf("*** Program crash.\n");
        abort();
}

/*-------------------------------------------------------------------------*/

static void print_title(void)
{
        printf("%s %s\n", PROGRAM_NAME, VERSION);
}

/*-------------------------------------------------------------------------*/

static void print_help(void)
{
        print_title();
        printf("This program requires Socket PortMaster (Spm) running.\n");
#ifdef NOTIFY_ON_CHANGE
        printf("This version notifies only when status changes.\n\n\n");
#else
        printf("This version notifies always.\n\n\n");
#endif
        print_usage();
        printf("\nIf no config file is specified, this program will search "
               "under the environment\n"
               "variable %s:\n\n"
               "        ${%s}%s\n\n", ROOT_DIR_ENV_VAR, ROOT_DIR_ENV_VAR,
               DEF_CONF_FILE_NAME);
        printf("If this file does not exists, this program will try "
               "the following file:\n\n"
               "        %s%s\n\n\n", DEF_ROOT_DIR, DEF_CONF_FILE_NAME);
        printf("Command line options:\n\n"
               "        -h / --help\n"
               "                This help screen.\n\n"

               "        -v / --version\n"
               "                Display version and copyright "
               "                information.\n\n"

               "        -d / --detach\n"
               "                Daemon mode.\n"
               "                Put the program in background.\n\n"

               "        -o <logfile> / --output <logfile>\n"
               "                Redirect output to <logfile>,\n"
               "                instead of showing it on the terminal.\n\n\n"
               );

        printf("Visit the home page\n"
               "%s\n"
               "for more information.\n\n", URL);
        exit(0);
}

/*-------------------------------------------------------------------------*/

static void print_version(void)
{
        print_title();
        printf("Copyright (C) 2001 Andre Luiz de Amorim\n");
        printf("%s comes with NO WARRANTY,\n"
               "to the extent permitted by law.\n", PROGRAM_NAME);
        printf("You may redistribute copies of %s\n"
               "under the terms of the GNU General Public License.\n"
                "For more information about these matters,\n"
                "see the files named COPYING.\n", PROGRAM_NAME);

        exit(0);
}

/*-------------------------------------------------------------------------*/

static void print_usage(void)
{
        printf("SYNTAX:\n"
               "       %s [-o <logfile>] [-d] [config_file]\n\n"
               "       %s {-h|--help}\n\n", exec_name, exec_name);
}

/*-------------------------------------------------------------------------*/

static void get_args(int argc, char **argv)
{
        int next_opt;
        const char *short_options = "hvdo:";
        const struct option long_options [] = {
                { "help", 0, NULL, 'h' },
                { "version", 0, NULL, 'v' },
                { "detach", 0, NULL, 'd' },
                { "output", 1, NULL, 'o' },
                { NULL, 0, NULL, 0 }
        };

        exec_name = argv[0];
        conffname = NULL;
        logfname  = NULL;
        do {
                next_opt = getopt_long(argc, argv, short_options,
                                       long_options, NULL);
                switch (next_opt) {
                case 'h':
                        print_help();
                        break;

                case 'v':
                        print_version();
                        break;

                case 'd':
                        detach = TRUE;
                        break;

                case 'o':
                        /* log file name */
                        logfname = optarg;
                        break;

                case '?':
                        /* Invalid option */
                        print_usage();
                        exit(1);
                        break;

                case -1:
                        /* end of options */
                        break;

                default:
                        abort();
                        break;
                }
        } while (next_opt != -1);

        if (optind < argc)
                /* config file is the first non-option argument */
                conffname = argv[optind];

        /* If config file is not specified, try to get it from environment */
        if (conffname == NULL) {
                int n;
                char *root_dir = getenv(ROOT_DIR_ENV_VAR);
                if (root_dir == NULL) root_dir = DEF_ROOT_DIR;

                n = strlen(root_dir) + strlen(DEF_CONF_FILE_NAME) + 1;
                conffname = calloc(n, sizeof(char));
                strncpy(conffname, root_dir, n);
                strncat(conffname, DEF_CONF_FILE_NAME, n);
        }
}

/*-------------------------------------------------------------------------*/

static void goto_bg(void)
{
        int daemon = 0;

        daemon = fork();
        if (daemon < 0) fprintf(stderr,
                               "*** Error: Could not detach from terminal\n");
        else if (daemon) exit(0); /* We're the parent, so bye-bye! */

        setsid(); /* release controlling terminal */

}

/*-------------------------------------------------------------------------*/
