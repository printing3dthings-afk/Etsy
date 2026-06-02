# Printify Setup Guide — OnBrandCraftz

## Step 1: Create Your Printify Account
1. Go to printify.com
2. Click "Get started for free"
3. Sign up with your email (Printing3dthings@outlook.com)
4. Complete your profile

## Step 2: Generate Your API Key
1. Click your profile icon (top right)
2. Go to "My Profile" → "Connections"
3. Click "API" tab
4. Click "Generate new token"
5. Copy the token

## Step 3: Add API Key to .env
Open your .env file and add:
```
PRINTIFY_API_KEY=your_token_here
```

## Step 4: Connect Your Etsy Store
1. In Printify, go to "My Stores"
2. Click "Add new store"
3. Select "Etsy"
4. Authorize the connection

## Step 5: Submit Your Products
```bash
python tools/printify_publisher.py --status       # verify connection
python tools/printify_publisher.py --submit-all   # submit all 55 wall art prints
```

## What Happens When an Order Comes In
1. Customer orders on Etsy
2. Printify receives the order automatically (via Etsy integration)
3. Printify prints and ships directly to customer
4. You receive Etsy payment minus Printify cost
5. You never touch the order

## Pricing Reference
| Size | Printify Cost | Your Etsy Price | Your Profit |
|------|--------------|-----------------|-------------|
| 8×10" | $8.45 | $19.99 | ~$9.00 |
| 12×16" | $12.25 | $27.99 | ~$12.00 |
| 18×24" | $17.80 | $39.99 | ~$18.00 |

Note: Etsy also charges 6.5% transaction fee + $0.20 listing fee.
Net profit after all fees: ~$7–15 per sale depending on size.

## Products Ready to Submit
See: data/printify/products_queue.json
55 wall art files are queued and ready.
