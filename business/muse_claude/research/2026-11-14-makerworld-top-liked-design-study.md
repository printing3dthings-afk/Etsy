# MakerWorld Top-Liked Design Study — November 2026

## Summary
Read 2026-11-14 (EST). Like counts in the mission are a snapshot; live pages on 2026-11-14 already show slightly higher numbers for several models (e.g. AMS Flipper collections 45.8k, Build Plate Cleaner 37,311 on its page counter, Mini Bag Clip 32,999, Poop Bucket 32,054, Clicker Master ~30.3k in collections). All 20 models were identified. 18 were read on their own MakerWorld page via the web index / page fetch (`index` verification — MakerWorld pages are JS-heavy; text was extracted, cover GIFs/photos described in alt/search text, not interactively sliced in Bambu Studio). Two models — #4 Combo pegboard and #17 Cascade Connect — could **not** be opened at a direct model URL despite repeated search; their MakerWorld existence/counts are verified from MakerWorld homepage/collection listings, and construction detail comes from clearly-labelled secondary sources. **Correction to the mission premise on #20:** the model at the bottom of the Likes list titled “Clicker Master” does **not** use a mechanical keyboard switch — its own page says it is a 100% printed, print-in-place clicker core whose printed spring *mimics* a keyboard switch, with no metal spring/screw. Keyboard-switch clickers are a different, large MakerWorld family (and MakerLab’s Clicker Generator); see §20.

**The one-sentence lesson:** almost none of these win on decoration. They win by (1) removing a daily friction for a huge installed base (Bambu printer or IKEA SKÅDIS owners), (2) a mechanism you can understand in a 3-second GIF, (3) zero or one cheap hardware item, (4) a quantified hook in the title/description (3.6 g / 8 min, <200 g / 5 h, 1.6 h, 96 h “serious upgrade”), and (5) versioning — V1.4, v4.0, Type 02, V2/V3 successors that keep the original URL and its likes.

Reader context applied in Synthesis: P1S, matte PLA, no-supports rules, decorative holiday village buildings + desk accessories.

---

## Findings

### 1. AMS Flipper — better access to your P1S/X1 — Jakob_K_Design (~46.1k mission; 45.8k in collections 2026-11-14)
- **What/problem:** Hinge kit that flips the AMS (4-spool unit) up/back off a P1S/X1C/P2S/X2D so you can open the top glass, clear stuck filament and service the toolhead without lifting the AMS off and parking it beside the printer. Page opens with the designer’s own annoyance: “I got tired of having to remove the AMS every time…”
- **Construction:** Assembled, not print-in-place. Printed AMS brackets + rear brackets + interchangeable angle brackets (default 75° open angle, others swappable) + printed axis/pivot pin, secured with a countersunk screw. All parts fit **one 256×256 mm plate, no supports**. Flipped AMS extends **132 mm** behind the printer — only 34 mm more than the stock external spool holder (a crucial “will it fit against my wall?” number). Rear brackets double as handles to move the printer.
- **Hardware:** **10× countersunk M3×30 mm** + **2× AMS transport screws or BT3×16-AA110** (reused from an AMS Combo transport bracket). Sold as an official Maker’s Supply MakerKit.
- **Materials:** Designer printed **Bambu ABS, scaled 100.5%** for shrinkage (that 3MF included); **PETG alternative; avoid PLA** — heat from the printer can warp it. Directly relevant warning for a matte-PLA-only studio.
- **Time/weight:** **<200 g, just over 5 h**.
- **Ecosystem fit:** Compatibility handled by *variant proliferation, not parametrics*: AMS 2 Pro brackets (separate STL folder), taller rear brackets for LED/vent risers **up to 70 mm, in 4 mm adjustment steps**, a separate side spool holder because the Flipper blocks the stock external spool mount, and a separate H2D/H2S version (complete redesign).
- **Page craft:** Title = product name + benefit + printer models. Lead = personal pain, then a GIF of the flip. Explicit “V1.4” changelog at the top (fitment + AMS 2 Pro). “This is my first model… leave a boost.” Standard licence/commercial via MakerWorld membership pattern in this cohort.
- **Decisive decision:** Making the pivot strong enough for **an AMS with four full 1 kg spools** and stating it — “ultra strong… easily hold an AMS with four full spools” — turns a scary mod (your £/€ AMS dangling) into a safe one.
- Source: https://makerworld.com/en/models/1363398-ams-flipper-better-access-to-your-p1s-x1-p2s?from=recommend — index, read 2026-11-14.

### 2. Dummy 13 — version 1.0! — Lucky 13 Toys / soozafone / Gabriel Rosiak (~39.1k)
- **What/problem:** A free, fully printable **13 cm-class articulated action figure** (“super expressive articulation and infinite customization”) — an artist’s mannequin / desk toy / remix platform anyone can print. Beta Oct 2023 → v1.0 13 Sep 2024 after a year of feedback; page says it won “3D Model of the Year” (per Printables mirror summary).
- **Construction:** Assembled kit, **not** print-in-place. Two-layer architecture: inner **frame** (skeleton with ball joints, swivel shoulder/hip joints) + outer **armor** snapped over it. Delivered three ways: **runners** (model-kit sprues — parts ~24 g, runners add ~9 g ≈ +40%), **pre-plated 2-plate 3MF** (1 frame plate + 1 armor plate), and individual STLs (files marked 2x/4x). No supports; brim as needed. Settings (100%, 0.4 nozzle): 0.2 mm first / **0.15 mm** other layers, 2 perimeters, 20% rectilinear infill (grid rejected — self-crossings knock parts loose), first-layer speed 25%, **elephant-foot compensation 0.15 mm**, Arachne walls, external perimeters first. Pictorial assembly guide + PDF (`dummy-13-v1_0-assembly-guide.pdf`) + video.
- **Engineering detail worth copying:** v1.0 release notes are a tolerance masterclass — press-fits **replaced by snap-fits** at head/neck/crotch/knee/ankle/stand because press-fits are “either too loose or too tight”; shoulder/hip swivels use a **compliant mechanism** to hold tension instead of relying on close tolerances; ball-joint necks flattened slightly for bridging; chest ball socket relieved (cracked at large scales); abdomen vs waist pieces made non-interchangeable (poka-yoke).
- **Hardware:** **None.**
- **Materials:** Armor = any (PLA/PETG/ASA tested). Frame = **ABS/ASA best, PETG usable, PLA explicitly not recommended** for three stated reasons: stiff (hard snap assembly), brittle (breaks under that force), creeps (joints loosen).
- **Time/weight:** Parts ~24 g at 100% (page does not state a single headline print time in the extracted text — **not verified**).
- **Ecosystem fit:** Scale-invariant design (community prints at 150–1150%; 1150% = 1.57 m / ~12 kg, secondary) + “first-party” bonus packs under the same licence: accessories starter pack, feminine torso, extra hand poses, display stand. CAD (Fusion 360 + STEP) sold via Printables Club/Store.
- **Page craft / licence:** **CC BY 4.0 — you may sell prints, no membership needed, attribution (Title/Author/Source/Licence) mandatory**, explained at length with an example. TL;DR at the top (“Yes, you can sell it”). Designer now directs support to Printables / lucky13toys.com and says he does not regularly check MakerWorld comments.
- **Decisive decision:** The permissive CC-BY licence + remixable frame/armor split. Dummy 13 is not a model, it is a *platform* — thousands of armor/weapon/character remixes all advertise the original.
- Source: https://makerworld.com/en/models/638587-dummy-13-version-1-0?from=search — index, read 2026-11-14.

