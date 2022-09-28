#include <stdio.h>
#include <sys/types.h>
#include <unistd.h>
#include <signal.h>
#include <sys/time.h>
#include <time.h>

int childFunc();

int main() {
    pid_t pid[4];
    pid[0] = fork();
    int i=0;

    if(pid[0]==0) {
        childFunc();
    } else if(pid[0]>0) {
        pid[1] = fork();
        if(pid[1]==0) {
            childFunc();
        } else if(pid[1]>0) {
            pid[2] = fork();
            if(pid[2]==0) {
                childFunc();
            } else if(pid[2]>=0) {
                pid[3] = fork();
                if(pid[3]==0) {
                    childFunc();
                } else if(pid[3]>0) {
                    sleep(5);
                    for(i=0; i<4; i++) {
                        kill(pid[i], SIGKILL);
                        printf("Child %d killed\n", pid[i]);
                    }
                }
            }
        }
    }
    return 0;
}

int childFunc() {
    while(1) {
        time_t t = time(NULL);
        struct tm *tm  = localtime((&t));
        printf("PID: %d Time: %s", getpid(), asctime(localtime(&t)));
        sleep(1);
    }
    return 0;
}
