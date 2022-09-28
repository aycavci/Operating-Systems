#include <iostream>
#include <cstdlib>
#include <cstdio>
#include "pthread_sleep.c"
#include <queue>
#include <cstdlib>
#include <pthread.h>
#include <vector>
#include <ctime>
#include <random>
#include <getopt.h>
#include <cassert>
#include <unistd.h>
#include <cstring>
#include <random>
#include <algorithm>

using namespace std;

int t=1;
int s=60;
int n=20;
double p=0.5;

time_t current_time=0;
time_t start_time=0;

int landing_plane_ID = 2;
int departing_plane_ID = 1;

// declare mutexes
pthread_mutex_t time_mutex=PTHREAD_MUTEX_INITIALIZER;

pthread_mutex_t landing_ID_mutex=PTHREAD_MUTEX_INITIALIZER;
pthread_mutex_t departing_ID_mutex=PTHREAD_MUTEX_INITIALIZER;

pthread_mutex_t landing_mutex=PTHREAD_MUTEX_INITIALIZER;
pthread_mutex_t departing_mutex=PTHREAD_MUTEX_INITIALIZER;
pthread_mutex_t emergency_mutex=PTHREAD_MUTEX_INITIALIZER;

pthread_mutex_t logList_mutex=PTHREAD_MUTEX_INITIALIZER;

// Plane struct
struct Plane {
    int ID=0;
    time_t arrivalTime=-1;
    time_t runwayTime=-1;
    time_t turnaroundTime=-1;
    pthread_mutex_t lock=PTHREAD_MUTEX_INITIALIZER;
    pthread_cond_t cond=PTHREAD_COND_INITIALIZER;
    string status="";
    bool permission = false;
};

// struct for comparing plane IDs to print them out in sorted order
struct PlaneComparator
{
    inline bool operator() (const Plane& plane1, const Plane& plane2)
    {
        return (plane1.ID < plane2.ID);
    }
};

// emergency, landing, departing queues
queue<Plane> emergency;
queue<Plane> landing;
queue<Plane> departing;

// vector to hold planes for log file
vector<Plane> logList;


// command line argument
void cmdline(int argc, char *argv[]) {
    int opt;
    while ((opt = getopt(argc, argv, "s:p:n:")) != -1) {
        switch (opt) {
            case 's':
                s = atoi(optarg);
                break;
            case 'p':
                p = atof(optarg);
                break;
            case 'n':
                n = atof(optarg);
                break;
            default:
                exit(EXIT_FAILURE);
        }
    }
}

// landing plane function
void *landing_plane(void *arrivalTime)
{
    Plane plane;
    plane.ID = landing_plane_ID;

    pthread_mutex_lock(&landing_ID_mutex);
    landing_plane_ID +=2;
    pthread_mutex_unlock(&landing_ID_mutex);

    plane.arrivalTime = (time_t) arrivalTime;

    plane.cond = PTHREAD_COND_INITIALIZER;
    pthread_cond_init(&plane.cond, NULL);

    plane.lock = PTHREAD_MUTEX_INITIALIZER;
    pthread_mutex_init(&plane.lock, NULL);

    //if arrival time is divisible to 40, then it is an emergency plane
    if((int)(size_t)arrivalTime%40==0 && (int)(size_t)arrivalTime!=0) {
        plane.status="E";
        pthread_mutex_lock(&emergency_mutex);
        pthread_mutex_lock(&logList_mutex);
        emergency.push(plane); // push plane to the emergency queue
        logList.push_back(plane); // add plane to the logList vector
        pthread_mutex_unlock(&logList_mutex);
        pthread_mutex_unlock(&emergency_mutex);
    } else { // else it is a landing plane
        plane.status="L";
        pthread_mutex_lock(&landing_mutex);
        pthread_mutex_lock(&logList_mutex);
        landing.push(plane); // push plane to the landing queue
        logList.push_back(plane); // add plane to the logList vector
        pthread_mutex_unlock(&logList_mutex);
        pthread_mutex_unlock(&landing_mutex);
    }
    pthread_mutex_lock(&plane.lock);

    while(!plane.permission) { // wait for permission from ATC tower
        pthread_cond_wait(&plane.cond, &plane.lock);
    }
    pthread_mutex_unlock(&plane.lock);

    pthread_cond_destroy(&plane.cond);
    pthread_mutex_destroy(&plane.lock);
    pthread_exit(0);
}