### 3. Sturdy Modular Filament Spool Rack Fully Printable — Antiphrasis (~39.1k; collections 38.2k)
- **What/problem:** Floor/desk filament storage for “small or tight places” / next-to-printer working spools, without buying dowels, rods or a rack.
- **Construction:** Modular assembled rack. Side frames + **fully printed hollow rods** the spools rest on — hollowed “to make them extra strong” (tube > solid bar in bending per gram). Rod lengths for **2, 3 or 4 spools**. Page headline claim, verbatim in spirit: **“No glue, mounts, screws or other non-printed parts required!”** and it “doesn’t need screws or glue to be stable.” Tested loaded with (almost) full spools. Exact plate count / print time / total weight **not stated in extracted page text — not verified**.
- **Hardware:** **Explicitly none.**
- **Materials:** **PLA is sufficient** (load-tested); PETG “even stronger” optional.
- **Ecosystem fit:** Modularity by rod length and stacking/repeating frames rather than parametrics; designer’s wider family (wall rack, bearing spool holders) cross-linked from his profile.
- **Page craft:** Title is a stack of search adjectives — *Sturdy / Modular / Fully Printable* — each answering an objection to rival racks (wobbly? fixed size? needs hardware?). Description leads with the no-hardware claim, not a story.
- **Decisive decision:** Printing the rods too. Every competing rack that needs a wooden dowel or metal tube loses the “print tonight, use tonight” buyer; this one has zero shopping list.
- Source: https://makerworld.com/en/models/1243778-fully-printable-spool-rack?from=search — index, read 2026-11-14. Note: MakerWorld search also surfaces several similarly-named Antiphrasis racks; this URL is the “Fully printable spool rack” page whose text matches the mission title.

### 4. Modular Pegboard Panel (IKEA compatible) — Combo (~37.8k)
- **⚠ Verification limit:** Repeated MakerWorld homepage/collection listings verify the model, author **Combo**, and counts (**~73.3–73.7k downloads/prints metric, 37.7–37.8k likes**, 2026-11-14), but a direct model URL / full description was **not retrieved** — do not confuse it with the different “Modular Pegboard (IKEA Skadis compatible)” by another author (1900963, 240×240 mm tiles, Ø3×15 mm chipboard screws) or MOSS 3D’s generator. Construction specifics below are therefore **inferred only from the title/listing, and flagged as unverified**.
- **What/problem (from title/listing):** Print your own SKÅDIS-compatible pegboard panel in the size your wall actually is, instead of IKEA’s fixed board sizes, and reuse the entire SKÅDIS hook/bin/shelf accessory ecosystem.
- **Construction / hardware / materials / time:** **Not verified from the model’s own page.** The category norm (verified on neighbouring models) is flat panels printed face-down, joined/screwed to the wall, PLA or PETG; treat any specific number for Combo’s panel as unconfirmed.
- **Ecosystem fit:** The whole value proposition is in the parenthetical: **(IKEA compatible)**. It sells no accessories — it borrows IKEA’s.
- **Page craft:** Shortest title formula in the top 20: *Modular + [category noun] + (incumbent-system compatible)*. The cover (per listings) is the panel wall itself.
- **Decisive decision (judged from positioning):** Compatibility as the product. A pegboard is worthless alone and priceless with 1,000 existing accessories.
- Sources (listings only): https://makerworld.com/en/collections/28899583-pegboard-fs and MakerWorld homepage listings — index, read 2026-11-14.

### 5. AMS Lite Top Mount for A1 & A2L — Bambu Lab (official) (~37.7k)
- **What/problem:** Official component set to mount the open-frame **AMS Lite on top of an A1/A2L** instead of beside it — reclaims the desk footprint the A1’s side-mounted AMS Lite eats.
- **Construction:** Two modules: **(1) Top Mount Bracket** (both A1 & A2L) — front-tilted for balance, upper half **spins left/right** for rear-spool access; **(2) Z-Axis Stiffener (A1 only)** with an **elastic damper** at its base to cancel fore-aft wobble “even… in ludicrous speed with AMS lite fully loaded.” **22 print files** listed; search snippet shows a **2-plate** A1 profile (0.2 mm, 2 walls, 15% infill). Assembled with screws, not print-in-place.
- **Hardware:** Required screw kit sold separately in the Bambu store (**AMS Lite Top Mount Screws Kit**); exact screw list is in the linked Wiki tutorial / parts PDF, **not enumerated in the extracted model text — not verified here**.
- **Materials:** Not specified in extracted text (**not verified**); the design is Bambu’s own tested solution.
- **Ecosystem fit:** Exemplary first-party documentation: per-printer **Bambu Wiki** installation guides (A1 and A2L separately), a YouTube install video, and an **Assembly Guide PDF (parts list & diagram)** attached to the page. Compatibility split is explicit: bracket = both printers, stiffener = A1 only.
- **Page craft:** No boost-begging, no story — a terse, corporate spec page that outsources depth to the Wiki. Trust comes from “tested solution” + the Bambu name.
- **Decisive decision:** The Z-axis stiffener with elastic damping. Top-mounting a loaded AMS Lite on a bed-slinger is a vibration problem first and a bracket problem second; Bambu solved (and named) the vibration.
- Source: https://makerworld.com/en/models/92486-ams-lite-top-mount-for-a1-a2l?from=search — index, read 2026-11-14. Wiki: https://wiki.bambulab.com/en/a1/manual/ams-lite-top-mount-tutorial

### 6. Build Plate Cleaner — Microfiber Holder — Maple DIY (~37.3k; page counter 37,311)
- **What/problem:** A handled block that clamps a microfiber cloth flat so you can wipe a build plate (fingerprints/grease = adhesion failures) without touching it or bunching the cloth. “A tool to hold microfiber towel to clean build plates with ease.”
- **Construction:** Two blocks + knob/screw clamp; cloth is cut using the two blocks as the template, wrapped around the edge and crimped down. Designer profile: **1.6 h, 2 plates**. Ecosystem of profiles around it: Store & Dry Tray **47 min / 1 plate**, Alternative Knob–Taller **42 min / 1 plate** (23 Mar 2024 update: alt knob for thin cloth **or sandpaper**; original knob “designed to bottom out to prevent vertical force to break the print apart” — a deliberate mechanical stop). **57 print files** total on the page (mostly community profiles). Weight **not stated on designer profile in extracted text — not verified** (a social post shows a 38 g PLA profile, secondary).
- **Hardware:** **None printed-hardware-wise; consumable = a microfiber cloth** (user-supplied, cut to size).
- **Materials:** Not specified in extracted description (**not verified**); profiles exist in PLA/PETG across the community.
- **Ecosystem fit:** Universal — any printer’s plate, plus a second life as a sanding block. Released 2024-03-21; **23,994 reviews/ratings** and a 5.0 designer-profile rating (12.8k ratings) — social proof is the page.
- **Page craft:** Shortest useful description in the cohort (one sentence + 2-step instruction + GIF). Commercial use via paid membership; licence badge CC BY-NC-ND shown in page assets.
- **Decisive decision:** Designing the *clamping geometry so the knob bottoms out* — the tool cannot be over-tightened to destruction, so a first-time printer’s first print succeeds and survives.
- Source: https://makerworld.com/en/models/386963?from=search — index, read 2026-11-14.

