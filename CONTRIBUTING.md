# Adding a skin

1. Make a skin in [Plinth's skin format](https://github.com/rubycatco/plinth/blob/main/docs/SKINS.md) and try it in Plinth at each fish size.
2. Put it in `skins/<id>/`, where `<id>` is lowercase letters, digits and hyphens, such as `paper-crane`. The id names the download, so choose one you'll keep.
3. In `skin.json`, besides `name`, and optionally `names`, `strike` and `voice`, add:

   ```json
   {
     "name": "Paper Crane",
     "names": { "zh-Hans": "纸鹤" },
     "author": "Your Name (@you)",
     "license": "CC0-1.0",
     "voice": "bamboo"
   }
   ```

   | Key | Required | Meaning |
   | --- | --- | --- |
   | `author` | yes | Who made it, shown in the gallery. |
   | `license` | yes | `CC0-1.0` (public domain) or `CC-BY-4.0` (credit the author). You must have the right to release the artwork under it. |
   | `likeness` | for real people | A link to the person's public consent. See below. |

   Plinth ignores these keys; the gallery reads them.
4. Run `python3 scripts/skins.py gallery`. It checks your skin and adds it to the gallery in `README.md`.
5. Open a pull request with a screenshot of the skin on your desktop.

## What the check looks for

- `idle.png` exists. Every PNG is square, has a transparent background, and frames are all the same size.
- Only skin files: `idle`, `blink` and `hit` frames (single or numbered from 1), `mallet.png`, `impact.png` and `skin.json`. No folders or links.
- The whole skin is under 3 MB.
- `skin.json` is valid JSON with `name`, `author` and `license`; `names`, if there, maps language codes to names; `voice` is one of Plinth's twenty-one; `strike` is two numbers from 0 to 1.

## Real people

A skin that depicts a real, identifiable person needs that person's consent, given publicly, such as a reply on social media or a comment on the pull request. Put the link in `likeness`. Without it, the pull request waits. If the person later asks for the skin to be removed, it is removed.

## No merit

Plinth keeps no score, and neither does this gallery: no rankings, no download counts.
