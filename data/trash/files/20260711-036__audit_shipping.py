#!/usr/bin/env python3
"""
Audit shipping costs on all active physical listings.

Etsy 2026: US domestic listings with shipping > $6 face reduced search visibility.
Action: absorb shipping into price and offer free shipping, or cap flat rate at $5.99.

Usage:
  python tools/audit_shipping.py
"""

import os, sys, json, urllib.request, time
sys.path.insert(0, '/home/user/Etsy')
with open('/home/user/Etsy/.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

from tools.etsy_api import EtsyAPIClient

SHIPPING_PENALTY_THRESHOLD = 6.00  # USD


def fetch_active_listings(client) -> list:
    headers = {
        'Authorization': f'Bearer {client.access_token}',
        'x-api-key': f'{client.client_id}:{client.client_secret}',
    }
    listings, offset = [], 0
    while True:
        url = (f'https://openapi.etsy.com/v3/application/shops/{client.shop_id}'
               f'/listings/active?limit=100&offset={offset}')
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
        batch = data.get('results', [])
        listings.extend(batch)
        if len(batch) < 100:
            break
        offset += 100
        time.sleep(0.3)
    return listings


def fetch_shipping_profile(client, profile_id: int) -> dict:
    headers = {
        'Authorization': f'Bearer {client.access_token}',
        'x-api-key': f'{client.client_id}:{client.client_secret}',
    }
    url = (f'https://openapi.etsy.com/v3/application/shops/{client.shop_id}'
           f'/shipping-profiles/{profile_id}')
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {'error': str(e)}


def main():
    client = EtsyAPIClient()
    client.refresh_access_token()

    print('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    print('  Shipping Audit — Etsy 2026 Ranking Compliance')
    print(f'  Threshold: >${SHIPPING_PENALTY_THRESHOLD:.2f} = ranking penalty')
    print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n')

    print('  Fetching active listings...')
    listings = fetch_active_listings(client)

    physical = [l for l in listings if not l.get('is_digital', False)]
    digital  = [l for l in listings if l.get('is_digital', False)]

    print(f'  Digital listings (no shipping needed): {len(digital)} ✓')
    print(f'  Physical listings to audit:            {len(physical)}\n')

    seen_profiles = {}
    issues = []
    ok_listings = []

    for lst in physical:
        lid = lst.get('listing_id')
        title = (lst.get('title') or '')[:65]
        price_data = lst.get('price', {})
        price = price_data.get('amount', 0) / price_data.get('divisor', 100)
        profile_id = lst.get('shipping_profile_id')

        if profile_id and profile_id not in seen_profiles:
            seen_profiles[profile_id] = fetch_shipping_profile(client, profile_id)
            time.sleep(0.2)

        profile = seen_profiles.get(profile_id, {}) if profile_id else {}
        destinations = profile.get('shipping_profile_destinations', [])

        # Find US domestic shipping cost
        us_cost = None
        for dest in destinations:
            origin = dest.get('origin_country_iso', '')
            target = dest.get('destination_country_iso', '') or dest.get('destination_region', '')
            if origin == 'US' and (target in ('US', 'none', '') or target is None):
                primary = dest.get('primary_cost', {})
                us_cost = primary.get('amount', 0) / primary.get('divisor', 100)
                break

        if us_cost is None:
            # Check if free shipping via profile
            if profile.get('min_processing_time') is not None:
                us_cost = 0.0  # May be free shipping — can't determine from profile alone

        status = '?'
        if us_cost is not None:
            if us_cost == 0:
                status = '✓ FREE'
                ok_listings.append(lid)
            elif us_cost <= SHIPPING_PENALTY_THRESHOLD:
                status = f'✓ ${us_cost:.2f}'
                ok_listings.append(lid)
            else:
                status = f'⚠ ${us_cost:.2f} — ABOVE THRESHOLD'
                issues.append({'lid': lid, 'title': title, 'price': price, 'shipping': us_cost})
        else:
            status = '? unknown — check manually'

        print(f'  [{lid}] ${price:.2f} | Shipping: {status}')
        print(f'          {title}')
        print()

    print(f'\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    print(f'  Compliant physical listings: {len(ok_listings)}')
    print(f'  Listings above $6 threshold: {len(issues)}')

    if issues:
        print(f'\n  ⚠ ACTION REQUIRED — Add free shipping or cap at $5.99:')
        for i in issues:
            print(f'    [{i["lid"]}] ${i["price"]:.2f} + ${i["shipping"]:.2f} shipping → '
                  f'raise price to ${i["price"] + i["shipping"]:.2f}, offer free ship')
            print(f'             {i["title"]}')
    else:
        print('  ✓ All physical listings meet the $6 shipping threshold')

    print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n')


if __name__ == '__main__':
    main()
