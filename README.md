# Android rank tracker — Imposter Game: Malayalam Party

Checks the Google Play **Top Free › Word** games chart in 16 countries once a day
and saves the app's position to `android_ranks.json` (blank = not in the top 200).

## Set up (about 5 minutes, free)

1. Create a new **public** repository on GitHub, e.g. `imposter-android-ranks`.
   (Public so the daily dashboard update can read the results file. It only
   contains chart positions — nothing private.)
2. Upload these files, keeping the folder structure:
   `package.json`, `track.mjs`, `.github/workflows/daily.yml`.
3. Open the repo's **Actions** tab, enable workflows, pick
   **Daily Android ranks**, and click **Run workflow** once to test it.
4. After it finishes, `android_ranks.json` appears in the repo. Send Claude the
   repo link and Android ranks will be added to your dashboard and email.

## Run it on your own computer instead

Needs Node.js 18+:

```
npm install
node track.mjs
```

## Notes

- Uses the open-source `google-play-scraper` library, which reads Google Play's
  public pages. It's unofficial: if Google changes its site the script may stop
  working until the library is updated (`npm update google-play-scraper`).
- To change countries, edit the `COUNTRIES` list in `track.mjs`.