### 7. Articulated Crystal Dragon — Saber3D (~37.1k; collections 232k downloads metric)
- **What/problem:** Pure desire object: a large, jewel-spined **flexi dragon** — the definitive “show me what your printer can do” print and craft-fair seller.
- **Construction:** **Print-in-place articulated chain** of linked segments with crystal spines; no assembly, no hardware. Page’s engineering claim is slicer-side: “every part… can be easily painted in your slicer… just make sure edge detection is turned off” — i.e. colour regions are modelled as separable bodies for AMS painting. Designed explicitly to **take less time** than rival large dragons while looking large. Exact time/weight **not stated in extracted page text — not verified** (a community video shows 15 h 46 m / 266 g for one make, secondary only). 200%/300% split-part versions are **Patreon-only**.
- **Hardware:** **None.**
- **Materials:** Not specified on page (**not verified**); community makes overwhelmingly PLA / silk / rainbow PLA, which is the point — the geometry sells filament.
- **Ecosystem fit:** None (no printer/IKEA fit) — its ecosystem is the designer’s catalogue + Patreon/MakerWorld commercial membership to **sell prints at shows/online**.
- **Page craft:** Cover = coiled dragon in gradient/silk filament, maximal colour. Description is almost pure funnel: boost ask → painting tip → Patreon 200/300% upsell → commercial licence. One of the earliest models in the list (model ID 55289).
- **Decisive decision:** Crystal spines on a flexi chain. Spines catch light in *any* filament (especially silk/rainbow), so every make photographs like an advertisement — 232k downloads of free marketing.
- Source: https://makerworld.com/en/models/55289-articulated-crystal-dragon-by-saber3d?appSharePlatform=copy — index, read 2026-11-14.

### 8. HydroBowl — Smart Fruit & Veggie Washer — kennyklak (~36.4k; collections 93.7k / 36.3k)
- **What/problem:** Washing berries/small produce without bruising or losing them down the drain. A sink bowl whose **side water inlet creates a vortex** that spins produce through the water — “no scrubbing needed.”
- **Construction:** Single bowl (per 3DSearch’s index of the page: single piece, supports listed, beginner) — exact plate count/time/weight **not in extracted MakerWorld text — not verified**. The mechanism is *fluid geometry*, not moving parts: inlet angle → vortex → drainage. Page explicitly notes “easily removable support structures” (an honest supports admission, rare in this list).
- **Hardware:** **None** (tap water is the motor).
- **Materials:** PLA per secondary index (**low confidence — flag**); food-contact / waterproofing caveats are **not addressed in the extracted page text**, a genuine gap a buyer should note (FDM layer lines + food use).
- **Ecosystem fit:** Kitchen, not printer — one of only ~4 non-printer-ecosystem models in the top 20, proving a demonstrable kitchen gadget can break the printer-accessory ceiling.
- **Page craft:** Consumer-product naming (*HydroBowl™-style + “Smart”*), benefit bullets with 🔹, “Love the swirl? Give it a boost and help it flow!” The demo is inherently viral: running tap + spinning strawberries is a 5-second video.
- **Decisive decision:** Using the tap as the power source. No motor, no crank, no assembly — the *water* does the trick the GIF shows.
- Source: https://makerworld.com/en/models/1507073-hydrobowl-smart-fruit-veggie-washer — index, read 2026-11-14.

### 9. Shoe Rack / Wall Shelf — Uzziel3D (~34.7k)
- **What/problem:** Compact, space-saving shoe storage — discovered during photography to also be a decorative wall shelf, and the title was/kept dual-purpose: *Shoe Rack / Wall Shelf*.
- **Construction:** Only **2 different parts** + **printable pins**, push-together (glue optional). Buildable to **any height/length** by repetition. Optional wall mounts **thread onto the pins between parts** (square/screw-hole face down), screwed to the wall. Print notes (rare, honest): **0.2 mm layers; 5% infill** shelf parts (raise to **8–15%** for taller/heavy use), **15% infill** pins & wall mounts; print pins **lying down** (layer orientation = pin strength); supports needed for the bottom bend of the end piece, pins and wall mount — **this model breaks the no-supports rule and says so**. Pins are “very tight” — rotate both ends in the holes first or you won’t get it apart again.
- **Hardware:** **None for freestanding**; wall screws only if wall-mounting.
- **Materials:** Not named in extracted text (**not verified**) — infill guidance substitutes for material guidance.
- **Ecosystem fit:** Grew into a system: page now funnels to **Modular Shelf for Wall/Floor/Desk** (all parts inter-compatible) and a **Modular LED Shelf** sibling.
- **Page craft:** “Flowing design” cover with shoes *and* shelf styling; success-story update at the top cross-selling the system; commercial licence via MakerWorld membership.
- **Decisive decision:** Two parts + one pin, repeated. Inventory, learning curve and failure modes are minimal, yet the result can be a 2-tier rack or a full wall — the classic “IKEA furniture” formula in print form.
- Source: https://makerworld.com/en/models/1087625-shoe-rack-wall-shelf — index, read 2026-11-14.

### 10. HelixCore — Press-to-Spin Spinner Ball — YY the panjang / Yun Goo (~34.3k)
- **What/problem:** A squishy-ball fidget that **spins when you press it** — “Press, Spin, Release. No twisting. No second step. No extra hand required.” Published June 2026; fastest-rising model in the list.
- **Construction:** Assembled mechanism ball: **ball-screw (helical) drive + clutch system + elastic-return drive + dual 608 bearings**. Pressing drives a plunger along a helical screw (linear → rotary), the clutch engages on the press and freewheels on return, the rubber band resets it (secondary review, mechanicalspinners.com, describes the same pump-top/ratchet action). Profiles: **Standard (Easy Assembly)** — shell/hinge printed grouped to cut part count — and **Color Custom Classic / Enhanced** (interchangeable petals). **26 Jun 2026 update:** travel stops behind each segment (segments could shift off-centre and spoil spin consistency) + all Color Custom petals made identical/interchangeable (poka-yoke). Optional flywheel: hinge pockets sized for **M5 nuts** (via Bambu Studio negative parts, user-resizable). Grease/light lubricant on clutch surfaces recommended. Print time/weight **not stated on page — not verified** (a secondary buying-guide claims 6–10 h, low confidence, do not rely on it).
- **Hardware:** **2× 608ZZ bearings (22×8×7 mm) + 1× rubber band (tested 28–40 mm)**. Explicitly “no magnets, no glue.”
- **Materials:** Not specified in extracted page text (**not verified**).
- **Ecosystem fit:** None — a standalone toy whose ecosystem is variants (designer invites commercial members to suggest fruit/themed shells).
- **Page craft:** The most professional page in the cohort: trademark/“**PATENT PENDING** — IP applications in multiple jurisdictions,” separate written authorisation required for injection moulding, commercial licence for printed copies only, Bambu Lab blog profile of the designer (16 years designing injection-moulded mass-production products). Tagline: “Funny Design, Serious Engineering.”
- **Decisive decision:** Hiding a real ball-screw + clutch inside a *familiar* squishy-ball silhouette. The outside promises nothing new; the first press delivers the surprise — that gap is what gets filmed and shared.
- Sources: https://makerworld.com/en/models/2910956-helixcore-press-to-spin-spinner-ball?from=recommend — index, read 2026-11-14; secondary mechanism review https://mechanicalspinners.com/helixcore-press-to-spin-ball/ ; designer profile https://blog.bambulab.com/yun-goo-the-man-behind-the-viral-helixcore-spinner/

