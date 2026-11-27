# Design-process videos (Scott, 2026-11-26)

## Claude, 2026-11-26 4:54 PM: a new kind of video, first one waiting on Scott

Scott, with a cutaway render of the Pie Drum Caddy v2: "I want you to use images like this from
your design process's to use in videos. From all of the prints you do this with. Can you
incorporate pictures like this into animations to transform from step to step until the final
product?"

- **What they are:**
  - the real exported parts animated in Blender: they move into place, the camera travels, and a
    cut sweeps through to the cutaway;
  - in the Product posts kit's frame, with the kit opener and end card;
  - every shot tagged RENDER, or REAL for Scott's own footage.
- **Where:** `business/social/design_process/` on branch `claude/new-session-o245bl` (README
  there). Each video ships with a SCRIPT.md: the timed lines for your voice-over, and the source
  of every figure on screen.
- **First one:** Pie Drum Caddy v2, 24.4 s, `out/pie_caddy_v2/pie_caddy_v2_design.mp4`.
  **Waiting on Scott's approval (STANDARDS 8). Please don't post it before he says yes.**
- **For you:**
  - **Series:** I've used the Product posts look. If you'd rather it be its own series or go
    under Maker's Blueprint, say which.
  - **No audio:** the video is silent; you add the voice-over and music when you post.

## Claude, 2026-11-26 5:06 PM: the caddy video is approved, and more are coming

- **Approved:** Scott, 2026-11-26: "That video for the caddy is awesome." He asked for one
  change, his name off the screen: the tested step now reads "We printed just the thread first.
  Our verdict here at OBC: great." It's rebuilt at the same path,
  `out/pie_caddy_v2/pie_caddy_v2_design.mp4`, with its SCRIPT.md (status: approved). **Clear to
  post.**
- **More coming:** Scott wants more of these, showing how each version came from the prototype
  prints and how it was designed. Next is the Gingerbread Tin: the white prototype clicker, the
  screw-on lid, the canister, and your media pack's photos of the colour canister. Gear Heart
  follows once the whole v2 heart is printed and put together.

## Claude, 2026-11-26 7:21 PM: Gingerbread Tin, waiting on Scott

- **The file:** `out/gingerbread_tin/gingerbread_tin_design.mp4` on the design branch, 34.6 s,
  with its SCRIPT.md.
- **The story:**
  - the white prototype with the lid pressed on;
  - Scott's white print, with his photo of the loose lid;
  - version 2's screw lid;
  - the first canister;
  - a cutaway of that canister's 3.4 mm gap and 2.7 mm thread turning into today's 1.86 mm seam,
    4 mm thread and guide ring;
  - your media pack's colour timelapse and photo.
- **Where the versions come from:** each one is the real source at its commit; SCRIPT.md names
  them.
- **Not to post until Scott approves it.**

## Claude, 2026-11-26 7:30 PM: the media library is up, for anything you post

Scott, 2026-11-27: "We need to start building an extensive library of photos and videos for use.
Including your images of how they are designed."

- **Where:** `business/media_library/` on the design branch:
  - `LIBRARY.md`: per build, what there is, by kind and version;
  - `library.json`: one record per file;
  - `sheets/<build>.jpg`: a labelled contact sheet per build, 124 in all.
- **Size:** 1,896 files across 116 builds.
- **The tag on each file is what a post must say:**
  - **REAL:** Scott's own photos and footage. Only from `real/`, `photos/` and
    `real_timelapses/` folders, never guessed from a name.
  - **EDITED:** his photo with an AI-made background (the OBC sign studio shots).
  - **RENDER:** a design render.
  - **SIMULATION:** drawn from the sliced toolpath. This includes the `*-timelapse.mp4` files
    in `video/` folders and `business/listing-videos/`: viewer replays, not printer footage.
  - **VIDEO:** a finished video of ours.
  - **LISTING:** a digital product's listing image.
- **Left out:** other people's work kept as design references.
- **Flagged:** Urban Kid v3 (Hunyuan licence: EU/UK/South Korea); Scott decides before any
  public post.
- **For your media packs:** please send Scott's photos and clips to me to file under the build's
  `real/`, so they land in the library with the right tag. Anything only in your local
  workspace isn't in it.
