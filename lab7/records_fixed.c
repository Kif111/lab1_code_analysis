/* records_fixed.c - reads student records "name,score" from a file, prints them,
   the best score and the average, then removes the first record.
   Usage: ./records_fixed FILE */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_RECORDS 100
#define MAX_NAME 63

struct record {
    char *name;
    int score;
};

static int parse_line(const char *line, struct record *r)
{
    const char *comma = strchr(line, ',');
    if (!comma)
        return -1;
    size_t len = (size_t)(comma - line);
    if (len == 0 || len > MAX_NAME)          /* Fix 1: check the length before copying */
        return -1;
    r->name = strndup(line, len);            /* the copy gets exactly the space it needs */
    if (!r->name)
        return -1;
    r->score = atoi(comma + 1);
    return 0;
}

static int load(const char *path, struct record **out, int *count)
{
    char line[256];
    int n = 0;
    FILE *f = fopen(path, "r");
    if (!f) {                                /* Fix 5: check every result that can fail */
        perror(path);
        return -1;
    }
    struct record *recs = malloc(MAX_RECORDS * sizeof *recs);
    if (!recs) {
        fclose(f);
        return -1;
    }
    for (int line_no = 1; n < MAX_RECORDS && fgets(line, sizeof line, f); line_no++) {
        line[strcspn(line, "\n")] = '\0';
        if (parse_line(line, &recs[n]) == 0)
            n++;
        else
            fprintf(stderr, "line %d skipped: expected \"name,score\" with a name of 1-%d characters\n",
                    line_no, MAX_NAME);
    }
    fclose(f);
    if (n == 0) {
        free(recs);
        recs = NULL;
    } else {
        struct record *smaller = realloc(recs, n * sizeof *recs);
        if (smaller)                         /* on failure the old block is still valid */
            recs = smaller;
    }
    *out = recs;
    *count = n;
    return 0;
}

static void print_record(const struct record *r)
{
    printf("%s: %d\n", r->name, r->score);   /* Fix 2: data is never used as a format string */
}

static int best_score(const struct record *recs, int n)
{
    int best = recs[0].score;                /* Fix 3: initialized; the caller ensures n > 0 */
    for (int i = 1; i < n; i++)
        if (recs[i].score > best)
            best = recs[i].score;
    return best;
}

static double average(const struct record *recs, int n)
{
    int sum = 0;
    for (int i = 0; i < n; i++)              /* Fix 4: indexes 0 .. n-1 only */
        sum += recs[i].score;
    return (double)sum / n;
}

static void remove_first(struct record *recs, int *n)
{
    printf("removed: %s\n", recs[0].name);   /* Fix 6: use the data before freeing it */
    free(recs[0].name);
    memmove(&recs[0], &recs[1], (size_t)(*n - 1) * sizeof recs[0]);
    (*n)--;                                  /* Fix 7: each pointer stays in the array once */
}

int main(int argc, char *argv[])
{
    if (argc != 2) {
        fprintf(stderr, "usage: %s FILE\n", argv[0]);
        return 2;
    }
    struct record *recs;
    int n;
    if (load(argv[1], &recs, &n) != 0)
        return 1;
    if (n == 0) {
        printf("no records\n");
        return 0;
    }
    for (int i = 0; i < n; i++)
        print_record(&recs[i]);
    printf("best: %d\n", best_score(recs, n));
    printf("average: %.1f\n", average(recs, n));
    remove_first(recs, &n);
    for (int i = 0; i < n; i++)
        free(recs[i].name);
    free(recs);
    return 0;
}
