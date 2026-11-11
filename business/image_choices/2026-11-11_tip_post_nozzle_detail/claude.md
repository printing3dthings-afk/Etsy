# Claude's tip post

- `claude.png`: the post, 1080 × 1350.
- `claude.mp4`: the reel, 1080 × 1920, 18 s, no audio (add music on your side).
  The headline holds 1.2 s, then each tip slides in and stays 2.2 s, then the
  whole card holds 3.5 s.

**Layout:**
- The OBC logo at the top: the master image's own letters, lifted off its
  background, not redrawn.
- Headline "What a 0.4 mm nozzle / can really print", with "Measured on our own
  detail test, not guessed." under it.
- Six tiles, each with a number, a title, a small diagram and one line of text.
- A gold bar: "Save this for your next detail print".
- The source line: "OnBrandCraftz detail tests on a 0.4 mm nozzle, measured from
  the sliced toolpath."

**The diagrams are explanations, not photos.** They're drawn shapes (layers, a
groove, a dome as rings, a letter, dots), so no label is needed.

**Make another one:** write a JSON like
`business/social/tip_posts/nozzle_detail.json` on the branch and run
`python3 business/social/tip_posts/make_tip_post.py <file>.json`. Diagram kinds so
far: groove_up, snap, grow, stairs, letters, dots; tell me what a new post needs and
I'll add the picture.
