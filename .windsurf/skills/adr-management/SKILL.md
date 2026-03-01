---
name: adr-management
description: Guides the creation and management of Architecture Decision Records (ADRs) for this project. Use when documenting significant technical decisions.
---

## Purpose

This skill provides a lightweight process for documenting architectural decisions in this repository, ensuring they are transparent and accessible. It is designed to be flexible, offering guidance rather than rigid enforcement.

## Workflow

### 1. Create a new ADR

When a significant architectural decision needs to be made and documented:

1.  **Identify the next ADR number**. Look in the `docs/adr` directory and find the highest existing number.
2.  **Create a new file**. The filename should follow the convention `docs/adr/NNN-short-title.md`, where `NNN` is the next number, zero-padded to three digits.
3.  **Use the template**. Copy the content from the ADR template to start the new file.
    - You can find the template at: `assets/adr-template.md`
4.  **Fill out the ADR**. Complete the status, context, decision, and consequences sections.

### 2. List existing ADRs

To review past decisions, you can list all ADRs stored in `docs/adr`.

### Naming Convention

-   **Directory**: `docs/adr/`
-   **Filename**: `NNN-short-title-in-kebab-case.md` (e.g., `001-use-postgres-database.md`)

### Template

A standard template is provided in this skill's `assets/` directory to ensure consistency.
