import subprocess

print("Installing Playwright browsers...")
subprocess.run(["playwright", "install"], check=True)
