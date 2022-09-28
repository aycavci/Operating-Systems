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
#include <sys/wait.h>
#include <sys/ipc.h>
#include <sys/msg.h

int main() {

    long int filesize;
    int shm_fd_A, shm_fd_B;
    void *ptrA, *ptrB;
    const char *name_A = "Memory_A";
    const char *name_B = "Memory_B";
    int size_A=0;
    int size_B=0;

    FILE *fp = stdin;
    fseek(fp, 0L, SEEK_END);
    filesize = ftell(fp);

    shm_fd_A = shm_open(name_A, O_CREAT | O_RDWR, 0666);
    ftruncate(shm_fd_A, filesize);
    ptrA =mmap(NULL, filesize, PROT_WRITE|PROT_READ, MAP_SHARED, shm_fd_A, 0);

    shm_fd_B = shm_open(name_B, O_CREAT | O_RDWR, 0666);
    ftruncate(shm_fd_B, filesize);
    ptrB =mmap(NULL, filesize, PROT_WRITE|PROT_READ, MAP_SHARED, shm_fd_B, 0);

    pid_t child_A;
    pid_t child_B;

    int fd[2];
    int fd2[2];

    if (pipe(fd) == -1) {
        fprintf(stderr,"Pipe failed");
        return 1;
    }

    if (pipe(fd2) == -1) {
        fprintf(stderr,"Pipe failed");
        return 1;
    }

    child_A = fork();
    if(child_A>0) {
        child_B = fork();
        if(child_B==0) {
            child_A = -5;
        }
    }

    if(child_A>0) { // inside parent
        close(fd[0]);
        close(fd2[0]);
        int c;
        write(fd[1], &filesize, sizeof(filesize)+1);
        write(fd2[1], &filesize, sizeof(filesize)+1);

        fseek(fp, 0, SEEK_SET);
        while(size_A<filesize) {
            c = fgetc(fp);
            write(fd[1], &c, sizeof(c)+1);
            size_A+= sizeof(c);
        }

        fseek(fp, 0, SEEK_SET);
        while(size_B<filesize*2) {
            c = fgetc(fp);
            write(fd[1], &c, sizeof(c)+1);
            size_B+= sizeof(c)*2;
        }

        close(fd2[1]);
        close(fd[1]);
        wait(NULL);
        wait(NULL);

    }else if(child_A==0) { //inside child_A
        char file[filesize];
        int c;
        close(fd[1]);
        fseek(fp, 0, SEEK_SET);
        for (int i=0; i<filesize; i++){
            read(fd[0], &c, 1);
            file[i] = (char)c;
        }
        file[filesize-1] = '\0';
        close(fd[0]);
        sprintf(ptrA, "%s", file);

        shm_unlink(name_A);

    } else if(child_A<0) { // inside child_B
        char file[filesize];
        int c;
        close(fd2[1]);
        fseek(fp, 0, SEEK_SET);
        for (int i=0; i<filesize; i++){
            read(fd2[0], &c, 1);
            file[i] = (char)c;
        }
        file[filesize-1] = '\0';
        close(fd2[0]);
        char * hexadecimal = malloc(2*filesize-1);
        for (int i = 0, j = 0; i < filesize - 1; ++i, j += 2)
            sprintf(hexadecimal + j, "%02x", file[i] & 0xff);
        sprintf(ptrB, "%s", file);

        shm_unlink(name_B);
    }

    return 0;
}



















