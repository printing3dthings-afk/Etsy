#!/usr/bin/env python3
"""
Generate new unique illustrated sticker sheets for each planner.
One sheet at a time — show for approval before proceeding.

Usage:
  python tools/gen_sticker_sheet.py --pid DP1026 --sheet 6
"""
import os, sys, json, base64, urllib.request, time, argparse
sys.path.insert(0, '/home/user/Etsy')
with open('/home/user/Etsy/.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

OPENAI_KEY = os.environ['OPENAI_API_KEY']
ART_DIR = '/home/user/Etsy/data/digital_products/product_files'

# ── Sticker sheet prompts per planner ────────────────────────────────────────
# Each sheet: 20-25 distinct kawaii illustrated sticker items
# Style: thick black outline, soft pastel colors, white background,
#        cute facial expressions, scattered layout (not a grid)

SHEET_PROMPTS = {
    'DP1026': {
        6: {
            'name': 'Self-Care & Wellness',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and soft pastel colors with lavender and purple accents. "
                "Stickers include: a round bath bomb with sparkles and a happy face, a green face mask sheet with cute eyes, a small purple amethyst crystal cluster, "
                "a sprig of lavender with a smiling face, a jade roller with rosy cheeks, a small pink yoga mat rolled up, a round tin of bath salts, "
                "a essential oil dropper bottle in purple, a fluffy cloud-shaped sleep mask with closed eyes, a meditation cushion with a serene face, "
                "a pair of cozy fuzzy socks with hearts, a small herbal tea sachet on a string, a lit aromatherapy candle in a glass jar with a tiny face, "
                "a tiny journal with a heart lock, a small flower crown of daisies, a pink rose in bloom, a moon-shaped soap bar, "
                "a face serum bottle with a sparkle, a warm heating pad with a smiley face, a calming sleep tea mug with ZZZs. "
                "Each sticker is approximately the same size, clean and detailed, kawaii chibi style. No text on stickers. Transparent-looking white background."
            ),
        },
        7: {
            'name': 'Affirmations & Milestones',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and soft pastel colors with gold and lavender accents. "
                "Stickers include: a golden trophy cup with a star on it and a happy face, a shooting star with sparkle trail, a gold laurel wreath circle, "
                "a magic wand with a star tip sparkling, a hot air balloon with a smiling sun pattern, a small rocket ship blasting off, "
                "a colorful confetti popper bursting, a glowing lightbulb with a cute face, a purple graduation mortarboard cap, "
                "a ribbon award badge that says 'YOU DID IT' in tiny text, a gold medal on a ribbon, an open book with sparkles coming out, "
                "a rainbow arching over fluffy clouds, a heart with little wings, a star cluster with one big center star, "
                "a tiny mountaintop with a flag planted, a crystal gem shaped like a heart, a cheerful sun with rays and a big smile, "
                "a colorful birthday balloon bunch, a four-leaf clover with a happy face. "
                "Each sticker is approximately the same size, clean and detailed, kawaii chibi style. No text on stickers. Clean white background."
            ),
        },
        8: {
            'name': 'Moon & Celestial',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and soft pastel lavender, navy and gold colors. "
                "Stickers include: a crescent moon with a sleepy face and small star earring, a full moon with big kawaii eyes and rosy cheeks, "
                "a shooting star with a golden trail, a Saturn-like planet with rings and a happy face, a fluffy cloud with a comet passing through, "
                "a small telescope pointing at stars, a crystal ball on a tiny stand with a galaxy inside, a dream catcher with feathers and beads, "
                "a night owl sitting on a branch with big sleepy eyes, a constellation of dots connected by thin lines in a recognizable shape, "
                "a sun and moon yin-yang style charm, a small glass bottle with a galaxy inside, a star cluster with a big winking star, "
                "a cozy night sky with three stars and a moon, a small aurora ribbon in pink and teal, "
                "a celestial eye with lashes and a star pupil, a tiny hourglass with star sand, a wishing fountain coin with a star, "
                "a cloud with lightning and stars, a lunar calendar circle showing moon phases. "
                "Each sticker is approximately the same size, clean and detailed, kawaii chibi style. No text on stickers. Clean white background."
            ),
        },
        9: {
            'name': 'Plants & Botanical',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and soft pastel green, lavender and earth tone colors. "
                "Stickers include: a round terra cotta pot with a smiling succulent, a big monstera leaf with a sleepy face, "
                "a round cactus with pink flowers and rosy cheeks, a tiny mushroom with red cap and white spots and a happy face, "
                "a sunflower with big kawaii eyes, a small daisy bouquet tied with a bow, a green watering can with a flower spout, "
                "a red and white toadstool on green grass, a curling fern frond with a soft expression, a small bonsai tree in a rectangular pot, "
                "a garden snail with a flower-patterned shell, a fuzzy bumblebee with heart-shaped wings, a flower crown of wildflowers, "
                "a seed packet envelope with flower illustration, a small honey jar with a bee on the label, "
                "a sprig of mint leaves with a fresh face, a clover patch with one four-leaf clover, "
                "a hanging air plant in a glass terrarium, a tiny garden trowel with a dirt patch, a morning glory vine with purple flowers. "
                "Each sticker is approximately the same size, clean and detailed, kawaii chibi style. No text on stickers. Clean white background."
            ),
        },
        10: {
            'name': 'Sweet Treats & Celebration',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and soft pastel pink, lavender and sweet colors. "
                "Stickers include: a birthday cake slice with a lit candle and a happy face, a tower of three colorful macarons, "
                "a swirled lollipop on a stick with a smiling face, a pink heart-shaped donut with sprinkles, "
                "a strawberry shortcake with a cream topping, a golden croissant with rosy cheeks, "
                "a boba tea cup with a wide straw and a kawaii face on the cup, a round white mochi with a cherry on top, "
                "a round cookie with pink icing and rainbow sprinkles, a swirled soft-serve ice cream cone, "
                "a small layered pudding cup with a cherry, a glass candy jar filled with colorful sweets, "
                "a berry smoothie cup with a straw and a smile, a stack of three fluffy pancakes with syrup dripping, "
                "a slice of cheesecake with a berry, a cupcake with lavender frosting and a star, "
                "a chocolate bar broken in pieces with a happy face, a round waffle with honey and a bee, "
                "a small pie with a star vent on top, a festive confetti cake pop on a stick. "
                "Each sticker is approximately the same size, clean and detailed, kawaii chibi style. No text on stickers. Clean white background."
            ),
        },
        11: {
            'name': 'Cozy Home',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and soft warm lavender and cream home decor colors. "
                "Stickers include: a small bookshelf with colorful books and a plant on top, a cozy armchair with a pillow and a sleeping cat, "
                "a record player with a vinyl disc spinning and musical notes, a small easel with a canvas painting on it, "
                "a window frame with a plant on the sill and sun shining through, a string of polaroid photos on a line with mini clips, "
                "a welcome doormat with a flower, a lantern with a glowing candle inside, a cozy desk lamp with a round shade, "
                "a round photo frame with a bow on top, a basket with yarn and knitting needles, a vintage globe on a small stand, "
                "a small vintage suitcase with stickers on it, a floating shelf with small plants and books, "
                "a teapot on a tray with a matching cup, a bread loaf fresh from the oven in a pan, "
                "a cuckoo clock with tiny bird coming out, a decorative wreath of flowers on a door, "
                "a cozy hammock strung between two points, a snow globe with a tiny house scene inside. "
                "Each sticker is approximately the same size, clean and detailed, kawaii chibi style. No text on stickers. Clean white background."
            ),
        },
    },
    'DP1027': {
        6: {
            'name': 'School Supplies',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and soft pastel pink and sky blue colors. "
                "Stickers include: a chunky pink pencil with a smiley eraser on top, a ruler with tick marks and rosy cheeks, "
                "a round pink eraser with a cute face, a glue stick with a happy expression, a pair of round-tipped scissors with eyes, "
                "a backpack in pastel pink with a front pocket and kawaii face, a pencil case pouch with a zipper smile, "
                "a round pencil sharpener with wood shavings, a stapler with a winking face, a tape dispenser with a bow, "
                "a set of three colored markers standing upright, a compass for geometry with a tiny face on the pivot, "
                "a protractor half-circle with sleepy eyes, a small notebook with a lock and heart, "
                "a three-ring binder with colorful tab dividers, a stack of index cards fanned out, "
                "a bottle of correction fluid with a happy face, a paper clip with googly eyes, "
                "a thumbtack with a star-shaped head, a small pencil holder cup with faces on pencils inside. "
                "Each sticker is approximately the same size, clean and detailed, kawaii chibi style. No text on stickers. Clean white background."
            ),
        },
        7: {
            'name': 'Subject Icons',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and soft cotton candy pink and blue pastel colors. "
                "Stickers include: a pink abacus with colorful beads for math, a round atom with orbiting electrons for science, "
                "an open book with a quill pen for English literature, a globe spinning with a happy face for geography, "
                "a paint palette with a brush and colorful blobs for art, a music note bubble with two eighth notes for music, "
                "a tiny Bunsen burner with a blue flame for chemistry, a calculator with a smiley screen for math, "
                "a DNA double helix strand for biology, a beaker with bubbling liquid for science, "
                "a small Greek column for history, a map scroll rolled open for social studies, "
                "a keyboard with music keys for music theory, a graph with plotted points for statistics, "
                "a tiny flag on a pin for geography, a test tube rack with three colorful tubes, "
                "a telescope pointed at a star for astronomy, a brain with a lightning bolt for psychology, "
                "a small computer screen with a cursor for technology, a language speech bubble with stars inside for languages. "
                "Each sticker is approximately the same size, clean and detailed, kawaii chibi style. No text on stickers. Clean white background."
            ),
        },
        8: {
            'name': 'Campus Life',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and soft cotton candy pink, sky blue, and cream pastel colors. "
                "Stickers include: a laptop with a kawaii screen and stickers on the lid, a takeaway coffee cup with a sleeve and happy face, "
                "a library building with columns and arched windows and a smiling face, a dorm room bunk bed with a tiny ladder, "
                "a small bicycle with a basket of books, a student ID card with a star, "
                "a cafeteria tray with a meal and drink, a grassy quad with a tree and bench, "
                "a bulletin board covered in pinned papers, a student planner open with a schedule, "
                "a headphones set around a small head with music notes, a tiny potted dorm plant on a windowsill, "
                "a laundry basket overflowing with clothes, a college pennant flag, "
                "a pop-up tent for studying outside, a small alarm clock showing early morning, "
                "a ramen cup with chopsticks for late-night studying, a desk with a monitor and coffee, "
                "a gym bag with a water bottle pocket, a graduation cap hanging on a peg. "
                "Each sticker is approximately the same size, clean and detailed, kawaii chibi style. No text on stickers. Clean white background."
            ),
        },
        9: {
            'name': 'Study Motivation',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and energetic pink, yellow, and blue pastel colors. "
                "Stickers include: a glowing lightbulb with a star burst and happy face for ideas, a small trophy with a star on top for achievement, "
                "a battery at 100% charge with a big smile for energy, a timer hourglass halfway through for focus time, "
                "a gold star burst badge for doing great, a checkmark in a pink circle for task complete, "
                "a tiny rocket lifting off for motivation, a flexed muscle arm for strength, "
                "a medal on a ribbon for working hard, a speech bubble with a heart inside for encouragement, "
                "a calendar page with a star marked day for goal day, a tiny mountain with a flag at the peak for reaching goals, "
                "a crown with gems for feeling like a champion, a sunrise with rays for a fresh start, "
                "a popcorn box for reward movie night, a thumbs up hand in a circle for approval, "
                "a small gift box with a bow for treating yourself, a progress bar almost full for near completion, "
                "a heart with wings for passion, a stack of coins building up for reward savings. "
                "Each sticker is approximately the same size, clean and detailed, kawaii chibi style. No text on stickers. Clean white background."
            ),
        },
        10: {
            'name': 'Back to School',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and fresh back-to-school pink, yellow, and blue pastel colors. "
                "Stickers include: a school bus in yellow with round windows and a happy face, a red school building with a bell tower, "
                "a metal locker with a combination dial and a bow on top, a fresh apple on a teacher's desk, "
                "a first-day-of-school sign held by tiny hands, a new clean notebook with no writing yet, "
                "a lunchbox with a fruit and sandwich inside, a hall pass on a lanyard, "
                "a class schedule sheet folded up, a chalkboard eraser with chalk dust, "
                "a small globe on a classroom desk, a world map rolled into a scroll, "
                "a paper plane made from a notebook page, a pop quiz paper with an A+ grade, "
                "a tiny clock showing 8am for first bell, a number line ruler for the classroom wall, "
                "a colorful alphabet block set, a science fair ribbon in first place, "
                "a school newspaper folded in half, a tiny school bell ringing with sound waves. "
                "Each sticker is approximately the same size, clean and detailed, kawaii chibi style. No text on stickers. Clean white background."
            ),
        },
        11: {
            'name': 'Academic Achievement',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and celebratory gold, pink, and pastel blue colors. "
                "Stickers include: a graduation mortarboard cap with a tassel swinging, a rolled diploma tied with a ribbon, "
                "a report card showing all A grades with a smile, a gold honor roll certificate with stars, "
                "a class ring with a gem and engraving, a dean's list letter in an envelope, "
                "a scholarship check with a star seal, a colorful confetti burst for celebrating, "
                "a stack of textbooks with a graduation cap on top, a proud owl in a tiny graduation gown, "
                "a champagne glass with apple cider and sparkles (non-alcoholic themed), "
                "a photo frame saying 'Class of 2026' with stars, a party hat with polka dots, "
                "a balloon bunch in school colors tied together, a gold star sticker seal of approval, "
                "a tiny podium with a first place plaque, a handshake between two small hands for networking, "
                "a university building with ivy growing on it, a professor's mortarboard with an apple on it, "
                "a pennant banner strung between two poles with stars. "
                "Each sticker is approximately the same size, clean and detailed, kawaii chibi style. No text on stickers. Clean white background."
            ),
        },
    },
    'DP1028': {
        6: {
            'name': 'Money & Finance',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and navy blue and gold pastel colors. "
                "Stickers include: a round gold coin stack with a smiley face, a pink piggy bank with a coin slot, "
                "a small wallet open showing cards and cash, a dollar bill folded into a fan shape, "
                "a credit card with a chip and stars, a receipt curling out of a register, "
                "a percentage sign badge with a sparkle for discounts, a bar chart growing upward with a happy face, "
                "a pie chart divided into colorful budget sections, a small safe with a dial lock and heart window, "
                "a money bag with a dollar sign and bow tie, a calculator displaying a number with eyes on the screen, "
                "an ATM machine with a card slot and smile, a small briefcase with a gold clasp, "
                "a bank building with columns and a clock, a savings jar with coins inside and a face, "
                "a line graph going up with a star at the peak, a checkbook with a pen resting on it, "
                "a cash register with a ding bell on top, a tiny vault door with a circular handle. "
                "Each sticker is approximately the same size, clean and detailed, kawaii chibi style. No text on stickers. Clean white background."
            ),
        },
        7: {
            'name': 'Savings Goals',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and hopeful gold, sky blue, and cream colors. "
                "Stickers include: a thermometer savings tracker filled halfway with a smile, a goal jar with coins and a label, "
                "a small house with a sold sign for home savings goal, a car with a bow on top for car fund goal, "
                "a suitcase with travel stickers for vacation fund, a diamond ring in a box for special savings, "
                "a graduation cap for education fund, a seedling growing into a money tree, "
                "a small investment graph with an upward arrow, a golden egg in a nest for nest egg savings, "
                "a treasure chest with a golden glow, a wishing well with a coin dropping in, "
                "a target bullseye with a coin in the center, a milestone flag on a path, "
                "a calendar with a circled savings date, a crystal clear piggy bank showing coins inside, "
                "a savings account book with a lock, a retirement sun setting peacefully, "
                "a gift to self wrapped with a ribbon, a cloud raining golden coins gently. "
                "Each sticker is approximately the same size, clean and detailed, kawaii chibi style. No text on stickers. Clean white background."
            ),
        },
        8: {
            'name': 'Debt Payoff',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and empowering navy, coral, and gold pastel colors. "
                "Stickers include: a pair of scissors cutting a credit card in half triumphantly, a chain link being broken free, "
                "a debt snowball rolling downhill getting bigger, an avalanche of coins tumbling down debt mountain, "
                "a zero balance display on a screen with confetti, a debt payoff thermometer reaching the top, "
                "a 'PAID IN FULL' stamp on a bill, a freedom bird flying out of a cage, "
                "a countdown calendar with last payment circled, a shredder eating a bill happily, "
                "a checkmark on a debt checklist, a before-and-after scale tipping to zero debt, "
                "a small victory podium with a coin on top, a tiny rocket escaping a ball and chain, "
                "a heart with wings free from financial stress, a sunrise over a debt-free horizon, "
                "a certificate of debt freedom with a seal, a piggy bank celebrating with confetti, "
                "a road map showing the final destination as debt free, a small party popper for every debt paid. "
                "Each sticker is approximately the same size, clean and detailed, kawaii chibi style. No text on stickers. Clean white background."
            ),
        },
        9: {
            'name': 'Budget Categories',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and organized navy and teal pastel colors. "
                "Stickers include: a grocery bag overflowing with vegetables and a smile, a house with a tiny heart for rent or mortgage, "
                "a power plug with electricity sparks for utilities, a car with a gas pump for transportation, "
                "a restaurant cloche with a lid for dining out, a movie ticket with stars for entertainment, "
                "a medical cross in a circle for healthcare, a clothing hanger with an outfit for clothing, "
                "a gift box with a bow for gifts and giving, a gym dumbbell for fitness expenses, "
                "a travel airplane for vacation budget, a book stack for education budget, "
                "a pet paw print for pet expenses, a phone with a signal bar for phone bill, "
                "a streaming remote for subscriptions, an umbrella over coins for insurance, "
                "a shopping bag with a price tag for personal spending, a baby bottle for family expenses, "
                "a flower pot for home decor fund, a coffee cup for daily treat budget. "
                "Each sticker is approximately the same size, clean and detailed, kawaii chibi style. No text on stickers. Clean white background."
            ),
        },
        10: {
            'name': 'Financial Wins',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and celebratory gold, navy, and green pastel colors. "
                "Stickers include: a trophy overflowing with gold coins, a confetti popper bursting with dollar signs, "
                "a bar chart hitting a new record high, a gold medal with a dollar coin design, "
                "a savings milestone flag at the top of a mountain, a happy wallet that is full and fat, "
                "a coin landing in a piggy bank with sparkles, a checkmark on a budget goal for the month, "
                "a thumbs up with a gold star on it, a crown made of coins for being a money boss, "
                "a tiny newspaper headline about financial success, a high-five between two small hands, "
                "a green arrow shooting upward for net worth increase, a balloon bunch for emergency fund complete, "
                "a certificate with a gold seal for first investment, a jar labeled 'VACATION FUND' full to the top, "
                "a star burst for no-spend day achievement, a smiley face bank account screen, "
                "a rainbow over a pot of gold coins, a fireworks burst for hitting a big savings milestone. "
                "Each sticker is approximately the same size, clean and detailed, kawaii chibi style. No text on stickers. Clean white background."
            ),
        },
        11: {
            'name': 'Smart Shopping',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and savvy navy, pink, and yellow pastel colors. "
                "Stickers include: a coupon being clipped with scissors and a happy face, a price tag with a sale percentage, "
                "a shopping list on a notepad with a pencil, a comparison scale weighing two prices, "
                "a cart with only needed items and a checkmark, a cashback coin flying back into a wallet, "
                "a store loyalty card with stars punched, a sale tag hanging on a rack, "
                "a bundle deal bow wrapping three items together, a price match stamp with a wink, "
                "a secondhand shop bag with a heart for thrifting, a meal prep container for saving on food, "
                "a flash sale clock counting down, a wish list scroll tied with a bow, "
                "a bulk buy box with a value badge, a referral bonus coin between two friends, "
                "a free shipping truck with stars, a returns receipt with a happy refund face, "
                "a smart phone showing a price comparison app, a rewards points star badge glowing. "
                "Each sticker is approximately the same size, clean and detailed, kawaii chibi style. No text on stickers. Clean white background."
            ),
        },
    },
    'DP1029': {
        6: {
            'name': 'Workout & Exercise',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and energetic coral, orange, and peach pastel colors. "
                "Stickers include: a pair of pink dumbbells with smiley faces, a yoga mat rolled up with a tiny lotus flower, "
                "a jump rope mid-swing with a happy face on the handles, a kettlebell with rosy cheeks, "
                "a resistance band stretched with a smile, a foam roller with a relaxed face, "
                "a punching bag with a tiny star, a pull-up bar with a character hanging from it, "
                "a bicycle with a water bottle in the holder, a running shoe mid-stride with motion lines, "
                "a swimming goggle with a splash, a tennis racket with a ball and stars, "
                "a soccer ball with hexagonal patches and rosy cheeks, a baseball glove holding a ball, "
                "a treadmill with a tiny character running, a gym bag with a towel hanging out, "
                "a stopwatch showing a personal record time, a heart rate monitor displaying a pulse, "
                "a protein shaker bottle with a star label, a medal on a ribbon for completing a workout. "
                "Each sticker is approximately the same size, clean and detailed, kawaii chibi style. No text on stickers. Clean white background."
            ),
        },
        7: {
            'name': 'Healthy Food & Nutrition',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and fresh coral, green, and peach pastel colors. "
                "Stickers include: a round avocado cut in half showing the pit with a smile, a broccoli floret with tiny arms and a happy face, "
                "a sliced watermelon wedge with seeds and rosy cheeks, a smoothie bowl topped with fruit and granola, "
                "a bunch of bananas with a kawaii face, a bowl of salad with a fork and sparkles, "
                "a glass of lemon water with a straw and bubbles, a small pot of overnight oats with berries, "
                "a protein bar with a star wrapper, a carrot with leafy top and a winking face, "
                "an egg sunny side up with a smiley yolk, a bowl of brown rice with a chopstick pair, "
                "a green matcha smoothie cup with a straw, a small mason jar of meal prep with a lid, "
                "a nutrition label with a happy checkmark, a colorful veggie wrap rolled up, "
                "a blueberry bunch with tiny faces, a red apple with a heart cut into it, "
                "a handful of almonds in a small bowl, a tall glass of milk with a moustache foam. "
                "Each sticker is approximately the same size, clean and detailed, kawaii chibi style. No text on stickers. Clean white background."
            ),
        },
        8: {
            'name': 'Wellness & Self-Care',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and calming coral, peach, and sage green colors. "
                "Stickers include: a cozy sleep mask with ZZZ floating above it, a glass of water with eight cups marked for hydration tracking, "
                "a moon and stars for a good night's sleep sticker, a sunrise for morning routine, "
                "a small journal open to a gratitude page with a heart, a meditation figure sitting in lotus pose, "
                "a warm herbal tea mug with steam and a smile, a bubble bath with rubber duck and suds, "
                "a small pill organizer for vitamins and supplements, a stretching figure doing a side bend, "
                "a heart rate calm icon with peaceful waves, a nature walk scene with trees and a path, "
                "a breathing exercise circle expanding and contracting, a positive affirmation scroll, "
                "a gentle yoga pose silhouette with a sun behind, a cozy blanket wrap figure, "
                "a soft diffuser with essential oil mist, a face serum with a glow effect, "
                "a massage tool with relaxation lines, a calendar marking a rest day with a heart. "
                "Each sticker is approximately the same size, clean and detailed, kawaii chibi style. No text on stickers. Clean white background."
            ),
        },
        9: {
            'name': 'Progress & Tracking',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and motivating coral, gold, and peach pastel colors. "
                "Stickers include: a progress bar filling up with a smiley face, a weight scale with a heart on the display, "
                "a body measurement tape curled with a bow, a before and after comparison mirror, "
                "a habit streak calendar with fire on day 30, a step counter showing 10000 steps with stars, "
                "a personal record trophy with a lightning bolt, a miles run badge with a runner icon, "
                "a calories burned flame with a happy face, a hydration tracker water glass filling up, "
                "a sleep hours moon chart with Zs, a flexibility measurement doing a split, "
                "a BMI chart showing a healthy range highlight, a muscle gain arm flexing bigger, "
                "a resting heart rate heart slowing to calm, a recovery star for rest day success, "
                "a photo progress polaroid strip, a fitness journal with a pencil writing entries, "
                "a milestone marker flag at a distance marker, a transformation star burst for visible results. "
                "Each sticker is approximately the same size, clean and detailed, kawaii chibi style. No text on stickers. Clean white background."
            ),
        },
        10: {
            'name': 'Sports & Activities',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and active coral, sky blue, and white pastel colors. "
                "Stickers include: a surfboard standing upright with a wave design, a pair of ice skates with lace bows, "
                "a rock climbing hold with a tiny hand gripping it, a kayak paddle with water droplets, "
                "a skiing figure going downhill with a scarf, a gymnastics ribbon twirling in a loop, "
                "a hiking boot with a mountain behind it, a volleyball mid-air with a smiling face, "
                "a basketball going through a hoop with a swish, a badminton birdie with feathers, "
                "a martial arts black belt tied in a bow, a horse with a rider in equestrian hat, "
                "a dance shoe with a bow and music note, a golf ball on a tee with a flag, "
                "a rowing oar in the water with ripples, a frisbee spinning with a grin, "
                "a trampoline with a bouncing figure mid-air, a boxing glove with a star impact, "
                "a lacrosse stick with a ball in the net, a relay race baton being passed. "
                "Each sticker is approximately the same size, clean and detailed, kawaii chibi style. No text on stickers. Clean white background."
            ),
        },
        11: {
            'name': 'Fitness Wins',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and celebratory coral, gold, and peach pastel colors. "
                "Stickers include: a first place medal with a muscle arm on it, a confetti burst for hitting a new PR, "
                "a trophy with a dumbbell on the top, a before-and-after star transformation, "
                "a streak fire badge for 30 days of workouts, a finish line ribbon being crossed, "
                "a checkmark on a fitness challenge completed, a star badge for consistent effort, "
                "a winner podium with a tiny figure on the top step, a high five between two workout gloves, "
                "a glowing progress thermometer at 100 percent, a tiny newspaper headline celebrating a goal, "
                "a body silhouette with a heart glow of health, a sweat drop turning into a sparkle, "
                "a mountain peak with a sunrise for reaching fitness goals, a cheer pompom for celebrating progress, "
                "a running figure crossing a finish flag, a crown made of protein bars and dumbbells, "
                "a 'NEW PR' burst badge with lightning bolts, a heart rate screen showing peak performance. "
                "Each sticker is approximately the same size, clean and detailed, kawaii chibi style. No text on stickers. Clean white background."
            ),
        },
    },
}


def gen_sticker_sheet(pid, sheet_num):
    info = SHEET_PROMPTS[pid][sheet_num]
    name = info['name']
    prompt = info['prompt']

    out_path = os.path.join(ART_DIR, f'{pid}_sticker_sheet_{sheet_num}.jpg')
    print(f"\nGenerating {pid} Sheet {sheet_num}: {name}")
    print(f"Output: {out_path}")

    payload = json.dumps({
        "model": "gpt-image-1",
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024",
        "quality": "high",
        "output_format": "jpeg"
    }).encode()

    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_KEY}"},
        method="POST"
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
            img_bytes = base64.b64decode(data["data"][0]["b64_json"])
            with open(out_path, "wb") as f:
                f.write(img_bytes)
            print(f"  Saved: {os.path.basename(out_path)} ({len(img_bytes)//1024}KB)")
            return out_path
        except Exception as e:
            if attempt < 2:
                print(f"  Retry {attempt+1}: {e}")
                time.sleep(20)
            else:
                print(f"  FAILED: {e}")
                return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pid', required=True)
    parser.add_argument('--sheet', type=int, required=True)
    args = parser.parse_args()
    gen_sticker_sheet(args.pid, args.sheet)
