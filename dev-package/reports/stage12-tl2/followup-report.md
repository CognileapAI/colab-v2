# TL-2 CLI input-readiness follow-up

- Base: `ce8a42f14e4d756142880e4e3a713b9db0a948b6`.
- Missing, unreadable, or non-UTF-8 d3/d5 ID input files now print
  `::관측입력준비실패::` and return 78 before constructing an S3 client or snapshot.
- Snapshot directory/create/write failures now print `::snapshot준비실패::` and return 78.
- The catches are limited to `OSError` and `UnicodeError`; programming defects are not hidden as readiness.
- RED: two tests raised unhandled `FileNotFoundError` and `FileExistsError`.
- GREEN: the focused CLI module has 6/6 passing tests, including snapshot absence for missing IDs.
- Actual S3 deletion, deployment, DB access/write, and ledger edit: 0.
