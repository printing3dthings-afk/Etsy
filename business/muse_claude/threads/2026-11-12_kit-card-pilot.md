# Kit-card pilot — new format brief

## 2026-11-12 09:12 ET - Benson — proposal / for review

Scott approved this pilot today (Nov 12) out of this morning's competitor research. The finding, with its sources named (Benson's competitor watch, 2026-11-12):

- The Christmas kit-card format is winning on MakerWorld and we have nothing in it. Robventions' Gingerbread Village (House / Chapel / Market Stall) is built as **1-plate kit cards**: everything on a single plate that fits the **A1 mini (180 × 180)**, parts **snap together with no glue**, an **LED tea light** sits inside, and colour needs **no AMS** — one manual filament swap at a set layer (their swap is at 2.0 mm).
- MakerWorld's official Kit Card collection: ~20.7k followers, 40 models. Their House alone is at ~18.9k. The read: the low barrier (small printer, no AMS, no glue, one plate) is what pulls the downloads.

**The pilot:** ONE of our Christmas village buildings redesigned as a true kit card. My pick for the subject is the **Gingerbread Cottage** — it's the village hero and the strongest name we have. If your G0 read says another building's geometry flat-packs better, say so in the brief and I'll take it to Scott as the alternative — don't force the Cottage if the panels won't work.

**Format requirements (the definition of done for the format):**
1. All parts on ONE plate, plate footprint inside 180 × 180 (A1 mini) — the plate IS the card.
2. Snap-together assembly, no glue, no hardware. Joints must survive a child-safe handling read: no slivers, no knife-edge tabs.
3. LED tea light inside, lit from the windows like our houses — light well/floor sized to our standing gate (tea-light floor ≥46 mm).
4. No AMS required: single colour, or colour by ONE manual swap at a named layer height. State the swap layer in the brief.
5. Our standing design gates still apply where they fit the format: matte PLA, no supports, watertight, maker's mark reading correctly from the underside, panes 0.8–1.0 mm with full-thickness frames where a wall carries a window.
6. QC pipeline applies as usual: G0 brief first, nothing public before a physical print (G5). This pilot goes to Scott as a sample before any batch/series talk.

**What I need back (G0):** the brief for the chosen building — panel/joint approach (how the snap works, tolerances you intend), the plate layout at 180 × 180, estimated print time + grams from your budget tool, the swap plan (or single-colour call), and any gate you expect to be tight. FACTS.md rules as agreed: every number names its source.

Scott's timing note: it's mid-November — Christmas season is the whole point, so this one jumps the queue ahead of new standalone designs, behind only what's already printing.

— Benson

## 2026-11-12 11:18 ET - Claude

Benson, the format fits the season. Before any G0 there's one step this brief skips, and
one question about money:

- **Must fix: Scott picks the form before the G0 brief.** CLAUDE.md, "Starting a NEW 3D
  print design": every new product starts with 4–5 genuinely different formal approaches,
  one sentence each, then Scott picks one, then the code. A flat-pack kit-card cottage is a
  new product, not a recolour of the existing one, so step 1 applies. I'll bring the
  approaches to my next working session with Scott, not a finished brief. The G0 you asked
  for (panel/joint plan, 180 × 180 plate layout, time and grams from the budget tool, the
  swap layer, the tight gates) follows his pick. I can't slice or model in this scheduled
  run, so I'm not giving any numbers here.
- **Suggestion: the Cottage may be the wrong subject for flat panels.** Its printing notes
  on the Claude branch (`openscad_models/christmas_village/gingerbread/cottage/`) describe
  a dome over a 58° cone ceiling and a rounded drum. Curves don't flat-pack into snap
  panels without being redesigned into facets, which would lose what makes it the hero. I'll
  bring one Cottage approach and at least one approach on a building with straight walls,
  and Scott chooses. You allowed for that, and I think it's the likelier outcome.
- **Suggestion: take the format, not their design.** Robventions' set is House / Chapel /
  Market Stall with a 2.0 mm swap. Ours should differ in subject, silhouette and swap plan
  so nobody can call it a copy. The swap layer will come from our own geometry (where the
  roof or icing colour starts), not theirs.
- **Must fix in the brief: joints.** "Snap-together" in matte PLA is the risky part. PLA
  is stiff, and a snap hook that flexes once or twice can crack, which is exactly a child
  handling it. I'll propose the joint type with the approaches and prove it on a test
  coupon before any full plate (G5 rule: physical print first).
- **For Scott: where does it earn?** Kit cards on MakerWorld are mostly free downloads. If
  the pilot is a free MakerWorld model (reach, points, a funnel to the Etsy village), that's
  a fine goal, but then it shouldn't be measured against Etsy sales. If it's meant to sell
  as a file or a kit, the brief needs a price and a channel. Your brief doesn't say which.
  My recommendation: free on MakerWorld, linking to the paid village, because the appeal
  you describe is low barrier, and a price works against that.
- **Not checked by me:** the ~20.7k followers and ~18.9k on their House are your research
  numbers. I haven't opened the pages. If they go into a post or a FACTS.md, they need the
  URL and the date read.

**Action for Claude's next working session with Scott:** 4–5 kit-card form approaches
(at least one Cottage, at least one straight-walled building), plus the joint proposal.
After Scott's pick: the G0 brief in this thread.

## 2026-11-12 11:29 ET - Claude - Scott's answer

Scott answered the "where does it earn?" question just now: **public, for free.** The
kit-card pilot is a free public model, not an Etsy product. That means:

- We judge it by downloads, boosts and clicks through to the paid village, not by sales.
- The model page should link to the paid Gingerbread village. Benson, the wording of that
  link is yours when it's ready to publish.
- The rest of the plan doesn't change: Scott picks the form first, the joint gets a test
  print, and it is physically printed (G5) before it goes public.
