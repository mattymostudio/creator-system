#!/usr/bin/env python3
"""
Build a combined contacts CSV for MM extraction.
Merges: VCF from MM Takeout + yourcompany contacts + yourbrand contacts + Google Contacts CSV.
"""
import csv
import re
import sys

emails = set()

# 1. Parse VCF
vcf_path = "MM Takeout/Takeout 2/Contacts/All Contacts/All Contacts.vcf"
try:
    with open(vcf_path, 'r', errors='replace') as f:
        for line in f:
            if line.upper().startswith('EMAIL'):
                # EMAIL;TYPE=INTERNET;TYPE=HOME:someone@example.com
                parts = line.strip().split(':')
                if len(parts) >= 2:
                    addr = parts[-1].strip().lower()
                    if '@' in addr and len(addr) > 5:
                        emails.add(addr)
    print(f"VCF contacts: {len(emails)}")
except FileNotFoundError:
    print(f"VCF not found: {vcf_path}")

# 2. yourcompany contacts
vcf_count = len(emails)
try:
    with open('yourcompany_contacts_clean.csv', 'r') as f:
        for row in csv.DictReader(f):
            addr = row.get('email', '').strip().lower()
            if '@' in addr:
                emails.add(addr)
    print(f"After yourcompany: {len(emails)} (+{len(emails) - vcf_count})")
except FileNotFoundError:
    print("yourcompany_contacts_clean.csv not found")

# 3. YOURBRAND contacts
prev = len(emails)
try:
    with open('yourbrand_contacts_clean.csv', 'r') as f:
        for row in csv.DictReader(f):
            addr = row.get('email', '').strip().lower()
            if '@' in addr:
                emails.add(addr)
    print(f"After yourbrand: {len(emails)} (+{len(emails) - prev})")
except FileNotFoundError:
    print("yourbrand_contacts_clean.csv not found")

# 4. Google Contacts CSV (different column names)
prev = len(emails)
try:
    with open('contacts.csv', 'r') as f:
        for row in csv.DictReader(f):
            for key in row:
                if 'mail' in key.lower() and 'value' in key.lower():
                    addr = row[key].strip().lower()
                    if '@' in addr and len(addr) > 5:
                        emails.add(addr)
    print(f"After Google Contacts CSV: {len(emails)} (+{len(emails) - prev})")
except FileNotFoundError:
    print("contacts.csv not found")

# Filter out the user's own addresses and obvious automation
MATTS_EMAILS = {
    'you@yourcompany.example', 'you@yourcompany.example',
    'you@yourdomain.example', 'you-personal@example.com',
    'you@yourcompany.example', 'your-handle@gmail.example',
}
emails -= MATTS_EMAILS

# Write output
out_path = 'mm_contacts_input.csv'
with open(out_path, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['email'])
    for addr in sorted(emails):
        w.writerow([addr])

print(f"\nTotal unique emails: {len(emails)}")
print(f"Written to {out_path}")