### 11. Ultimate Filament Spool Enclosure — TYPE 01 — Supergrapher (~34k)
- **What/problem:** The **AMS Lite is open to the air** (unlike the enclosed P/X-series AMS), so spools re-absorb moisture and gather dust. This is a printable dry enclosure that snaps over AMS Lite spools, with desiccant storage and humidity monitoring. Fabbaloo “Design of the Week” (secondary, 2024-09-02).
- **Construction:** Large assembled system, **10 plates, most printed twice** (left/right): Plates 1–2 spool buckets ×2; 3–4 covers (horizontal AMS Lite) ×2 **xor** 5–6 covers (vertical/wall-mount) ×2; Plate 7 Action-Panels — choose 1 of 3 (no/one/two hygrometer openings) per side; Plate 8 Action-Buckets — large (loose desiccant, sliding lid) or small (desiccant bags); Plate 9 stability brackets ×1; Plate 10 clips + snap-in 2-part grommets ×2. Backwards-compatible Sep/Nov 2024 updates: angled filament exit + **sliding grommet** (moves with filament pull angle → less binding), larger desiccant bucket, 2-part airtight-er hygrometer panel. Optional **1.5–3 cm PTFE tube** through a grommet. Clips in **PETG**, rest in PLA per Fabbaloo’s summary of the page; page itself: “**PLA is recommended**, many users succeed with PETG.”
- **Hardware:** No tools/parts *required* by design; **hygrometer(s)** for the monitoring panels and **desiccant** are the functional extras (user-supplied / Maker’s Supply ecosystem).
- **Time/weight:** **Not stated in extracted text — not verified**; by plate count it is one of the largest prints in the list. Cannot be printed on an A1 mini (page notes buy-a-printed-one partnerships: Blurolls3D, AliExpress, eBay).
- **Ecosystem fit:** Works side-mounted **and** on Bambu’s / the designer’s AMS Lite top mount (with a low-profile screw swap); cardboard-spool adapter in beta; **Type 02 released as beta** and linked at the very top.
- **Page craft:** A manual, not a listing: table of contents, Updates → Introduction → Instructions → Videos, plate-by-plate “print this twice / do NOT print 5–6 if…” logic, and credit/traffic-sharing to YouTubers who covered it.
- **Decisive decision:** The modular **Action-Panel / Action-Bucket** choice architecture — one enclosure, but *your* hygrometer count and *your* desiccant format, without a redesign.
- Source: https://makerworld.com/en/models/486153 — index, read 2026-11-14.

### 12. Stainless Katana Sword (Print in Place) — Mr_Andre (~33.8k)
- **What/problem:** Desire/prop: a **collapsible/folding katana** whose telescoping blade extends from the handle — a cosplay/display toy that prints as one piece.
- **Construction:** **Print-in-place telescoping blade segments**; v2 changes are all mechanism refinement: **curved blade** with correctly angled tip, blades “extend and retract more smoothly,” handle revised, **pommel more securely attached**. **No supports, fits an A1 mini.** Single-colour or AMS multicolour; tip for printing one blade only: right-click → “Split into objects” in Bambu Studio. Time/weight **not stated — not verified**.
- **Hardware:** **None.**
- **Materials:** **PLA+ or PETG on Textured PEI**; glue stick advised if adhesion weakens (long thin print-in-place parts are adhesion-critical).
- **Page craft:** Franchise page: top of description cross-sells the newest katana (Hiken — Hidden Blade, plus Ocean/Golden Guard/Twisted variants in the designer’s catalogue; 13.8k followers, “100,000 successful prints” badge). Safety note prominent: model katana, not a weapon, not for children. Commercial sales via **Patreon**.
- **Decisive decision:** Telescoping print-in-place. The “magic” is the transformation from a short handle on the bed to a full-length sword in one flick — no assembly skill between download and video.
- Source: https://makerworld.com/en/models/1033319-stainless-katana-sword-print-in-place?appSharePlatform=fb — index, read 2026-11-14. Published 2025-01-24 (per 3DSearch index).

### 13. Fidget Cube Toy: Angled — Austin Vojta (~33.4k; page 33,257, 199k downloads, 176k prints)
- **What/problem:** An **infinity cube** fidget — endless folding for restless hands, desk/school.
- **Construction:** **Print-in-place, 8 small cubes joined by printed hinges**, “precisely engineered for smooth movement straight off the print bed. **Does not require any support or assembly!**” Variants are the product line: **3 textures** (no texture / knurled / etc. — profile names show “no texture, light (15% infill)”, “knurled, light (15% infill)”) and sibling geometries **Rounded / Spherical / Mini / Jack-o’-lantern** in a 24-model Fidget Toys collection. **30 print files** (community + designer). Released 2023-11-15. Time/weight for the Angled designer profile **not in extracted text — not verified** (secondary video for the related infinity cube: ~1 h / 30 g, do not attribute to this exact profile).
- **Hardware:** **None.**
- **Materials:** Not specified in extracted text (**not verified**); hinge life in practice favours tougher filament, but the page sells PLA-friendly immediacy.
- **Licence:** **Standard Digital File License (personal/non-commercial)** for most of his models — page itself contrasts this with his *Yet Another Fidget Infinity Cube v2* under CC BY-SA 4.0.
- **Page craft:** One-paragraph description. The collection *is* the marketing: “Each prints in place and is ready to work right off the bed.”
- **Decisive decision:** Zero-friction everything — no supports, no assembly, no hardware, works in the first minute off the bed, in a texture you choose. Infinity cubes existed; this one removed every reason a print could fail or feel rough.
- Source: https://makerworld.com/en/models/65426-fidget-cube-toy-angled?from=search — index, read 2026-11-14.

