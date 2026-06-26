import subprocess, sys, os, threading, asyncio, json, base64, time

for lib in ["websockets","cryptography"]:
    try: __import__(lib)
    except ImportError:
        subprocess.check_call([sys.executable,"-m","pip","install",lib,"-q"])

import tkinter as tk
from tkinter import filedialog, messagebox
import websockets
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, padding as sym_pad
from cryptography.hazmat.backends import default_backend

SALT = b"sc_salt_v3"

def derive(pw):
    def k(s):
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(),length=32,salt=s,iterations=100000,backend=default_backend())
        return kdf.derive(pw.encode())
    return k(SALT), k(SALT+b"2")

def enc(txt, ak, ck):
    iv = os.urandom(16)
    c  = Cipher(algorithms.AES(ak), modes.CBC(iv), backend=default_backend())
    e  = c.encryptor()
    p  = sym_pad.PKCS7(128).padder()
    pd = p.update(txt.encode()) + p.finalize()
    at = iv + e.update(pd) + e.finalize()
    ch = ChaCha20Poly1305(ck); n = os.urandom(12)
    return base64.b64encode(n + ch.encrypt(n, at, None)).decode()

def dec(ct, ak, ck):
    r  = base64.b64decode(ct); n = r[:12]
    ch = ChaCha20Poly1305(ck); at = ch.decrypt(n, r[12:], None)
    iv, c = at[:16], at[16:]
    ci = Cipher(algorithms.AES(ak), modes.CBC(iv), backend=default_backend())
    d  = ci.decryptor(); u = sym_pad.PKCS7(128).unpadder()
    pd = d.update(c) + d.finalize()
    return (u.update(pd) + u.finalize()).decode()

BG    = "#0d0d14"
BG2   = "#12121e"
BG3   = "#1a1a2a"
GREEN = "#00ff88"
BLUE  = "#4488ff"
DIM   = "#555577"
WHITE = "#e0e0ff"
RED   = "#ff4466"
YEL   = "#ffcc44"
GME   = "#0a200a"
GFR   = "#0a0a20"
FONT  = ("Segoe UI", 11)
MONO  = ("Courier New", 10)

NGROK = "anything-elsewhere-verse.ngrok-free.dev"

