import codecs
import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup


USER_AGENT = "Mozilla/5.0"
REQUEST_HEADERS = {"User-Agent": USER_AGENT}


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
        "challenge_api": "https://www.hackerearth.com/profiles/api/{handle}/challenge-activity/",
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


def safe_int(value):
    try:
        return int(str(value).replace(",", "").strip())
    except Exception:
        return None


def first_number(value):
    if value is None:
        return None
    match = re.search(r"([0-9][0-9,]*)", str(value))
    if not match:
        return None
    return safe_int(match.group(1))


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


def scrape_hackerearth_metrics_with_browser(url: str):
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return {}

    labels = ["Points", "Contest Ratings", "Problems Solved", "Solutions Submitted"]

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent=USER_AGENT,
                viewport={"width": 1440, "height": 1200},
            )
            page.goto(url, wait_until="load", timeout=60000)
            page.wait_for_timeout(3000)

            metrics = page.evaluate(
                """(labels) => {
                    const result = {};
                    const nodes = Array.from(document.querySelectorAll("div, section, article"));
                    for (const node of nodes) {
                        const text = (node.innerText || "").trim();
                        if (!text) {
                            continue;
                        }

                        const lines = text
                            .split(/\\n+/)
                            .map((line) => line.trim())
                            .filter(Boolean);

                        for (const label of labels) {
                            const idx = lines.indexOf(label);
                            if (idx < 0) {
                                continue;
                            }

                            const value = [...lines.slice(0, idx)]
                                .reverse()
                                .find((line) => /^[0-9,]+$/.test(line));

                            if (value && !(label in result)) {
                                result[label] = value;
                            }
                        }
                    }
                    return result;
                }""",
                labels,
            )
            browser.close()
            return metrics or {}
    except Exception:
        return {}


def fetch_hackerearth_stats():
    stats = {
        "points": None,
        "contest_rating": None,
        "problem_solved": None,
        "solutions_submitted": None,
    }

    try:
        r = requests.get(
            CFG["hackerearth"]["profile"],
            timeout=20,
            headers=REQUEST_HEADERS,
        )
        if r.ok:
            profile_data = extract_hackerearth_profile_data(r.text)
            if profile_data:
                badge_progress = profile_data.get("global_badge_progress") or {}
                stats["points"] = safe_int(badge_progress.get("current_score"))
    except Exception:
        pass

    try:
        api = CFG["hackerearth"]["challenge_api"].format(
            handle=CFG["hackerearth"]["handle"],
        )
        r = requests.get(api, timeout=20, headers=REQUEST_HEADERS)
        if r.ok:
            contest_data = (r.json() or {}).get("contest_data") or {}
            ratings_graph = contest_data.get("ratings_graph") or []
            if ratings_graph:
                latest = ratings_graph[-1] or {}
                stats["contest_rating"] = safe_int(latest.get("rating"))
    except Exception:
        pass

    browser_metrics = scrape_hackerearth_metrics_with_browser(CFG["hackerearth"]["profile"])
    if browser_metrics:
        stats["points"] = first_number(browser_metrics.get("Points")) or stats["points"]
        stats["contest_rating"] = (
            first_number(browser_metrics.get("Contest Ratings"))
            or stats["contest_rating"]
        )
        stats["problem_solved"] = first_number(browser_metrics.get("Problems Solved"))
        stats["solutions_submitted"] = first_number(
            browser_metrics.get("Solutions Submitted")
        )

    return stats


def fetch_spoj():
    out = OUT_DIR / "spoj.json"
    label, color = "SPOJ", "0A0A0A"
    logo = "spoj"

    url = CFG["spoj"]["profile"]
    solved, rank = None, None
    try:
        r = requests.get(url, timeout=20, headers=REQUEST_HEADERS)
        if r.ok:
            soup = BeautifulSoup(r.text, "lxml")
            txt = soup.get_text(" ", strip=True)
            solved_match = re.search(r"Problems\s*solved\s*:\s*([0-9,]+)", txt, re.I)
            if solved_match:
                solved = safe_int(solved_match.group(1))
            rank_match = re.search(r"World\s*Rank\s*:\s*([0-9,]+)", txt, re.I)
            if rank_match:
                rank = rank_match.group(1)
    except Exception:
        pass

    if solved and rank:
        message = f"Solved {solved} | Rank {rank}"
    elif solved:
        message = f"Solved {solved}"
    else:
        message = load_existing_message(out) or "Visit profile"
    write_endpoint_json(out, label, message, color, logo)


