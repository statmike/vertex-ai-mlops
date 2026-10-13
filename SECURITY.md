# Security Policy

## Reporting a Vulnerability

Please **do not** report security vulnerabilities or exposed credentials through public GitHub issues, discussions, or pull requests.

Instead, report vulnerabilities privately through **[GitHub Security Advisories](https://github.com/statmike/vertex-ai-mlops/security/advisories/new)** on this repository. Please include:

1. A description of the issue and its potential impact.
2. The affected notebook, script, or subproject path in the repository.
3. Minimal steps to reproduce or verify the issue.

We will acknowledge receipt within 5 business days and coordinate a fix and disclosure timeline with you.

---

## Credential & Authentication Policy

Workflows, notebooks, and agents in `vertex-ai-mlops` are designed to run on Google Cloud without static secrets:

1. **No service account keys:** Notebooks and scripts authenticate via short-lived [Application Default Credentials (ADC)](https://cloud.google.com/docs/authentication/provide-credentials-adc) (`gcloud auth application-default login` locally, or attached IAM service accounts in Vertex AI Workbench, Colab Enterprise, Agent Engine, Cloud Run, Dataflow, and Dataproc).
2. **Never commit credentials:** Service account JSON key files (`*-key.json`, `*.json.key`, `service-account*.json`, `*credentials*.json`) and local secret overrides (`.env.local`) are blocked by [`.gitignore`](./.gitignore) and must never be committed to the repository.
