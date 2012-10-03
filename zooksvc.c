#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <sys/un.h>
#include <unistd.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <errno.h>

int
main(int ac, char *av[])
{
    if (ac != 4) {
	printf("Usage: %s dummy-fd sockpath binary\n", av[0]);
	exit(-1);
    }

    char *sockpn = av[2];
    char *bin = av[3];

    int srvfd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (srvfd < 0) {
	perror("socket");
	exit(-1);
    }

    fcntl(srvfd, F_SETFD, FD_CLOEXEC);

    struct stat st;
    if (stat(sockpn, &st) >= 0) {
	if (!S_ISSOCK(st.st_mode)) {
	    fprintf(stderr, "socket pathname %s exists and is not a socket\n",
		    sockpn);
	    exit(-1);
	}

	unlink(sockpn);
    }

    struct sockaddr_un addr;
    addr.sun_family = AF_UNIX;
    snprintf(&addr.sun_path[0], sizeof(addr.sun_path), "%s", sockpn);
    if (bind(srvfd, (struct sockaddr *) &addr, sizeof(addr)) < 0) {
        fprintf(stderr, "WARNING: cannot bind to socket %s (%s), exiting\n",
                sockpn, strerror(errno));
	exit(-1);
    }

    // allow anyone to connect; for access control, use directory permissions
    chmod(sockpn, 0777);

    listen(srvfd, 5);
    signal(SIGCHLD, SIG_IGN);
    signal(SIGPIPE, SIG_IGN);

    for (;;) {
	struct sockaddr_un client_addr;
	unsigned int addrlen = sizeof(client_addr);

	int cfd = accept(srvfd, (struct sockaddr *) &client_addr, &addrlen);
	if (cfd < 0) {
	    perror("accept");
	    continue;
	}

	int pid = fork();
	if (pid < 0) {
	    perror("fork");
	    close(cfd);
	    continue;
	}

	if (pid == 0) {
	    // Child process
	    dup2(cfd, 0);
	    dup2(cfd, 1);
	    close(cfd);

            signal(SIGCHLD, SIG_DFL);
            signal(SIGPIPE, SIG_DFL);

	    execl(bin, bin, 0);
	    perror("execl");
	    exit(-1);
	}

	close(cfd);
    }
}
