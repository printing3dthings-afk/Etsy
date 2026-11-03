# Cartoon, Kawaii and Chibi Character Design + Flat Silhouette and Bézier Outline Craft

Scope: rules a designer drawing *in code* (point lists, Bézier segments, OpenSCAD/SVG polygons) can apply when building a stylized character (e.g. a flying cherub/Cupid with a bow, a kawaii animal) that must read as one flat silhouette (pendant, charm, stencil, die-cut sticker, extruded sign) or a simple 3D-printed figurine.

Research note on source quality, read first: the primary books (Stanchfield's *Drawn to Life*, Blair's *Cartoon Animation*, Bancroft's *Creating Characters with Personality*, Thomas & Johnston's *Illusion of Life*) are not freely available online. Searches returned table-of-contents listings and secondary summaries, not their text. Where a claim below is attributed to one of those books, it is via a listing or a secondary source and is marked as such. Many search hits were SEO spam pages that mimic these books; those were discarded and are not cited.

---

## 1. Shape language, silhouette readability, line of action, gesture, appeal, exaggeration and simplification

### Takeaway
Build the character as a few big, simple masses hung on one line of action; make it asymmetric (avoid "twinning"), give every joint a different angle, set straights against curves, and test it as a solid black shape. If the black shape doesn't say what the character is doing, the design isn't finished. Detail is added last and only where it doesn't break the outline.

