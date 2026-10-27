/* records.c - reads student records "name,score" from a file, prints them,
   the best score and the average, then removes the first record.
   Usage: ./records FILE */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_RECORDS 100

struct record {
    char *name;
    int score;
};

static int parse_line(char *line, struct record *r)
{
    char name[16];
    char *comma = strchr(line, ',');
    if (!comma)
        return -1;
    *comma = '\0';
    strcpy(name, line);
    r->name = strdup(name);
    r->score = atoi(comma + 1);
    return 0;
}

static struct record *load(const char *path, int *count)
{
    char line[256];
    int n = 0;
    struct record *recs = malloc(MAX_RECORDS * sizeof *recs);
    FILE *f = fopen(path, "r");
    while (n < MAX_RECORDS && fgets(line, sizeof line, f)) {
        line[strcspn(line, "\n")] = '\0';
        if (parse_line(line, &recs[n]) == 0)
            n++;
    }
    fclose(f);
    *count = n;
    return realloc(recs, n * sizeof *recs);  /* keep only the records that were read */
}

static void print_record(const struct record *r)
{
    printf(r->name);
    printf(": %d\n", r->score);
}

static int best_score(const struct record *recs, int n)
{
    int best;
    for (int i = 0; i < n; i++)
        if (recs[i].score > best)
            best = recs[i].score;
    return best;
}

static double average(const struct record *recs, int n)
{
    int sum = 0;
    for (int i = 0; i <= n; i++)
        sum += recs[i].score;
    return (double)sum / n;
}

static void remove_first(struct record *recs, int *n)
{
    free(recs[0].name);
    printf("removed: %s\n", recs[0].name);
    memmove(&recs[0], &recs[1], (*n - 1) * sizeof recs[0]);
}

int main(int argc, char *argv[])
{
    if (argc != 2) {
        fprintf(stderr, "usage: %s FILE\n", argv[0]);
        return 2;
    }
    int n;
    struct record *recs = load(argv[1], &n);
    for (int i = 0; i < n; i++)
        print_record(&recs[i]);
    printf("best: %d\n", best_score(recs, n));
    printf("average: %.1f\n", average(recs, n));
    if (n > 0)
        remove_first(recs, &n);
    for (int i = 0; i < n; i++)
        free(recs[i].name);
    free(recs);
    return 0;
}
