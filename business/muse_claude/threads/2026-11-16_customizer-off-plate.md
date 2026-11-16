# Customizers print off the plate: turn Auto Arrangement on (2026-11-16)

**To Benson, from Claude.** Scott, today: the Name Ornament and Love Letter
customizers are broken. "It puts the print off the plate when customizing.
Can't be sliced or printed that way."

## Cause
- PMM's preview draws the plate centred on the origin, so the files are
  centred on (0, 0). That's why the preview looks right.
- The 3MF PMM generates for printing keeps the model's raw coordinates. In a
  3MF, (0, 0) is the plate's front-left corner, so the model hangs off it.
- Bambu Studio only moves the model onto the plate if the profile has
  **Auto Arrangement** turned on. It's a per-plate setting in the creator's
  profile configuration (Bambu's PMM v0.10.0 announcement,
  forum.bambulab.com/t/144618).
- This is why the placement flip-flopped: (128, 128) printed fine but
  previewed off the corner (Nov 10); (0, 0) previews fine but prints off
  (today). Neither works without the setting. With it on, (0, 0) works for
  both, so the files stay as they are.

## The fix: a MakerWorld setting, no new file
For each customizer: **Name Ornament (3549622)**, **Love Letter Mailbox
(3549413)**, and **Soft Frame label (3560650)** if its customizer is
attached (it's centred the same way):
1. Open the model's edit page and click the profile configuration button
   (top right).
2. Turn **Auto Arrangement** on for **every plate**.
3. Upload to save.
4. Generate a name (try "Olivia" and "Christopher"), open the generated file
   and check the model sits on the plate.
5. Customize and cloud-slice it in Bambu Handy. It should slice.

If the toggle isn't there, or Save hits the "Failed to download SCAD file"
wall again, reply here with what you saw. Don't swap the files: the committed
.scad is correct for this.

The rule is recorded in `tools/pmm_build.py` (rule 3) and both customizers'
notes, on branch claude/new-session-o245bl, commit f85e0cd6.

## Separately: the Handy slice failure you diagnosed (0500-4014)
Noted: bambu_slice.py's 3MFs have no `<model_instance>` in the plate section.
Not fixed yet; I'll reply in your Nov 15 thread when it is.
