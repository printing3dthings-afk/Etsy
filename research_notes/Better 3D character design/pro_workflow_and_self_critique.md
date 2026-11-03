# Professional 3D character / toy / figurine workflow and self-critique

Researched 2026-11-03. Scope: how character artists, designer-toy studios and figurine sculptors work from concept to finished model, how they critique their own work, the usual amateur mistakes, and how they handle "circled" feedback from a client. Written for a small shop that designs printable figurines, ornaments and charms in OpenSCAD/Blender and prints on a Bambu P1S.

Source quality: the best primary sources found were Kidrobot's own production post, an 80 Level interview with a working character artist (Patrick Yeung), James Gurney's own blog, a character-design teaching blog (Jennifer G. Oliver), a peer-reviewed cuteness study (Glocker et al. 2009), and Polycount critique threads (practitioner opinion). A lot of the search results were tutorial or SEO material. Where I relied on those, I say so. Several sources I wanted (Marco Bucci, Proko critique methods, Funko's internal process, Muddy Colors' revision-notes article, which returned 403) could not be retrieved. They are listed under Gaps.

---

## 1. Pro workflow: reference, thumbnails, blockout, form hierarchy, silhouette checks, refinement order, iterations, studio critique

### Takeaway
Every practitioner source gives the same order: define the concept, then draw turnarounds (front, side, back, top), then block out big primary shapes and stay there "as long as possible", then add secondary forms, then tertiary detail last. The silhouette is checked at every stage. Studios iterate in written, angle-by-angle feedback rounds, and each round should need about half the notes of the one before.

