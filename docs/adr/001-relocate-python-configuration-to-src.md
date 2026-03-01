# 001. Relocate Python Configuration to Src

* Status: accepted
* Date: 2026-03-01

## Context

The project structure had two separate directories for configuration: `config/` for Python-based configuration logic and `configs/` for user-facing TOML configuration files. This separation was confusing and made the project layout less intuitive. All application source code, including Python configuration loaders, should reside within the `src/` directory to maintain a clear and standard project structure.

## Decision

We decided to move all Python configuration files from the root `config/` directory into a new `src/config/` directory. This consolidates all Python source code under a single `src/` root, clarifying the distinction between application code and user-editable configuration files (which remain in `configs/`).

## Consequences

*   **Positive**: The project structure is now cleaner and more aligned with standard Python project layouts. It is clearer which files are part of the application's source code.
*   **Negative**: Import statements in the codebase that referenced the old `config` module had to be updated to `src.config`.
*   **Neutral**: This change does not affect the application's runtime behavior but improves maintainability.