// departing plane function
void *departing_plane(void *arrivalTime)
{
    Plane plane;
    plane.ID = departing_plane_ID;
    plane.status="D";

    pthread_mutex_lock(&departing_ID_mutex);
    departing_plane_ID += 2;
    pthread_mutex_unlock(&departing_ID_mutex);

    plane.arrivalTime = (time_t) arrivalTime;

    plane.cond = PTHREAD_COND_INITIALIZER;
    pthread_cond_init(&plane.cond, NULL);

    plane.lock = PTHREAD_MUTEX_INITIALIZER;
    pthread_mutex_init(&plane.lock, NULL);

    pthread_mutex_lock(&departing_mutex);
    pthread_mutex_lock(&logList_mutex);
    departing.push(plane); // push plane to the departing queue
    logList.push_back(plane); // add plane to the logList vector
    pthread_mutex_unlock(&logList_mutex);
    pthread_mutex_unlock(&departing_mutex);

    pthread_mutex_lock(&plane.lock);

    while(!plane.permission) { // wait for permission from ATC tower
        pthread_cond_wait(&plane.cond, &plane.lock);
    }

    pthread_mutex_unlock(&plane.lock);

    pthread_cond_destroy(&plane.cond);
    pthread_mutex_destroy(&plane.lock);
    pthread_exit(0);
}

