# Question schema

Each true/false **pair** is one YAML file: `questions/<area>/<id>.yaml`. The folder names match the article domains in [business-knowledge-graph](https://github.com/john1hsu/business-knowledge-graph) (strategy, corporate-finance, marketing, …). The quiz serves one side of a pair at random and never both sides in one session.

```yaml
id: bz-000002                     # stable, never reused
area: strategy                    # = source article's domain = folder
kind: origin                      # definition | origin | mechanism | evidence | application | figure
topic: Barriers to Entry          # the source article's title, shown after answering
topic_type: Concept               # the article's class: Concept, Framework, Theory, Person, Case, Metric, ...
true_statement: Joe Bain's 1950s work defined an entry barrier as anything that lets incumbents earn above-normal profits without attracting entry.
false_statement: George Stigler's 1950s work defined an entry barrier as anything that lets incumbents earn above-normal profits without attracting entry.
explanation: Bain (1956) framed barriers around persistent above-normal profits. Stigler (1968) proposed the narrower test of a cost entrants bear that incumbents did not.
as_of: FY2024                     # only on figure pairs: the year or period the number is for
source:
  repo: john1hsu/business-knowledge-graph
  path: articles/strategy/barriers-to-entry.md
  commit: <source repo HEAD when written or last verified>
  blob: <git blob of the article at that point>
concepts: [kt:barriers-to-entry, kt:industrial-organization]   # graph node ids; the source article's id comes first
related: []                       # optional: other pair ids
supersedes: bz-000041             # only on a pair that replaced an outdated one
difficulty: 2                     # 1 foundations | 2 MBA core | 3 advanced
created: '2026-11-16'
status: active                    # active | stale | retired
stale_reason: ...                 # only while stale
retired_reason: ...               # optional, on retired pairs
```

`schema/question.schema.json` has the same rules as a JSON Schema for editors.

## Kinds

Each pair says what it teaches, so a topic gets learned from several sides and you can drill one kind (for example "Who and when" before an exam).

| kind | App label | Tests |
| --- | --- | --- |
| definition | What it is | What the idea is, and what it is not |
| origin | Who and when | Who introduced it, where, and when |
| mechanism | How it works | Its parts, steps, formula, cause and effect |
| evidence | Evidence and critiques | What research shows; the main criticisms and limits |
| application | In practice | How managers, consultants or regulators use it; real examples |
| figure | Numbers and dates | A dated number (`as_of` required, and dated in the statement) |

## Lifecycle

Business ideas don't ship in releases, so a pair changes only when its source article does.

| Status | Meaning | In the quiz? |
| --- | --- | --- |
| active | Matches the latest version of its source article | Yes |
| stale | The source article changed (or disappeared) since the pair was verified | Only with `--include-stale` |
| retired | The fact changed (a newer pair `supersedes` it), the article is gone, or the pair repeated a fact another pair already tests | No |

## Checks (`scripts/validate.py`)

| Check | Fails when |
| --- | --- |
| Schema | A required field is missing, malformed or unknown |
| Unique ID | An ID repeats, or the file name or folder doesn't match |
| Kind | `kind` isn't one of the six kinds |
| Dated figures | A `figure` pair has no `as_of`, `as_of` names no year, or the true statement doesn't mention it |
| Duplicate | A statement closely matches one in another non-retired pair |
| Same fact | Two non-retired pairs, from any articles, have true statements that state one fact in different words: most of their words match, or they share their numbers and most of the shorter statement's words |
| Pair quality | The two statements are identical or differ only by negation |
| Explanation | Shorter than 60 characters |
| Statement form | A statement is a question, under 20 or over 280 characters |
| Source | Repo, path, commit or blob is malformed; with `--source`, the article's domain differs, or an active pair's article is missing or changed (run `refresh.py mark-stale` first; stale pairs are exempt because they are waiting to be refreshed or retired) |
| Supersedes | Points to an ID that is missing or not retired |
| Exam-like wording | "Which of the following", "Choose two", "according to the article" and similar |
