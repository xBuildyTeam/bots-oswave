#!/usr/bin/env python3
"""uBase packet checker 0.2 (https://bots.oswave.io/ubase/). Python 3, standard library only.

  python3 check_packet.py my-packet.ubase            # any packet (old layouts get warnings)
  python3 check_packet.py --strict my-packet.ubase   # wave.ubase/2 rules (required for bot submissions)
  python3 check_packet.py --json ...                  # machine-readable result

Exit code 0 = no errors. A packet is ready only with 0 errors.
"""
import hashlib, json, re, sys, zipfile, os

VERSION = "0.3.0"
CATEGORIES = {"UI Components", "Integrations", "Utilities", "Data", "Messaging", "Payments", "Security", "AI", "Dev"}
TOP_DIRS = ("components/", "functions/", "entities/", "assets/")
ROOT_FILES = {"meta.json", "prompt.md", "README.md", "INSTALL.md", "LICENSE", "LICENSE.md"}
ASSET_EXT = (".png", ".jpg", ".jpeg", ".svg", ".html", ".json", ".md", ".txt", ".css")
CODE_EXT = (".jsx", ".tsx", ".ts", ".js")
TEXT_EXT = CODE_EXT + (".json", ".md", ".html", ".txt", ".css", ".svg")
SECRET = re.compile(r"(sk_live_[0-9a-zA-Z]{10,}|sk_test_[0-9a-zA-Z]{10,}|rk_live_[0-9a-zA-Z]{10,}|AKIA[0-9A-Z]{16}|"
                    r"ghp_[0-9A-Za-z]{30,}|github_pat_[0-9A-Za-z_]{30,}|xox[bapr]-[0-9A-Za-z-]{10,}|AIza[0-9A-Za-z_-]{35}|"
                    r"-----BEGIN [A-Z ]*PRIVATE KEY|\bAC[0-9a-f]{32}\b|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}|"
                    r"\b0x[0-9a-fA-F]{64}\b|hooks\.slack\.com/(services|workflows|triggers)/[A-Za-z0-9/_-]{12,}|"
                    r"discord(app)?\.com/api/webhooks/\d+/[A-Za-z0-9_-]{20,}|outlook\.office\.com/webhook/[A-Za-z0-9@/_-]{20,}|"
                    r"[a-z0-9.-]+\.webhook\.office\.com/[A-Za-z0-9@/_-]{20,}|api\.telegram\.org/bot\d+:[A-Za-z0-9_-]{30,}|"
                    r"[?&](api_?key|access_token|token|secret|key)=[A-Za-z0-9_\-]{16,})")
BLOCKED = [(re.compile(r"\beval\s*\("), "eval()"), (re.compile(r"\bnew\s+Function\s*\("), "new Function()"),
           (re.compile(r"<script[^>]+src\s*=", re.I), "outside <script src>"),
           (re.compile(r"\bimport\s*\(\s*['\"`]https?://"), "dynamic import from a URL")]
REVIEW = [(re.compile(r"dangerouslySetInnerHTML"), "dangerouslySetInnerHTML"),
          (re.compile(r"\bdocument\.write\s*\("), "document.write()")]
def strip_comments(t):
    """Removes // and /* */ comments (outside strings, roughly) so a comment that MENTIONS eval() doesn't fail."""
    out, i, n, q = [], 0, len(t), None
    while i < n:
        c = t[i]
        if q:
            out.append(c)
            if c == "\\" and i + 1 < n: out.append(t[i + 1]); i += 2; continue
            if c == q: q = None
            i += 1; continue
        if c in "'\"`": q = c; out.append(c); i += 1; continue
        if t.startswith("//", i) and (i == 0 or t[i - 1] != ":"):
            j = t.find("\n", i); i = n if j < 0 else j; continue
        if t.startswith("/*", i):
            j = t.find("*/", i + 2); i = n if j < 0 else j + 2; continue
        out.append(c); i += 1
    return "".join(out)


FENCE = re.compile(r"```[a-zA-Z]*\n(.*?)```", re.S)
TEMPLATE_LEFT = re.compile(r"<(Title|Component|one line[^>]*|list[^>]*|one sentence[^>]*)>")
INSTRUCT_BAD = re.compile(r"\b(use|call|add|keep|wrap[^.\n]{0,20}in)\s+(an?\s+)?`?(eval|new Function)\b", re.I)
NEGATED = re.compile(r"(\bnot|n't|\bnever|\bno|\bavoid|\bwithout|\binstead of)\W+(\w+\W+){0,2}$", re.I)


def tells_to_use_eval(t):
    for m in INSTRUCT_BAD.finditer(t):
        if not NEGATED.search(t[max(0, m.start() - 40):m.start()]): return True
    return False


