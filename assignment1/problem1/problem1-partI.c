#include <stdio.h>
#include <sys/types.h>
#include <unistd.h>
#include <signal.h>
#include <sys/time.h>
#include <time.h>



int main() {
    pid_t pid;
    pid = fork();

    if(pid==0) {
        while(1) {
            time_t t = time(NULL);
            struct tm *tm  = localtime((&t));
            printf("PID: %d Time: %s", getpid(), asctime(localtime(&t)));
            sleep(1);
        }
    }
    else if (pid>0) {
        sleep(5);
        kill(pid, SIGKILL);
        printf("Child %d killed\n", pid);
    }
    return 0;
}