### 14. BLV — AMS / AMS 2 Riser v4.0 — benlevi (~33.3k)
- **What/problem:** AMS sitting directly on a P/X printer **blocks the view of the print and prevents opening the top glass** (needed for airflow on high-temp materials). A riser lifts the AMS, holds the glass, and adds storage/lighting.
- **Construction:** The heavyweight of the list: tab-and-slot assembled frame (Parts 1–4 interlock, dashboard panels slide in), **2 tool drawers**, build-plate storage, top-glass holder with **TPU gaskets**, TPU button inserts (P1S/X1C), dual integrated **LED strips** (angled for X1 LiDAR), standard **or** modular side panels (modular = slide-in accessory slots; fitting them needs **18× M3 heat-set threaded inserts + 18× M3×10 mm flat-head screws**, soldering iron at 200 °C). Base build is “screw-free, no tools.” Optional magnets (glued) in side panels for scraper/hex keys. **~96 print hours including colour switching; ~2.7 kg grey PETG + ~0.7 kg accent PETG + ~15 g black PETG + ~50 g TPU.** Page warns, honestly: “If you’re looking for a quick 2 hour print… this isn’t it.” Also warns drawers must be the **same material family** as the body or tolerance/friction suffers.
- **Hardware (full build):** LED strips, magnets + superglue, and (modular panels only) the inserts/screws above.
- **Materials:** **PETG structure + TPU gaskets/inserts** — a multi-material bill on purpose.
- **Ecosystem fit:** **X2D / P2S / X1C / P1S × AMS & AMS 2 Pro**, printer-specific dashboards/gaskets, **F3D + STEP CAD included free** for remixing (no commercial use without permission), and a genuine third-party accessory ecosystem (AMS-HT holder, AMS 2 Pro PSU holder, tool holders; “search AMS Riser V2” finds community attachments — a slot standard inherited across versions). **v4.0 mega-update 18 Apr 2026**: X2D/P2S support, magnetic attachments, extra build-plate support, improved print time.
- **Page craft:** Founder letter (“Hi, I’m Ben Levi…”), coffee/boost humour, animated GIF assembly steps for every sub-assembly, parts-reference plates, PayPal “buy me a beer” + membership for selling prints.
- **Decisive decision:** Giving the CAD away and standardising the accessory slot. The riser stopped being a product and became a *platform other designers design for* — every attachment is an ad for the riser.
- Source: https://makerworld.com/en/models/19535-blv-ams-ams-2-riser-p2s-x2d-x1c-p1s-v4?from=search — index, read 2026-11-14 (545-line page; first 387 lines extracted, remainder is LED/community add-on detail).

### 15. Mini Bag Clip — fifindr (~32.9k; page 32,999)
- **What/problem:** Sealing opened chip/pasta/cereal/snack bags to keep food fresh — the smallest possible useful print.
- **Construction:** Single-piece **compliant living-flexure clip** (the body flexes to clamp; no hinge pin, no spring). **1 plate.** Two strengths: **Normal** and **Stronger** versions; a PETG profile at **0.2 mm / 2 walls / 15% infill** among **24 print files**. Successor line shows the material lesson explicitly: V2/V3 pages warn **PETG recommended — PLA (especially matte PLA) loses elasticity/flexibility over time**; V3 is 2.5 g and “tested to hold up to 3 kg” (successor data, not the original page).
- **Hardware:** **None.**
- **Materials:** PETG profile offered for the original; see elasticity warning above — this is the cohort’s clearest *compliant-mechanism material* case study, and a direct caution for a matte-PLA studio: a flexure that works on day 1 can creep/soften.
- **Time/weight — the hook, in the title block:** **8 minutes, 3.6 g.**
- **Page craft:** Five ✅ bullets, nothing else needed. Designer’s signature joke prices a boost in filament: **“Boost = 43 g of filament :)”** — i.e. one boost ≈ 12 bag clips. Commercial licence via membership; Standard Digital File License badge. Released 2025-02-12; **11,114 reviews**.
- **Decisive decision:** Optimising for *filament-end economics* — 3.6 g means the last scrap on every spool, the sample filament in every printer box, and every “what can I print in 10 minutes?” search all become this clip.
- Source: https://makerworld.com/en/models/1101226-mini-bag-clip — index, read 2026-11-14.

### 16. Compact Poop Bucket S (A1, A1 mini) — Michal (~32k; page 32,054)
- **What/problem:** Bambu A1/A1 mini printers flick purge “poop” off the side; this compact basket catches it instead of the desk/floor. “Very easy to attach and remove.”
- **Construction:** Single-piece basket, **1 plate, 1.6 h** (designer profile: 0.2 mm, 2 walls, **30% infill**; community “Clean” profile 1.2 h). **37 print files**, **28,086 reviews, 4.9★ (20.8k ratings on designer profile)**. **19 Jun 2024 upgrade driven verbatim by comments:** (1) **latches added** so vibration can’t walk the basket off, (2) internal shelf where poop stuck **removed**, (3) wall **raised** so poop can’t bounce out, (4) height **+5 mm** volume, (5) tip: stick thin sponge inside the bottom to quieten it. Weight **not stated — not verified**. No hardware; sponge optional.
- **Materials:** Profiles in PLA (incl. a “PLA Speed Optimized” profile); no PETG requirement stated.
- **Ecosystem fit:** Size system, not a single SKU: **S here, L linked** (model 501368), plus a separate with-drawer variant and an M bucket for X1/P1 on the designer’s page. Released 2024-05-02.
- **Page craft:** The description *is* the changelog, with a colour-coded annotated photo (yellow/red/green arrows for each fix) — visible proof the designer reads comments.
- **Decisive decision:** The latches. Every rival bucket works on a still printer; this one stays on a *vibrating* printer — the failure mode users actually complained about.
- Source: https://makerworld.com/en/models/451897-compact-poop-bucket-s-a1-a1-mini?from=search — index, read 2026-11-14.

### 17. Cascade Connect — A Self Sorting Connect 4 — CyberYeti (~32k; collections 91.2k / 31.9k)
- **⚠ Verification limit:** MakerWorld collection listings verify title/author/counts; the direct MakerWorld page was **not retrieved**, so mechanism detail below is from **secondary sources** (maker videos + a licensed-print retailer) and is labelled as such.
- **What/problem:** Connect 4, re-engineered so that **clearing the board sorts the pieces by colour automatically** — removing the tedious manual sort before the next game, and turning reset into the best moment of play.
- **Construction (secondary):** Vertical grid + stand + two sets of **chiral (mirror-twist) spiral pieces** — one colour twists clockwise, the other counter-clockwise — and matching **threaded/helical channels** in the board. On release, each piece’s handedness routes it to its own collection tray. Crucially, sorting depends on the piece’s **chirality, not its orientation** — flipping a piece over does not change its handedness (the “screw” analogy demonstrators use), which generated millions of sceptical comments and explainer videos (Mike’s Quest Log, 6M+ views claimed, Mar 2026). Retailer (RapidParts3D, selling prints from $20, PLA or PETG, ages 6+) notes “precision-tuned tolerances” and that some makers report pieces sticking/needing light sanding — the tolerance risk of the design. Hardware: **none reported**. MakerWorld plate/time/weight: **not verified**.
- **Page craft (from listings/virality):** Title formula *New Name — A Self Sorting [familiar game]*. The cover/video moment is the cascade itself.
- **Decisive decision:** Encoding player identity in **geometry (handedness) instead of a sensor, magnet or mechanism**. It costs zero extra parts, works every time, and is just counter-intuitive enough to be un-shut-up-able in comments — free algorithmic reach.
- Sources: MakerWorld collection listing https://makerworld.com/en/collections/3562849-games — index; secondary https://www.rapidparts3d.store/shop/p/product-2-5c6mb-j8mng-zsl73-kpfnd — read 2026-11-14.