### Cited Findings
- **Kidrobot's pipeline from artwork to vinyl toy.**
  - The senior graphic designer makes rough turnarounds ("back, side, top, and bottom views") to check contrast and to settle missing details, such as whether the eyes are raised or engraved and which accessories are removable.
  - The production manager then adds the questions the factory will need answered before sculpting.
  - The factory sculpts in clay and sends photos of each angle.
  - Feedback is written by one person, reviewed by the designer and the artist, then sent back. The cycle repeats until the sculpt is right. Quote: "Each round, the number of comments you have for the factory is half as many as the round before."
  - The team does not hold a physical object until late. When they do, scale can surprise them, especially on tiny parts like zipper pulls.
  - For a mini series they keep scale and features consistent across figures so that every figure in the series is equally strong.
  - [Kidrobot: From Paper to Plastic – How a Toy Gets Made](https://blog.kidrobot.com/how-a-toy-gets-made/)
- **Patrick Yeung's blockout method** (character artist, Lightstorm Entertainment / Avatar sequels; trained at Gnomon).
  - He builds the blockout from a subdivided cube using only the Move brush plus duplicates of that cube ("use a subdivided cube as a building block").
  - He stays in blockout "as long as possible" to keep the focus on main shapes, because "primary form affects how light reflects off of surfaces."
  - He says this approach "promotes strong silhouettes."
  - His summary rule is "Think big": silhouette and big shapes before detail.
  - [80 Level: Stylized Character Production Tips and Tricks](https://80.lv/articles/stylized-character-production-tips-and-tricks)
- **Form hierarchy in practice.** In an 80 Level breakdown, the artist moved to tertiary forms (wrinkles, age marks, imperfections) only "with the primary shapes established." — [80 Level: Sculpting a Dwarf King](https://80.lv/articles/breakdown-sculpting-a-dwarf-king-using-zbrush-and-substance-3d-painter)
- **Roughen the primaries, then refine at lower subdivision.** Bailey Wheatland advises that after laying down primary forms "you should give them a little bit more character and randomize some of those neat straight lines." Once the flesh was added, he went back down a subdivision level or two to refine secondary and tertiary forms. — [80 Level: Real-time character creation by Bailey Wheatland](https://80.lv/articles/005cg-004adk-001agt-real-time-character-creation-by-bailey-wheatland)
- **Definitions** (via a search snippet attributed to a ZBrush character-creation book): primary = largest basic shapes; secondary = muscle forms and folds of flesh; tertiary = pores, fine wrinkles, scale detail. Primary and secondary forms matter most for a sculpture to work. — [ZBrush Character Creation (O'Reilly/Safari), "Form and Details"](https://www.safaribooksonline.com/library/view/zbrush-character-creation/9781118037065/c04-anchor-1.xhtml) (snippet only; not fetched in full)
- **Designer-toy production stages** (FormX guide): sketch ideas, then detailed front/side/back/top drawings, then armature and block out major forms, then refine, then add details. It also advises to "step back often and photograph the sculpt to spot proportion problems," and to plan mold parting lines during design refinement. — [FormX: Designer Toys Complete Process](https://www.formx.eu/posts/designer-toys-complete-process/) (vendor guide)
- **Silhouette first in toy sketching.** A toy and character designer advises picking favourites from initial sketches and paying attention to their silhouettes. A sculpting workshop describes blocking out main shapes and capturing the core silhouette before refining in second and third passes. — [Morgan Goble, "designing a character from start"](https://morgangoble.substack.com/p/designing-a-character-from-start) (search snippet)
- **Reference and turnarounds.**
  - A turnaround is the set of views (front, side, back) that underpins an accurate digital model. [Unity Learn: Turnaround model reference sheet](https://learn.unity.com/tutorial/turnaround-model-reference-sheet)
  - In Blender, use orthographic view (Numpad 5) to align front and side references. PureRef's strength is a free-floating, always-on-top reference board, but it cannot place references in 3D at scale. Add-ons such as "Reference Board" fill that gap. [Superhive: Reference Board add-on](https://superhivemarket.com/products/reference-board) (vendor page; treat its claims with caution)

### Inferences
**A concept-to-finished-model workflow for this shop**, synthesised from the sources above and adapted to OpenSCAD/Blender and FDM:

1. **Concept and brief, one sentence.** Who is the character, what is the one emotion it should give off, and what is it (figurine, ornament or charm)? Pick a size class now, because scale decisions surprise people late (Kidrobot).
2. **Reference board.** Collect best-seller photos, real-animal or real-object reference, and the chosen style's proportion examples into one PureRef board. Keep it open beside the modelling window the whole time.
3. **Thumbnails / silhouettes.** Make 4–5 tiny black-fill silhouettes of genuinely different forms (this matches the shop's existing "4–5 formal approaches" rule). Choose by silhouette alone.
4. **Turnaround.** Draw or block front, side, back and top views. Settle raised vs engraved features, separate parts and colour zones at this stage (Kidrobot's turnaround questions).
5. **Blockout of primary forms only.** Use spheres, capsules and hulls. No detail. Check the silhouette from front, side, 3/4 and top. Stay here until it reads (Yeung).
6. **Secondary forms.** Add ears, limbs, belly, big folds and the main face planes. Re-check the silhouette and the proportions against the reference.
7. **Tertiary detail, last and sparingly.** On FDM this means only detail that survives the nozzle (see the minimum-detail findings in section 2).
8. **Review rounds.** Render the same fixed set of angles each round and write numbered notes. Expect the notes to halve each round; if they don't, the design direction is the problem, not the detail (Kidrobot's heuristic).
9. **Series check.** If the piece belongs to a set, line it up with its siblings at the same scale.

**Inference:** "Stay in blockout as long as possible" fits OpenSCAD's strengths well. Primitives and hulls *are* a blockout. The temptation to avoid is adding surface pattern to a weak primary form.

### Gaps
- No source gave a typical number of iterations in hours or rounds, beyond Kidrobot's "half as many comments each round" heuristic.
- I could not retrieve Yansculpts, Danny Mac or Michael Pavlovich material in this pass. No practitioner account of a PureRef-specific workflow was found, only SEO and vendor pages.

---

## 2. Toy and designer-toy practice: simplification, stylisation, proportion, design for manufacturing, appeal

### Takeaway
Designer toys get their appeal from a big head, a simplified body and an expressive face, which matches the peer-reviewed "baby schema" findings: round face, high forehead, big eyes, small nose and mouth. Manufacturing shapes the design from the turnaround stage on: part splits, demoldability, separate vs integrated accessories, and details too small to survive at real scale.

### Cited Findings
- **Baby schema, experimentally tested.** Glocker et al. (2009) manipulated infant photos. "High" baby-schema faces (round face, high forehead, big eyes, small nose, small mouth) were rated cuter and drew stronger caretaking motivation than unmanipulated or "low" faces. This builds on Lorenz's 1943 proposal that a large head, round face and big eyes trigger caretaking. — [Glocker et al., "Baby Schema in Infant Faces Induces Cuteness Perception and Motivation for Caretaking in Adults" (PDF)](https://www.cceb.upenn.edu/csa/assets/user-content/documents/BabySchemainInfantFacesInducesCutenessPerceptionandMotivationforCaretakinginAdults.pdf)
- **Big head, little body, from a designer.** The designer MAD said his MAD*L figure's big-head, little-body proportions were "based off a kid," and the overall design was chosen mainly for maximum printing surface. — [Vinyl Pulse interview (search snippet)](https://www.vinylpulse.com/?p=77763)
- **Simple base forms that carry many characters.** Qee figures share one body with different head sculpts, and Toy2R's model is artists customising basic shapes. — [Wikipedia: Toy2R](https://www.wikipedia.com/wiki/Toy2R); [Wikipedia: Art toy](https://en.wikipedia.org/wiki/Art_toy)
- **Personality over form.** Successful vinyl designs "have personality and emotion attached to them," using shape, colour, accessories and expression to stand out. — [Creative Bloq: Vinyl toy industry needs you](https://www.creativebloq.com/character-design/vinyl-toy-industry-needs-you-12108730)
- **Simple-looking is not simple.** The LEGO BrickHeadz designer said BrickHeadz seem simple "until you start designing hair." — [Brickset interview with Austin Carlson](https://brickset.com/article/27035/interview-with-brickheadz-designer-austin-carlson)
- **Chibi proportions** (tutorial-level sources, which disagree on exact numbers):
  - 1–4 heads tall, with 2, 2.5 and 3 heads the common ratios.
  - "The face is the most important thing of the whole Kawaii feature."
  - Remove any detail that doesn't add to the kawaii factor.
  - Keep 3D volume, since depth reads as cuter.
  - [Clip Studio: How to draw chibi body ratio](https://tips.clip-studio.com/es-es/articles/4806?org=1); [Clip Studio: Easy Steps to Creating Chibi Characters](https://clipstudio.net/how-to-draw/archives/155423); [Clip Studio: Chibi, Simplify and Adorable](https://tips.clip-studio.com/zh-tw/articles/4973?org=1)
- **Manufacturing constrains the sculpt.**
  - Molds split the toy into pieces, so a design that can't be demolded may need factory changes.
  - Mini series are injection-moulded in two-part metal molds. Dunnys are rotocast and pulled out warm through the neck hole.
  - A 3D problem can force a design change: Kidrobot's Junko blood bag needed a stand, and its "blood" became transparent red plastic instead of paint.
  - [Kidrobot](https://blog.kidrobot.com/how-a-toy-gets-made/)
- **Resin/handmade toy DFM.** Two-part molds are most common, and multi-part molds suit heavy undercuts. Plan parting lines during refinement and decide early which parts are separate. Use hemispherical registration keys and plan vents for air traps. — [FormX](https://www.formx.eu/posts/designer-toys-complete-process/)
- **3D-printed figurine splitting and detail** (vendor and freelancer sources; numbers vary by machine):
  - Split along natural seams.
  - Mortise-and-tenon joints suit static figurines.
  - Printed pegs can snap; dowels are an alternative.
  - Plug-and-socket clearance is about 0.15–0.2 mm.
  - Chamfered pegs align more easily.
  - Rough FFF minimums: embossed detail about 0.5 mm, engraved detail about 0.5 mm, walls of at least 1 mm.
  - Orient the part so supports avoid critical surfaces.
  - [JLC3DP: How to split large 3D prints](https://jlc3dp.com/blog/how-to-split-large-3d-prints-for-better-quality-and-asembly); [Professional3DServices: Tips to design 3D print miniatures](https://professional3dservices.com/blog/3d-print-miniature-tips.html); [Additive-X: Designing parts for 3D printing](https://www.additive-x.com/blog/designing-parts-for-3d-printing/)
  - Note: the shop's own measured standard (`openscad_models/detail_calibration/DETAIL_STANDARD.md`) and the 1.2 mm wall rule in CLAUDE.md should override these generic numbers.

### Inferences
- **Appeal recipe for kawaii figurines, ornaments and charms:**
  - Head about 40–50% of total height (2–2.5 heads tall).
  - Face low on the head, so the forehead is high.
  - Eyes large and widely spaced.
  - Nose and mouth tiny.
  - Every contour rounded.
  - Limbs short, thick nubs.
  - Each choice is one of Glocker's tested baby-schema features or a toy-industry convention.
- **Thick limbs and big shapes are also what FDM prints well.** Short, chunky limbs are both cuter and less fragile, which suits `tools/fragility.py`. Thin "noodle" limbs fail both the appeal test and the strength test.
- **Simplify to what reads at real size.** A charm about 30–40 mm tall cannot carry the detail of a 100 mm figurine. Kidrobot's scale-surprise lesson argues for printing or rendering at true size early.
- **Series design.** Use one shared body and vary the heads, ears and accessories (the Qee/Toy2R model). This gives a family look across a set and reuses proven geometry.

### Gaps
- No practitioner source on draft angles for vinyl/injection toys was retrieved. Draft matters less for FDM, but the source gap remains.
- No primary Funko or kawaii-collectible studio process post was found. The search snippet about adult judgments of child likeability fading after about 4.5 years had no clearly attributable URL, so I left it out.
- Lorenz's cross-species claim is less settled than the infant-face findings.

---

## 3. Self-critique techniques with concrete how-to

### Takeaway
Practitioners rely on a small set of "fresh eye" tricks that remove familiarity and detail so the big shapes can be judged: flip or invert, shrink (reducing glass, mirror, thumbnail), squint or reduce to two values, step away, photograph it, and ask someone else. For 3D work, the equivalents are a black-fill silhouette from several angles, a tiny-thumbnail view, a mirrored render, a grayscale or flat-lit render, and an overlay against reference.

### Cited Findings
- **James Gurney's six "fresh eye" methods, in his words:**
  1. "Turn it upside down and look at it (or work on it) inverted." He spends about a quarter of his painting time working this way.
  2. "Step back from it, squinting and tilting your head."
  3. "Use a reducing glass," which shrinks the whole composition.
  4. Photograph it and look at it on the LCD, rotated 180°, or converted to two values in Photoshop.
  5. "Set up an adjustable mirror on the wall behind and above your shoulder," so you see it smaller and reversed.
  6. "Ask a trusted friend, family member, or visitor to take a look at it." What they notice first often differs from what he intended.
  - [Gurney Journey: Getting a Fresh Eye](https://gurneyjourney.blogspot.com/2008/08/getting-fresh-eye.html)
- **A cheap convex mirror.** Gurney recommends a few-dollar stick-on convex mirror from an auto-parts store for a quick fresh look. — [Gurney Journey: Rear-view tip](https://gurneyjourney.blogspot.com/2009/06/rear-view-tip.html)
- **Mirror check, with a caution.** Leonardo's advice to check work often in a flat mirror is cited as giving "a fresh pair of eyes without needing another person." — [Will Kemp Art School: 7 tools to check your own work](https://willkempartschool.com/7-essential-tools-every-artist-can-use-to-check-their-own-work-a-guide-for-painters/). If you flip your work, flip the reference too. — [Painter's Keys: Smoke, mirrors and viewfinders](https://painterskeys.com/?p=6898)
- **Step away overnight.** Looking at work the next morning often exposes problems that were invisible the day before. — [WetCanvas thread](https://www.wetcanvas.com/forums/topic/why-does-setting-work-aside-have-such-an-impact-2) (forum opinion)
- **Photograph it.** "Step back often and photograph the sculpt to spot proportion problems." — [FormX](https://www.formx.eu/posts/designer-toys-complete-process/)
- **Black-fill silhouette.** "If your character doesn't read in pure black, the design needs work!" A related check is whether too many lines are touching. — [Cursa: Readable poses, silhouettes and line of action](https://cursa.app/en/page/character-animation-starter-kit-readable-poses-silhouettes-and-line-of-action) (tutorial site)
- **Polycount critique norms (practitioner opinion):**
  - "Say it, or don't": any form you include needs a strong presence in the silhouette or rhythm.
  - Remove geometry that doesn't contribute to silhouette.
  - A "smooth" silhouette reads as weak, so push and tilt it.
  - Present work rendered large, on a background that isn't mid-grey or black, so the silhouette can be judged.
  - [Polycount comment 2790513](https://polycount.com/discussion/comment/2790513); [Polycount comment 2581167](https://polycount.com/discussion/comment/2581167); [Polycount comment 654050](https://polycount.com/discussion/comment/654050)
- **Zoom out and check the skeleton.** When something looks wrong, check skeleton proportions and zoom out, because "it's not so much about the detail ... as it is about the silhouette." — [Creative Bloq: 5 tips for sculpting in double-quick time](https://www.creativebloq.com/how-to/5-tips-for-sculpting-in-double-quick-time)
- **Keep reference on screen.** Sculpting from imagination is flagged as a beginner error. — [VCAD: How to sculpt in ZBrush](https://www.vcad.ca/about/spotlights/how-to-sculpt-in-zbrush-a-beginner-s-guide-for-future-3d-animators/)

### Inferences
**A self-critique checklist for a printable figurine, ornament or charm.** Each item is a 3D adaptation of a cited 2D technique; run it at blockout, after secondary forms, and before final.

1. **Silhouette (black fill).** Render front, side, back, 3/4 and top as solid black on white. Can you name the character from each one? Is there negative space between the limbs and the body? Are there any tangents where two contours just touch? (Cursa, Polycount)
2. **Thumbnail test.** Downscale the hero render to about 150–200 px, roughly the size of an Etsy search thumbnail. Does it still read and still look cute? (Gurney's reducing glass)
3. **Squint / two-value test.** Make a flat-lit or grayscale render posterised to 2–3 values. Do the big masses still separate: head from body, face features from face? (Gurney's two-value photo)
4. **Flip test.** Mirror the render horizontally, or view it upside down. Asymmetries and leaning that you had stopped noticing jump out. Flip the reference too. (Gurney; Painter's Keys)
5. **Turntable.** Rotate through 360° in steps of 45° or less. Look for an angle that is lumpy, flat or confusing. A figurine is seen from every side; a listing photo usually shows the 3/4 view. (Kidrobot's every-angle photos)
6. **Overlay against reference.** Put the orthographic render at 50% opacity over the turnaround or a best-seller photo scaled to the same height. Measure head-to-body ratio, eye size and eye spacing, not "feel". (Inference from Kidrobot turnarounds plus the proportion advice)
7. **"Say it or don't".** For each form, ask whether it earns a presence in the silhouette. If not, enlarge it or delete it. (Polycount)
8. **Baby-schema scorecard.** Is the face round? Is the forehead high? Are the eyes big? Are the nose and mouth small? Are the limbs short and chunky? (Glocker)
9. **Real-size check.** View or print at true size. Do the tertiary details survive at nozzle scale? (Kidrobot's scale surprise; shop DETAIL_STANDARD)
10. **Fresh eyes.** Leave it overnight, then look at the thumbnail first thing. If you can, show it to someone and ask "what do you notice first?" without telling them what to look for. (Gurney, WetCanvas)
11. **Best-seller lineup.** Put your thumbnail in a grid beside 6–8 top-selling competitor thumbnails. Does it stand out or disappear? (Inference from Creative Bloq's "stand out" and Kidrobot's "equally strong" series check)

### Gaps
- No Marco Bucci or Proko source specifically documenting the squint and flip tests was retrievable. Bucci appears in Proko and SVS critique listings, but the excerpts did not describe his method.
- No source quantified how effective any of these tests are. Their status is practitioner consensus, not measured fact.

---

## 4. Most common amateur mistakes in 3D character / figurine modelling, and the fix for each

### Takeaway
The dominant beginner failure is detail before form: subdividing or adding detail before the primary shapes and silhouette are right, which produces lumpy, uneven surfaces. Next come stiff, symmetrical ("twinned") poses, weak or tangent-filled silhouettes, and stylisation that drifts into plain disproportion.

### Cited Findings
- **Subdividing too early leads to lumpy forms.** "A common mistake among new users is to subdivide too soon ... without having adequately blocked out the basic forms first. This results in models that tend to be lumpy and uneven." The biggest problem new sculptors have is "they jump to doing detail at high subdivisions much too quickly." Fix: drop to the lowest level and make big changes there. — [Polycount comment 1878957](https://polycount.com/discussion/comment/1878957/); [Polycount comment 1473648](https://polycount.com/discussion/comment/1473648) (forum consensus via search snippets)
- **Lumpiness, a second fix.** Reinforce angular forms as you go and use trim or planar tools to sharpen them. — [ZBrushCentral: model comes out lumpy](https://www.zbrushcentral.com/t/model-comes-out-lumpy/308724)
- **Wrong underlying proportion.** If the skull is the wrong size, "no amount of pores or wrinkles will save the design." — [VCAD](https://www.vcad.ca/about/spotlights/how-to-sculpt-in-zbrush-a-beginner-s-guide-for-future-3d-animators/)
- **Bypassing basic shapes / sculpting on high-poly meshes too early** is listed first among Marlon R. Nunez's "7 mistakes in ZBrush" (the fixes are in his video). — [80 Level: Do you make these 7 mistakes in ZBrush](https://80.lv/articles/do-you-make-these-7-mistakes-in-zbrush)
- **Twinning and parallels make a pose stiff** (Jennifer G. Oliver, after Thomas & Johnston's *The Illusion of Life*).
  - Mirrored left and right sides produce "stiff, lifeless poses that seem more wooden and flat than Egyptian hieroglyphics."
  - Fix: "Variance within an otherwise symmetrical design is what creates a natural and visually engaging figure."
  - Use head and body tilts, vary the limbs and fingers, avoid limbs running parallel, and present in 3/4 view, which "doesn't offer many opportunities for twinning."
  - Twinning is fine deliberately for robots or insects.
  - Symmetry is acceptable on schematic model sheets.
  - [Character and Creature Design Notes: How to kill a great character design](https://characterdesignnotes.blogspot.com/2010/11/how-to-kill-great-character-design-part.html)
- **Straights vs curves.** All-curves (or all-straights) designs lack rhythm. Fix: set straights (stable, solid parts) against curves (fleshy parts), and cut strong verticals with diagonals from hair, props or drapery. — [Character Design Notes](https://characterdesignnotes.blogspot.com/2010/11/how-to-kill-great-character-design-part.html); [Animated Spirit: Straights & Curves](https://animatedspirit.com/straights-curves)
- **Tangents.** Edges that touch or nearly touch flatten depth and muddy the silhouette, for example a wrist lining up exactly with the hip contour. Fix: overlap the forms clearly or separate them clearly. — [Cursa](https://cursa.app/en/page/character-animation-starter-kit-readable-poses-silhouettes-and-line-of-action) (tutorial site)
- **Stylised turning into disproportioned.** In one critique, a too-small head and too-long legs and hips drew the comment "Its one thing being stylized but another being disproportioned." — [Polycount comment 2790620](https://polycount.com/discussion/comment/2790620)
- **Weak, smooth silhouette.** "push that silhouette, tilt it a bit more maybe, its looking a bit stiff right now." — [Polycount comment 2581167](https://polycount.com/discussion/comment/2581167)
- **Too much detail.** For chibi and kawaii: remove any detail that doesn't add to the kawaii factor. — [Clip Studio: Chibi, Simplify and Adorable](https://tips.clip-studio.com/zh-tw/articles/4973?org=1)

### Inferences
Mistake-to-fix table for this shop. Each fix applies the cited principle, translated for OpenSCAD/Blender and FDM:

| Mistake | Symptom in a render | Fix |
|---|---|---|
| Lumpy forms | Bumpy contours, wobbly highlights in a turntable | Go back to primitives and hulls. Fewer, larger, smoother masses. Use `smooth_path` or higher `$fn` only after the masses are right |
| Too much detail | Thumbnail looks noisy; detail lost at nozzle scale | Delete everything that fails the "say it or don't" and real-size tests. Keep only features above DETAIL_STANDARD |
| Poor silhouette | Black fill unrecognisable; limbs merged into body | Open up negative space, push a characteristic feature (ears, tail), and avoid tangents |
| Stiff, flat front-facing pose | Everything symmetric about the YZ plane | Tilt the head 5–15°, shift the weight, vary arm and ear angles, and design for the 3/4 hero view |
| Twinning / parallels | Both arms and both ears identical | Vary angle, length or position on one side only |
| Noodle limbs | Thin, uniform-diameter tubes | Taper limbs and make them short and chunky (also fixes `fragility.py` flags) |
| Wrong proportions | Head-to-body ratio drifts from the chosen style | Fix a numeric ratio up front (e.g. 2–2.5 heads) as a named parameter and overlay against reference |
| All curves, no structure | Reads as a blob | Add a few straight or flat planes (base, a flat belly plane, a crisp brow) against the curves |
| Tangents | Two contours kiss in the silhouette | Overlap decisively or separate by at least a clear gap |

### Gaps
- No source specific to FDM figurines catalogued mistakes. The list comes from digital sculpting and animation character-design teaching, so FDM-specific failures (e.g. detail lost to layer lines) rest on the shop's own measured standards rather than on external sources.

---

## 5. Iterating with a client/owner who gives feedback by circling problems

### Takeaway
Professionals treat a circled note as a symptom. They identify the underlying principle, confirm it if it is unclear, make a targeted change to the isolated area, and show before and after at the same angle and scale. Each round's notes are tracked so that every earlier note is visibly closed, and a healthy design converges as the notes roughly halve each round.

### Cited Findings
- **Look past the requested fix to the issue.** "Try to focus on the issues they have," for example "this scene isn't as exciting as it should be" rather than "this should be faster." A non-expert reviewer is still an audience member. — [CGMA: How to read minds and decode artistic feedback](https://cgmasteracademy.com/blog/how-to-read-minds-and-decode-artistic-feedback.html)
- **Ask, don't nod along.** "Feedback is not a one-way street." Technical Director Mathias Royrvik said he wished he had "asked more dumb questions." — [CGMA](https://cgmasteracademy.com/blog/how-to-read-minds-and-decode-artistic-feedback.html)
- **Show, don't argue.** Build what the client asked for so they can see the result, and offer your own alternative beside it: "Try sketching (or modeling ...) it for them the way they ask." Acknowledge every note, even the ones you don't apply. — [CGMA](https://cgmasteracademy.com/blog/how-to-read-minds-and-decode-artistic-feedback.html)
- **Agree the process.** Settle review frequency, who gives final approval, and whether notes are creative or technical. Limit the number of early reviewers to avoid contradictions. — [CGMA](https://cgmasteracademy.com/blog/how-to-read-minds-and-decode-artistic-feedback.html)
- **Track every round.** Submit, then approve or get feedback, then revise and resubmit, until approved. "Feedback for each version needs to be documented, organized, and tracked" so the director can confirm earlier notes landed. — [Game Developer: 2D game art feedbacking and management](https://gamedeveloper.com/art/2d-game-art-work-feedbacking-and-management-tool) (search snippet)
- **Isolate and redline.** If anatomy or posing is off, isolate the problem area and suggest a redline fix rather than repainting the whole piece. Paintovers should explain the principle, not just demand a copy. Riot encourages artists to paintover each other's work as a way to communicate. — search summary covering [Riot via ImagineFX/PressReader](https://www.pressreader.com/australia/imagine-fx/20151231/283661118760483) and [Blender Durian: paint-over revision](https://durian.blender.org/concept-art/paint-over-revision) (snippets; not fetched in full)
- **Vague notes come from knowing something is wrong without pinpointing it.** Muddy Colors' article on translating frustrating revision notes says vague notes most often happen when the AD knows something is wrong but can't name it, and the remedy is to translate the note into specific, actionable changes. — [Muddy Colors: Three frustrating revision notes](https://www.muddycolors.com/2015/04/three-frustrating-revision-notes-and-how-to-translate-them-into-something-actionable) (403 on fetch; snippet only)
- **Angle-by-angle rounds that converge.** Clay photos of each angle go back with written notes, and the notes halve each round. — [Kidrobot](https://blog.kidrobot.com/how-a-toy-gets-made/)

### Inferences
**A protocol for Scott's circled feedback:**

1. **Restate each circle as a numbered note** in one line: "1. Ears: read as too small vs head." Describe the problem, not the solution, and ask if it is ambiguous (CGMA).
2. **Name the principle behind it.** For example: silhouette, proportion, tangent, lumpiness, symmetry or stiffness, or detail lost at scale. This keeps the fix from being a blind nudge (paintover "explain the principle").
3. **Measure before changing.** Example: ear height is 18% of head height, and the reference best-seller is about 30%. Overlay the reference at the same scale.
4. **Change one thing per note,** isolated to the circled area (redline principle). For a direction you disagree with, build the requested version *and* an alternative side by side (CGMA).
5. **Show before and after** at the identical camera, angle, scale and lighting as the circled image. Include the black-fill silhouette and thumbnail versions if the note was about readability.
6. **Close the loop** with a table of note number, the change made, the before/after image, and a status of open or closed, so earlier notes are visibly resolved (Game Developer tracking).
7. **Watch convergence.** If round N+1 has about as many notes as round N, step back to blockout and revisit the form rather than polishing (Kidrobot heuristic, inverted).

### Gaps
- The Muddy Colors article's three specific notes could not be retrieved (403).
- No source specifically described resolving *circled photo* feedback on 3D figures. The protocol above combines the 2D paintover/redline practice with Kidrobot's angle-photo rounds.
