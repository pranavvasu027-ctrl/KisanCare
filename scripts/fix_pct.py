with open('frontend/src/screens/FarmEconomics/FarmEconomics.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

# Add pct field to each item
items_old = """            {[
              { name: 'Labour (Intercultural operations)', val: '₹50,000', ambiguity: 'Period & area basis unclear', color: 'bg-[#B6532A]' },
              { name: 'Other Cost (yechan)', val: '₹40,000', ambiguity: 'Local dialect entry; category clarification pending', color: 'bg-[#E5DDCF]' },
              { name: 'Fertilizers (Bulk unitemized)', val: '₹20,000', ambiguity: 'Reported as ~₹20,000+ without component split', color: 'bg-[#A8C69A]' },
              { name: 'Machinery (Rental & fuel)', val: '₹20,000', ambiguity: 'Basis unclear', color: 'bg-[#17643E]' },
              { name: 'Seed Cost (godavari)', val: '₹11,000', ambiguity: 'Range ₹10k–12k; whole farm vs Field A unclear', color: 'bg-[#17643E]' },
              { name: 'Land Preparation', val: '₹10,000', ambiguity: 'Reported total', color: 'bg-[#E5DDCF]' },
              { name: 'Transport (To Akot APMC)', val: '₹5,000', ambiguity: 'Basis unclear', color: 'bg-[#B6532A]' },
              { name: 'Pesticide Application', val: '₹10', ambiguity: 'Preserved verbatim; likely recording anomaly for ₹10,000', color: 'bg-red-400' },
            ].map(item => ("""

items_new = """            {[
              { name: 'Labour (Intercultural operations)', val: '₹50,000', pct: 32, ambiguity: 'Period & area basis unclear', color: 'bg-[#B6532A]' },
              { name: 'Other Cost (yechan)', val: '₹40,000', pct: 26, ambiguity: 'Local dialect entry; category clarification pending', color: 'bg-[#E5DDCF]' },
              { name: 'Fertilizers (Bulk unitemized)', val: '₹20,000', pct: 13, ambiguity: 'Reported as ~₹20,000+ without component split', color: 'bg-[#A8C69A]' },
              { name: 'Machinery (Rental & fuel)', val: '₹20,000', pct: 13, ambiguity: 'Basis unclear', color: 'bg-[#17643E]' },
              { name: 'Seed Cost (godavari)', val: '₹11,000', pct: 7, ambiguity: 'Range ₹10k–12k; whole farm vs Field A unclear', color: 'bg-[#17643E]' },
              { name: 'Land Preparation', val: '₹10,000', pct: 6, ambiguity: 'Reported total', color: 'bg-[#E5DDCF]' },
              { name: 'Transport (To Akot APMC)', val: '₹5,000', pct: 3, ambiguity: 'Basis unclear', color: 'bg-[#B6532A]' },
              { name: 'Pesticide Application', val: '₹10', pct: 1, ambiguity: 'Preserved verbatim; likely recording anomaly for ₹10,000', color: 'bg-red-400' },
            ].map(item => ("""

if items_old in c:
    c = c.replace(items_old, items_new)

with open('frontend/src/screens/FarmEconomics/FarmEconomics.tsx', 'w', encoding='utf-8') as f:
    f.write(c)

print('Updated FarmEconomics items with pct')