### 18. IKEA SKADIS Add-Ons: Parametric Bins and Shelves — Kino (~31.8k; customised 130,000+ times per secondary)
- **What/problem:** SKÅDIS owners never need *a* bin, they need *the bin that fits this gap / these screws / that tool*. A fixed bin is wrong; a generator is right.
- **Construction:** **OpenSCAD Parametric Model Maker** customizer (MakerWorld “Customize” button), not fixed STLs — though 13 print profiles of presets exist. Parameters documented like an API: bin dimensions, **horizontal_compartments / vertical_compartments arrays** (relative sizes summing to 1, edited on script lines 11–12), **wall_thickness default 3 mm, corner_radius default 5 mm** (must be < any bin dimension), **frontal_drop default 0.2 (20%)**, rounded vs flat base boolean, and a fully specified SKÅDIS hook: **hole_spacing 40 mm (do not change), hook_body_length 30 mm, hook_thickness 4.3 mm, hook_outer_radius 4.7 mm, hook_bend_angle 167.4°, hook_tip_length 4.5 mm, inferior_hook_length 2 mm, inferior_support_offset 26.513 mm** — hooks **auto-position** from bin width. Hooks at **100% infill**; **tree supports** recommended (another honest supports exception). Single generated part per bin/shelf; no hardware.
- **Materials / time / weight:** Inherently variable — depends what you generate (**by design, no single number exists**).
- **Ecosystem fit:** Pure SKÅDIS (40 mm spacing). Published Nov 2024; secondary generator review (SkipTheCAD, checked 26 Sep 2026) reports **130,000+ customizations** — the usage metric that replaces downloads for a generator.
- **Page craft:** Documentation-as-product: parameter tables, defaults, and “do not modify unless…” warnings. Designer (Kino, 5.3k followers) has since released a “new fully parametric model” and cross-links it at the top.
- **Decisive decision:** Shipping the **generator instead of the bins**. Every user’s perfect-fit bin is a unique success story, and none of them required the designer to model it.
- Source: https://makerworld.com/en/models/799571 — index, read 2026-11-14 (MakerWorld redirects this ID to the SKADIS Add-Ons page). Secondary: https://skipthecad.com/generators/skadis-parametric-bins-shelves/

### 19. Mechanical Phone Holder Desk Mounted Stand Arm — Hodzinets (~31.2k; 3DFinder index 31,197 likes / 44,467 downloads)
- **What/problem:** A robot/mecha-style **desk-clamped articulated arm** that holds a phone at any angle for video, calls, streaming or overhead shots — without buying a metal arm.
- **Construction:** Assembled multi-part mechanism. Official **assembly-instruction PDF** parts list: Front, Back, **Hand ×2**, Mount Bolt, Leg, **Arm ×2, Retainer ×2, Arm Bolt ×3, Washer ×2**, Mount Connector, Connector, Desk Mount, **Screw ×8 (BT2.6×8 self-tapping)**, **Rubber Band (1.4×20 mm)** — i.e. printed structure + printed bolts/washers, with elastic return from the rubber band. Secondary print index (FilRef): **2 plates, ~167 g, 6 h 36 m** (one user’s profile — treat as indicative, not designer-stated). The spring/grip “hand” + geared/mechanical aesthetic is the visual signature (Maker’s Supply features it; designer’s “Office Desk” collection).
- **Hardware:** **Maker’s Supply hardware kit ZH151 sold by Bambu** ($2.68 US store listing, “hardware kit only — printed parts not included”): the BT2.6×8 screws + rubber band above. This is the cohort’s cleanest example of MakerWorld’s kit economy: free files, $2.68 kit, no Amazon hunting.
- **Materials:** Not stated in extracted sources (**not verified**).
- **Ecosystem fit:** Desk edge (clamp mount), phones; part of Hodzinets’ desk-accessory family.
- **Page craft:** “Mechanical / robot” styling as differentiation in a sea of plain stands; official PDF instructions + a purchasable kit remove the two biggest drop-offs (assembly confusion, hardware sourcing).
- **Decisive decision:** Designing *for* the Maker’s Supply kit from the start — standard screws + one standard rubber band, buyable in one click from Bambu, instead of a bespoke hardware scavenger hunt.
- Sources: Assembly PDF https://makerworld.bblmw.com/makerworld/model/US3e09becace8daf/design/2025-01-29_b77875d063926.pdf ; kit https://asia.store.bambulab.com/products/mechanical-phone-holder-desk?id=741199891352231937&modelId=1052740&terminal=handy ; collection https://makerworld.com/en/collections/2204002-office-desk — index, read 2026-11-14. Direct model URL not extracted from search results — **flagged**.

### 20. Clicker Master: The Heart of the Fidget — Jos MA (~31.2k mission; ~30.3k in collections, 92k downloads metric)
- **Identification:** This **is** the “Clicker Master” at the bottom of the Likes list — exact title match, single model by **Jos MA (@user_3380298830, “MOLD DESIGNER”, 50,000 successful prints badge)**, 9 print profiles. **⚠ Correction:** the mission describes it as “using a mechanical keyboard switch.” Its own page says the opposite: it is a **print-in-place clicker core with a printed spring — “100% Mechanical: the spring is part of the print. No metal springs, screws, or glue required”** — *engineered to mimic* “an industrial switch or a mechanical keyboard.” If the parent meant a keyboard-switch clicker, that is a different design family (e.g. MakerLab Clicker Generator housings for real MX switches); no top-liked model matching both “Clicker Master” *and* a real switch was found.
- **What/problem:** Not a fidget — a **component**: a compact click “sound engine” other designers embed in their own cases/buttons/toys. “It’s not a standalone fidget, but an internal mechanism.”
- **Construction:** Print-in-place, tiny contact area (page warns to fix it to the plate with lacquer/glue or it will detach). Two sizes: **Standard 17 mm** (matches “original-style” clicker footprint — drop-in compatibility with the existing clicker ecosystem) and **Large 19.6 mm** (more robust click). Must be installed with a **small clearance gap** or the sound part can’t move. Needs **break-in**: “at first, it might not make a sound. Keep pressing it repeatedly.”
- **Hardware:** **None.**
- **Materials/settings:** **PLA+ for a “crisper” sound, PETG for long-term spring durability; 220 °C; 0.2 mm** resolution (“precise tolerances are key to a great sound”).
- **Page craft:** Component-marketing: “Easy Integration: designed as a ‘block’ ready to be inserted into your CAD files.” Every fidget that embeds it becomes a distribution channel.
- **Decisive decision:** Selling the *engine, not the toy* — and sizing the 17 mm version to the incumbent clicker’s footprint so switching costs are zero.
- Source: https://makerworld.com/en/models/2409022-clicker-master-the-heart-of-the-fidget — index, read 2026-11-14.

