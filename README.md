# BiasClear GitHub Action

Scan your repository for structural bias on every PR.

BiasClear detects Persuasion-Induced Thinking (PIT) distortions — rhetorical patterns that substitute emotional framing, false consensus, or authority claims for evidence.

## Usage

```yaml
name: Bias Check

on:
  pull_request:
    paths:
      - 'docs/**'
      - '*.md'

jobs:
  biasclear:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: bws82/biasclear-action@v1
        with:
          paths: 'docs/**/*.md'
          threshold: 70
          domain: general
```

## Inputs

| Input | Description | Default |
|-------|-------------|---------|
| `paths` | Glob pattern for files to scan | `**/*.md` |
| `threshold` | Minimum truth score (0-100) | `70` |
| `domain` | Analysis domain: `general`, `legal`, `media`, `financial` | `general` |
| `fail-on-bias` | Fail the workflow if bias detected | `true` |
| `python-version` | Python version | `3.12` |

## Outputs

| Output | Description |
|--------|-------------|
| `total-files` | Number of files scanned |
| `flagged-files` | Number of files with bias detected |
| `avg-score` | Average truth alignment score |
| `report` | Full scan report (JSON) |

## Examples

### Scan all markdown files

```yaml
- uses: bws82/biasclear-action@v1
  with:
    paths: '**/*.md'
```

### Legal domain with strict threshold

```yaml
- uses: bws82/biasclear-action@v1
  with:
    paths: 'legal/**/*.md'
    threshold: 85
    domain: legal
```

### Scan without failing

```yaml
- uses: bws82/biasclear-action@v1
  with:
    paths: 'content/**/*.md'
    fail-on-bias: false
```

## What it detects

BiasClear scans for 34+ structural patterns across 3 PIT tiers:

- **Tier 1 (Ideological):** False consensus, selective framing, assumed conclusions
- **Tier 2 (Psychological):** Anchoring, authority appeals, emotional manipulation
- **Tier 3 (Institutional):** Credential substitution, regulatory capture framing

## License

AGPL-3.0 — See [BiasClear](https://github.com/bws82/biasclear) for details.
