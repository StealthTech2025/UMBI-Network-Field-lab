# UMBI Network+ Field Lab

A self-contained, single-file web course for CompTIA Network+ (N10-009): five weeks of lessons, graded quizzes, hands-on labs on a simulated network, practice exams, and the Neon Grid training game.

## Files

| Path | What it is |
|---|---|
| `fieldlab.html` | The course. Open it in any current browser; nothing to install. |
| `it/fieldlab-it.html` | A copy adapted to run as an [It](#running-it-on-it) page: progress is kept in It's storage instead of the browser's. |
| `it/make-it-copy.py` | Builds `it/fieldlab-it.html` from `fieldlab.html`. |
| `tests/` | Headless-Chromium tests that click through the course. |

## Running it on It

```sh
python3 -I it/make-it-copy.py fieldlab.html it/fieldlab-it.html
it create "Network+ Field Lab" --id fieldlab --file it/fieldlab-it.html --open
```

On It, progress is saved per page. Features that relied on claude.ai's shared database (class schedule sync, leaderboard, gradebook sync) are not available there.

## Tests

The tests need Chromium (`sudo apt-get install chromium` on Debian) and Python 3. Run them from the `tests` folder:

```sh
cd tests
python3 -I t_labs.py       # runs every lab's solution through the simulator, 25 variants each
python3 -I t_routes.py     # opens every page and lesson tab, reports script errors
python3 -I t_quizflow.py   # takes a graded quiz in every lesson
python3 -I t_labflow.py    # does a graded lab in every lesson through the terminal
python3 -I t_grid.py       # plays every Neon Grid mission and Port Runner
python3 -I t_exam.py       # takes full and half-length practice exams
python3 -I t_monkey.py     # random-clicks through every module looking for crashes
```

`t_labs.py` reports solution note lines (starting with `#`) as rejected commands; those are expected. Lab 2.3's `show ip ospf neighbor` is a known unsupported command.

## Known issues

- Grade codes and retake codes are checked with values that are in the page source, so they can be forged.
- Scores are stored in the student's browser (or It's storage) and can be edited.
- Quiz and practice-exam answers are readable in the page source; only the sealed exams and unlock codes are protected.
