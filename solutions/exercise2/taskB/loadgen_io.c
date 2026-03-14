#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>
#include <omp.h>
#include <signal.h>

#define MAX_FILENAME_LENGTH 256

static int run = 1; 

void random_string(char *s, const int len) {
    static const char charset[] = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    for (int i = 0; i < len; i++) {
        int r = rand() % (int) (sizeof(charset) - 1);
        s[i] = charset[r];
    }
    s[len-1] = '\0';
}

int random_number(int min, int max) {
    return min + rand() % (max - min + 1);
}

void create_files(const char* dirname, int num_files, int min_file_size, int max_file_size) {
    char full_dirname[MAX_FILENAME_LENGTH];
    snprintf(full_dirname, MAX_FILENAME_LENGTH, "generated/%s", dirname);
    mkdir(full_dirname, 0755); // Create the directory
    int j;
    for (j = 0; j < num_files; j++) {
        char filename[MAX_FILENAME_LENGTH];
        int written = snprintf(filename, MAX_FILENAME_LENGTH, "%s/file_%d", full_dirname, j);
        if(written < 0 || written >= MAX_FILENAME_LENGTH) {
            fprintf(stderr, "Error building file path");
        }

        int size = random_number(min_file_size, max_file_size);
        char *data = (char*)malloc(size);
        random_string(data, size);

        FILE *fp = fopen(filename, "wb");
        fwrite(data, 1, size, fp);
        fclose(fp);

        free(data);
    }
    for (int i = 0; i < num_files; i++){
        char filename[MAX_FILENAME_LENGTH];
        int written = snprintf(filename, MAX_FILENAME_LENGTH, "%s/file_%d", full_dirname, j);
        if(written < 0 || written >= MAX_FILENAME_LENGTH) {
            fprintf(stderr, "Error building file path");
        }
        remove(filename);
    }
}

void handler(int param) {
  (void)(param);
  run = 0;
}

int main(int argc, char** argv) {
    signal(SIGINT, handler);
    signal(SIGTERM, handler);
    int num_directories, num_files, min_file_size, max_file_size, seed, number_of_threads;

    // Set default values for the parameters
    num_directories = 1;
    num_files = 10;
    min_file_size = 1024;
    max_file_size = 1048576;
    seed = 1234; // Set default seed to 1234
    number_of_threads = 1;

    // Parse command line arguments
    switch (argc) {
        case 7:
            number_of_threads = atoi(argv[6]);
        case 6:
            seed = atoi(argv[5]);
            // fall through
        case 5:
            num_directories = atoi(argv[1]);
            num_files = atoi(argv[2]);
            min_file_size = atoi(argv[3]);
            max_file_size = atoi(argv[4]);
            break;
        default:
            fprintf(stderr, "Usage: %s <num_directories> <num_files_per_directory> <min_file_size> <max_file_size> [<seed>] [<threads>]\n", argv[0]);
            return 1;
    }

    srand(seed); // Seed the random number generator

    mkdir("generated", 0755); // Create the parent directory

    #pragma omp parallel for
    for (int i = 0; i < number_of_threads; i++){
        while(run){
            for (int j = 0; j < num_directories; j++) {
                char dirname[MAX_FILENAME_LENGTH];
                snprintf(dirname, MAX_FILENAME_LENGTH, "dir_thread_%d_%d",i, j);
                create_files(dirname, num_files, min_file_size, max_file_size);
            }
        }
    }
    

    return 0;
}
