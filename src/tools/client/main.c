#include <stdio.h>
#include <unistd.h>
#include <ctype.h>
#include "sockets.h"

int main (int argc, char **argv)
{
	Socket *skt;
	int i, n;
	char buffer[500];
	int waitresponse = 0;

	skt = Sopen(argv[1],"c");
	if (skt == NULL) exit (1);

	Smaskset(skt);
	Smaskfdset(0);

	for(;;)	{
	        // is there anything new?
		i = Smaskwait();
		if (i <= 0) break;

		i = Stest(skt);
		if (i <= -1) break; // socket error
		else if (i > 0) {
		        // something new from server
			Sgets(buffer, 500, skt);
			printf("server> %s\n", buffer);
			waitresponse = 0;
			continue;
		}

		// only get new command after server response
		if (waitresponse) continue;

		if (Smaskfdisset(0)) {
		        // something new from stdin
			if (fgets(buffer, 500, stdin) == NULL) break;
			n = strlen(buffer);
			buffer[n-1] = '\0';
			if (n > 1) {
				Sputs(buffer, skt);
				printf("client> %s\n", buffer);
				waitresponse = 1;
			}
		}
	}
	Sputs("QUIT", skt); 
}
