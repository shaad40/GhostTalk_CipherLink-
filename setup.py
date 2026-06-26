"""
CipherLink — Auto Setup
"""
import os, sys, platform, subprocess

def c(text, color):
    if platform.system() == "Windows": return text
    cols = {"g":"\033[92m","r":"\033[91m","y":"\033[93m","b":"\033[96m","d":"\033[2m","R":"\033[0m","B":"\033[1m"}
    return f"{cols.get(color,'')}{text}{cols['R']}"

def log(m):  print(c(f"  [*] {m}","b"))
def ok(m):   print(c(f"  [+] {m}","g"))
def err(m):  print(c(f"  [!] {m}","r"))
def warn(m): print(c(f"  [~] {m}","y"))
def run(cmd):
    r = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return r.returncode == 0, r.stdout.strip(), r.stderr.strip()

def banner():
    print(c("""
  ╔══════════════════════════════════════╗
  ║        CipherLink — Auto Setup       ║
  ║   AES-256 + ChaCha20 Encrypted Chat  ║
  ╚══════════════════════════════════════╝
""","g"))

def detect_os():
    s = platform.system()
    if s == "Linux":
        ok2, out, _ = run("cat /etc/os-release 2>/dev/null")
        if ok2 and "kali" in out.lower(): return "kali"
        return "linux"
    elif s == "Windows": return "windows"
    elif s == "Darwin":  return "mac"
    return "unknown"

def check_python():
    v = sys.version_info
    log(f"Python {v.major}.{v.minor}.{v.micro} detected")
    if v.major < 3 or (v.major == 3 and v.minor < 8):
        err("Python 3.8+ দরকার!"); sys.exit(1)
    ok("Python version OK")

def install_libs(os_type):
    print(c("\n  ▓ Python libraries install করছি...","B"))
    libs = ["websockets", "cryptography"]
    for lib in libs:
        log(f"{lib} install হচ্ছে...")
        if os_type == "kali":
            s,_,e = run(f"{sys.executable} -m pip install {lib} --break-system-packages -q")
        else:
            s,_,e = run(f"{sys.executable} -m pip install {lib} -q")
        if s: ok(f"{lib} ✓")
        else: warn(f"{lib} manually install করো: pip install {lib}")

def install_tor(os_type):
    print(c("\n  ▓ Tor install করছি...","B"))
    if os_type in ("kali","linux"):
        s,_,_ = run("which tor")
        if s: ok("Tor already installed!"); return
        log("Tor install হচ্ছে...")
        run("sudo apt-get update -qq && sudo apt-get install -y tor")
        s2,_,_ = run("which tor")
        if s2: ok("Tor installed!")
        else: warn("Tor manually install করো: sudo apt install tor -y")
    elif os_type == "mac":
        s,_,_ = run("which tor")
        if s: ok("Tor already installed!"); return
        s2,_,_ = run("which brew")
        if s2: run("brew install tor"); ok("Tor installed!")
        else: warn("Homebrew install করো তারপর: brew install tor")
    else:
        ok("Windows-এ Tor Browser ব্যবহার করো (optional)")

def check_files(os_type):
    print(c("\n  ▓ Files check করছি...","B"))
    d = os.path.dirname(os.path.abspath(__file__))
    needed = ["server.py"] if os_type in ("kali","linux","mac") else ["client.py"]
    all_ok = True
    for fn in needed:
        path = os.path.join(d, fn)
        if os.path.exists(path): ok(f"{fn} পাওয়া গেছে ✓")
        else: err(f"{fn} পাওয়া যায়নি — একই folder-এ রাখো"); all_ok = False
    return all_ok

def instructions(os_type):
    print(c("""
  ╔══════════════════════════════════════╗
  ║         SETUP COMPLETE! ✓            ║
  ╚══════════════════════════════════════╝""","g"))
    if os_type in ("kali","linux","mac"):
        print(c("""
  তোমার কাজ (Server):
  ──────────────────────────────────────
  1. python3 server.py চালাও
  2. নাম ও port দাও, Session Key দেখাবে
  3. ngrok চালাও:
     ngrok http --domain=anything-elsewhere-verse.ngrok-free.dev <port>
  4. Session Key বন্ধুকে পাঠাও
  5. বন্ধু connect করলে chat শুরু!
""","b"))
    else:
        print(c("""
  তোমার কাজ (Client):
  ──────────────────────────────────────
  1. python client.py চালাও
  2. নাম, port ও Session Key দাও
  3. CONNECT চাপলেই chat শুরু!
""","b"))
    print(c("  ⚠  প্রতিবার server চালু হলে নতুন Session Key আসবে\n","y"))

def main():
    banner()
    os_type = detect_os()
    names = {"kali":"Kali Linux","linux":"Linux","windows":"Windows","mac":"macOS","unknown":"Unknown"}
    print(c(f"\n  ▓ OS Detect","B"))
    ok(f"{names.get(os_type,'Unknown')} detected")
    if os_type == "unknown":
        err("OS চেনা গেল না!"); sys.exit(1)

    check_python()
    install_libs(os_type)
    install_tor(os_type)
    check_files(os_type)
    instructions(os_type)

if __name__ == "__main__":
    main()
