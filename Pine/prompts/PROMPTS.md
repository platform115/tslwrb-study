# Task prompts

Paste the matching block at the start or end of a request. Kept in one file so they stay in step.

## 1. Opener — first message of every Pine chat

```
Read Pine/README.md, Pine/CONVENTIONS.md, Pine/setup.md and Pine/OPEN_QUESTIONS.md in
platform115/tslwrb-study and follow them. Before any code, state: (1) which file and version this
chat works on, (2) the target chart from setup.md, (3) what is NOT in scope, (4) which open
questions block the task. Wait for my OK.
```

## 2. Build — append to any request for code

```
Use only built-ins listed in Pine/reference/v6_signatures.md; list any other as UNVERIFIED in the
header. Deliver the full file with the header template filled in. Show the Python it translates
beside the Pine. Answer the 5-point pre-delivery checklist. List every assumption as "UNCERTAIN: ...".
Do not commit.
```

## 3. Compiler error

```
Compiler output below, verbatim. Fix only what the error requires. Show the changed lines, then the
full file. Add the LOG.md row. Do not refactor anything else.
```

## 4. Chart check — when reporting what the chart shows

```
Chart: [symbol / timeframe / session / date and time CT]. I see: [...]. Spec expects: [...].
Explain the cause before proposing any change. If it could be a data-feed difference rather than a
bug, say how to tell them apart. Add the LOG.md row.
```

## 5. Change request

```
This is a change, not a fix. New version file, "Changed from previous version" filled in, full
checklist re-run. The old file is not touched.
```

## 6. Signature paste — adding to the verified list

```
Reference Manual entry below, pasted from TradingView. Add it to Pine/reference/v6_signatures.md
with source RM and today's date, and remove it from the unverified list.
```
