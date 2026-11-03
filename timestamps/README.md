# Timestamps

External timestamps of this repository's history, so that "frozen before the comparison runs" does not rest on commit dates alone (those can be set by whoever commits). Required by the pre-registration rule in `vault/_CLAUDE.md` (Section 1). No anchor exists yet (2026-11-03): the first is made when `vault/project/Hypotheses.md` is frozen, before any A/B/C comparison run.

- **`seal_anchor_N.txt`** names a commit (HEAD), its tree and the UTC time of stamping, and lists the commits up to it. A git commit hash fixes the entire history before it, so the anchor covers every commit listed.
- **`seal_anchor_N.txt.ots`** is the [OpenTimestamps](https://opentimestamps.org) proof of the anchor file. Only the file's hash is sent to the public calendars; no content leaves the machine.
- **Stamping:** `uvx --from opentimestamps-client ots stamp seal_anchor_N.txt`
- **Upgrading.** A fresh proof is "pending" until the calendars' Bitcoin transaction confirms, a few hours later. Run `ots upgrade seal_anchor_N.txt.ots` and commit the upgraded proof. (In the-elo-of-e-aura, `ots upgrade` failed on Windows because python-bitcoinlib could not load OpenSSL; it was run on Linux instead. Use WSL2 here if that recurs.)
- **Verifying:** `ots verify seal_anchor_N.txt.ots` reports the Bitcoin block that attests the anchor. `git cat-file -p <HEAD>` shows that the commit exists with that tree.
- Every anchor is logged in `vault/project/Decision Log.md` with its commit.

| Anchor | HEAD | Stamped (UTC) | Covers |
|---|---|---|---|
| (none yet) | | | |
