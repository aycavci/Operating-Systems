#include <stdio.h>
#include <sys/types.h>
#include <unistd.h>
#include <signal.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <string.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <stdlib.h>
#include <signal.h>
#include <sys/wait.h> // wait()
#include <sys/ipc.h>
#include <sys/msg.h>

// for message passing
struct mesg_buffer {
    long mesg_type;
    char mesg_text[100];
} message1, message2;


int main()
{
   
    // creating message

    key_t key1, key2;
    int msgid1, msgid2;
 
    // ftok to generate unique key1
    key1 = ftok("progfile", 65);
    key2 = ftok("progfile", 66);
 
    // msgget creates a message queue
    // and returns identifier
    msgid1 = msgget(key1, 0666 | IPC_CREAT);
    msgid2 = msgget(key1, 0666 | IPC_CREAT);

FILE *f = stdin;
fseek(f, 0, SEEK_END);
long len = ftell(f);
fseek(f, 0, SEEK_SET);  

char * shm_1 = "Child A SHM";
char * shm_2 = "Child B SHM";
void* ptr1, *ptr2;
int shmfd1, shmfd2;

shmfd1=shm_open(shm_1, O_CREAT| O_RDWR, 0666); //returns a fd that we can use in subsequent calls child A
ftruncate(shmfd1, len);
ptr1 =mmap(NULL, len, PROT_WRITE|PROT_READ, MAP_SHARED, shmfd1, 0);

shmfd2=shm_open(shm_2, O_CREAT| O_RDWR, 0666); //returns a fd that we can use in subsequent calls child B
ftruncate(shmfd2, 2 * len - 1);
ptr2 =mmap(NULL, 2 * len - 1, PROT_WRITE|PROT_READ, MAP_SHARED, shmfd2, 0);

int pipe1[2];
if (pipe(pipe1) == -1)
{
perror("pipe");
exit(EXIT_FAILURE);
}
int pipe2[2];
if (pipe(pipe2) == -1)
{
perror("pipe");
exit(EXIT_FAILURE);
}
pid_t pid1 = fork();
if (pid1 == 0) // child A
{
close(pipe1[1]);
close(pipe2[1]);
close(pipe2[0]);
int c;
char str[len];
for (int i=0; i<len; i++){
read(pipe1[0], &c, 1);
str[i] = (char)c;
//printf("%s", str);
}
str[len-1] = '\0';
close(pipe1[0]);

//printf("Child A from pipe:\n%s", str);
sprintf(ptr1, "%s", str);

message1.mesg_type = 1;
//message.mesg_text = malloc(strlen("done")+1);
strcpy(message1.mesg_text, "done");
msgsnd(msgid1, &message1, sizeof(message1), 0);

shm_unlink(shm_1);
shm_unlink(shm_2);
}
else {
pid_t pid2 = fork();
if (pid2 == 0) // child B
{
close(pipe1[1]);
close(pipe1[0]);
close(pipe2[1]);
int c;
char str[len];
for (int i=0; i<len; i++){
read(pipe2[0], &c, 1);
str[i] = (char)c;
//printf("%s", str);
}
str[len-1] = '\0';
close(pipe2[0]);
//printf("Child B from pipe:\n%s", str);
char * hex = malloc(2*len-1);
for (int i = 0, j = 0; i < len - 1; ++i, j += 2)
    sprintf(hex + j, "%02x", str[i] & 0xff);

    //printf("Child B hex:\n%s", hex);
    sprintf(ptr2, "%s", hex);

    message2.mesg_type = 1;
//message.mesg_text = malloc(strlen("done")+1);
strcpy(message2.mesg_text, "done");
msgsnd(msgid2, &message2, sizeof(message2), 0);

shm_unlink(shm_1);
shm_unlink(shm_2);

}
else // parent
{
close(pipe1[0]);
int c;

while ((c = fgetc(f)) != EOF) {
write(pipe1[1], &c, 1);
write(pipe2[1], &c, 1);
}

close(pipe1[1]);
close(pipe2[1]);

wait(NULL);
wait(NULL);

//if (strcmp(msg1, "done"))
msgrcv(msgid1, &message1, sizeof(message1), 1, 0);
if (strcmp(message1.mesg_text, "done") == 0)
printf("Parent from child A: %s\n",(char*)ptr1);

msgrcv(msgid2, &message2, sizeof(message2), 1, 0);
if (strcmp(message2.mesg_text, "done") == 0)
fprintf(stderr,"Parent from child B: %s\n",(char*)ptr2);

}
}

return 0;
}