---

## Synthesis

### Recurring design patterns (counts out of 20)
| Pattern | Count | Models |
|---|---|---|
| Printer-ecosystem accessories (fix/upgrade a Bambu printer or its AMS) | 7 | #1 Flipper, #3 Spool Rack, #5 Top Mount, #6 Plate Cleaner, #11 Enclosure, #14 BLV Riser, #16 Poop Bucket |
| IKEA SKÅDIS ecosystem (board or add-ons) | 2 (+ #6/#9 adjacent) | #4 Pegboard, #18 Parametric Bins |
| Modular / expandable systems (repeat a unit to any size) | 6 | #3, #4, #9, #11, #14, #18 |
| Print-in-place mechanisms (no assembly) | 5 | #7 Dragon, #12 Katana, #13 Fidget Cube, #15 Bag Clip (compliant, single piece), #20 Clicker Core |
| Assembled mechanisms with real engineering (bearings/clutch/compliant/chiral) | 5 | #2 Dummy 13, #10 HelixCore, #17 Cascade, #19 Phone Arm, #1 Flipper |
| Fidgets / toys / games (pure play) | 6 | #2, #7, #10, #12, #13, #17 (+ #20 as component) |
| Micro / quantified-hook prints | 3 explicit | #15 (3.6 g/8 min), #6 (1.6 h), #16 (1.6 h/1 plate); counter-example #14 (96 h as a *premium* hook) |
| Parametric / generator / CAD-given-away | 3 | #18 OpenSCAD, #14 F3D+STEP, #2 CAD (paid) + CC-BY files |
| Zero non-printed hardware | 9–10 | #2, #3, #7, #9 (freestanding), #12, #13, #15, #16, #18, #20 |
| One cheap standard hardware item as the *only* ask | 5 | #1 (M3×30 kit), #10 (608ZZ + band), #11 (hygrometer), #19 (ZH151 kit), #6 (a cloth you already own) |

### Shared engineering techniques worth copying
1. **Prefer snap-fits and compliant mechanisms over press-fits** where tolerances vary printer-to-printer (Dummy 13 v1.0 notes, verbatim reasoning; BLV tab/slot + drawer friction note; Bag Clip flexure).
2. **Design the failure stop in:** Plate Cleaner knob bottoms out; HelixCore travel stops; Poop Bucket latches + raised wall; Flipper 75° rest angle.
3. **Poka-yoke:** Dummy 13 non-swappable abdomen/waist; HelixCore identical petals (v2 fix); Enclosure “do not print plates 5–6 if you chose 3–4.”
4. **Material-by-function, not by habit:** frame PETG/ABS vs armor PLA (Dummy 13); clips PETG vs body PLA (Enclosure); PETG structure + TPU gasket (BLV); PLA+ sound vs PETG spring life (Clicker Master); **ABS scaled 100.5% for shrinkage** (Flipper). Matte PLA is the *wrong* answer for flexures (Bag Clip V2/V3: loses elasticity; matte PLA explicitly soft), heat-adjacent brackets (Flipper: PLA warps), and stressed joints (Dummy 13: stiff/brittle/creep).
5. **Standard interfaces as free R&D:** SKÅDIS 40 mm spacing + published hook geometry (Kino: 4.3 mm thick, 167.4° bend…); 608ZZ bearing (22×8×7); M3×30 / M3 inserts; MX-clicker footprint (17 mm); AMS/AMS 2 Pro mounting points.
6. **Hollow tubes > solid bars** for printed load members (Spool Rack rods); **pins printed lying down** so layers aren’t the weak plane (Shoe Rack).
7. **Orientation & slicer settings are design:** Dummy 13’s 0.15 mm / rectilinear / 0.15 mm elephant-foot / Arachne recipe; runners/sprues as an adhesion strategy (+9 g to save a 24 g print).

### Shared page / marketing patterns worth copying
- **Title = [Name] + [one-line benefit] + [compatibility].** “better access to your P1S/X1”, “(IKEA compatible)”, “for A1 & A2L”, “Print in Place” in the title itself.
- **Lead with the pain or the number, never the story.** Flipper: “I got tired of…”; Bag Clip: 8 min / 3.6 g; BLV: the honest anti-hook (96 h).
- **The cover is a GIF of the transformation:** flip, cascade-sort, press-spin, telescope, fold. Static beauty shots (Dragon) only win when the object itself is the spectacle.
- **Version loudly, on the same page:** V1.4, v4.0 (18/04/26), Type 02 beta, 19.06.2024 upgrade with colour-coded arrows. Updates *are* the comments section, answered.
- **Funnel, don’t finish:** every page cross-links siblings/variants/successors (katana family, shelf system, S/L buckets, H2 Flipper). One hit manufactures the next.
- **Licence as strategy, chosen per goal:** CC-BY for platform growth (Dummy 13), Standard + paid membership for income (most others), patent-pending + commercial-only-for-prints for a mechanism business (HelixCore).
- **Boost ask with personality:** “Boost = 43 g of filament :)”, “Toss me a boost (I’m running on coffee and dreams)”, “Love the swirl? Give it a boost.”

### What these top models do that a small studio focused on decorative holiday village buildings + desk accessories does NOT currently do — honest gaps
*(Inferred from the studio profile given in the mission — matte PLA, P1S, no-supports, decorative buildings/desk accessories — not from auditing the studio’s actual pages.)*
1. **No mechanism.** Village buildings are static; every toy/game winner here *does* something in 3 seconds (flip, spin, sort, telescope, fold, click). Desk accessories are the studio’s closest bridge — none of the top 20 is a purely static desk object.
2. **No ecosystem host.** The studio’s products stand alone; 9–10 of the top 20 plug into a host the buyer already owns (Bambu printer, SKÅDIS, AMS, a clicker footprint). A building that only fits *your* village has no borrowed installed base.
3. **No quantified hook.** No equivalent of “3.6 g / 8 min” or “fits one 256 plate, no supports, <200 g” in a decorative-building pitch — yet the studio’s no-supports/matte-PLA discipline *is* a quantifiable hook it apparently isn’t selling.
4. **Matte PLA as a silent constraint, not a tested boundary.** Top designers publish *where PLA fails* (flexures, heat, joints). A matte-PLA-only range needs that honesty — and designs that route around it (rigid geometry, no living hinges under sustained load) — rather than discovering it in reviews.
5. **No parametric/generator offer.** One OpenSCAD customizer (name, date, house number, village scale) would do for the studio what Kino’s did for SKÅDIS: infinite SKUs, zero modelling.
6. **No versioning theatre / comment-driven changelog.** Top pages visibly *change* in response to comments; a static “final” listing reads as abandoned next to a V1.4 / v4.0 page.
7. **No component play.** Clicker Master and Kino sell *inputs to other makers’ products*. The studio sells only finished objects — no shared scale standard, no accessory slot other designers can design for.

