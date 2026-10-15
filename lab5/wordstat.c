/* wordstat.c - prints the number of words, the longest word
   and the average word length of a text file */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char *argv[])
{
    if (argc != 2) {
        fprintf(stderr, "usage: %s FILE\n", argv[0]);
        return 2;
    }

    FILE *f = fopen(argv[1], "r");
    if (!f) {
        perror(argv[1]);
        return 1;
    }

    char line[256];
    char *longest = NULL;
    int count = 0, total = 0;
    while (fgets(line, sizeof line, f)) {
        for (char *tok = strtok(line, " \t\n"); tok; tok = strtok(NULL, " \t\n")) {
            count++;
            total += strlen(tok);
            if (!longest || strlen(tok) > strlen(longest)) {
                longest = malloc(strlen(tok));
                strcpy(longest, tok);
            }
        }
    }
    fclose(f);

    printf("words: %d\n", count);
    printf("longest: %s\n", longest);
    printf("average length: %d\n", total / count);
    return 0;
}