HOST = re.compile(r"https?://([a-z0-9.-]+\.[a-z]{2,})", re.I)
SAFE_HOSTS = {"base44.app", "base44.com", "ubase.tech", "bots.oswave.io", "oswave.io", "web.oswave.io", "example.com", "github.com"}


def check(path, strict=False):
    r = {"file": os.path.basename(path), "size": os.path.getsize(path), "format": None, "errors": [], "warnings": [], "info": []}
    E, W, I = r["errors"].append, r["warnings"].append, r["info"].append
    try:
        z = zipfile.ZipFile(path)
    except Exception as e:
        E(f"not a zip file ({e})"); return r
    names = [n for n in z.namelist() if not n.endswith("/")]
    if any(n.startswith("/") or ".." in n.split("/") for n in names):
        E("unsafe file path in the zip"); return r
    metas = [n for n in names if n.split("/")[-1] == "meta.json"]
    if not metas:
        E("no meta.json"); return r
    m = min(metas, key=len); root = m[: -len("meta.json")]
    if root:
        (E if strict else W)(f"files are inside a folder ({root}); put them at the zip root")
    try:
        meta = json.loads(z.read(m))
    except Exception as e:
        E(f"meta.json isn't valid JSON ({e})"); return r
    inner = meta["meta"] if isinstance(meta.get("meta"), dict) else meta
    if inner is not meta:
        (E if strict else W)("old single-file layout (everything inside meta.json); split it into files")
    r["format"] = inner.get("format") or "legacy"
    rel = {n[len(root):]: n for n in names if n.startswith(root)}
    text = {k: z.read(v).decode("utf-8", "replace") for k, v in rel.items() if k.endswith(TEXT_EXT)}

    # meta fields
    for k in ("name", "version", "description", "category"):
        if not inner.get(k): E(f"meta.json is missing {k}")
    if strict:
        if inner.get("format") != "wave.ubase/2": E('meta.json needs "format": "wave.ubase/2"')
        if inner.get("target") != "base44": E('meta.json needs "target": "base44" (the only target so far)')
        if not isinstance(inner.get("permissions"), dict): E("meta.json needs a permissions object")
        if inner.get("name") and not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", str(inner["name"])): E("name must be lowercase-with-dashes")
        if inner.get("category") and inner["category"] not in CATEGORIES: E(f"category must be one of: {', '.join(sorted(CATEGORIES))}")
        if "price" in inner and not (isinstance(inner["price"], (int, float)) and inner["price"] >= 0): E("price must be a number, 0 or more")
        aw = inner.get("author_wallet")
        if aw and not re.fullmatch(r"0x[0-9a-fA-F]{40}", str(aw)): E("author_wallet isn't a 0x address")
    if inner.get("version") and not re.fullmatch(r"\d+\.\d+\.\d+", str(inner["version"])): (E if strict else W)("version must be x.y.z")

    # required docs
    if "prompt.md" not in rel and not (meta.get("prompt") or meta.get("installation_notes")): E("no prompt.md (the install prompt for the builder AI)")
    if "README.md" not in rel and not inner.get("readme"): (E if strict else W)("no README.md")

    # layout
    code = [k for k in rel if k.startswith(TOP_DIRS)]
    for k in rel:
        if k in ROOT_FILES or k.startswith(TOP_DIRS) or k.startswith("previews/"): continue
        (E if strict else W)(f"unexpected file {k}")
    for k in code:
        if k.startswith(("components/", "functions/")) and not k.endswith(CODE_EXT): E(f"{k}: only .jsx/.tsx/.ts/.js allowed here")
        if k.startswith("assets/") and not k.lower().endswith(ASSET_EXT): E(f"{k}: asset type not allowed")
        if k.lower().endswith((".zip", ".ubase", ".exe", ".sh", ".bat", ".dll", ".so", ".wasm")): E(f"{k}: archives and executables aren't allowed")

    # files map + hashes
    files = inner.get("files") if isinstance(inner.get("files"), dict) else meta.get("files")
    if isinstance(files, dict):
        listed = set()
        for k, v in files.items():
            target = v if isinstance(v, str) else k
            listed.add(target); listed.add(k)
            if target not in rel: E(f"files lists {target}, which isn't in the zip")
            elif strict:
                want = v.get("sha256") if isinstance(v, dict) else None
                got = hashlib.sha256(z.read(rel[target])).hexdigest()
                if not want: E(f"files.{k} needs a sha256")
                elif want.lower() != got: E(f"{k}: sha256 doesn't match the file")
        for k in code:
            if k not in listed: (E if strict else W)(f"{k} isn't listed in files")
    elif code:
        (E if strict else W)("meta.json has no files map")

    # entities
    for k in [k for k in rel if k.startswith("entities/") and k.endswith(".json")]:
        try:
            s = json.loads(text[k]); assert isinstance(s, dict) and ("properties" in s or "schema" in s)
        except Exception:
            E(f"{k} isn't a valid entity schema (needs properties)")

    # placeholders
    code_text = " ".join(v for k, v in text.items() if k.endswith(CODE_EXT + (".html",)))
    used_any = set(re.findall(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}", code_text))
    for p in sorted(x for x in used_any if not re.fullmatch(r"[A-Z0-9_]+", x)): E(f"{{{{{p}}}}}: placeholder names must be UPPER_SNAKE_CASE")
    used = {x for x in used_any if re.fullmatch(r"[A-Z0-9_]+", x)}
    declared = {p.get("key") for p in (inner.get("placeholders") or []) if isinstance(p, dict)}
    for p in sorted(used - declared): (E if strict else W)(f"{{{{{p}}}}} is used in code but not declared in placeholders")
    if strict:
        for p in sorted(declared - used - {None}): W(f"placeholder {p} is declared but never used in code")

    # safety
    for k, t in text.items():
        if SECRET.search(t): E(f"possible secret or private key in {k}")
        if k.endswith(CODE_EXT + (".html", ".json")):
            body = strip_comments(t) if k.endswith(CODE_EXT) else t
            for rx, label in BLOCKED:
                if rx.search(body): E(f"{label} in {k}")
                elif rx.search(t): I(f"{label} is only mentioned in a comment in {k}")
            for rx, label in REVIEW:
                if rx.search(t): W(f"{label} in {k} (needs review; say why in README)")
            if k.endswith(CODE_EXT) and max((len(l) for l in t.splitlines()), default=0) > 2000: E(f"{k} looks minified (a line over 2,000 characters)")
    for k in [k for k in text if k.endswith(".md")]:
        t = text[k]
        for blk in FENCE.findall(t):
            for rx, label in BLOCKED:
                if rx.search(strip_comments(blk)): E(f"{label} in a code example in {k}")
        if tells_to_use_eval(t): E(f"{k} tells the installer to use eval/new Function")
        if k == "prompt.md":
            left = sorted(set(m.group(0) for m in TEMPLATE_LEFT.finditer(t)))
            if left: E(f"prompt.md still has template blanks: {', '.join(left)}")
            if len(t.strip()) < 200: E("prompt.md is too short to install from")
    admin = any("asServiceRole" in t for k, t in text.items() if k.endswith(CODE_EXT + (".json",)))
    hosts = sorted({h.lower() for k, t in text.items() if k.endswith(CODE_EXT) for h in HOST.findall(t)} - SAFE_HOSTS)
    perms = inner.get("permissions") if isinstance(inner.get("permissions"), dict) else None
    if admin: I("uses admin access (asServiceRole)")
    if hosts: I(f"calls outside hosts: {', '.join(hosts)}")
    if strict and perms is not None:
        if admin and not perms.get("admin_access"): E("code uses asServiceRole but permissions.admin_access isn't true")
        missing = [h for h in hosts if h not in set(perms.get("outside_hosts") or [])]
        if missing: E(f"outside hosts not listed in permissions.outside_hosts: {', '.join(missing)}")
        envs = set(re.findall(r"Deno\.env\.get\(\s*['\"]([A-Z0-9_]+)['\"]", code_text))
        if envs - set(perms.get("secrets") or []): E(f"secrets not listed in permissions.secrets: {', '.join(sorted(envs - set(perms.get('secrets') or [])))}")
        ents = {os.path.basename(k)[:-5] for k in rel if k.startswith("entities/") and k.endswith(".json")}
        if ents - set(perms.get("entities") or []): E(f"entities not listed in permissions.entities: {', '.join(sorted(ents - set(perms.get('entities') or [])))}")
        fns = {os.path.basename(k).rsplit(".", 1)[0] for k in rel if k.startswith("functions/")}
        if fns - set(perms.get("functions") or []): E(f"functions not listed in permissions.functions: {', '.join(sorted(fns - set(perms.get('functions') or [])))}")
    if r["size"] > 45_000: (E if strict else W)(f"{r['size']:,} bytes zipped; keep packets under 45,000 bytes")
    r["sha256"] = hashlib.sha256(open(path, "rb").read()).hexdigest()
    return r


def main(argv):
    strict = "--strict" in argv; as_json = "--json" in argv
    paths = [a for a in argv if not a.startswith("--")]
    if not paths: print(__doc__); return 2
    res = [check(p, strict) for p in paths]
    if as_json:
        print(json.dumps({"checker": VERSION, "strict": strict, "results": res}, indent=2))
    else:
        for x in res:
            st = "FAIL" if x["errors"] else ("WARN" if x["warnings"] else "PASS")
            print(f"{st}  {x['file']}  ({x['size']} B, {x['format']})")
            for e in x["errors"]: print("   x", e)
            for w in x["warnings"]: print("   !", w)
            for i in x["info"]: print("   i", i)
    return 1 if any(x["errors"] for x in res) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
