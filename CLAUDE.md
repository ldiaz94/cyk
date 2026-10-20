# Working on cyk

`cyk` is a bytebeat synthesizer, braille oscilloscope and `.wav`
recorder for the terminal, written in raz. Read `README.md` first, then
`src/Beat.raz`, `src/Wave.raz` and `src/Cyk.raz` from top to bottom. Follow
the workspace rules in `~/r/CLAUDE.md` and `~/r/raz/STANDARDS.md`.

## Tooling and checks

`cyk` is a personal project in `~/r`, so it uses `sauce` (`~/r/sauce`),
`robbie` (`~/r/robbie`) and `concha` (`~/r/concha`), with `git` kept as
a mirror backup to `ldiaz94/cyk`.

    robbie              # list tasks, files and variables
    robbie build/cyk    # compile build/cyk with raz -Werror
    robbie check        # Beat's and Wave's tests, test/check.cn, and doc/cyk.1
    robbie fmt          # src/*.raz formatted as raz's Pretty.raz writes them
    robbie loc          # lines of code, by rloc
    robbie cast         # doc/demo.cast and doc/img/demo.gif made again
    robbie install      # cyk and cyk.1 into ~/.local

`robbie check` and `robbie fmt` must pass before every commit.

## How we work

- Order of priorities: **correct > readable > simple > small > fast**.
- Every module opens with what it is, what it depends on, and what it
  leaves out; comments say what and why, and never contain `*)`.
- Parameters follow `~/r/raz/STANDARDS.md`: a value for scalars and
  slices, `const` for read-only records/arrays, `var` for mutated ones,
  and a pointer only when kept.
- A key, option or screen layout changed is updated in `doc/cyk.1`,
  `README.md` and `test/cases/*.expect` in the same commit.
- Commit in `sauce` (`sauce commit -m "..."`) and mirror to `git` (`git
  commit` as `Luis <42945842+ldiaz94@users.noreply.github.com>`,
  `--no-gpg-sign`, no trailer, pushed to `origin main`).
