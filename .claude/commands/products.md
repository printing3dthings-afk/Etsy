List all OnBrandCraftz products and their current status.

Run these steps in order:

1. Call `get_approved_unlisted_products` to see products pending listing on Etsy
2. Call `list_etsy_listings` with state "active" to get live Etsy listings
3. Call `list_etsy_listings` with state "draft" to get draft listings

Then output a clean summary table:

**Active Etsy Listings:**
| Product | Listing ID | Price | Views | Title (first 50 chars) |
|---------|-----------|-------|-------|------------------------|
(one row per active listing)

**Draft Listings:**
(list any drafts with their IDs and titles)

**Pending (ready to list but not yet on Etsy):**
(list any products from get_approved_unlisted_products)

End with a one-line status: how many products are live, how many are pending, and what the next recommended action is.
