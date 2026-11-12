# Cable Hook — delete or redo (Scott's call, 2026-11-11)

## 2026-11-11 15:18 EST - Benson — for review

Scott pulled up the Cable Hook on MakerWorld today (Sjack7, Private, dated
11/06/2026) and his direction, verbatim: "This needs to be deleted or redone
by Claude." The delete-or-redo choice is yours.

What he was looking at (his screenshot, Bambu Handy): a thick C-shaped hook
rising from an oversized flat rectangular plate, two small unexplained holes
in the plate beside the hook, gallery 1/7 renders, description reads fine
(matte white PLA, no supports, personal use only). The problem is the design
itself, same class as the Mochi Fox G3 failure: the silhouette reads as a
chunky blob on a slab, not as a considered cable hook — the hook's purpose
isn't legible at a glance and the plate is far bigger than the function needs.

**If you redo it:** keep the constraints the listing already promises —
matte PLA, no supports, prints flat — and bring it back through the gates
(G1 geometry, G2 slice, G3 render read) with a READY line here when it
passes: "READY: cable_hook v<n> — fact sheet: <path>, media kit: <path>".
A smaller plate, a hook profile that reads instantly, and no leftover holes
that don't earn their place.

**If you delete it:** remove the design and all references from the repo
working tree and say so in this thread. Flag the cost before any literal
history purge (same rule as the Mochi Fox deletion).

**MakerWorld side (mine):** the model stays up, Private, untouched until you
call it. On a delete verdict I delete the model; on a redo I swap the
profiles when your new version is READY. Nothing about this design gets
posted or promoted meanwhile.

## 2026-11-11 22:55 ET - Claude

**Verdict: redo, not delete.** A cable hook is a useful, searchable thing; this one just isn't designed. Agreed on the diagnosis:
- the oversized slab;
- the two holes that don't explain themselves;
- a hook that doesn't read as a hook.

**Process:** a new form needs Scott's pick before any modelling. I'm sending him 4–5 different forms today, in my working session. Once he picks:
- G1–G3, then a FACTS.md;
- the READY line here: "READY: cable_hook v2 — fact sheet: <path>, media kit: <path>";
- the old files go to the trash vault (tools/trash.py), not just deleted.

**Keep the model Private and untouched until then,** as you said.

## 2026-11-12 23:07 ET - Claude

**Scott picked form C, the desk-edge rail: a slim J-channel about 60 mm long that screws under the desk edge and holds several cables in a row.** Building now; READY line here when it passes its gates.

## 2026-11-12 23:18 ET - Claude

READY: cable_hook v2 (now the **Desk Cable Rail**) — fact sheet: openscad_models/cable_rail/FACTS.md, media kit: openscad_models/cable_rail/images/ (branch claude/new-session-o245bl, commit 7b02066f)

- **What it is:** a 60 mm J-channel that screws or tapes under a desk edge. Cables drop in through a 9 mm gap and lie in a row; three angled notches let any cable leave.
- **Gates:**
  - product gate pass: 0 support moves, 0 overhang perimeters, min wall 2.4;
  - fidelity 0 flags, fragility 0.
- **Print:** 28 m 26 s, 9.1 g.
- **must fix (for the MakerWorld swap):** the old page says "prints flat". This one **prints standing on its end** (laid flat, the J's curl would hang in the air). The fact sheet has safe wording and a don't-say list.
- **suggestion:** a new name in the title ("Desk Cable Rail"), since it's no longer a hook. Your call with Scott.
- **Old files:** `openscad_models/cable_hook.*` stay until you've swapped the model, then I'll archive them through the trash vault.
