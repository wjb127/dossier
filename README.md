# dossier

**A cross-project index your AI coding agent can search.**

[한국어](README.ko.md)

> Status: early design. The first release will ship as a Claude Code plugin + skill (`/dossier`).
> Nothing to install yet — watch the repo for v0.1.0.

---

## The problem

AI coding agents know the repository they are standing in. They do not know the other two hundred.

If you run many projects at once — freelance work, an agency, a pile of side projects — the questions you ask
every day are not about code. They are about *which project* and *what happened last time*:

- "The client with this phone number — which folder is theirs?"
- "Is `shop.example.com` a site we deployed, or just a reference they sent us?"
- "How do I deploy this one again? Which account, which branch?"
- "Where is the API token for this client? (Not the value. Where.)"
- "What broke the last time someone touched this project?"

Per-repo memory files (`CLAUDE.md`, `AGENTS.md`) cannot answer these, because the answer lives *across* repos.
Conversation memory tools remember what you said, not how your projects are laid out.

## The idea

Keep one local index — a *dossier* per project — and give your agent a skill to search it, update it,
and act on it.

| Principle | What it means |
|---|---|
| **Search by the things humans remember** | Client name, alias, phone number, domain, tag — not just folder names. Each axis has a weight, so a client-name hit outranks a passing mention. |
| **Domains have roles** | A domain is either *ours* (we deployed it), a *reference* (someone sent it as an example), or *the client's other site*. Mixing them makes search confidently wrong. |
| **Humans win merges** | Automatic extraction refreshes what it can detect, but never overwrites what a person classified. |
| **Pointers, not secrets** | Store *where* a credential lives (vault, item id, field), never the value. Warn when the item title will not match the project name. |
| **Lessons accumulate** | When the agent hits a trap in a project, it appends one line to that project's `gotchas`. The next run reads them before touching anything. |
| **Search, then act** | One command finds the project, reads its gotchas and deploy recipe, makes the change, builds, and deploys — the index is a launchpad, not a phone book. |
| **Check the live state** | For a domain query, resolve DNS and fetch the site, then label it live / expired / never connected. |

## How it compares (preview)

A full comparison — with sources — will live in `docs/en/comparison.md`. The short version of the hypothesis:

| Tool family | Scope | Searches by client / phone / domain | Secret locations | Deploy recipe | Learns from traps |
|---|---|---|---|---|---|
| Path jumpers (ghq, zoxide) | Directories | No | No | No | No |
| Software catalogs (Backstage) | Org services | By owner team | Via plugins | Partly | No |
| Per-repo memory (CLAUDE.md, AGENTS.md) | One repo | No | As prose | As prose | Partly |
| Agent memory layers (mem0, Letta, Zep, …) | Conversations | Semantic | No | No | Indirect |
| Codebase indexes (repomix, code-graph MCPs) | Code structure | No | No | No | No |
| **dossier** | **All your projects** | **Yes, weighted** | **Pointers only** | **Yes** | **Yes** |

Every cell above is a claim to verify. Anything that turns out to exist elsewhere moves to "prior art" instead of "difference".

## Roadmap

- [ ] Research existing approaches and publish the comparison (EN / KO)
- [ ] Index schema (`schema/index.schema.json`) with configurable folder prefixes
- [ ] Search / save / domain-check script — Python standard library only
- [ ] Synthetic sample index + generator (no real data, ever)
- [ ] Claude Code skill `/dossier` + plugin manifest (`/plugin install`), compatible with `npx skills add`
- [ ] Optional adapters: secret managers, messenger rooms, deploy targets
- [ ] v0.1.0 release

## Privacy

Your index is personal data: client names, phone numbers, domains, where your credentials live.
dossier is designed so that it never leaves your machine.

- The index file is git-ignored by default.
- Examples and tests use synthetic data only.
- `tools/privacy-scan.py` checks files *and* commit metadata against a local deny-list before you push.

## License

[MIT](LICENSE)
