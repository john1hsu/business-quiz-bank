# Business quiz bank: daily run playbook

This repo is a bank of paired true/false questions that help John learn business, generated from the cited articles in [john1hsu/business-knowledge-graph](https://github.com/john1hsu/business-knowledge-graph). A daily scheduled run handles up to **100 pairs**: it refreshes stale pairs first, then spends the rest of the budget on new ones, at most **3 per article**. Everything goes to `main` as **one combined commit** with one push, and only when every check passes. Read `SCHEMA.md` before writing.

## 1. Sync

```bash
git pull --rebase origin main
rm -rf .source && git clone --depth 1 https://github.com/john1hsu/business-knowledge-graph .source/business-knowledge-graph
python3 scripts/validate.py   # the repo's own checks, without the source; must print OK; fix the repo first if not
```

Don't pass `--source` here: source articles change between runs, and step 2 is what handles that.

## 2. Mark stale pairs

```bash
python3 scripts/refresh.py mark-stale
python3 scripts/validate.py --source .source/business-knowledge-graph   # must print OK now; fix the repo first if not
```

`mark-stale` marks active pairs stale when their source article changed since they were verified (drift: a corrected date, a newer figure, a reworded claim), or when the article was removed or renamed. Always run it before validating against the source: a changed or missing article is an error on an active pair, but expected on a stale one that is waiting for step 4a.

## 3. Pick this run's work

The budget is 100 pairs per run (refreshed plus new). Repeat this step until the budget is used or `pick` returns `"none"`:

```bash
python3 scripts/generate.py pick --n 3
```

- `"mode": "refresh"` → do step 4a for every pair in `batch`.
- `"mode": "generate"` → do step 4b for `article`, writing `n` pairs.
- `"mode": "none"` → stop picking and go to step 5. If nothing was refreshed or added but step 2 marked pairs stale, commit that with the message `quiz: mark <n> pairs stale`; if nothing changed at all, stop without committing.

Don't commit between picks. Run `python3 scripts/validate.py --source .source/business-knowledge-graph` after roughly every 15 new pairs to catch problems early.

Stale pairs always come before new ones (dated figures first). New articles are picked fewest-pairs first, and among those from the business area with the fewest pairs, so practice stays spread across strategy, finance, accounting, marketing, operations and the rest.

## 4a. Refresh a stale pair

Read the pair (`questions/*/<id>.yaml`) and the **current** source article in full. Decide:

| Outcome | Command |
| --- | --- |
| Both statements still hold (true one true, false one false) per the article | `python3 scripts/refresh.py verify <id>` |
| The fact changed (a corrected year, a newer figure, a revised claim) | Write one replacement pair to a JSON file (format in 4b), then `python3 scripts/refresh.py supersede <id> --input <file>` |
| The article is gone, or no longer supports the fact | `python3 scripts/refresh.py retire <id> --reason "<why>"` |

If the article now says something that makes the explanation wrong but both statements still hold, supersede rather than verify.

## 4b. Write new pairs

Read the whole article (`.source/business-knowledge-graph/<path>`). Check `existing_pairs_for_article` and `related_pairs_in_other_articles` so you don't repeat a fact: the second list holds the true statements already written from neighbouring articles, and a fact any of them tests is taken, even if this article words it differently. Write `n` pairs to a JSON file outside the repo (the scratchpad):

```json
{"article": "articles/<domain>/<slug>.md",
 "pairs": [{"kind": "mechanism", "true_statement": "...", "false_statement": "...", "explanation": "...",
            "difficulty": 2, "concepts": ["kt:<article-id>", "kt:<other-node>"]},
           {"kind": "figure", "as_of": "FY2024", "true_statement": "<a number the article dates to FY2024, with FY2024 in the sentence>",
            "false_statement": "...", "explanation": "...", "difficulty": 2}]}
```

The goal is learning, so each pair should teach something worth knowing about the topic. Rules for each pair:

- **Grounding:** every pair must be answerable from this article alone. Don't add facts from memory, even true ones.
- **One fact per pair**, and a different fact for each pair in the run and from every pair already in the bank, whichever article it came from.
- **Cover the topic from different sides.** Give each pair a `kind`, and prefer the kinds in pick's `kinds_not_yet_used`, so a topic is learned as more than a definition:

  | kind | Tests | Example true statement |
  | --- | --- | --- |
  | `definition` | What the idea is and what it is not | Accrual accounting records revenue when it is earned, not when cash arrives. |
  | `origin` | Who introduced it, where, and when | Michael Porter introduced the five forces in a 1979 Harvard Business Review article. |
  | `mechanism` | How it works: its parts, steps, formula, cause and effect | Under the matching principle, expenses are recorded in the period of the revenue they helped earn. |
  | `evidence` | What research shows, and the main critiques or limits | Critics argue the five forces treat industry structure as static. |
  | `application` | How managers, consultants or regulators use it; the article's real example | U.S. merger review asks whether new entry would be timely, likely and sufficient. |
  | `figure` | A dated number from the article (needs `as_of`) | A revenue, market share or statistic, with the year or fiscal period written into the statement |

- **Plausible false twin:** swap the person, year or decade, a number, the direction of an effect, a cause, a step, or a neighbouring idea that is easy to confuse (for example NPV vs IRR, Six Sigma vs lean, Herzberg's hygiene factors vs motivators). Never make the false statement by just adding "not". Keep the wording otherwise parallel so the reader must know the fact.
- **Statements:** declarative, 20–280 characters, readable on a phone card. No exam phrasing ("Which of the following", "Choose two") and never "according to the article".
- **Dates and figures:** a time-sensitive number (revenue, market share, a statistic) is only a `figure` pair, with `as_of` set and that year or period written into the true statement. Never undated.
- **Explanation:** 1–3 sentences in your own words saying why the true statement is true and what's wrong with the false one. Make it teach: add the "why" or the context the article gives, so the explanation is worth reading even when the answer was right. No quote over 15 words.
- **Difficulty:** 1 = foundations (core definitions, famous names), 2 = MBA core (how it works, key distinctions, typical uses), 3 = advanced (evidence, critiques, edge cases, trade-offs).
- **Concepts:** the article's own id plus any graph node ids the fact involves (from the article's edges).
- No investment advice, and no statement that a living person or company did something wrong beyond what the article states.

Then add them:

```bash
python3 scripts/generate.py add --input <file>
```

## 5. Validate, build, commit, push

```bash
python3 scripts/validate.py --source .source/business-knowledge-graph
python3 scripts/build_index.py
git add -A
git commit -m "<message>"
git pull --rebase origin main && git push origin main
```

- Make **one** commit for the whole run, containing every refresh and new pair, and push it once.
- If validation fails on a new or replacement pair, delete that pair's file, rewrite it once, and validate again. If it still fails, drop just that pair (remove its new file, or undo that refresh) and carry on, so the final commit always validates. Report dropped pairs in the run output.
- If validation says a new pair states the same fact as an existing one, the rewrite must test a different fact from the article, not the same fact reworded. If it flags two pairs that were both already in the bank, keep the older one and run `python3 scripts/refresh.py retire <newer id> --reason "duplicate of <older id>"`.
- Commit message subject: `quiz: refresh <r> pairs, +<n> pairs from <k> articles` (drop the part that is zero). In the body, list one line per pair (`bz-000123: verified` / `superseded by bz-000130` / `retired: <why>` / `added`).
- If the push is rejected, pull --rebase, re-run `build_index.py`, amend that same commit (don't add a second one) and push again (once).

## Don'ts

- Don't handle more than 100 pairs in one run, or write more than 3 pairs from one article in one run.
- Don't make more than one commit or push per run.
- Don't edit `index/` or `coverage/` by hand; `build_index.py` writes them.
- Don't delete question files or reuse an id; retire instead.
- Don't edit business-knowledge-graph from this run, and never commit `.source/`.
- Don't commit if validation fails.
