#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <stdlib.h>
#include <time.h>
#include <sys/time.h>
#include <sys/mman.h>
    
void main(int argc,char *argv[])
{
    int pgsz, memtoget;
    int memgotten = 0;
    void *region;

    memtoget = atoi(argv[1]);
    printf("obtaining at least %d MB\n",memtoget);
    memtoget *= 1000000;

    // pgsz = getpagesize();
    // printf("PGSZ %d\n",pgsz);

    while (memgotten < memtoget)
    {
        region = mmap(NULL, 1000000, PROT_READ|PROT_WRITE, MAP_ANONYMOUS|MAP_PRIVATE, -1, 0);
        printf("region %p\n",region);
        if (region == ((void *) -1)) 
        {
            perror("mmap failed");
            exit(-1);
        }
        memset(region,'Z',pgsz);
        memgotten += 1000000;
    }

    printf("DONE getting memory\n");
}