### Cited Findings
**Line of action and construction order (Blair)**
- Blair's construction sequence starts with the line of action/stance: a line running through the 3D parts that sets the attitude of the figure's solid masses. Then come rounded masses for head and body, then details "fitted or hinged into position", then cleanup around construction lines. He calls proportion "one of the most important factors when constructing a cartoon character." These are excerpts quoted on secondary pages, not verified against the book. — [Scribd copy of Cartoon Animation by Preston Blair (unofficial)](https://www.scribd.com/doc/164046754/Cartoon-Animation-by-Preston-Blair); [Line of Action notes citing Blair](https://jamshidnoori.blogspot.com/p/animation.html)
- The revised edition's Chapter 4, "Basic Character Movement", covers Line of Action and Rhythm & Design. — [Quarto: Cartoon Animation with Preston Blair, revised edition](https://quarto.com/books/9781633228900/cartoon-animation-with-preston-blair-revised-edition)

**Stanchfield (Disney gesture classes)**
- *Drawn to Life* Vol. 1 has a lecture titled "Straights and Curves", placed right after "Simplify Where Possible" (numbered 13 in one listing, 14 in Routledge's). — [Routledge listing, Drawn to Life Vol. 1](https://www.routledge.com/Drawn-to-Life-20-Golden-Years-of-Disney-Master-Classes-Volume-1-The-Walt-Stanchfield-Lectures/Stanchfield-Hahn/p/book/9781032104416)
- Stanchfield's gesture-drawing handouts (compiled by Leo Brodie) include a section titled "Straight against Curve: Squash and Stretch in the Pose". Only the heading could be checked. — [archive.org gesture drawing PDF](https://archive.org/download/ART15PDT/ART-7-GDF.pdf)

**Concrete posing rules (Animator Island, "Perfect Posing 2")**
- Judge the pose by its outline alone. Viewers should be able to tell "what your character is doing (and maybe even what he is feeling) just by the silhouette." If a limb has to sit in front of the body, make it stick out from what is behind it and move it away from crowded areas. — [Animator Island: Perfect Posing 2](https://www.animatorisland.com/perfect-posing-2-appealing-and-readable/)
- Use "a different angle for every joint" to break symmetry. Shoulders, hips and head are often left too level, so tilt them. Alternating tilts give varied positive and negative shapes and make the pose more dynamic. — [Animator Island: Perfect Posing 2](https://www.animatorisland.com/perfect-posing-2-appealing-and-readable/)
- Put a straight line next to a curved line, including on opposite sides of the same body part. Stylized work may need this contrast more strongly than realistic work. — [Animator Island: Perfect Posing 2](https://www.animatorisland.com/perfect-posing-2-appealing-and-readable/)
- Keep shapes flowing: transitions between shapes should be smooth. — [Animator Island: Perfect Posing 2](https://www.animatorisland.com/perfect-posing-2-appealing-and-readable/)

**Appeal and twinning (Disney principle)**
- Appeal: avoid mirror symmetry, since asymmetry is generally more interesting and appealing. Balance simplicity and complexity: not so simple it bores, not so complex the viewer can't follow it. — [ACM SIGGRAPH HyperGraph: Appeal](https://education.siggraph.org/static/HyperGraph/animation/character_animation/principles/appeal.htm)
- Twinning means unintentionally mirroring both sides of the body. Thomas and Johnston demonstrated its "killing effect" in *The Illusion of Life*. Sources disagree on which principle it falls under: Animation Mentor puts it under Solid Drawing, SIGGRAPH under Appeal. — [Animator Island: Defining the Art: Twinning](https://www.animatorisland.com/defining-the-art-twinning/); [Animation Mentor: Solid Drawing](https://animationmentor.com/blog/solid-drawing-the-12-basic-principles-of-animation); [UW CSE posing lecture ("avoid perfect symmetries")](https://courses.cs.washington.edu/courses/cse458/10au/content/projects_458/project6a/posing.pdf)

**Shape language (circle/square/triangle)**
- The common vocabulary: circles, squares and triangles signal personality. Relaxed characters use curves, softer angles and open flowing shapes; tense ones use straighter lines and sharper angles. A character should still read in grayscale, with colour supporting shape structure rather than replacing it. This is a game-art studio blog, a secondary source. — [RocketBrush: Shape language in game character design](https://rocketbrush.com/blog/shape-language-in-game-character-design-how-to-make-characters-readable-and-consistent)
- That same blog's "70/30 rule" (silhouette drives ~70% of impact) is a rule of thumb with no study behind it. Do not quote it as fact. — [RocketBrush](https://rocketbrush.com/blog/shape-language-in-game-character-design-how-to-make-characters-readable-and-consistent)

**Bancroft**
- *Creating Characters with Personality* (2006) has a basics section on shape, size and variance, and a later chapter on groupings, variety and pairs. The catalog doesn't include the text. — [ICPL catalog record](https://search.icpl.org/Record/1277092)
- Bancroft's Skillshare class lists four tips, the first being shape variety. The others are depth in the final line, a review pass, and Photoshop finishing. — [Class Central: Character Design with Personality (Tom Bancroft)](https://www.classcentral.com/course/skillshare-character-design-with-personality-4-core-concepts-for-creating-better-characters-with-tom-bancroft-81726)

### Inferences
- Code workflow implied by Blair's order: (1) define the line of action as one spline (a C or S curve, never straight); (2) place head, torso and pelvis masses as ellipses along it, each rotated to that curve's local tangent so no two share an axis; (3) hang limbs and props; (4) only then union and trace the outline. Placing details first is what produces stiff, symmetric results.
- "A different angle for every joint" translates directly to code: if two segment angles in your skeleton are equal or mirrored (e.g. left and right wings at ±30°), change one. For a Cupid, tilt the head, offset the wings (near wing larger and higher, far wing smaller and partly hidden), and keep the bow arm and string arm at clearly different angles.
- "Straight against curve" for an outline: on each limb, make one side a nearly straight segment and the opposite side a full convex curve. Examples: the straight shin front against the curved calf; the flat back of a tummy against the round belly front. Two parallel curves of equal radius produce the "sausage" look.
- Shape variety ("big, medium, small", per Bancroft's "size/variance" heading): give the masses clearly different sizes, such as a huge head, medium body and small limbs for chibi. Equal-sized masses read as bland.

### Gaps
- The actual text of Stanchfield's "Straights and Curves" lecture, Bancroft's "Shape/Size/Variance" chapter, and Stephen Silver's shape-language teaching couldn't be retrieved. Only titles and summaries were found. No Pixar/Disney talk transcripts with numeric rules were found.
- No source gave a numeric "how much exaggeration" rule.

---

## 2. Cartoon, chibi, kawaii and cherub proportions: head-to-body ratio, features, hands, feet, chubby limbs, knee and foot bends

### Takeaway
Chibi is 2–3 heads tall, with 2.5 the usual "standard". Use 2 for toy-like or maximum cute, and 3 when the pose or costume needs to read. Real infants (the basis of putti and cherubs) are about 4 heads tall. Eyes sit at or below the vertical middle of the head. Necks, noses, fingers and joint detail are dropped or reduced to simple shapes. The torso is a bean or pear with weight low. Legs are never one straight line; the lower leg is offset from the upper at a one-way hinge.

### Cited Findings
**Head-to-body ratio**
- "The chibi body ranges from 3-heads-tall to 2-heads-tall"; the head is about ½ to ⅓ of total height. Three types: *head-heavy* (very large head, babyish), *body-heavy* (like a 4-year-old in manga style; the body can look too long, so keep the head the focal point), and *balanced* (the "safe zone"). — [Clip Studio Tips: General guide to drawing chibis](https://tips.clip-studio.com/en-us/articles/4863)
- Other guides give 1.75–3 heads, with 2.5 called standard. 2 heads looks very young and toy-like; 3 heads leans toward "chibi-lite" anime. Use 3 heads when you want viewers to focus on costume or pose, and define shapes more clearly at 3 heads than at 2. Counting: a body one head long makes a 2-head chibi; a body two heads long makes a 3-head chibi. (Search-summary aggregate of Clip Studio articles; ratios on fightcancer.org and fiskerforum conflicted and were discarded.) — [Clip Studio Tips: Chibi: Simplify and Adorable](https://tips.clip-studio.com/en-us/articles/4973); [Clip Studio Tips: How to draw chibis (different styles)](https://tips.clip-studio.com/en-us/articles/4868); [Clip Studio Tips: Body proportion in chibi drawing](https://tips.clip-studio.com/fr-fr/articles/4829?org=1)
- Infants are about 4 heads tall (head ≈ ¼ of height), with a relatively long torso and short, chubby limbs. Young children are about 5–6 heads tall with a prominent forehead. — [DrawingHowToDraw: Proportions of children's figures](https://www.drawinghowtodraw.com/drawing-lessons/drawing-faces-lessons/articles/proportions-children-figures.html)
- A putto is a naked, sometimes winged, cherub. Chubby cheeks, a prominent forehead and a soft round contour define the baby face. Limbs are chubby "with minimal joint definition"; hands and feet are small and stubby. (Secondary/aggregated; no canonical putto construction with measurements was found.) — [DrawingHowToDraw: Proportions of children's figures](https://www.drawinghowtodraw.com/drawing-lessons/drawing-faces-lessons/articles/proportions-children-figures.html); [Google Arts & Culture: Flying Putto, Annibale Carracci (reference artwork)](https://artsandculture.google.com/asset/flying-putto-annibale-carracci/jQH62ZjnzmBKSw)

**Feature placement and simplification (chibi)**
- Eyes sit "low on the skull", at the middle of the head or lower, oversized with exaggerated pupils, and not too far apart. — [Clip Studio Tips: General guide to drawing chibis](https://tips.clip-studio.com/en-us/articles/4863)
- The neck is often omitted; if present it is short and slim. The nose is rarely drawn (a dot or shadow at most). Front-view ears sit lower than the eyebrows. Teeth are omitted unless needed. — [Clip Studio Tips: General guide to drawing chibis](https://tips.clip-studio.com/en-us/articles/4863)
- The torso is a bean or pear shape with weight in the lower part, no real shoulders, and curved hips. — [Clip Studio Tips: General guide to drawing chibis](https://tips.clip-studio.com/en-us/articles/4863)
- Hands are simplified: some or all fingers omitted. A plain circle (mitten/nub) is used, rarely, for a frustrated or waving character. — [Clip Studio Tips: General guide to drawing chibis](https://tips.clip-studio.com/en-us/articles/4863)

**Legs, knees, feet**
- "The leg is not a straight line." Upper and lower leg in one straight line "very rarely happens" (over-extension). The lower leg is offset from the upper. The knee is a hinge: it bends one way and stops at a set point the other way. — [Artists Network: Common Mistakes of Drawing the Leg](https://www.artistsnetwork.com/art-mediums/drawing/common-mistakes-of-drawing-the-leg)
- Set a slight bend at the knee so legs don't look stiff. — [secondary tutorial summary](https://garrendoperelpland.blogspot.com/2021/11/how-to-draw-bent-leg.html)

### Inferences
- Default cherub/Cupid for a pendant or figurine: 2.5–3 heads tall (chibi-cherub) rather than the 4-head anatomical infant. A 2-head body leaves too little room for a bow, wings and a readable leg pose in one silhouette. The Clip Studio note that 3 heads "focuses on pose/costume" supports this choice when a prop must read.
- Face layout for a kawaii head of height H: put the eye line at about 0.5–0.6 H from the top (at or below the middle, per Clip Studio). Eye spacing should be about one eye-width or less. Cheek blush goes just below and outside the eyes. Mouth is a small dot or "w" well above the chin. These offsets are practice-based inference from the "middle or lower" rule, not a sourced number.
- Chubby leg shape (inferred from "not a straight line" + "minimal joint definition" + straight-against-curve): draw the thigh as a teardrop wider at the hip. Pinch in slightly at the knee: for babies this is a crease on the inner side, not a bony knee. The calf bulge goes to the back (posterior). The shin front stays nearly straight. The ankle is a tight pinch. The foot is a rounded wedge whose toes point the same way the knee points. "Backwards" knees happen when the calf bulge is on the front, or the foot points opposite to the knee's bend; the knee always bends so the shin swings *behind* the thigh.
- Arms: sausage-like, with a crease (narrow notch) at the elbow and wrist rather than a joint bump. A mitten hand with at most a thumb separated is enough at pendant scale.

### Gaps
- No source with numeric cherub/putto canon (e.g. Renaissance putto head counts) was found.
- No authoritative source specifically on chubby cartoon knees and calves or on cartoon foot construction was found; the leg rules above come from a realistic-anatomy article and are extended by inference.
- Kawaii-specific (as opposed to chibi) guidance (e.g. Sanrio-style "no mouth", eye spacing numbers) was not found in primary sources.

---

## 3. Silhouette design for flat cut-outs: negative space, separating limbs, tangents, overlap, view choice, cut-through gaps and internal detail

### Takeaway
Fill the design solid black. Every limb, wing tip and prop should break the outline with its own negative-space hole or notch. Edges either overlap decisively or are clearly separated, never just touching (tangent). For physical cut parts, every bridge and gap must meet a minimum width tied to material thickness or nozzle. For die-cut stickers, the cut line is a smooth offset of the art with no thin tabs.

### Cited Findings
**Silhouette test and negative space**
- Silhouette test: fill the character solid black with no interior lines and check it is still recognisable. "If the pose is unclear as a black shape, it will likely be unclear in motion." If it fails, adjust spacing, overlap, limb angles or costume contour, then repeat. — [Binus University DKV: The Power of Silhouette](https://binus.ac.id/bandung/dkv/2025/11/04/the-power-of-silhouette-designing-readable-characters-in-motion/); [Cursa: Readable Poses, Silhouettes, and Line of Action](https://cursa.app/en/page/character-animation-starter-kit-readable-poses-silhouettes-and-line-of-action)
- Gaps between limbs and torso (arm/torso, hat/shoulder) keep the silhouette from becoming a blob. — [RocketBrush: Shape language](https://rocketbrush.com/blog/shape-language-in-game-character-design-how-to-make-characters-readable-and-consistent)
- A limb in front of the body must stick out from what is behind it and be moved away from crowded areas. — [Animator Island: Perfect Posing 2](https://www.animatorisland.com/perfect-posing-2-appealing-and-readable/)

**Tangents**
- Tangents are outlines of separate objects meeting at one point. They make the depth relationship unclear and flatten the drawing. Keep them only when deliberate. — [Animator Island: Perfect Posing 2](https://www.animatorisland.com/perfect-posing-2-appealing-and-readable/)
- John Baldessari recalled a professor's rule: elements should either overlap or have space between them; near-touching ("kissing") creates discomfort. — [Gurney Journey: Tangencies in Real Life](https://gurneyjourney.blogspot.com/2010/11/tangencies-in-real-life.html?m=1)
- Fixes: separate clearly or overlap decisively; make one line dominant; move one shape behind the other. — [Gurney Journey: Overlapping](https://gurneyjourney.blogspot.ch/2012/07/overlapping.html); [Cursa: Clean line art techniques](https://cursa.app/en/page/digital-drawing-on-a-tablet-clean-line-art-techniques-line-weight-tapers-and-corners)

**Pendant/laser-cut bridges and islands**
- An "island" is an internal shape that falls out after cutting (the classic stencil problem: the middle of an O). It needs bridges. SendCutSend's DFM guide sets minimum bridge width at 50% of material thickness. Tighter curves need more clearance to keep strength and prevent burn-through. — [SendCutSend DFM guide (PDF)](https://sendcutsend.com/wp-content/uploads/2025/11/5.2.pdf)
- Ponoko (laser-cut metal): bridge width = material thickness; minimum hole size = 1.5× material thickness. — [Ponoko: How do I design for laser cut metal](https://help.ponoko.com/en/articles/3204835-how-do-i-design-for-laser-cut-metal)
- Laserboost: minimum distance between cut features and the outer contour = sheet thickness (aluminium). — [Laserboost: Design Guide for Flat Laser-Cut Parts](https://laserboost.com/?p=13394)
- No jewelry-specific bridge standard was found. Vendor numbers span 0.5–1× thickness. — (synthesis of the three sources above)

**Die-cut stickers**
- Minimum line weight is 1 pt (Sticker Mule). Minimum border is 1/16" (0.0625"), default 1/10" (0.1"). — [Sticker Mule: artwork requirements](https://stickermule.com/support/what-are-your-artwork-requirements-for-stickers-and-labels)
- About 2 mm (0.075") margin between cut line and design is needed for a precise cut. — [StickerApp: thinner border](https://stickerapp.com/support/artwork-design/is-a-thinner-border-achievable-for-my-stickers)
- Bleed 1/8" (3 mm); keep key content at least 1/8" (3 mm) inside the trim. Body text >6 pt, brand/important text >8 pt. A 0.5 pt hairline border "is a trap": use a border thick enough to absorb trim shift, or none. Simplify intricate lines on small stickers because ink spreads. — [MOO: Sticker design mistakes](https://www.moo.com/blog/uk/inspiration/sticker-design-mistakes)
- Make the cut path a smooth offset border. Avoid long thin protrusions and tiny tabs, which peel or tear. Extend the border 2–3 mm past the cut so drift eats spare border, not the art. — [Atomm: How to design stickers (outline, bleed, cut line)](https://www.atomm.com/cs/blog/2645-how-to-design-stickers)

### Inferences
- For a flying Cupid silhouette, prefer a near-profile or shallow 3/4 view in which:
  - the bow is held *out* in front, so its arc and string make a clear negative-space "D" separate from the body;
  - both wings fan up and back from the shoulder blades, with a visible gap between each wing's trailing edge and the back or bottom;
  - the legs are bent at clearly different angles (one tucked, one trailing) with a hole between them;
  - the arrow line crosses no other edge at a tangent.
  A frontal, symmetric pose with arms against the torso fails all of these.
- One-piece rule for pendants and stencils: every enclosed hole needs a path to the outside (stencil), or the whole piece must stay connected (pendant). Use the bridge minimum from your process. For FDM printing of flat charms, use the shop's own extrusion-width floor (see the repo's `DETAIL_STANDARD.md` and the 1.2 mm minimum wall rule in CLAUDE.md) instead of the laser numbers.
- How much internal detail to keep: only what survives at actual size. Translate MOO's "simplify for ink spread" and the 1 pt line minimum to physical cut parts: an interior cut-through should be at least about the bridge minimum wide; anything thinner should be engraved or omitted, not cut. Prefer two or three large, meaningful cut-throughs (the eye, the gap between bow and body, the gap under the wing) over many small ones.
- Make the sticker cut line with a positive offset (e.g. 2–3 mm), then smooth it with a round join and a closing operation (offset +r then −r) to remove notches narrower than about 2r. This is the vector form of "no tiny tabs".

### Gaps
- No primary source from a jewelry or pendant designer on choosing *where* to place cut-through gaps for character pendants was found. Guidance above is inferred from silhouette and fabrication rules.
- No source gave a numeric negative-space target (e.g. % hole area).
- Profile vs. 3/4 for silhouette clarity is common animation practice, but no citable primary source stated it explicitly.

---

## 4. Vector craft for clean outlines: Bézier best practice

### Takeaway
Use as few anchors as possible, placed at horizontal and vertical extremes. Use smooth nodes with collinear handles everywhere except deliberate corners. Each segment should fit inside the triangle formed by its two anchors and the intersection of its handles. Keep handle lengths balanced, about 55% of the way to the intersection for circular arcs and up to about 60–70% for "fuller" shapes (the "1/3 of chord" rule of thumb is the same idea measured differently). Avoid inflections inside a segment, and match curvature (G2) at joins.

### Cited Findings
- Place nodes at horizontal and vertical extremes: this simplifies paths, reduces point count and is required for hinting. Avoid very shallow curves only a few units deep. — [Glyphs: Drawing Good Paths](https://glyphsapp.com/learn/drawing-good-paths)
- "Every curve segment should fit nicely in a triangle" formed by its two on-curve nodes and the point where the handle extensions intersect. Handles must not extend outside that triangle, cross each other, or cross each other's extension. Each segment has two handles; a single handle or a zero-length handle is a defect. — [Glyphs: Drawing Good Paths](https://glyphsapp.com/learn/drawing-good-paths)
- Handle length as a percentage of distance to the intersection (100% = handles meet): circles and ellipses about 55–56%; type-design handles usually just under 60% to above 70%. Keep handles balanced (similar percentages) to avoid flat spots. — [Glyphs: Drawing Good Paths](https://glyphsapp.com/learn/drawing-good-paths)
- Avoid inflections in a segment unless the curve truly needs one; if both handles are horizontal or vertical no inflection is needed. Match curvature at node joins (G2 "harmony"). Remove superfluous nodes and zero-length segments. Use corner and smooth node types deliberately. Outer contours run counter-clockwise and holes clockwise. — [Glyphs: Drawing Good Paths](https://glyphsapp.com/learn/drawing-good-paths)
- Rule of thumb from Illustrator teaching: handle length about one third of the distance between the anchors ("Rule of 30"). — [Noble Desktop: Drawing curves in Illustrator](https://blog.nobledesktop.com/learn/illustrator/drawing-curves-illustrator-video-tutorial); [Carbide 3D community thread](https://community.carbide3d.com/t/carbide-create-re-drawing/15811)
- Deke McClelland's "rule of thirds": keep the invisible third leg of the control polygon (joining the two handle ends) about 1/3 of the curve. — [Deke.com: The Rule of Thirds for Smooth Bézier Curves](https://deke.com/content/the-rule-of-thirds-for-smooth-bezier-curves)
- Anchor points belong at the extremes of each path (also standard in FontLab practice). — [Webucator: Bezier curves in Illustrator](https://www.webucator.com/article/how-to-work-with-bezier-curves-in-adobe-illustrato/); [Typography.guru forum: handles](https://typography.guru/forums/topic/106309-handles)
- Quarter-circle cubic constant: the common κ = 4(√2−1)/3 ≈ 0.5522847. — [Grida docs: kappa](https://grida.co/docs/math/kappa)
- A better least-error constant, c ≈ 0.551915, used by libraries citing Mortensen. Mortensen says it gives 5× less maximum radial drift than the standard. — [flo-bezier3 source (cites Mortensen)](https://cdn.jsdelivr.net/npm/flo-bezier3@6.0.6/src/create/generate-quarter-circle.ts); [Spencer Mortensen: Approximate a circle with cubic Bézier curves](https://spencermortensen.com/articles/bezier-circle/)
- Only higher-order curves can approximate a full circle with a single Bézier. Standard Bézier curves can never describe a circle exactly. — [Pomax: A Primer on Bézier Curves](https://pomax.github.io/bezierinfo/)

### Inferences
- Computed for this note (numerical check, not from a source): κ = 0.5522847 gives a maximum radial error of +0.027% of radius (always outside). c = 0.5519150 gives ±0.0196%. Either is invisible at pendant scale. Use 4 segments per full circle or ellipse.
- The Glyphs "55–56% for circles" figure and κ ≈ 0.552 are the same fact: for a 90° arc, the handles' intersection is at the corner of the bounding square, at distance r, so handle = 0.552 r ≈ 55%.
- Recipe for code-generated outlines:
  1. List the extreme points of each blob (top, bottom, left-most, right-most in the shape's own rotated frame) as anchors. A limb or body mass usually needs 4–6 anchors, a whole simple character outline about 20–40.
  2. At smooth anchors, make the in and out handles collinear (same direction, opposite sign). Lengths can differ, but keep each segment's two handles balanced at about 0.5–0.6 × the distance to the handle intersection. That is roughly 1/3 of the chord for gentle arcs.
  3. Use true corners (non-collinear handles) only where the design wants a point: wing tips, arrow tip, heart point, ear tips. A deliberate sharp corner next to a full curve is the vector form of "straight against curve".
  4. For an S-curve (e.g. the back of a wing, the line of action), put the inflection *on* an anchor between two C segments rather than inside one segment.
  5. For a tapered element (bow string ends, hair curl, arrow fletching), make two outlines that converge to a point or a small round cap. Vary the width monotonically, never with bumps.
  6. Lumps and kinks come from handles that are too long (bulges past the triangle), handles of very unequal length on one segment (flat spot then bulge), or collinear handles breaking (a visible kink). Check each segment against the triangle rule programmatically.
- When sampling Béziers into polygons for OpenSCAD, sample by arc-length or curvature, not uniform t. Uniform t over-samples flat parts and facets tight curves; the 3d-print-design skill already documents visible facet artifacts from coarse sampling.

### Gaps
- The full text of Pomax's "Circular arcs and cubic Béziers" and "Curve offsetting" sections wasn't retrieved (page too long; the fetch truncated). Offset-curve guidance (offsetting a Bézier is not a Bézier; approximate with subdivision) is therefore unsourced here.
- Bartosz Ciechanowski's Bézier article wasn't fetched.
- No Adobe primary documentation states the 1/3 rule; it is teaching folklore, consistent with the Glyphs percentages.

---

## 5. Common amateur mistakes in cartoon character silhouettes and how to fix them

### Takeaway
The recurring failures are: symmetric, frontal "twinned" poses; limbs pressed against the body (blob silhouette); tangents; uniform curves everywhere (no straights, no size variety); straight, locked or backwards-bending legs; and too much small internal detail that disappears at actual size. Each has a mechanical fix.

### Cited Findings
- **Twinning/symmetry.** Fix: offset one limb instead of mirroring, give "a different angle for every joint", and tilt shoulders, hips and head. — [Animator Island: Twinning 102: Change It Up](https://www.animatorisland.com/?p=2053); [Animator Island: Perfect Posing 2](https://www.animatorisland.com/perfect-posing-2-appealing-and-readable/); [SIGGRAPH: Appeal](https://education.siggraph.org/static/HyperGraph/animation/character_animation/principles/appeal.htm)
- **Blob silhouette (limbs inside the outline).** Fix: move limbs out of crowded areas and open negative space between limbs and torso, then re-run the black-fill test. — [Animator Island: Perfect Posing 2](https://www.animatorisland.com/perfect-posing-2-appealing-and-readable/); [Binus DKV: The Power of Silhouette](https://binus.ac.id/bandung/dkv/2025/11/04/the-power-of-silhouette-designing-readable-characters-in-motion/)
- **Tangents.** Fix: overlap decisively or separate clearly. — [Gurney Journey: Tangencies in Real Life](https://gurneyjourney.blogspot.com/2010/11/tangencies-in-real-life.html?m=1)
- **Uniform curves / no contrast.** Fix: set a straight against a curve, more strongly in stylized work. — [Animator Island: Perfect Posing 2](https://www.animatorisland.com/perfect-posing-2-appealing-and-readable/)
- **Straight or wrong-bending legs.** Fix: offset the lower leg from the upper and treat the knee as a one-way hinge. — [Artists Network: Common Mistakes of Drawing the Leg](https://www.artistsnetwork.com/art-mediums/drawing/common-mistakes-of-drawing-the-leg)
- **Too much fine detail at small size.** Fix: simplify; lines no thinner than 1 pt (print); no hairline borders; no tiny tabs or protrusions on cut parts. — [MOO: Sticker design mistakes](https://www.moo.com/blog/uk/inspiration/sticker-design-mistakes); [Sticker Mule: artwork requirements](https://stickermule.com/support/what-are-your-artwork-requirements-for-stickers-and-labels); [Atomm: How to design stickers](https://www.atomm.com/cs/blog/2645-how-to-design-stickers)
- **Too simple or too complex.** Fix: balance; neither so simple it bores nor so complex it can't be followed. — [SIGGRAPH: Appeal](https://education.siggraph.org/static/HyperGraph/animation/character_animation/principles/appeal.htm)
- **Body-heavy chibi looks wrong.** Fix: keep the head the focal point; the safe zone is "balanced" proportions. — [Clip Studio Tips: General guide to drawing chibis](https://tips.clip-studio.com/en-us/articles/4863)

### Inferences
- Pre-export checklist a script can run on a character outline (each item maps to a cited rule above):
  1. **Mirror test.** Reflect the outline about its vertical axis and compute IoU with the original. Very high IoU (e.g. >0.9) means it is twinned; tilt or offset something. The threshold is a suggestion, not sourced.
  2. **Joint-angle test.** No two skeleton segments share an angle, or a mirrored angle, within about 5°.
  3. **Tangent test.** Between separately-drawn parts, the minimum distance is either 0 with real overlap (more than a few line widths) or at least the gap minimum. Flag anything in between, i.e. "kissing".
  4. **Negative-space test.** Each limb, wing and prop should create its own concavity or hole in the union outline. If removing a part barely changes the union outline, that part isn't reading.
  5. **Thin-feature test.** Erode the shape by half the minimum feature width, then dilate back (morphological opening). Anything that vanishes is too thin to cut, print or peel.
  6. **Detail-at-size test.** Render at actual product size (e.g. a 30 mm pendant at 1:1 on screen, or downsample to roughly thumbnail pixel scale) and check that face, bow and wings are still identifiable.
  7. **Knee-direction test.** For each leg, the knee vertex lies on the front side of the hip–ankle line, the calf bulge is on the back side, and the toe points toward the knee's side.
- For a Cupid specifically, the most likely amateur failures are: (a) a symmetric front view with two identical wings, (b) the bow drawn overlapping the torso so its arc disappears in the black fill, (c) the arrow line kissing the wing edge, (d) straight stick legs, and (e) curls of hair or feathers too fine to survive cutting. Fix (a)–(c) with a 3/4 or profile pose and the bow held out from the body, (d) with tucked and trailing bent legs, and (e) by merging feathers into 3–5 large scalloped lobes per wing.

### Gaps
- No primary source (e.g. Stephen Silver, Proko or Ctrl+Paint lessons) listing amateur silhouette mistakes with numbers was retrieved. The checklist thresholds above are proposed, not sourced.
