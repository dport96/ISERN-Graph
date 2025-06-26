import sys

def check_package(package_name):
    try:
        __import__(package_name)
        print(f"✅ {package_name}")
        return True
    except ImportError:
        print(f"❌ {package_name} - NOT INSTALLED")
        return False

print("Python Installation Verification")
print(f"Python version: {sys.version}")
print("\nChecking required packages:")

packages = [
    'pandas', 'numpy', 'matplotlib', 'seaborn', 
    'networkx', 'plotly', 'requests', 'bs4', 
    'lxml', 'openpyxl', 'scipy', 'tqdm'
]

all_good = True
for package in packages:
    if not check_package(package):
        all_good = False

if all_good:
    print("\n🎉 All packages installed successfully!")
else:
    print("\n⚠️  Some packages are missing. Run: pip install -r requirements.txt")
