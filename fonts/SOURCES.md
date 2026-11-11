# Font sources

All fonts here are from Google Fonts (SIL Open Font License 1.1).

**2026-11-11:** eight files in this folder were GitHub web pages saved under font
names, not fonts. They were Cinzel-Regular, CormorantGaramond (Bold, Italic,
BoldItalic), DancingScript-Bold, DancingScript-Regular.woff2, IMFellEnglish-Regular,
Oswald-Bold and PlayfairDisplay-Italic. Benson found the first when it blocked the
Name Ornament customiser. The originals are in the trash vault (`data/trash/`).

**How they were replaced:**
- Each comes from `github.com/google/fonts` (`ofl/`): the variable font, instanced
  to the named weight with `fonttools varLib.instancer --update-name-table`.
- IM Fell English is `IMFeENrm28P.ttf`, renamed.
- DancingScript-Regular.woff2 was removed, not replaced: nothing used it.

Check before trusting a new file: `file fonts/<name>` must say TrueType, not HTML.
