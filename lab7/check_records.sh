#!/bin/bash
# check_records.sh - proves the fixes in records_fixed.c with the compiler, sanitizers and Valgrind.
# Every check must print PASS. Usage: bash check_records.sh [source.c]
set -u
SRC=${1:-records_fixed.c}
fail=0
check() {  # check "description" command...
    local name=$1; shift
    if ( "$@"; exit $? ) > /dev/null 2>&1; then echo "PASS  $name"; else echo "FAIL  $name"; fail=1; fi
}

printf 'Aigerim,92\nDaniyar,78\nMadina,85\n' > t_sample.txt
printf 'Aigerim,92\nAigerim-Nurlanovna-Seitkali,88\n' > t_long.txt
printf 'Aigerim,92\n%s,70\n' "$(printf 'a%.0s' $(seq 64))" > t_toolong.txt
printf 'Aigerim,92\nTop 5%%d student,90\n' > t_percent.txt
: > t_empty.txt
gcc -Wall -Wextra -g -O0 -fsanitize=address,undefined "$SRC" -o rc_asan 2> /dev/null || { echo "build failed"; exit 1; }
gcc -Wall -Wextra -g -O0 "$SRC" -o rc_plain 2> /dev/null || { echo "build failed"; exit 1; }

# The compiler and its static analyzer find nothing
check "gcc -Wall -Wextra -Wformat=2 -fanalyzer: no warnings" \
    bash -c "[ -z \"\$(gcc -Wall -Wextra -Wformat=2 -fanalyzer -O2 -c '$SRC' -o /dev/null 2>&1)\" ]"
# 1. A long name is stored in full; only names over 63 characters are rejected
check "ASan: long name causes no overflow" ./rc_asan t_long.txt
check "Long name printed in full" bash -c './rc_asan t_long.txt | grep -qx "Aigerim-Nurlanovna-Seitkali: 88"'
check "Name of 64 characters: line skipped with a message" bash -c './rc_asan t_toolong.txt 2>&1 | grep -q "line 2 skipped"'
# 2. A name with % is printed as text
check "Percent sign printed literally" bash -c './rc_asan t_percent.txt | grep -qF "Top 5%d student: 90"'
# 3 and 4. Correct best score and average, no out-of-bounds read
check "ASan and UBSan: sample runs clean" ./rc_asan t_sample.txt
check "Best score is 92" bash -c './rc_asan t_sample.txt | grep -qx "best: 92"'
check "Average is 85.0" bash -c './rc_asan t_sample.txt | grep -qx "average: 85.0"'
# 5. A missing file gives an error message and exit code 1, not a crash
check "Missing file: exit code 1" bash -c './rc_plain t_missing.txt 2> /dev/null; [ $? -eq 1 ]'
# 6 and 7. No use after free, no double free, no leaks, no uninitialized values
check "Valgrind: no errors, no leaks" valgrind -q --leak-check=full --error-exitcode=1 ./rc_plain t_sample.txt
check "Removed record is printed correctly" bash -c './rc_asan t_sample.txt | grep -qx "removed: Aigerim"'
check "Empty file handled" bash -c './rc_asan t_empty.txt | grep -qx "no records"'

rm -f t_sample.txt t_long.txt t_toolong.txt t_percent.txt t_empty.txt rc_asan rc_plain
exit $fail