// air traffic control function
void *air_traffic_control(void *)
{
    time_t temp_time;

    // get current time
    pthread_mutex_lock(&time_mutex);
    time(&current_time);
    temp_time=current_time;
    pthread_mutex_unlock(&time_mutex);

    while(temp_time < start_time + s) {
        pthread_mutex_lock(&landing_mutex);
        pthread_mutex_lock(&departing_mutex);
        pthread_mutex_lock(&emergency_mutex);

        // first pop the emergency plane if the emergency queue is not empty
        if(!emergency.empty()) {
            pthread_mutex_lock(&emergency.front().lock);
            emergency.front().permission = true;
            pthread_mutex_unlock(&emergency.front().lock);

            // get plane's runway and turnaround time
            emergency.front().runwayTime = (int) (temp_time - start_time + 2*t);
            emergency.front().turnaroundTime = emergency.front().runwayTime - emergency.front().arrivalTime;

            // update plane's request time, runway time, turnaround time and permission in the logList
            pthread_mutex_lock(&logList_mutex);
            for(auto & i : logList) {
                if(emergency.front().ID==i.ID) {
                    i.runwayTime=emergency.front().runwayTime;
                    i.turnaroundTime=emergency.front().turnaroundTime;
                    i.permission=true;
                }
            }
            pthread_mutex_unlock(&logList_mutex);

            pthread_cond_signal(&emergency.front().cond);
            emergency.pop(); // pop the plane from emergency queue
            pthread_mutex_unlock(&emergency_mutex);
            pthread_mutex_unlock(&departing_mutex);
            pthread_mutex_unlock(&landing_mutex);
            pthread_sleep(2*t);
        } else if((!landing.empty() && landing.size()>=10 && (temp_time-start_time)-landing.front().arrivalTime>s/8) ||
        (!departing.empty() && departing.size()>=5 && (temp_time-start_time)-departing.front().arrivalTime>s/10)) {

            time_t min_arrivalTime = min(landing.front().arrivalTime, departing.front().arrivalTime);

            if(min_arrivalTime==landing.front().arrivalTime) {
                pthread_mutex_lock(&landing.front().lock);
                landing.front().permission = true;
                pthread_mutex_unlock(&landing.front().lock);

                // get plane's runway and turnaround time
                landing.front().runwayTime = (int) (temp_time - start_time + 2*t);
                landing.front().turnaroundTime = landing.front().runwayTime - landing.front().arrivalTime;

                // update plane's request time, runway time, turnaround time and permission in the logList
                pthread_mutex_lock(&logList_mutex);
                for(auto & i : logList) {
                    if(landing.front().ID==i.ID) {
                        i.runwayTime=landing.front().runwayTime;
                        i.turnaroundTime=landing.front().turnaroundTime;
                        i.permission=true;
                    }
                }
                pthread_mutex_unlock(&logList_mutex);

                pthread_cond_signal(&landing.front().cond);
                landing.pop(); // pop the plane from landing queue
                pthread_mutex_unlock(&emergency_mutex);
                pthread_mutex_unlock(&departing_mutex);
                pthread_mutex_unlock(&landing_mutex);
                pthread_sleep(2*t);
            } else {

                pthread_mutex_lock(&departing.front().lock);
                departing.front().permission = true;
                pthread_mutex_unlock(&departing.front().lock);

                // get plane's runway and turnaround time
                departing.front().runwayTime = (int) (temp_time - start_time + 2*t);
                departing.front().turnaroundTime = departing.front().runwayTime - departing.front().arrivalTime;

                // update plane's request time, runway time, turnaround time and permission in the logList
                pthread_mutex_lock(&logList_mutex);
                for(auto & i : logList) {
                    if(departing.front().ID==i.ID) {
                        i.runwayTime=departing.front().runwayTime;
                        i.turnaroundTime=departing.front().turnaroundTime;
                        i.permission=true;
                    }
                }
                pthread_mutex_unlock(&logList_mutex);

                pthread_cond_signal(&departing.front().cond);
                departing.pop(); // pop the plane from departing queue
                pthread_mutex_unlock(&emergency_mutex);
                pthread_mutex_unlock(&departing_mutex);
                pthread_mutex_unlock(&landing_mutex);
                pthread_sleep(2*t);
            }
        } else if(!landing.empty()) {

            pthread_mutex_lock(&landing.front().lock);
            landing.front().permission = true;
            pthread_mutex_unlock(&landing.front().lock);

            // get plane's runway and turnaround time
            landing.front().runwayTime = (int) (temp_time - start_time + 2*t);
            landing.front().turnaroundTime = landing.front().runwayTime - landing.front().arrivalTime;

            // update plane's request time, runway time, turnaround time and permission in the logList
            pthread_mutex_lock(&logList_mutex);
            for(auto & i : logList) {
                if(landing.front().ID==i.ID) {
                    i.runwayTime=landing.front().runwayTime;
                    i.turnaroundTime=landing.front().turnaroundTime;
                    i.permission=true;
                }
            }
            pthread_mutex_unlock(&logList_mutex);

            pthread_cond_signal(&landing.front().cond);
            landing.pop(); //pop the plane form landing queue
            pthread_mutex_unlock(&emergency_mutex);
            pthread_mutex_unlock(&departing_mutex);
            pthread_mutex_unlock(&landing_mutex);
            pthread_sleep(2*t);
        } else if(!departing.empty()) {

            pthread_mutex_lock(&departing.front().lock);
            departing.front().permission = true;
            pthread_mutex_unlock(&departing.front().lock);

            // get plane's runway and turnaround time
            departing.front().runwayTime = (int) (temp_time - start_time + 2*t);
            departing.front().turnaroundTime = departing.front().runwayTime - departing.front().arrivalTime;

            // update plane's request time, runway time, turnaround time and permission in the logList
            pthread_mutex_lock(&logList_mutex);
            for(auto & i : logList) {
                if(departing.front().ID==i.ID) {
                    i.runwayTime=departing.front().runwayTime;
                    i.turnaroundTime=departing.front().turnaroundTime;
                    i.permission=true;
                }
            }
            pthread_mutex_unlock(&logList_mutex);

            pthread_cond_signal(&departing.front().cond);
            departing.pop(); // pop the plane from departing queue
            pthread_mutex_unlock(&emergency_mutex);
            pthread_mutex_unlock(&departing_mutex);
            pthread_mutex_unlock(&landing_mutex);
            pthread_sleep(2*t);
        } else {

            pthread_mutex_unlock(&emergency_mutex);
            pthread_mutex_unlock(&departing_mutex);
            pthread_mutex_unlock(&landing_mutex);
        }
        // get current time
        pthread_mutex_lock(&time_mutex);
        time(&current_time);
        temp_time=current_time;
        pthread_mutex_unlock(&time_mutex);
    }
    pthread_exit(0);
}


