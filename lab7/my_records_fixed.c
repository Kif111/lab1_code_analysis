/* records_fixed.c - Final secure version */
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
    char *comma = strchr(line, ',');
    if (!comma)
        return -1;
    *comma = '\0';
    
    // Fix 1 & 3: Allocate exact size dynamically (no truncation, no stack overflow)
    size_t name_len = strlen(line);
    r->name = malloc(name_len + 1);
    if (!r->name) return -1;
    strcpy(r->name, line); // Safe because we allocated enough space
    
    r->score = atoi(comma + 1);
    return 0;
}

static struct record *load(const char *path, int *count)
{
    char line[256];
    int n = 0;
    struct record *recs = malloc(MAX_RECORDS * sizeof *recs);
    if (!recs) return NULL;
    
    FILE *f = fopen(path, "r");
    if (!f) {
        free(recs);
        return NULL;
    }
    
    while (n < MAX_RECORDS && fgets(line, sizeof line, f)) {
        line[strcspn(line, "\n")] = '\0';
        if (parse_line(line, &recs[n]) == 0)
            n++;
    }
    fclose(f);
    *count = n;

    if (n == 0) {
        free(recs);
        return NULL;
    }

    // Fix: Safe realloc without leaking names on failure
    struct record *tmp = realloc(recs, n * sizeof *recs);
    if (tmp == NULL) {
        // If realloc fails, free everything to avoid leaks
        for (int i = 0; i < n; i++) {
            free(recs[i].name);
        }
        free(recs);
        return NULL;
    }
    return tmp;
}

static void print_record(const struct record *r)
{
    printf("%s: %d\n", r->name, r->score);
}

static int best_score(const struct record *recs, int n)
{
    if (n == 0) return 0;
    int best = recs[0].score;
    for (int i = 1; i < n; i++)
        if (recs[i].score > best)
            best = recs[i].score;
    return best;
}

static double average(const struct record *recs, int n)
{
    if (n == 0) return 0.0;
    int sum = 0;
    for (int i = 0; i < n; i++)
        sum += recs[i].score;
    return (double)sum / n;
}

static void remove_first(struct record *recs, int *n)
{
    if (*n <= 0) return;
    printf("removed: %s\n", recs[0].name);
    free(recs[0].name);
    memmove(&recs[0], &recs[1], (*n - 1) * sizeof recs[0]);
    (*n)--;
}

int main(int argc, char *argv[])
{
    if (argc != 2) {
        fprintf(stderr, "usage: %s FILE\n", argv[0]);
        return 2;
    }
    int n;
    struct record *recs = load(argv[1], &n);
    if (!recs) {
        fprintf(stderr, "Error loading file\n");
        return 1;
    }
    for (int i = 0; i < n; i++)
        print_record(&recs[i]);
    printf("best: %d\n", best_score(recs, n));
    printf("average: %.1f\n", average(recs, n));
    
    if (n > 0) {
        remove_first(recs, &n);
    }
    
    for (int i = 0; i < n; i++) {
        free(recs[i].name);
        recs[i].name = NULL; // Prevent double-free
    }
    free(recs);
    return 0;
}
