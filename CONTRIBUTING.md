# Contributing to `vertex-ai-mlops`

Thank you for your interest in contributing to `vertex-ai-mlops`. This repository is a collection of **470+ interactive notebooks**, end-to-end reference workflows, solution prototypes, and packaged [Agent Skills](./agent-skills/README.md) across Google Cloud's AI and data ecosystem (Gemini Enterprise, Vertex AI, BigQuery ML, BigQuery AI Functions, Agent Development Kit, Dataflow, Dataproc, Managed Airflow, AlloyDB, Spanner, Bigtable, and more).

Issues and pull requests for bug fixes, documentation improvements, link updates, and workflow enhancements are welcome.

---

## 1. Before You Open a Pull Request

- **Small fixes (typos, broken links, API parameter updates):** Feel free to open a pull request directly with a clear description of the fix.
- **New notebooks, subprojects, or major restructuring:** Please open an [issue](https://github.com/statmike/vertex-ai-mlops/issues) first to discuss scope and directory placement so it aligns with the repository's structure.

---

## 2. Public-Repository & Credential Hygiene

Every contribution must follow these security and privacy rules:

- **Application Default Credentials (ADC) only:** Never load or commit service account JSON key files (`*-key.json`, `*.json.key`, `service-account*.json`). Notebooks, scripts, and agents authenticate via Application Default Credentials (`gcloud auth application-default login` locally or attached service accounts in Google Cloud runtimes).
- **Zero proprietary or customer data:** Never include customer names, engagement identifiers, internal hostnames, credentials, or personal local filesystem paths in notebooks, code, configs, or persisted cell outputs.
- **Self-contained, reproducible workflows:** Notebooks should rely on public datasets, synthetic data generated in-notebook, or resources created by the workflow's own setup steps.

---

## 3. Verification Gates

Depending on what your pull request touches, run the relevant checks before submitting:

### Agent Skills & BigQuery Reference Workflows (`agent-skills/`, `data+ai/bq-ml/`, `data+ai/bq-ai-functions/`)

If you modify any file under [`agent-skills/`](./agent-skills/README.md), [`data+ai/bq-ml/`](./data+ai/bq-ml/README.md), or [`data+ai/bq-ai-functions/`](./data+ai/bq-ai-functions/README.md), run the `agent-skills` verification sweep and test suite:

```bash
cd agent-skills/tooling
uv sync
uv run agent-skills sweep ../.agents/skills --repo-root ../..
uv run pytest -q
```

`sweep` validates all skill manifests, outward/sibling markdown links and `#anchors`, `RESOURCES.md` coverage, extracted notebook narratives, and pinned model allowlists ([`agent-skills/pinned-models.json`](./agent-skills/pinned-models.json)).

### Python Subprojects (`Applied ML/`, `data+ai/`, `MLOps/`)

When modifying a standalone Python or ADK subproject that includes its own `pyproject.toml`, run its local linter, type checker, and test suite (for example, `uv run ruff check .`, `uv run mypy`, and `uv run pytest`) from that subproject's directory.

---

## 4. Contributor License Agreement

Contributions to this project must be accompanied by a [Contributor License Agreement](https://cla.developers.google.com/about) (CLA). You (or your employer) retain the copyright to your contribution; this simply gives permission to use and redistribute your contributions as part of the project.

If you have not already done so, please complete your CLA at <https://cla.developers.google.com/> before submitting a pull request.

---

## 5. Community Guidelines & License

This project follows [Google's Open Source Community Guidelines](https://opensource.google/conduct/) and [`CODE_OF_CONDUCT.md`](./CODE_OF_CONDUCT.md).

By contributing to `vertex-ai-mlops`, you agree that your contributions will be licensed under the [Apache License 2.0](./LICENSE).

This is not an officially supported Google product. It is built on Google products and is neither endorsed nor supported by Google.
