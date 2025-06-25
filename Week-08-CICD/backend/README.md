# Test docker builder

# try context with github.workspace

# Specify file

# Find down that I make wrong path

# Need to checkout to correct path for context in github.workspace

Absolutely — let's dig into what **`${{ github.workspace }}`** is and why **`actions/checkout@v4`** is required for `context:` to work properly in your Docker build step.

---

## 📦 What is `github.workspace`?

`${{ github.workspace }}` is a special GitHub Actions [**context variable**](https://docs.github.com/en/actions/learn-github-actions/contexts#github-context) that refers to the **root folder on the GitHub runner** where all your code will be available — **if you explicitly check it out**.

> 🔹 On a self-hosted runner or default GitHub-hosted runner, it's usually:
>
> ```
> /home/runner/work/<repo-name>/<repo-name>
> ```

### 🧱 But by default, this folder is **empty**.

---

## 🧩 So what happens when your workflow is triggered via `workflow_run`?

When a workflow is triggered this way:

```yaml
on:
  workflow_run:
    workflows: ["CI pipeline"]
    types: [completed]
```

👉 GitHub **does not automatically check out your code**
(unlike `on: push` or `on: pull_request`, where code checkout is implied).

> 🛑 So if you try to use:
>
> ```yaml
> context: Week-08-CICD/backend
> ```
>
> It resolves to:
>
> ```
> /home/runner/work/your-repo/your-repo/Week-08-CICD/backend
> ```
>
> …but that folder **doesn't exist** unless you ran:
>
> ```yaml
> - uses: actions/checkout@v4
> ```

---

## ✅ How `actions/checkout@v4` solves this

When you add:

```yaml
- name: Checkout code
  uses: actions/checkout@v4
```

GitHub Actions:

1. Clones your repository (the one the event was triggered from)
2. Puts it inside `${{ github.workspace }}`
3. Restores all files and folders, including your `Week-08-CICD/backend/Dockerfile`

So now your `context:` and `file:` become valid paths:

```yaml
with:
  context: Week-08-CICD/backend
  file: Dockerfile
```

Because they point to:

```
/home/runner/work/your-repo/your-repo/Week-08-CICD/backend
```

Which now exists.

---

## ✅ Summary

| Without `checkout`                 | With `checkout`                  |
| ---------------------------------- | -------------------------------- |
| `${{ github.workspace }}` is empty | Contains your repo files         |
| Dockerfile/context path not found  | Paths are valid and build works  |
| Workflow fails at build step       | Workflow builds and pushes image |

---

Let me know if you'd like a visual diagram of this folder layout, or to use a specific ref/branch when checking out.
