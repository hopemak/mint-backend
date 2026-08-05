#!/bin/bash

echo "========================================="
echo "📊 COMPLETE API VERIFICATION"
echo "========================================="

cd ~/Documents/Mint-incubator/mint-platform/backend

echo ""
echo "📁 1. ROUTE FILES"
echo "-----------------------------------------"
ls -1 app/routes/*.py 2>/dev/null | wc -l
echo "route files found"

echo ""
echo "📊 2. API ENDPOINTS"
echo "-----------------------------------------"
python -c "
from app import create_app
app = create_app()
count = 0
for rule in app.url_map.iter_rules():
    if '/api/' in str(rule):
        count += 1
print(f'Total: {count} APIs')
"

echo ""
echo "📋 3. API LIST"
echo "-----------------------------------------"
python -c "
from app import create_app
app = create_app()
for rule in sorted(app.url_map.iter_rules()):
    methods = ','.join(rule.methods - {'HEAD', 'OPTIONS'})
    if '/api/' in str(rule):
        print(f'{methods:10} {rule}')
"

echo ""
echo "📊 4. API COUNT BY MODULE"
echo "-----------------------------------------"
python -c "
from app import create_app
app = create_app()

modules = {
    'auth': [],
    'users': [],
    'startups': [],
    'funding': [],
    'grants': [],
    'ml': [],
    'mentors': [],
    'dashboard': [],
    'documents': []
}

for rule in app.url_map.iter_rules():
    url = str(rule)
    if '/api/' in url:
        for module in modules.keys():
            if f'/api/{module}' in url:
                modules[module].append(url)
                break

total = 0
for module, routes in modules.items():
    count = len(routes)
    total += count
    print(f'{module.capitalize():12} : {count:2} APIs')

print(f'{"TOTAL":12} : {total:2} APIs')
"

echo ""
echo "========================================="
echo "✅ VERIFICATION COMPLETE"
echo "========================================="