int main(int argc, char *argv[]) {
    // random seed
    srand(time(NULL));

    // create file called plane.log
    FILE *planeLog;
    planeLog = fopen("./plane.log", "w+");

    time_t temp_time;

    pthread_t ATC_thread;
    pthread_t landing_thread;
    pthread_t departing_thread;

    cmdline(argc, argv);

    // initialize mutexes
    pthread_mutex_init(&landing_ID_mutex, NULL);
    pthread_mutex_init(&departing_ID_mutex, NULL);

    pthread_mutex_init(&time_mutex, NULL);

    pthread_mutex_init(&landing_mutex, NULL);
    pthread_mutex_init(&departing_mutex, NULL);
    pthread_mutex_init(&emergency_mutex, NULL);

    pthread_mutex_init(&logList_mutex, NULL);

    // get current time
    pthread_mutex_lock(&time_mutex);
    time(&current_time);
    temp_time=current_time;
    start_time=current_time;
    pthread_mutex_unlock(&time_mutex);

    // create planes at time 0 and create air traffic control thread
    pthread_create(&ATC_thread, NULL, air_traffic_control, NULL);
    pthread_create(&landing_thread, NULL, landing_plane, (void *)(temp_time-start_time));
    pthread_create(&departing_thread, NULL, departing_plane, (void *)(temp_time-start_time));

    printf("Running simulation...\n");

    while(temp_time < start_time + s) {
        double random_num = (double) rand() / (double) RAND_MAX;

        // if p>=random number, create landing thread
        if(random_num<=p ) {
            pthread_create(&landing_thread, NULL, landing_plane, (void *)(temp_time-start_time));
        }
        //if p<random number, create departing thread
        if(random_num<1-p) {
            pthread_create(&departing_thread, NULL, departing_plane, (void *)(temp_time-start_time));
        }
        pthread_sleep(1);

        // get current time
        pthread_mutex_lock(&time_mutex);
        time(&current_time);
        temp_time=current_time;
        pthread_mutex_unlock(&time_mutex);

        if(current_time - start_time >= n && current_time - start_time <= s) {
            printf("-----At %ld sec----- \n", current_time - start_time);

            // print planes waiting in the landing queue starting from time n (n is defined as 20 initially)
            printf("Air: ");

            pthread_mutex_lock(&landing_mutex);
            queue<Plane> temp_landing = landing;
            pthread_mutex_unlock(&landing_mutex);

            int size1 = temp_landing.size();

            if(size1!=0) {
                for(int i = 0; i<size1-1; i++) {
                    printf("%d, ", temp_landing.front().ID);
                    temp_landing.pop();
                }
                printf("%d\n", temp_landing.front().ID);
                temp_landing.pop();
            } else {
                printf("Landing queue is empty!\n");
            }

            // print planes waiting in the departing queue starting from time n (n is defined as 20 initially)
            printf("Ground: ");

            pthread_mutex_lock(&departing_mutex);
            queue<Plane> temp_departing = departing;
            pthread_mutex_unlock(&departing_mutex);

            int size2 = temp_departing.size();

            if(size2!=0) {
                for(int i = 0; i<size2-1; i++) {
                    printf("%d, ", temp_departing.front().ID);
                    temp_departing.pop();
                }
                printf("%d\n\n", temp_departing.front().ID);
                temp_departing.pop();
            } else {
                printf("Departing queue is empty!\n\n");
            }
        }
    }
    fprintf(planeLog, "PlaneID\tStatus\tRequest Time\tRunway Time\tTurnaround Time\n");
    fprintf(planeLog, "-------------------------------------------------------------------\n");

    // sort the logList according to IDs in increasing order
    sort(logList.begin(), logList.end(), PlaneComparator());

    // print planes to the plane.log file with their ID, status, request, runway and turnaround time
    for(auto & i : logList) {
        if(i.permission) {
            fprintf(planeLog, "%d\t\t\t%s\t\t\t%ld\t\t\t%ld\t\t\t%ld\n", i.ID, i.status.c_str(),
                    i.arrivalTime, i.runwayTime, i.turnaroundTime);
        } else {
            fprintf(planeLog, "%d\t\t\t%s\t\t\t%ld\n", i.ID, i.status.c_str(),
                    i.arrivalTime);
        }
    }
    fclose(planeLog); // close file
    printf("Simulation ended!"); // simulation ends
    return 0;
}