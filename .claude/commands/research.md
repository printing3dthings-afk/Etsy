Research a keyword or product niche on Etsy and return actionable competitive intelligence for OnBrandCraftz.

The argument to this command is the search query to research: $ARGUMENTS

Steps:
1. Call the `search_etsy` tool with the query "$ARGUMENTS" and limit 15
2. Analyze the results and extract:
   - **Price range**: min, max, and most common price point
   - **Title patterns**: what keywords appear most in competitor titles
   - **Missing keywords**: what terms competitors use that OnBrandCraftz listings may be missing
   - **Review counts**: which listings have the most reviews (proxy for best sellers)
   - **Gaps**: anything the top sellers offer that OnBrandCraftz doesn't (cover count, sticker count, formats, etc.)
3. Compare against our known products: DP1026 ($14.99), DP1027 ($9.99), DP1028 ($12.99), DP1029 ($12.99)
4. Output a concise brief:
   - Top 3 price insights
   - Top 3 keyword opportunities
   - 1-2 product gap observations
   - Recommended next action (e.g., add a tag, adjust price, create new product)

Be specific. Numbers over vague impressions. If Etsy is blocked in this environment, note that and provide what analysis you can from the search structure.
