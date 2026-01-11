This repository is a Python project for analyzing VALORANT VODs.
It is currently in a **stable state**.

Your primary responsibility as an AI agent is to **improve functionality and analysis quality without breaking the existing system**.

You must strictly follow the rules below.

---

## 🚫 ABSOLUTE RESTRICTIONS (CRITICAL)

The following actions are **strictly forbidden**, even if you believe they are beneficial.

- Do NOT modify, create, or delete:
  - `pyproject.toml`
  - `uv.lock`
  - `requirements.txt`

- Do NOT add new dependencies
- Do NOT run `uv add`, `pip install`, `pip uninstall`
- Do NOT introduce workspace or multi-project structures
- Do NOT perform large-scale refactoring
- Do NOT move or delete many files at once
- Do NOT remove existing logic because you think it is unnecessary

**System stability is the highest priority.**

---

## ✅ ALLOWED ACTIONS

The following actions are explicitly allowed:

- Add or modify functions **inside existing `.py` files**
- Improve analysis accuracy, robustness, or performance
- Add logging or debug output
- Add small helper scripts under `scripts/`
- Improve output formats under `output/` (JSON, CSV, images, etc.)
- Add comments and docstrings for clarity

---

## 🧠 PROJECT ASSUMPTIONS

- This is a **single uv-managed Python project**
- There is only **one** `pyproject.toml`
- No workspace or package separation is currently in use
- The current phase prioritizes **working results over architectural cleanliness**

Do not attempt to redesign the project structure.

---

## 🎯 YOUR ROLE AS AN AGENT

You will be assigned one or more of the following roles:

- Improve VOD downloading logic
- Improve frame extraction logic
- Improve minimap / position / state analysis
- Improve output generation and visualization
- Improve pipeline stability and error handling

You are **not** responsible for system redesign or dependency management.

---

## 🧪 IMPLEMENTATION RULES

When implementing changes:

- Do NOT change existing function signatures
- Do NOT break existing call flows
- Keep changes **small, local, and incremental**
- Do NOT reorder or restructure the pipeline without explicit instruction
- Prefer extending existing logic over replacing it

---

## 📝 WHEN YOU THINK A NEW DEPENDENCY IS NEEDED

If you believe a new library would significantly help:

- Do NOT install it
- Do NOT modify configuration files
- Leave a clear comment explaining why it may be useful

Example:


```python
# TODO: This logic could be simplified using OpenCV contour utilities
```

## 🛑 WHEN YOU ARE UNSURE

If a change might:

* Affect multiple unrelated files
* Alter the core pipeline behavior
* Require architectural decisions

**Do not implement it.**

Instead, leave a comment or TODO describing the idea.

---

## 📌 MOST IMPORTANT RULE

> **Do not break what already works.**
> **Small, safe improvements are always preferred over bold changes.**

Your goal is to help this project progress toward usable, reliable results.