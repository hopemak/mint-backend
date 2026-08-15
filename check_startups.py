import os, glob, re

base = os.path.expanduser('~/Documents/Mint-incubator/mint-platform')

# 1. Frontend Startups page
startup_files = glob.glob(os.path.join(base, '**/Startups.jsx'), recursive=True) + \
               glob.glob(os.path.join(base, '**/Startup.jsx'), recursive=True) + \
               glob.glob(os.path.join(base, '**/startup.jsx'), recursive=True)
print("=== FRONTEND STARTUP FILES ===")
for f in startup_files:
    print("  ", f)

if startup_files:
    with open(startup_files[0], 'r', encoding='utf-8') as f:
        frontend = f.read()
    print(f"\nSize: {len(frontend)} chars")
    
    print("\n--- Imports ---")
    for line in frontend.split('\n')[:30]:
        if line.strip():
            print(line[:100])
    
    print("\n--- API calls ---")
    for m in re.finditer(r"(startupAPI|useApiData|fetch|axios)\.\w+\(.*?\)|useApiData\(.*?\)", frontend):
        print(m.group(0))
    
    print("\n--- Data fields used ---")
    fields = set()
    for m in re.finditer(r'startup\.(\w+)|data\.(\w+)', frontend):
        fields.add(m.group(1) or m.group(2))
    for f in sorted(fields):
        if f:
            print(f"  - {f}")
else:
    print("❌ No Startups.jsx found")

# 2. Backend startups.py
startup_backend = os.path.join(base, 'backend/app/routes/startups.py')
if os.path.exists(startup_backend):
    with open(startup_backend, 'r', encoding='utf-8') as f:
        backend = f.read()
    print("\n=== BACKEND startups.py ===")
    print(f"Size: {len(backend)} chars")
    
    print("\n--- Routes ---")
    for m in re.finditer(r'@startups_bp\.route.*?\n.*?def .*?\(.*?\):.*?(?=\n@startups_bp|\Z)', backend, re.DOTALL):
        print(m.group(0)[:250])
        print("---")
    
    print("\n--- Create function fields ---")
    m = re.search(r'def create_startup.*?(?=def |\Z)', backend, re.DOTALL)
    if m:
        print(m.group(0)[:800])
else:
    print("\n❌ backend/app/routes/startups.py not found")

# 3. api.js for startupAPI
print("\n=== api.js startupAPI ===")
with open('src/services/api.js', 'r', encoding='utf-8') as f:
    api = f.read()
start = api.find('startupAPI = {')
if start != -1:
    end = api.find('}', start) + 1
    print(api[start:end])
else:
    print("startupAPI not found")