def fetch_leetcode():
    out = OUT_DIR / "leetcode.json"
    label, logo, color = "LeetCode", "leetcode", "FFA116"
    api = CFG["leetcode"]["api"].format(handle=CFG["leetcode"]["handle"])
    message = None
    try:
        r = requests.get(api, timeout=25)
        if r.ok:
            total = (r.json() or {}).get("totalSolved")
            if total:
                message = f"Solved {total}"
    except Exception:
        pass
    if not message:
        message = load_existing_message(out) or "Visit profile"
    write_endpoint_json(out, label, message, color, logo)


def fetch_codechef_stats():
    stats = {
        "rating": None,
        "problem_solved": None,
        "stars": None,
    }

    try:
        r = requests.get(
            CFG["codechef"]["profile"],
            timeout=25,
            headers=REQUEST_HEADERS,
        )
        if r.ok:
            rating_match = re.search(
                r'class="rating-number">\s*([0-9,]+)\s*<',
                r.text,
                re.I,
            )
            if rating_match:
                stats["rating"] = safe_int(rating_match.group(1))

            solved_match = re.search(
                r"Total Problems Solved:\s*([0-9,]+)",
                r.text,
                re.I,
            )
            if solved_match:
                stats["problem_solved"] = safe_int(solved_match.group(1))

            star_block = re.search(
                r'class="rating-star">(.*?)</div>',
                r.text,
                re.I | re.S,
            )
            if star_block:
                stats["stars"] = len(
                    re.findall(r"&#9733;|&#x2605;", star_block.group(1), re.I)
                )
    except Exception:
        pass

    return stats


def write_hackerearth_badges(stats):
    solved_out = OUT_DIR / "hackerearth.json"
    rating_out = OUT_DIR / "hackerearth_rating.json"

    solved_message = None
    if stats.get("problem_solved") is not None:
        solved_message = f"Solved {stats['problem_solved']}"
    if not solved_message:
        solved_message = load_existing_message(solved_out) or "Visit profile"

    rating_message = None
    if stats.get("contest_rating") is not None:
        rating_message = f"Rating {stats['contest_rating']}"
    if not rating_message:
        rating_message = load_existing_message(rating_out) or "Visit profile"

    write_endpoint_json(
        solved_out,
        "HackerEarth",
        solved_message,
        "323754",
        "hackerearth",
    )
    write_endpoint_json(
        rating_out,
        "HackerEarth Rating",
        rating_message,
        "323754",
        "hackerearth",
    )


def write_codechef_badges(stats):
    solved_out = OUT_DIR / "codechef.json"
    rating_out = OUT_DIR / "codechef_rating.json"

    solved_message = None
    if stats.get("problem_solved") is not None:
        solved_message = f"Solved {stats['problem_solved']}"
    if not solved_message:
        solved_message = load_existing_message(solved_out) or "Visit profile"

    rating_message = None
    if stats.get("rating") is not None:
        rating_message = f"Rating {stats['rating']}"
    if not rating_message:
        rating_message = load_existing_message(rating_out) or "Visit profile"

    write_endpoint_json(
        solved_out,
        "CodeChef",
        solved_message,
        "326f9f",
        "codechef",
    )
    write_endpoint_json(
        rating_out,
        "CodeChef Rating",
        rating_message,
        "326f9f",
        "codechef",
    )


def main():
    hackerearth_stats = fetch_hackerearth_stats()
    codechef_stats = fetch_codechef_stats()

    write_hackerearth_badges(hackerearth_stats)
    fetch_spoj()
    fetch_leetcode()
    write_codechef_badges(codechef_stats)
    (OUT_DIR / "last_run.txt").write_text(str(int(time.time())), encoding="utf-8")


if __name__ == "__main__":
    main()
