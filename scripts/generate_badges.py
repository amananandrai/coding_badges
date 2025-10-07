import json, re, time
from pathlib import Path
import requests
from bs4 import BeautifulSoup

def write_endpoint_json(path, label, message, color="0A0A0A", logo=None):
    data = {
        "schemaVersion": 1,
        "label": label,
        "message": str(message),
        "color": color,
        "cacheBuster": int(time.time())  # forces a tiny change every run
    }
    if logo:
        data["logo"] = logo
    path.write_text(json.dumps(data), encoding="utf-8")
# ==== YOUR PROFILES ====
CFG = {
    "hackerrank": {
        "handle": "aman_rai",
        "profile": "https://www.hackerrank.com/profile/aman_rai",
        # legacy API (may or may not work; we try it first)
        "api": "https://www.hackerrank.com/rest/contests/master/hackers/{handle}/profile",
    },
    "hackerearth": {
        "handle": "amananandrai",
        "profile": "https://www.hackerearth.com/@amananandrai/",
    },
    "spoj": {
        "handle": "amananandrai",
        "profile": "https://www.spoj.com/users/amananandrai/",
    },
    "leetcode": {
        "handle": "aman_rai",
        "profile": "https://leetcode.com/u/aman_rai/",
        # community API used widely for public stats
        "api": "https://leetcode-stats-api.herokuapp.com/{handle}",
    },
    "codechef": {
        "handle": "sangadak",
        "profile": "https://www.codechef.com/users/sangadak",
    },
}

OUT_DIR = Path("badges")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def write_endpoint_json(path: Path, label: str, message: str, color="0A0A0A", logo=None):
    data = {"schemaVersion": 1, "label": label, "message": str(message), "color": color}
    if logo:
        data["logo"] = logo
    path.write_text(json.dumps(data), encoding="utf-8")

def load_existing_message(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("message")
    except Exception:
        return None

def safe_int(x):
    try:
        return int(str(x).replace(",","").strip())
    except Exception:
        return None

# --- HackerRank ---
def fetch_hackerrank():
    out = OUT_DIR / "hackerrank.json"
    label, logo, color = "HackerRank", "hackerrank", "1ba94c"

    h = CFG["hackerrank"]["handle"]
    api = CFG["hackerrank"]["api"].format(handle=h)
    solved = None

    try:
        r = requests.get(api, timeout=20)
        if r.ok:
            data = r.json()
            solved = (
                data.get("solved_challenges")
                or data.get("total_problems_solved")
                or data.get("model", {}).get("total_solved")
            )
            if not solved:
                tracks = data.get("model", {}).get("tracks", [])
                if tracks:
                    solved = sum([t.get("solved_challenges_count") or 0 for t in tracks])
    except Exception:
        pass

    if solved is not None:
        msg = f"Solved {solved}"
    else:
        msg = load_existing_message(out) or "Visit profile"
    write_endpoint_json(out, label, msg, color, logo)

# --- HackerEarth ---
def fetch_hackerearth():
    out = OUT_DIR / "hackerearth.json"
    label, logo, color = "HackerEarth", "hackerearth", "323754"
    url = CFG["hackerearth"]["profile"]
    message = None
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        if r.ok:
            soup = BeautifulSoup(r.text, "lxml")
            txt = soup.get_text(" ", strip=True)
            m = re.search(r"Problems?\s*Solved\s*:?\s*([0-9,]+)", txt, re.I)
            if m:
                message = f"Solved {m.group(1)}"
            else:
                m2 = re.search(r"Followers\s*:?\s*([0-9,]+)", txt, re.I)
                if m2:
                    message = f"Followers {m2.group(1)}"
    except Exception:
        pass
    if not message:
        message = load_existing_message(out) or "Visit profile"
    write_endpoint_json(out, label, message, color, logo)

# --- SPOJ ---
def fetch_spoj():
    out = OUT_DIR / "spoj.json"
    label, color = "SPOJ", "0A0A0A"
    # (no official SPOJ logo in SimpleIcons; codeforces icon looks neutral)
    logo = "codeforces"

    url = CFG["spoj"]["profile"]
    solved, rank = None, None
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        if r.ok:
            soup = BeautifulSoup(r.text, "lxml")
            txt = soup.get_text(" ", strip=True)
            m = re.search(r"Problems\s*solved\s*:\s*([0-9,]+)", txt, re.I)
            if m:
                solved = safe_int(m.group(1))
            m2 = re.search(r"World\s*Rank\s*:\s*([0-9,]+)", txt, re.I)
            if m2:
                rank = m2.group(1)
    except Exception:
        pass

    if solved and rank:
        msg = f"Solved {solved} • Rank {rank}"
    elif solved:
        msg = f"Solved {solved}"
    else:
        msg = load_existing_message(out) or "Visit profile"
    write_endpoint_json(out, label, msg, color, logo)

# --- LeetCode ---
def fetch_leetcode():
    out = OUT_DIR / "leetcode.json"
    label, logo, color = "LeetCode", "leetcode", "FFA116"
    h = CFG["leetcode"]["handle"]
    api = CFG["leetcode"]["api"].format(handle=h)
    message = None
    try:
        r = requests.get(api, timeout=25)
        if r.ok:
            j = r.json()
            total = j.get("totalSolved")
            rating = j.get("contestRating")
            if total and rating:
                message = f"Solved {total} • Rating {int(rating)}"
            elif total:
                message = f"Solved {total}"
    except Exception:
        pass
    if not message:
        message = load_existing_message(out) or "Visit profile"
    write_endpoint_json(out, label, message, color, logo)
    print("[leetcode] status:", getattr(r, "status_code", "?"), "message:", message)


# --- CodeChef ---
def fetch_codechef():
    out = OUT_DIR / "codechef.json"
    label, logo, color = "CodeChef", "codechef", "326f9f"
    url = CFG["codechef"]["profile"]
    rating, stars = None, None
    try:
        r = requests.get(url, timeout=25, headers={"User-Agent": "Mozilla/5.0"})
        if r.ok:
            soup = BeautifulSoup(r.text, "lxml")
            txt = soup.get_text(" ", strip=True)
            m = re.search(r"Rating\s*:\s*([0-9,]+)", txt, re.I)
            if m:
                rating = m.group(1)
            ms = re.search(r"(\d)\s*Star", txt, re.I)
            if ms:
                stars = ms.group(1)
    except Exception:
        pass

    if rating and stars:
        msg = f"{rating} • {stars}★"
    elif rating:
        msg = f"{rating}"
    else:
        msg = load_existing_message(out) or "Visit profile"
    write_endpoint_json(out, label, msg, color, logo)

def main():
    fetch_hackerrank()
    fetch_hackerearth()
    fetch_spoj()
    fetch_leetcode()
    fetch_codechef()
    (OUT_DIR / "last_run.txt").write_text(str(int(time.time())), encoding="utf-8")

if __name__ == "__main__":
    main()
