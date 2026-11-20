---
name: sqe-sonar
description: "Run SonarQube Community on the SQE repo, read and explain the metrics (complexity, duplication, smells, bugs, vulnerabilities, coverage, debt, ratings), and compare hand-calculated cyclomatic complexity with Sonar. Use for \"sonar\", \"static analysis\", \"code smells\", \"technical debt\", \"cyclomatic complexity vs sonar\"."
---

# SonarQube (Area 1, 5 marks)

Area 1 adds a `sonarqube` CI job (SonarQube Community as a service container, so no external account is needed) and a
`sonar-project.properties` (suggested: sources = `indico/modules/rb` + `tests/team`, Python coverage from
`tests/team/reports/unit/coverage.xml`, which `bash tests/team/run.sh unit` already produces).

## Local run (for screenshots and exploring)
```bash
docker run -d --name sqe-sonar -p 9000:9000 sonarqube:25.11.0.114957-community   # first start ~2 min, login admin/admin then change it
# create a token in My Account > Security, then:
bash tests/team/run.sh unit                                    # produces coverage.xml for Sonar
docker run --rm -e SONAR_HOST_URL=http://host.docker.internal:9000 -e SONAR_TOKEN=<token> \
  -v "$(pwd -W 2>/dev/null || pwd):/usr/src" sonarsource/sonar-scanner-cli:11.5
```

## What to report (template `docs/team/templates/static-analysis.md`)
| Metric | Where in Sonar | What it tells you |
|---|---|---|
| Cyclomatic complexity | Measures > Complexity (per function) | number of independent paths = minimum tests for branch coverage |
| Cognitive complexity | Measures > Complexity | how hard it is to read; nesting is penalised |
| Duplications | Measures > Duplications | % duplicated lines/blocks, where a change must be made twice |
| Code smells | Issues > Code Smell | maintainability problems → technical debt |
| Bugs / Vulnerabilities / Hotspots | Issues | reliability / security problems |
| Coverage | Measures > Coverage | from our coverage.xml (rule surface ≠ whole module, explain) |
| Technical debt | Measures > Maintainability | estimated fix time; debt ratio drives the A–E rating |
| Ratings A–E | Overview | reliability, security, maintainability, security review |
Interpret them: link the high-complexity functions to the risk register and to test depth (white-box focus).

## Hand CC vs Sonar
Pick `Reservation.can_cancel`. Sonar counts +1 per `if`, each `and`/`or`, loops, etc. Your CFG with compound conditions split
into atomic decisions should match. If you treat `a and b` as one node, you get fewer; explain the difference.