class ClientApp:
    def __init__(self, root):
        self.root   = root
        self.root.withdraw()
        self.ws     = None
        self.loop   = None
        self.tjob   = None
        self.myname = ""
        self.akey = self.ckey = None
        self._setup_dialog()

    def _setup_dialog(self):
        win = tk.Toplevel(self.root)
        win.title("Connect")
        win.configure(bg=BG)
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text="SECRET CHAT", font=("Courier New",18,"bold"),
                 bg=BG, fg=BLUE).pack(pady=(28,4))
        tk.Label(win, text="Server-এ connect করো", font=MONO,
                 bg=BG, fg=DIM).pack(pady=(0,20))

        def row(label, default="", show=None, fg=WHITE):
            f = tk.Frame(win, bg=BG)
            f.pack(fill="x", padx=40, pady=5)
            tk.Label(f, text=label, font=("Courier New",9),
                     bg=BG, fg=DIM).pack(anchor="w", pady=(0,3))
            inner = tk.Frame(f, bg=BG3)
            inner.pack(fill="x")
            kw = dict(font=("Courier New",11), bg=BG3, fg=fg,
                      insertbackground=BLUE, relief="flat", bd=0)
            if show: kw["show"] = show
            e = tk.Entry(inner, **kw)
            e.pack(fill="x", ipady=8, padx=8)
            if default: e.insert(0, default)
            return e

        name_e = row("তোমার নাম")
        port_e = row("Port", "5000", fg=YEL)
        key_e  = row("Session Key", show="●")

        tk.Frame(win, bg=BG).pack(pady=6)

        def go():
            nm  = name_e.get().strip()
            pt  = port_e.get().strip()
            key = key_e.get().strip()
            if not nm:
                messagebox.showwarning("!","নাম দাও"); return
            if not pt:
                messagebox.showwarning("!","Port দাও"); return
            if not key:
                messagebox.showwarning("!","Session Key দাও"); return
            try: int(pt)
            except: messagebox.showwarning("!","Port number হতে হবে"); return
            self.myname = nm
            self.akey, self.ckey = derive(key)
            win.destroy()
            self.root.deiconify()
            self._build()
            self._start(pt)

        btn_wrap = tk.Frame(win, bg=BLUE, padx=1, pady=1)
        btn_wrap.pack(fill="x", padx=40, pady=(4,28))
        tk.Button(btn_wrap, text="CONNECT", font=("Courier New",11,"bold"),
                  bg=BG2, fg=BLUE, relief="flat", cursor="hand2",
                  activebackground=BG3, activeforeground=BLUE,
                  pady=10, command=go).pack(fill="x")

        win.update_idletasks()
        w,h = 440,430
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build(self):
        self.root.title(f"Secret Chat — Client  [{self.myname}]")
        self.root.configure(bg=BG)
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w,h = 640,760
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.root.minsize(500,500)
        self.root.resizable(True, True)

        # ── Header ──
        hdr = tk.Frame(self.root, bg=BG2, height=58)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="SECRET CHAT", font=("Courier New",14,"bold"),
                 bg=BG2, fg=BLUE).pack(side="left", padx=16, pady=14)
        tk.Label(hdr, text=f"[ {self.myname} ]  //  CLIENT",
                 font=MONO, bg=BG2, fg=DIM).pack(side="left", pady=14)
        self.dot = tk.Label(hdr, text="⬤  OFFLINE",
                            font=("Courier New",9,"bold"), bg=BG2, fg=RED)
        self.dot.pack(side="right", padx=16, pady=14)
        tk.Frame(self.root, bg=BLUE, height=2).pack(fill="x")

        # ── Chat canvas ──
        chat = tk.Frame(self.root, bg=BG)
        chat.pack(fill="both", expand=True, padx=4, pady=(4,0))
        self.canvas = tk.Canvas(chat, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(chat, command=self.canvas.yview, width=6,
                          troughcolor=BG2, bg=BG3)
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.msgs = tk.Frame(self.canvas, bg=BG)
        self.cw = self.canvas.create_window((0,0), window=self.msgs, anchor="nw")
        self.msgs.bind("<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>",
            lambda e: self.canvas.itemconfig(self.cw, width=e.width))

        # ── Typing ──
        self.tlbl = tk.Label(self.root, text="",
                             font=("Courier New",9,"italic"), bg=BG, fg=DIM)
        self.tlbl.pack(anchor="w", padx=14, pady=(2,0))

        tk.Frame(self.root, bg=BG3, height=1).pack(fill="x")

        # ── Input ──
        inp = tk.Frame(self.root, bg=BG2, pady=10)
        inp.pack(fill="x", side="bottom")

        tk.Button(inp, text="📎", font=("Segoe UI Emoji",14),
                  bg=BG2, fg=DIM, relief="flat", cursor="hand2",
                  activebackground=BG3, bd=0, padx=10, pady=6,
                  command=self._send_file).pack(side="left", padx=(12,4))

        msg_wrap = tk.Frame(inp, bg=BG3)
        msg_wrap.pack(side="left", fill="x", expand=True, padx=4)
        self.ibox = tk.Text(msg_wrap, height=3, font=FONT,
                            bg=BG3, fg=WHITE, insertbackground=BLUE,
                            relief="flat", padx=12, pady=8,
                            wrap="word", bd=0)
        self.ibox.pack(fill="x")
        self.ibox.bind("<Return>", self._enter)
        self.ibox.bind("<KeyPress>", self._typing_ev)

        tk.Button(inp, text="SEND", font=("Courier New",10,"bold"),
                  bg=BLUE, fg=BG, relief="flat", cursor="hand2",
                  activebackground="#2266cc", bd=0, padx=18, pady=10,
                  command=self._send).pack(side="right", padx=(4,14))

    def _start(self, port):
        self._sys(f"✦ Connecting to server ...")
        self._sys(f"✦ Address: wss://{NGROK}")
        threading.Thread(target=self._run, args=(port,), daemon=True).start()

    def _run(self, port):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._connect())

    async def _connect(self):
        url = f"wss://{NGROK}"
        try:
            async with websockets.connect(url) as ws:
                self.ws = ws
                self.root.after(0, lambda: self.dot.config(text="⬤  CONNECTED", fg=GREEN))
                self.root.after(0, lambda: self._sys("✓ Connected! চ্যাট শুরু করো।"))
                async for raw in ws:
                    p = json.loads(raw)
                    if p["type"] == "typing":
                        self.root.after(0, self._show_typing)
                    elif p["type"] == "text":
                        nm = p.get("name","Friend")
                        m  = dec(p["data"], self.akey, self.ckey)
                        self.root.after(0, lambda x=m,n=nm: self._bubble(x,"fr",name=n))
                    elif p["type"] == "file":
                        fn  = p["name"]
                        d   = dec(p["data"], self.akey, self.ckey)
                        fb  = base64.b64decode(d)
                        sp2 = os.path.join(os.path.expanduser("~"),"Downloads",fn)
                        with open(sp2,"wb") as f: f.write(fb)
                        nm  = p.get("sender","Friend")
                        self.root.after(0, lambda n=fn,nm2=nm:
                            self._bubble(f"📎  {n}  →  Downloads-এ save হয়েছে",
                                         "fr", is_file=True, name=nm2))
        except Exception as e:
            self.ws = None
            self.root.after(0, lambda: self.dot.config(text="⬤  OFFLINE", fg=RED))
            self.root.after(0, lambda err=str(e): self._sys(f"✗ Failed: {err}"))

    def _enter(self, e):
        if not e.state & 0x1: self._send(); return "break"

    def _typing_ev(self, e):
        if self.ws and self.loop:
            asyncio.run_coroutine_threadsafe(
                self.ws.send(json.dumps({"type":"typing","name":self.myname})), self.loop)

    def _send(self):
        msg = self.ibox.get("1.0","end-1c").strip()
        if not msg: return
        if not self.ws:
            messagebox.showwarning("!","Server connected নেই"); return
        self.ibox.delete("1.0","end")
        self._bubble(msg,"me")
        e2 = enc(msg, self.akey, self.ckey)
        asyncio.run_coroutine_threadsafe(
            self.ws.send(json.dumps({"type":"text","data":e2,"name":self.myname})), self.loop)

    def _send_file(self):
        if not self.ws:
            messagebox.showwarning("!","Connected নেই"); return
        path = filedialog.askopenfilename()
        if not path: return
        fn = os.path.basename(path)
        with open(path,"rb") as f: raw = f.read()
        e2 = enc(base64.b64encode(raw).decode(), self.akey, self.ckey)
        asyncio.run_coroutine_threadsafe(
            self.ws.send(json.dumps({"type":"file","name":fn,"data":e2,"sender":self.myname})), self.loop)
        self._bubble(f"📎  {fn}", "me", is_file=True)

    def _bubble(self, text, who, is_file=False, name=None):
        me    = who == "me"
        bgc   = GME   if me else GFR
        bdr   = GREEN if me else BLUE
        nc    = GREEN if me else BLUE
        dname = self.myname if me else (name or "Friend")
        anch  = "e"   if me else "w"
        ts    = time.strftime("%H:%M")
        fc    = "#aaffcc" if me else "#aaccff"
        if is_file: fc = YEL

        outer = tk.Frame(self.msgs, bg=BG, pady=5)
        outer.pack(fill="x", padx=10)

        meta = tk.Frame(outer, bg=BG)
        meta.pack(anchor=anch, padx=10)
        tk.Label(meta, text=dname, font=("Courier New",8,"bold"),
                 bg=BG, fg=nc).pack(side="left")
        tk.Label(meta, text=f"  {ts}", font=("Courier New",8),
                 bg=BG, fg=DIM).pack(side="left")

        bwrap = tk.Frame(outer, bg=bdr, padx=1, pady=1)
        bwrap.pack(anchor=anch, padx=10)
        card = tk.Frame(bwrap, bg=bgc, padx=16, pady=10)
        card.pack()
        tk.Label(card, text=text, font=FONT, bg=bgc, fg=fc,
                 wraplength=380, justify="left").pack(anchor="w")

        self.root.after(80, lambda: self.canvas.yview_moveto(1.0))

    def _sys(self, text):
        f = tk.Frame(self.msgs, bg=BG, pady=1)
        f.pack(fill="x", padx=14)
        tk.Label(f, text=text, font=("Courier New",9),
                 bg=BG, fg=DIM, justify="left").pack(anchor="w")
        self.root.after(80, lambda: self.canvas.yview_moveto(1.0))

    def _show_typing(self):
        self.tlbl.config(text="বন্ধু লিখছে ...")
        if self.tjob: self.root.after_cancel(self.tjob)
        self.tjob = self.root.after(2000, lambda: self.tlbl.config(text=""))

if __name__ == "__main__":
    root = tk.Tk()
    ClientApp(root)
    root.mainloop()
