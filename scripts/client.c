/*
 * NagiosLogger C Client
 * Author: Thomas Guyot-Sionnest <tguyot@gmail.com>
 *
 * Dev build:
 *   gcc -Wall -lzmq -o client client.c
 *
 * Normal build:
 *   gcc -O2 -DNDEBUG -lzmq -o client client.c && strip client
 *
 */

/* This is the send timeout in miliseconds */
#define SEND_TIMEOUT 1000000 /* 1 second */

#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
#include <string.h>
#include <zmq.h>


/* Send formatted message to url */
int
logevent(char *url, char *message)
{
	int rc, result;
	void *ctx, *socket;
	zmq_msg_t query;
	zmq_pollitem_t items[1];

	/* Send the message */
	rc = zmq_msg_init_size(&query, strlen(message));
	assert(rc == 0);

	memcpy(zmq_msg_data(&query), message, strlen(message));

	ctx = zmq_init (1, 1, ZMQ_POLL);
	assert(ctx);

	socket = zmq_socket(ctx, ZMQ_REQ);
	assert(socket);

	rc = zmq_connect(socket, url);
	assert(rc == 0);

	rc = zmq_send(socket, &query, 0);
	assert(rc == 0);

	zmq_msg_close(&query);

	/* Wait for a reply */
	rc = zmq_msg_init(&query);
	assert(rc == 0);

	items[0].socket = socket;
	items[0].events = ZMQ_POLLIN;
	rc = zmq_poll(items, 1, SEND_TIMEOUT); /* FIXME: zmq_poll may return 0 before timeout */
	assert(rc >= 0);

	rc = zmq_recv(socket, &query, ZMQ_NOBLOCK);
	if (rc == -1 && errno == EAGAIN) {
		result = 0;
	} else {
		assert(rc == 0);
		zmq_msg_close(&query);
		result = 1;
	}

	/* Clean up - FIXME: random SEGV on zmq_term
	zmq_close(socket);
	zmq_term(ctx);
	*/

	return result;
}

/* Print usage and exit */
void
usage(const char *progname, const char *error_msg)
{

	assert(progname != NULL);
	if (error_msg)
		printf("Error: %s\n", error_msg);

	printf("\n");
	printf("Usage: %s <ZMQ_URL> <Server> <Notification Type> <Service State ID> <Host> <Service Desc> <Message>\n", progname);
	printf("Usage: %s <ZMQ_URL> <Server> <Notification Type> <Host State ID> <Host> <Message>\n", progname);

	if (error_msg)
		exit(1);

	exit(0);
}

/* Parse arguments and format message */
int
main(int argc, char **argv)
{
	int i, rc;
	char *url, *server, *notype, *stateid, *host, *message;
	char *fmt_msg = NULL;
	char *service = NULL;
	const char *paramtype = "";

	if (argc < 7 || argc > 8) {
		for (i=1; i<argc; i++) {
			if (strcmp(argv[i], "-h") == 0 ||
			    strcmp(argv[i], "--help") == 0) {
				usage(argv[0], NULL);
			}
		}
		usage(argv[0], "Wrong number of arguments");
	}

	for (i=1; i<argc; i++) {
		switch (i) {
			case 1:
				url = strdup(argv[i]);
				break;
			case 2:
				server = strdup(argv[i]);
				break;
			case 3:
				notype = strdup(argv[i]);
				break;
			case 4:
				stateid = strdup(argv[i]);
				if (strlen(stateid) != strspn(stateid, "0123456789"))
					usage(argv[0], "State ID is not a number");
				break;
			case 5:
				host = strdup(argv[i]);
				break;
			case 6:
				if (argc == 7) {
					message = strdup(argv[i]);
					paramtype = "Host";
				}	else {
					service = strdup(argv[i]);
					paramtype = "Service";
				}
				break;
			case 7:
				message = strdup(argv[i]);
				break;
		}
	}

	/* Format is: server(str)[Tab]notificationtype(str)[Tab]stateid(int)[Tab]host(str)[Tab]service(str)[Tab]message(str) */
	i = strlen(server) + strlen(notype) + strlen(stateid) + strlen(host) + (service ? strlen(service) : 0) + strlen(message) + 5 ;
	fmt_msg = malloc(i+1);
	assert(fmt_msg != NULL);
	rc = snprintf(fmt_msg, i+1, "%s\t%s\t%s\t%s\t%s\t%s", server, notype, stateid, host, service ? service : "", message);
	assert(rc == i);

	if (logevent(url, fmt_msg)) {
		printf("Successfully sent %s Alert event to %s\n", paramtype, url);
		exit(0);
	}
	printf("Failed sending %s Alert event to %s\n", paramtype, url);
	exit(1);

}

