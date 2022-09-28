#include <stdio.h>
#include <sys/types.h>
#include <unistd.h>
#include <signal.h>
#include <sys/time.h>
#include <time.h>


int main() {
    int i;
    int j;

    scanf("%d", &i);

    pid_t child_pid;
    pid_t grandchild_pid;

    int fd[2];
    int fd1[2];
    int fd2[2];
    int fd3[2];

    if (pipe(fd) == -1) {
        fprintf(stderr,"Pipe failed");
        return 1;
    }

    if (pipe(fd1) == -1) {
        fprintf(stderr,"Pipe failed");
        return 1;
    }

    if (pipe(fd2) == -1) {
        fprintf(stderr,"Pipe failed");
        return 1;
    }

    if (pipe(fd3) == -1) {
        fprintf(stderr,"Pipe failed");
        return 1;
    }

    child_pid = fork();
    sleep(5);

    if(child_pid==0) {
        grandchild_pid = fork();
        sleep(5);
        if(grandchild_pid==0){
            close(fd2[1]);
            close(fd3[0]);
            sleep(5);
            read(fd2[0], &i, sizeof(i));
            sleep(5);
            j = i*2;
            printf("Grandchild Input %d, Output %d\n", i, j);
            sleep(5);
            write(fd3[1], &j, sizeof(j));
            sleep(5);
            close(fd3[1]);
            close(fd2[0]);
        } else if(grandchild_pid>0) {
            close(fd[1]);
            close(fd2[0]);
            close(fd3[1]);
            close(fd1[0]);
            sleep(5);
            read(fd[0], &i, sizeof(i));
            sleep(5);
            j = i*2;
            printf("Child Input %d, Output %d\n", i, j);
            sleep(5);
            write(fd2[1], &j, sizeof(j));
            sleep(5);
            read(fd3[0], &i, sizeof(i));
            sleep(5);
            write(fd1[1], &i, sizeof(i));
            sleep(5);
            write(fd1[1], &grandchild_pid, sizeof(grandchild_pid));
            sleep(5);
            close(fd1[1]);
            close(fd3[0]);
            close(fd2[1]);
            close(fd[0]);
        }

    } else if(child_pid>0) {
        close(fd[0]);
        close(fd1[1]);
        sleep(5);
        write(fd[1], &i, sizeof(i));
        sleep(5);
        read(fd1[0], &i, sizeof(i));
        sleep(5);
        read(fd1[0], &grandchild_pid, sizeof(grandchild_pid));
        sleep(5);
        printf("Final result: %d\n", i);
        sleep(5);
        close(fd1[0]);
        close(fd[1]);
        kill(grandchild_pid, SIGKILL);
        kill(child_pid, SIGKILL);

    }
    return 0;
}


