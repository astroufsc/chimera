#include <stdio.h>
#include <unistd.h>
#include <ctype.h>
#include "sockets.h"

int main (int argc, char **argv)
{
	Socket *skt;
	int i, n;
	char buffer[500];

	skt = Sopen(argv[1],"c");
	if (skt == NULL) exit (1);

	for(;;)	{
		printf("client> ");
		fflush(stdout);
		fgets(buffer, 500, stdin);
		n = strlen(buffer);
		buffer[n-1] = '\0';
		if (n > 1)
			Sputs(buffer, skt);
		usleep(100000);
		i = Stest(skt);
		if (i == -1) exit(-1);
		else if (i > 0) {
			Sgets(buffer, 500, skt);
			printf("server> %s\n", buffer);
		}
	}
}