### 8–12 concrete new product ideas for that studio (original, borrowing proven patterns)
1. **Village Advent Gate — a building a day.** 24 tiny façades that snap (Dummy-13-style snap-fit, not press-fit) onto **one shared printed street base** across December. *Pattern:* modular system + advent ritual. *Travel:* daily posting cadence is built-in marketing; each façade is a <30 min print. *Risk:* snap tolerance across 24 variants in matte PLA — prototype the snap in the stiffest geometry, generous clearance.
2. **Press-to-Light Village Chapel.** Press the roof; a compliant printed mechanism (HelixCore *principle*, original geometry — no copying its ball-screw) toggles a coin-cell LED tealight puck seated in a standard cavity. *Pattern:* press-to-actuate surprise in a familiar silhouette. *Travel:* “press the roof” is a perfect 3-second GIF. *Risk:* **matte PLA flexure fatigue/creep** — use the mechanism only for a momentary toggle, never a sustained spring; LED/battery is the one hardware ask, state it upfront.
3. **Self-Sorting Desk Coin / SD-Card Chapel.** A desk “village post office” whose chute sorts two coin denominations (or SD vs microSD adapters) by **size/geometry into two trays** — Cascade’s *encode identity in geometry* idea, original implementation. *Travel:* sorting demos are inherently shareable. *Risk:* coin-size variance by country — ship a parametric/OpenSCAD version per currency.
4. **SKÅDIS Village Shelf.** A matte-PLA village-façade shelf/bin using **Kino-published SKÅDIS hook spacing (40 mm)** — a row of tiny shopfronts that *are* bins (open roofs). *Pattern:* borrowed IKEA ecosystem + decorative strength. *Travel:* every SKÅDIS owner is a prospect; façade = cover photo. *Risk:* hook strength — 100% infill hooks, and do not exceed modest loads; test, don’t assume.
5. **8-Minute Village Tree / Lamp Post (the Bag Clip play).** A **<5 g, <10 min** mini lamp post/tree designed to use spool ends, sold/given as the free “first print” that seeds the whole village scale. *Pattern:* micro-print gram/minute hook. *Travel:* lowest possible trial cost; every printer owner can afford to try the studio’s scale. *Risk:* tiny parts = adhesion; design a shared brim/runner (Dummy 13 runner lesson).
6. **Telescoping Village Clock Tower.** Print-in-place telescoping tower (Katana principle, original design) that ships/stores flat-short and extends tall for display. *Pattern:* print-in-place transformation. *Travel:* extension moment = video. *Risk:* telescoping clearances in matte PLA are unforgiving — needs iterative tolerance testing per printer; **flag as the highest-risk idea here**.
7. **Infinity-Fold Desk Calendar.** An Austin-Vojta-style print-in-place hinged cube (original geometry/textures: brick, timber, slate) whose faces carry month/day tiles — a fidget that is also a perpetual calendar. *Pattern:* print-in-place fidget + desk utility. *Travel:* works off the bed, no assembly — giftable. *Risk:* hinge wear in PLA; keep hinges thick, motion low-load, and test 500+ folds.
8. **Parametric Village House-Number / Nameplate Generator.** OpenSCAD/MakerWorld Customizer: house number + name + 3 façade styles (Kino pattern). *Pattern:* generator, not SKU. *Travel:* every output is personal — buyers post *their* number, not your product. *Risk:* font/licensing and Customizer support load; limit parameters ruthlessly (Kino’s “do not change 40 mm” discipline).
9. **Village Train / Sleigh with Shared Snap Coupler — and publish the coupler as a free component.** A Clicker-Master move: give away the **coupler standard** so other designers’ wagons/sleighs/buildings-on-wheels connect to the studio’s system. *Pattern:* component-as-platform, CC-BY the interface. *Travel:* remixes advertise the host system. *Risk:* giving away the interface invites clones of the whole system — licence the *interface* open, keep vehicles commercial.
10. **Poop-Bucket Lesson Desk Catch-All: the “Chimney Pot” Pen Pot with Latch-On Saucer Base.** A village chimney-pot pen pot whose base **latches** (Michal’s latch lesson) so it can’t be knocked/skidded off a desk tray system; S/M/L sizes linked like Michal’s buckets. *Pattern:* comment-proofed utility + size family. *Travel:* desk-accessory buyers already understand pen pots; latch demo is filmable (shake test). *Risk:* low — rigid PLA part; main risk is being *too* ordinary, so the shake-test GIF must lead.
11. **Flipper-Style Folding Village Bridge / Market Stall.** A stall/bridge that **flips/folds flat** for storage and pops up for display (Flipper’s hinge thinking, domestic scale), all parts on one plate, no supports, quantified (“one plate, X g, folds flat”). *Pattern:* transformation + storage pain (holiday decor’s real #1 pain is January storage). *Travel:* “your whole village folds flat” is a category claim competitors don’t make. *Risk:* hinge pins in PLA — use loose, replaceable printed pins (Shoe Rack pin lesson, printed lying down), not living hinges.

---

## Could not verify
- #4 Combo pegboard: direct model URL, description, construction, hardware, materials, time — **not retrieved** (listings only). Do not cite neighbouring SKÅDIS models’ specs as Combo’s.
- #17 Cascade Connect: direct MakerWorld page text, plate/time/weight, designer-stated materials — **not retrieved**; mechanism from secondary video/retail sources.
- #19 Phone Holder: direct model URL and designer-stated materials/time — not extracted; parts list from the official assembly PDF, time/weight from a third-party print index (indicative only).
- Print time/weight **not stated** on the extracted pages for: #2, #7, #8, #11, #12, #13, #16 (flagged in each section). Secondary figures found for #7/#13 are labelled secondary and should not be quoted as designer specs.
- Licence type for several models is shown only as a page badge/membership prompt in extracted text; where not explicit in text it is described as such, not asserted.
- Like counts move daily; mission counts and 2026-11-14 live counts differ slightly throughout — neither is “wrong.”

## Sources
All MakerWorld URLs are listed verbatim in each numbered section above (index reads, 2026-11-14). Key secondary sources, used only where flagged: Fabbaloo, Design of the Week — Ultimate Filament Spool Enclosure (2024-09-02) https://www.fabbaloo.com/news/design-of-the-week-ultimate-filament-spool-enclosure-for-ams-lite ; MechanicalSpinners HelixCore review https://mechanicalspinners.com/helixcore-press-to-spin-ball/ ; Bambu Lab blog, Yun Goo / HelixCore https://blog.bambulab.com/yun-goo-the-man-behind-the-viral-helixcore-spinner/ ; SkipTheCAD, SKADIS Bins and Shelves Generator https://skipthecad.com/generators/skadis-parametric-bins-shelves/ ; RapidParts3D Cascade Connect listing https://www.rapidparts3d.store/shop/p/product-2-5c6mb-j8mng-zsl73-kpfnd ; Bambu Wiki AMS Lite Top Mount tutorial https://wiki.bambulab.com/en/a1/manual/ams-lite-top-mount-tutorial
