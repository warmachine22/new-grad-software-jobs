# Job Search Overhaul

Reviewed and implemented: July 28, 2026

This document records the search strategy for a Hunter College CUNY Computer Science graduate with a B.A. completed in May 2026. It is intentionally written without the candidate's name or contact details.

## Original Goal

Find real, current, resume-relevant software engineering opportunities that a new graduate can reasonably apply to. Prioritize New York City and the wider Tri-State area, then Philadelphia, remote U.S. roles, and relocation. Every published link should lead to the employer's own career page or the employer's named ATS posting.

## Resume Profile Used

- B.A. in Computer Science, GPA 3.5, May 2026.
- Professional software work plus internship and product-release experience.
- Python, SQL, MySQL, AWS RDS, AWS S3, FastAPI, React, React Native, Git, Linux.
- Strong evidence of API work, database quality, validation, indexing, query optimization, testing, debugging, documentation, Agile coordination, and user support.
- Teaching-assistant experience: 100+ one-on-one code reviews and technical explanations.
- Good target families: software engineer I, new-grad software engineer, junior/full-stack engineer, backend/API engineer, application developer, software engineering associate, paid engineering apprenticeship, and carefully screened technical support or database-development roles.
- Poor target families: senior/staff/principal/lead/manager roles, research-heavy roles requiring graduate degrees, hardware/robotics roles without a software match, and roles requiring several years of specialized production experience.

## What The Original Approach Did Well

1. Used direct employer or employer-managed ATS links instead of publishing LinkedIn or Indeed application redirects.
2. Added a fit note, location, caveat, and a visible live-check date to most rows.
3. Prioritized Tri-State opportunities and allowed remote or relocation options.
4. Compared normalized application URLs against earlier snapshots so the July 28 page did not repeat the July 14, July 21, or July 26 links.
5. Kept each dated snapshot static and easy to browse.

## What Failed

The archive contained 102 embedded rows in the newer three snapshots, but link existence and application readiness were treated too similarly. The primary failure was using an HTTP 200 response as if it proved the job was open.

- A page can return 200 while showing a generic ATS shell, a filled job, or a search page.
- Six of the seven July 28 rows had no posting date exposed in the source page. Several were supported by search captures three to five months old.
- The prior search had no persistent source registry, so coverage depended on ad hoc search queries and could miss predictable employer career pages.
- Discovery-board evidence was not always separated from employer-source evidence.
- There was no reusable validator for redirects, generic pages, stale markers, required fields, or manual-review status.
- Candidate-level experience checks were not hard gates. A role could look like a match from its title while requiring 3, 4, or 5 years of experience.

Examples found during this overhaul:

