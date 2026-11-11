# Image choices: Muse and Claude each make one, Scott picks

**Scott, 2026-11-11:** "I want you to design the images for my MakerWorld profile.
I need you to put something on GitHub that tells Muse to work with you to each
produce an image and give me the choice to pick. This goes for post images also
until I see which path I want to take."

Scott, later the same day: "I'm not changing the logo. I just want you to design
images for post and MakerWorld. Alongside Muse."

**To Muse:** until Scott says otherwise, every post image and every MakerWorld
image (banner, model cover and gallery pictures) is made twice: once by you and
once by Claude, from the same brief. Scott picks one, and only the picked image
is used.

**Videos too** (Scott, 2026-11-11, yes to "treating videos the same way"): every
post video is made twice in the same way, one each, and Scott picks. The entry is
`muse.mp4` / `claude.mp4` beside its `.md`.

**The logo is not part of this.** Profile pictures stay the existing
OnBrandCraftz logo, unchanged, everywhere. Use the logo as it is wherever an
image carries it; never redraw it.

## How a choice works

Each image gets a folder here: `business/image_choices/<YYYY-MM-DD>_<short-name>/`.

1. **The brief: `REQUEST.md`.** Whoever starts the image (Muse or Claude)
   writes it:
   - where the image goes: platform and slot, e.g. MakerWorld banner,
     Instagram carousel slide 1;
   - the exact size in pixels, and what may get cropped;
   - what it must show, and which real files to use;
   - any text that must appear, word for word;
   - when it's needed.
2. **Two entries, one each:**
   - `muse.png` (or `.jpg`, `.mp4`) and `muse.md`
   - `claude.png` and `claude.md`

   The `.md` says how the image was made and lists every source file it uses.
   Make yours from the brief, not from the other's image. If you see the
   other's first, still make your own take.
3. **Scott picks.** He says "Muse" or "Claude" for a folder, in either chat.
   Whoever he tells writes `CHOICE.md`: the pick, the date, and his words if he
   gave a reason. Then they add a line to `CHOICES.md`.
4. **Only then is it posted or uploaded,** by Muse, as usual. Log it in
   `data/social/muse_log.md`, with this folder's name in the Media line.

## Rules for both sides

- **Show only real designs.**
  - Renders or photos of OnBrandCraftz's own files.
  - No AI-invented products, no stand-ins, and nothing the buyer won't get.
  - A render is labelled a render wherever a buyer could take it for a photo.
- **Use the current version.** If a design has a v2, the image shows v2.
- **Every claim must be checked:** free, price, size, print time, "tested".
  - Take it from the design's own README or printing notes.
  - "Free" only when the file really is free on that platform.
- **No other brands' logos or characters**, and no copies of other makers' designs.
- **Same brief, same size,** so the two entries can be compared side by side.
- **Nothing is posted until Scott picks.**

## Running record

`CHOICES.md` lists every pick, so the pattern shows which path Scott wants.
Once he chooses a path, he'll say so, and this file changes.

## Timing

Claude only works when Scott opens a session.
- **When Muse starts a folder:** Scott tells Claude "check image choices", and
  Claude adds its entry.
- **When Claude starts one:** Muse adds its entry the next time it runs.
