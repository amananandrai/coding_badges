import codecs
import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup


USER_AGENT = "Mozilla/5.0"


def write_endpoint_json(path, label, message, color="0A0A0A", logo=None):
    data = {
        "schemaVersion": 1,
        "label": label,
        "message": str(message),
        "color": color,
    }
    if logo:
        data["namedLogo"] = logo
    path.write_text(json.dumps(data), encoding="utf-8")


CFG = {
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
        "api": "https://leetcode-stats-api.herokuapp.com/{handle}",
    },
    "codechef": {
        "handle": "sangadak",
        "profile": "https://www.codechef.com/users/sangadak",
    },
}

OUT_DIR = Path("badges")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_existing_message(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("message")
    except Exception:
        return None


def safe_int(x):
    try:
        return int(str(x).replace(",", "").strip())
    except Exception:
        return None


def extract_json_object(source: str, marker: str):
    idx = source.find(marker)
    if idx < 0:
        return None

    start = idx + len(marker)
    while start < len(source) and source[start].isspace():
        start += 1
    if start >= len(source) or source[start] != "{":
        return None

    depth = 0
    in_string = False
    escaped = False
    for i in range(start, len(source)):
        ch = source[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return source[start : i + 1]

    return None


def extract_hackerearth_profile_data(html_text: str):
    fragments = re.findall(
        r'self\.__next_f\.push\(\[1,"(.*?)"\]\)</script>',
        html_text,
        flags=re.S,
    )
    if not fragments:
        return None

    payload = []
    for fragment in fragments:
        try:
            payload.append(codecs.decode(fragment, "unicode_escape"))
        except Exception:
            payload.append(fragment)

    profile_data_text = extract_json_object("".join(payload), '"profileData":')
    if not profile_data_text:
        return None

    try:
        return json.loads(profile_data_text)
    except Exception:
        return None


# --- HackerEarth ---
def fetch_hackerearth():
    out = OUT_DIR / "hackerearth.json"
    label, logo, color = "HackerEarth", "hackerearth", "323754"
    url = CFG["hackerearth"]["profile"]
    message = None
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": USER_AGENT})
        if r.ok:
            profile_data = extract_hackerearth_profile_data(r.text)
            if profile_data:
                badge_progress = profile_data.get("global_badge_progress") or {}
                badges = (profile_data.get("global_badges") or {}).get("badges") or []
                latest_badge = None
                if badges:
                    latest_badge = (badges[-1].get("badge") or {}).get("name")
                score = safe_int(badge_progress.get("current_score"))

                if latest_badge and score is not None:
                    message = f"{latest_badge} | {score} pts"
                elif score is not None:
                    message = f"Score {score}"
                elif latest_badge:
                    message = latest_badge
    except Exception:
        pass
    if not message:
        message = load_existing_message(out) or "Visit profile"
    write_endpoint_json(out, label, message, color, logo)


# --- SPOJ ---
def fetch_spoj():
    out = OUT_DIR / "spoj.json"
    label, color = "SPOJ", "0A0A0A"
    logo = "spoj"

    url = CFG["spoj"]["profile"]
    solved, rank = None, None
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": USER_AGENT})
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
        msg = f"Solved {solved} | Rank {rank}"
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
            if total:
                message = f"Solved {total}"
    except Exception:
        pass
    if not message:
        message = load_existing_message(out) or "Visit profile"
    write_endpoint_json(out, label, message, color, logo)


# --- CodeChef ---
def fetch_codechef():
    out = OUT_DIR / "codechef.json"
    label, logo, color = "CodeChef", "codechef", "326f9f"
    url = CFG["codechef"]["profile"]
    rating, solved, stars = None, None, None
    try:
        r = requests.get(url, timeout=25, headers={"User-Agent": USER_AGENT})
        if r.ok:
            rating_match = re.search(
                r'class="rating-number">\s*([0-9,]+)\s*<',
                r.text,
                re.I,
            )
            if rating_match:
                rating = rating_match.group(1)

            solved_match = re.search(r"Total Problems Solved:\s*([0-9,]+)", r.text, re.I)
            if solved_match:
                solved = solved_match.group(1)

            star_block = re.search(r'class="rating-star">(.*?)</div>', r.text, re.I | re.S)
            if star_block:
                stars = len(re.findall(r"&#9733;|&#x2605;", star_block.group(1), re.I))
    except Exception:
        pass

    if solved and rating:
        msg = f"Solved {solved} | Rating {rating}"
    elif solved:
        msg = f"Solved {solved}"
    elif rating and stars:
        star_label = "star" if stars == 1 else "stars"
        msg = f"Rating {rating} | {stars} {star_label}"
    elif rating:
        msg = f"Rating {rating}"
    else:
        msg = load_existing_message(out) or "Visit profile"
    write_endpoint_json(out, label, msg, color, logo)


def main():
    fetch_hackerearth()
    fetch_spoj()
    fetch_leetcode()
    fetch_codechef()
    (OUT_DIR / "last_run.txt").write_text(str(int(time.time())), encoding="utf-8")


if __name__ == "__main__":
    main()