- [Canonical Graduate Software Engineer](https://canonical.com/careers/7957239): search results described a strong new-grad role, but a direct fetch returned 404 during the audit. It is rejected until the employer publishes a working application page again.
- [Epic Kids Junior Software Engineer](https://job-boards.greenhouse.io/epickids/jobs/7751646003): the direct URL redirected to a generic jobs page with no matching role. It is rejected.
- [Fuze Health Data Engineer](https://job-boards.eu.greenhouse.io/fuzehealth/jobs/4881017101): the page is real and open, but it requires at least four years of software-engineering experience. It is rejected for this resume.
- [Fuze Health Software Engineer](https://job-boards.eu.greenhouse.io/fuzehealth/jobs/4838340101): the page is real and open, but it requires five-plus years and deep Ruby on Rails experience. It is rejected for this resume.
- [BlackRock Associate Software Engineer](https://blackrock.wd1.myworkdayjobs.com/en-US/BlackRock_Professional/job/Associate--Software-Engineer---Aladdin-Graph_R263961): the employer page is real, but the role requires at least three years of software-engineering experience. It is rejected.

## New Search Architecture

The new approach has two distinct lanes.

### Lane A: Discovery

Use broad sources to find leads and freshness signals:

- LinkedIn Jobs, Indeed, Built In NYC, Wellfound, and Handshake.
- Search-engine queries with exact phrases: `new grad`, `new graduate`, `early career`, `entry level`, `software engineer I`, `associate software engineer`, `apprentice`, and `graduate software engineer`.
- Location variants: New York City, Jersey City, Newark, Hoboken, Uniondale, Stamford, Norwalk, Hartford, Philadelphia, King of Prussia, Wilmington, remote U.S., and United States.
- Skill variants tied to the resume: Python, JavaScript, React, React Native, FastAPI, SQL, MySQL, AWS, RDS, S3, APIs, testing, debugging, data quality, and documentation.

Discovery results are never published directly. Each lead must be followed to a current employer page or employer-managed ATS record.

### Lane B: Employer Source Verification

Use `tools/source_registry.json` as the fixed coverage list. It contains 50+ public-company career sources, Tri-State finance/health/telecom employers, large technology employers, and a separate set of high-yield early-career programs.

For each employer source:

1. Search its own career page or ATS for the target title and location variants.
2. Capture the exact job URL, title, location, job type, posting or update date, and application state.
3. Follow redirects and inspect the final page.
4. Keep the employer URL as the published link. Preserve the board URL only as research metadata.

## New Quality Gates

A role reaches **Ready to Apply** only if every hard gate passes.

1. **Employer identity:** the page is on the employer domain or a clearly employer-managed ATS such as Greenhouse, Lever, Ashby, Workday, iCIMS, Jobvite, SmartRecruiters, or Oracle Cloud.
2. **Job identity:** the final page contains the company and role or structured ATS data that unambiguously identifies them.
3. **Application state:** the page has an active Apply action or application form. A generic careers page is not enough.
4. **Redirect integrity:** redirects must retain the job identity. A redirect to a board root, search page, or generic careers page fails.
5. **Dead-posting scan:** reject explicit markers such as `job not found`, `position has been filled`, `no longer accepting applications`, and equivalent wording.
6. **Experience:** explicit new-grad, graduate, apprentice, early-career, or 0-2/0-3 years is preferred. Any mandatory 3+ years is excluded unless the posting clearly says equivalent education or experience and the role is genuinely junior.
7. **Education:** a bachelor's degree in Computer Science or a related technical field is sufficient. A mandatory master's, Ph.D., or unusual school filter is a rejection or a separate low-priority monitor item.
8. **Technical relevance:** the role must use software engineering, application development, backend/API, full-stack, testing, or closely related work. Resume overlap is scored from the evidence listed above, not from title similarity alone.
9. **Freshness:** prefer an employer-posted or updated date within 30 days. A search-engine crawl date can support discovery, but it cannot replace an employer date when the page is otherwise stale. No-date pages are marked `manual-review` and are not placed in the top tier.
10. **Deduplication:** normalize scheme, host aliases, trailing slashes, and tracking parameters; compare against every historical snapshot, not just the immediately previous page.

## Fit Scoring

Fit is a ranking aid after the hard gates, not a substitute for them.

| Signal | Weight |
| --- | ---: |
| Explicit new graduate, graduate program, apprenticeship, or 0-2 years | +4 |
| Direct match to Python, JavaScript, React, SQL/MySQL, AWS, APIs, testing, or debugging | +3 |
| Direct match to data quality, documentation, Agile coordination, or technical communication | +2 |
| Tri-State or Philadelphia location | +3 |
| Remote U.S. or realistic relocation | +1 |
| Exact employer date within 14 days | +3 |
| Employer date within 15-30 days | +1 |
| Mandatory specialized stack absent from resume | -2 |
| Mandatory 3+ years of experience | reject |
| Senior/staff/principal/lead/manager title | reject |
| Dead, generic, redirected, or unverified application page | reject |

Interpretation: `Excellent` is a realistic first application; `Strong` is a good application with one meaningful caveat; `Good` is publishable only when the role is still clearly early-career and the caveat is explicit; `Adjacent` belongs in a separate monitor list, not the main shortlist.

## Implemented Assets

- [`tools/source_registry.json`](tools/source_registry.json): persistent employer coverage list and discovery-only board list.
- [`tools/validate_snapshots.py`](tools/validate_snapshots.py): standard-library validator for schema, normalized duplicates, live status, dead markers, redirects, and generic ATS shells.
- [`jobs/2026-07-28-overhaul.html`](jobs/2026-07-28-overhaul.html): new-only additions found through the expanded method. It does not repeat any link in the earlier snapshots or the July 28 baseline page.

Run the structural validator from the project folder:

```text
python tools/validate_snapshots.py
```

Run a live smoke check on a limited set of URLs:

```text
python tools/validate_snapshots.py --check-live --limit 20
```

Use the live option before publishing a new snapshot. Any `ERR`, non-200 result, dead marker, or generic JavaScript shell must be resolved or moved to manual review before the row is published.

## Expanded Results

The July 28 baseline contained seven new rows. The expanded search added five additional new-only rows that cleared the stronger fit and source checks:

| Employer | Role | Geography | Why it cleared |
| --- | --- | --- | --- |
| AHEAD | Software Engineer | Remote U.S. | Explicitly early-career; no prior Elixir required; mentorship, testing, debugging, code review, and full-stack work. |
| SkillStorm | Entry Level Software Developer | New York City | Paid 12-week training, recent graduates accepted, SQL/programming fundamentals, testing and technical documentation. |
| SkillStorm | Entry Level Software Developer | Philadelphia | Same employer program with a distinct Philadelphia posting and direct employer application. |
| Microchip Technology | Engineer I - Software | Santa Rosa, CA | Employer source explicitly describes a recent-graduate/0-2.5-year role; embedded C/C++ is the main skill gap. |
| Rocket Software | Software Engineering NextGen Academy | Vilnius, Lithuania | Posted yesterday in the employer ATS; six-month paid graduate program with training, mentorship, Git/testing/Linux exposure, and a path to engineering. |

The result is intentionally five rather than an arbitrary target such as 100. The expanded source coverage found more leads, but the gates correctly removed stale, duplicate, inaccessible, specialized, and experience-mismatched postings. The next refresh should re-scan the registry and discovery lanes, but should never lower the gates to inflate the count.

## Operating Procedure For Future Refreshes

1. Load the resume profile and historical normalized URL set.
2. Scan the registry's employer sources by Tri-State, Philadelphia, remote, and relocation priority.
3. Run discovery-board searches in parallel with the same title, skill, and location matrix.
4. Resolve every lead to an employer or employer ATS page.
5. Apply hard gates before ranking.
6. Run the validator and manually inspect every live failure or generic shell.
7. Write rejected leads and reasons into the refresh notes instead of silently dropping them.
8. Publish only unique, employer-source rows with checked dates and visible caveats.
9. Re-run the validator, `git diff --check`, and a browser smoke test before pushing.
10. On the next refresh, treat every previous snapshot as immutable history and dedupe against all of them.

This balances breadth with the original objective: a smaller list of real, relevant, currently actionable jobs is more useful than a large list of links that cannot be opened or do not fit the candidate.
