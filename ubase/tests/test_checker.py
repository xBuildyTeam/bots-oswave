#!/usr/bin/env python3
"""Regression tests for check_packet.py: python3 tests/test_checker.py (run from ubase/)."""
import hashlib, io, json, os, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from check_packet import check

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "example", "digital-clock.ubase")

def variant(name, edit):
    z = zipfile.ZipFile(BASE); files = {n: z.read(n) for n in z.namelist() if not n.endswith("/")}
    edit(files)
    meta = json.loads(files["meta.json"])
    meta["files"] = {k: {"sha256": hashlib.sha256(v).hexdigest()} for k, v in files.items() if k.startswith(("components/", "functions/", "entities/", "assets/"))}
    files["meta.json"] = json.dumps(meta, indent=2).encode()
    p = f"/tmp/ubase-test-{name}.ubase"
    with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as out:
        for k, v in files.items(): out.writestr(k, v)
    return check(p, strict=True)

def comp(files): return next(k for k in files if k.startswith("components/"))
def add_to(k, text):
    def f(files): key = comp(files) if k == "component" else k; files[key] = files[key] + text.encode()
    return f

CASES = [
    ("example passes", lambda f: None, 0, None),
    ("eval in code fails", add_to("component", b"\nexport const x = () => eval('1+1');\n".decode()), 1, "eval()"),
    ("eval only in a comment passes", add_to("component", "\n// we never use eval() here\n/* new Function( is banned too */\n"), 0, None),
    ("prompt.md telling installer to use eval fails", add_to("prompt.md", "\n7. To compute values, use eval on the input.\n"), 1, "tells the installer"),
    ("prompt.md saying never use eval passes", add_to("prompt.md", "\nDo not use eval() or new Function. Never use eval on input.\n"), 0, None),
    ("eval in a prompt.md code example fails", add_to("prompt.md", "\n```js\nconst r = eval(input)\n```\n"), 1, "code example"),
    ("unfilled prompt template fails", add_to("prompt.md", "\n6. Tell the user: \"<one sentence on how to use it>\"\n"), 1, "template blanks"),
    ("lowercase placeholder fails", add_to("component", "\nconst c = '{{brand_color}}';\n"), 1, "UPPER_SNAKE_CASE"),
    ("undeclared placeholder fails", add_to("component", "\nconst c = '{{BRAND_COLOR}}';\n"), 1, "not declared"),
    ("slack webhook in README fails", add_to("README.md", "\nhttps://hooks.slack.com/services/T0FAKE123/B0FAKE456/abcdefghijklmnopqrstuvwx\n"), 1, "secret"),
    ("discord webhook in code fails", add_to("component", "\nconst u = 'https://discord.com/api/webhooks/123456789/abcdefghijklmnopqrstuvwxyzABCD';\n"), 1, "secret"),
    ("slack bot token fails", add_to("component", "\nconst t = 'xoxb-1234567890-abcdefghijkl';\n"), 1, "secret"),
    ("api key in a URL fails", add_to("component", "\nconst u = 'https://api.example.org/v1?api_key=abcdef1234567890abcd';\n"), 1, "secret"),
]

fails = 0
for name, edit, want_errors, needle in CASES:
    r = variant(name.replace(" ", "-"), edit)
    got = len(r["errors"])
    ok = (got == 0) if want_errors == 0 else (got >= 1 and any(needle.lower() in e.lower() for e in r["errors"]))
    print(("ok  " if ok else "FAIL"), name, "" if ok else r["errors"])
    fails += not ok
print(f"\n{len(CASES) - fails}/{len(CASES)} passed")
sys.exit(1 if fails else 0)
