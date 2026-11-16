# Coding Badges

Auto-updating [Shields.io](https://shields.io/) badges for my competitive programming profiles on **LeetCode, CodeChef, HackerEarth and SPOJ**.

A GitHub Actions workflow scrapes each profile every 12 hours and writes the latest numbers to small JSON files in [`badges/`](badges). Shields.io's [endpoint badge](https://shields.io/badges/endpoint-badge) reads those files, so the badges on my GitHub profile and website stay current without any manual updates.

## Badges

### Problems solved
<!-- HackerEarth -->
<a href="https://www.hackerearth.com/@amananandrai/" target="_blank" rel="noreferrer">
  <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/amananandrai/coding_badges/main/badges/hackerearth.json&cacheSeconds=1800" alt="HackerEarth Badge" />
</a>

<!-- LeetCode -->
<a href="https://leetcode.com/u/aman_rai/" target="_blank" rel="noreferrer">
  <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/amananandrai/coding_badges/main/badges/leetcode.json&cacheSeconds=1800" alt="LeetCode Badge" />
</a>

<!-- CodeChef -->
<a href="https://www.codechef.com/users/sangadak" target="_blank" rel="noreferrer">
  <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/amananandrai/coding_badges/main/badges/codechef.json&cacheSeconds=1800" alt="CodeChef Badge" />
</a>

<!-- SPOJ -->
<a href="https://www.spoj.com/users/amananandrai/" target="_blank" rel="noreferrer">
  <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/amananandrai/coding_badges/main/badges/spoj.json&cacheSeconds=1800" alt="SPOJ Badge" />
</a>
<br/>

### Ratings
<!-- HackerEarth Rating -->
<a href="https://www.hackerearth.com/@amananandrai/" target="_blank" rel="noreferrer">
  <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/amananandrai/coding_badges/main/badges/hackerearth_rating.json&cacheSeconds=1800" alt="HackerEarth Rating Badge" />
</a>

<!-- CodeChef Rating -->
<a href="https://www.codechef.com/users/sangadak" target="_blank" rel="noreferrer">
  <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/amananandrai/coding_badges/main/badges/codechef_rating.json&cacheSeconds=1800" alt="CodeChef Rating Badge" />
</a>

## How it works

```
GitHub Actions (every 12 h)
  └─ scripts/generate_badges.py
       ├─ HackerEarth  profile page + challenge API + headless Chromium (Playwright)
       ├─ LeetCode     leetcode-stats-api
       ├─ CodeChef     profile page (rating, problems solved)
       └─ SPOJ         profile page (problems solved, world rank)
  └─ writes badges/*.json  →  commits if anything changed
                                   ↓
                     img.shields.io/endpoint?url=<raw JSON URL>
```

- Each JSON file follows the Shields.io endpoint schema (`schemaVersion`, `label`, `message`, `color`, `namedLogo`).
- If a site can't be reached or its layout changes, the script keeps the previous value instead of breaking the badge.
- `badges/last_run.txt` records the Unix timestamp of the last successful run.

The workflow ([`.github/workflows/badges.yml`](.github/workflows/badges.yml)) runs on a schedule (`17 */12 * * *`), on manual dispatch, and whenever the script changes.

## Use it for your own profiles

1. Fork this repo.
2. Edit the handles and profile URLs in the `CFG` dictionary at the top of [`scripts/generate_badges.py`](scripts/generate_badges.py).
3. In **Settings → Actions → General**, make sure workflows have read and write permissions.
4. Run the **Update profile badges** workflow once from the Actions tab.
5. Embed a badge anywhere with:

   ```markdown
   ![LeetCode](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/<you>/coding_badges/main/badges/leetcode.json)
   ```

### Run locally

```bash
pip install requests beautifulsoup4 lxml playwright
python -m playwright install chromium
python scripts/generate_badges.py
```

## License

[MIT](LICENSE) © 2026 Aman Anand Rai
