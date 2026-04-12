# Windsurf Prompt: Add Extended Islamic Niche Library

## Mandatory Rules (apply to ALL work in this project)

### 1. Maxton Template Adherence
This project uses the **Maxton Bootstrap 5 Admin Dashboard Template** (purchased). All UI work MUST use the actual Maxton template components, classes, and layout patterns. Reference existing pages in `static/assets/` for correct HTML structure. Do NOT invent custom CSS or components when a Maxton equivalent exists.

### 2. Documentation & Git
After completing all implementation work:
- Update `PROJECT.md` — add a changelog entry, add any decisions to Notes & Decisions Log
- Git commit and push: `git add . && git commit -m "Add extended Islamic niche library — 30+ niches with keyword bundles" && git push`

### 3. Agent Skills
- Read and follow: `.agent-skills/skills/incremental-implementation/SKILL.md`

---

## Context

Phase 1 (Research Agent) is complete. The research agent searches Etsy for Islamic digital products across configured niches, analyses results with Claude, and displays findings on the dashboard.

There is an existing `ResearchNiche` model with fields: `name`, `keywords` (JSON array), `enabled` (boolean). Currently there are 8 niches seeded.

---

## Task

Add an expanded library of Islamic digital product niches to the seed script and run it. This adds all niches to the database with appropriate enabled/disabled states. Some existing niches need their keywords expanded rather than duplicated.

### Rules for this task

1. **Do NOT create duplicate niches** — if a new niche overlaps with an existing one, merge the keywords into the existing niche instead
2. **Set `enabled` flags** according to the tables below — seasonal niches (Ramadan, Eid) are disabled since those seasons just passed, lower-priority niches start disabled, high-priority niches start enabled
3. **Every niche must have at least 4-6 keywords** for thorough search coverage
4. **Keywords should be how real Etsy buyers search** — think like a customer, not a cataloguer

---

## Niches to Add or Update

### UPDATE existing niches (merge new keywords into these)

**"Ramadan Planners" (DISABLE — Ramadan just passed)**
Add keywords: `"ramadan planner beginners"`, `"ramadan planner busy moms"`, `"ramadan planner students"`, `"ramadan planner new revert"`, `"ramadan business planner"`, `"ramadan content calendar"`, `"ramadan charity planner"`
Set `enabled = False`

**"Hajj & Umrah" (keep enabled — Hajj season approaching)**
Add keywords: `"umrah trip planner"`, `"hajj ritual checklist"`, `"hajj budget sheet"`, `"hajj dua list"`, `"umrah packing list printable"`, `"hajj step by step guide"`

**"Islamic Education" (keep enabled)**
Add keywords: `"islamic lesson plan"`, `"weekend madrasah plan"`, `"islamic homeschool printable"`, `"islamic studies worksheet"`

**"Eid Printables" (DISABLE — Eid just passed)**
Add keywords: `"eid al adha printable"`, `"eid party games"`, `"eid thank you card"`, `"eid money envelope printable"`
Set `enabled = False`

**"Islamic Wall Art" (keep enabled)**
Add keywords: `"minimalist arabic calligraphy"`, `"islamic calligraphy set"`, `"three piece islamic wall art"`, `"modern islamic print"`

**"Du'a Collections" (keep enabled)**
Add keywords: `"daily dua journal"`, `"answered dua log"`, `"shukr gratitude journal"`, `"islamic gratitude prompts"`

**"Islamic Wedding" (keep enabled)**
Add keywords: `"nikah planning kit"`, `"mahr planner"`, `"walimah seating chart"`, `"muslim wedding vendor tracker"`, `"islamic wedding guest list"`

---

### ADD new niches — ENABLED (high priority, run immediately)

```python
{
    "name": "Tajweed Practice Sheets",
    "keywords": [
        "tajweed worksheet", "tajweed rules printable", "tajweed practice sheet",
        "quran recitation tracker", "tajweed colour coded", "tajweed mistakes log"
    ],
    "enabled": True
},
{
    "name": "Daily Muslim Productivity",
    "keywords": [
        "muslim productivity planner", "daily muslim planner", "salah habit tracker",
        "adhkar tracker printable", "islamic daily routine", "muslim goal planner",
        "islamic habit tracker"
    ],
    "enabled": True
},
{
    "name": "New Revert Roadmap",
    "keywords": [
        "new muslim guide", "revert islam planner", "new shahada planner",
        "convert islam checklist", "new muslim learning plan", "islam basics printable",
        "new revert salah guide"
    ],
    "enabled": True
},
{
    "name": "Salah & Wudu Charts for Kids",
    "keywords": [
        "salah chart kids", "wudu steps printable", "how to pray poster kids",
        "salah reward chart", "wudu chart children", "islamic prayer steps kids"
    ],
    "enabled": True
},
{
    "name": "Arabic Alphabet Workbooks",
    "keywords": [
        "arabic alphabet tracing", "arabic letter worksheet", "arabic flashcards printable",
        "learn arabic alphabet kids", "arabic writing practice", "arabic alphabet poster"
    ],
    "enabled": True
},
{
    "name": "Aqiqah & Baby Naming",
    "keywords": [
        "aqiqah planner", "aqiqah invitation printable", "islamic baby naming",
        "aqiqah checklist", "islamic nursery print", "bismillah baby shower",
        "muslim baby shower printable"
    ],
    "enabled": True
},
{
    "name": "Minimalist Arabic Calligraphy Sets",
    "keywords": [
        "arabic calligraphy bundle", "bismillah calligraphy print",
        "subhanallah alhamdulillah print set", "islamic typography art",
        "modern arabic art print", "islamic calligraphy trio"
    ],
    "enabled": True
},
{
    "name": "Kids Islamic Affirmation Prints",
    "keywords": [
        "islamic kids poster", "muslim affirmation print", "islamic bedroom art kids",
        "i am kind islamic print", "islamic values poster children",
        "muslim kids room decor"
    ],
    "enabled": True
},
{
    "name": "Dhul Hijjah & Arafah Planners",
    "keywords": [
        "dhul hijjah planner", "day of arafah planner", "dhul hijjah ibadah tracker",
        "10 days dhul hijjah", "dhul hijjah fasting tracker", "takbeer printable",
        "dhul hijjah dua list"
    ],
    "enabled": True
},
{
    "name": "Halal Budgeting & Finance",
    "keywords": [
        "halal budget planner", "islamic finance printable", "zakat calculator printable",
        "riba free budget", "sadaqah tracker", "muslim savings planner",
        "halal debt free planner"
    ],
    "enabled": True
},
```

### ADD new niches — DISABLED (medium priority, enable later)

```python
{
    "name": "Islamic Parenting Journals",
    "keywords": [
        "islamic parenting planner", "tarbiyah journal", "muslim parenting reflection",
        "raising muslim children planner", "islamic character building worksheet",
        "muslim mom planner"
    ],
    "enabled": False
},
{
    "name": "Istikhara & Decision Journals",
    "keywords": [
        "istikhara journal", "islamic decision journal", "istikhara dua printable",
        "muslim life choices planner", "tawakkul journal", "islamic reflection prompts"
    ],
    "enabled": False
},
{
    "name": "Qur'an Memorisation Trackers for Kids",
    "keywords": [
        "hifz tracker kids", "juz amma chart", "quran memorization chart children",
        "surah tracker printable kids", "hifz reward chart", "quran progress kids"
    ],
    "enabled": False
},
{
    "name": "Adult Hifz & Revision Planners",
    "keywords": [
        "hifz planner adult", "quran revision calendar", "spaced repetition quran",
        "surah revision log", "hifz journal", "quran memorization planner adult"
    ],
    "enabled": False
},
{
    "name": "Qur'anic Vocabulary Flashcards",
    "keywords": [
        "quranic arabic flashcards", "quran vocabulary cards", "arabic quran words",
        "islamic vocabulary printable", "quran word meanings cards"
    ],
    "enabled": False
},
{
    "name": "Tawakkul & Sabr Workbooks",
    "keywords": [
        "islamic mindset journal", "sabr journal", "tawakkul workbook",
        "islamic mental health printable", "muslim wellbeing journal",
        "islamic self care planner"
    ],
    "enabled": False
},
{
    "name": "Canva Social Media Packs for Muslim Brands",
    "keywords": [
        "islamic social media templates", "muslim brand canva templates",
        "jummah reminder template", "islamic instagram post template",
        "ramadan social media kit", "eid announcement template"
    ],
    "enabled": False
},
{
    "name": "Islamic Event Invitation Templates",
    "keywords": [
        "islamic invitation template", "quran khatam invitation",
        "islamic party invitation", "ameen ceremony invitation",
        "islamic housewarming invitation", "walimah invitation template"
    ],
    "enabled": False
},
{
    "name": "Halal Small Business Finance",
    "keywords": [
        "halal business planner", "islamic profit sharing calculator",
        "halal product costing sheet", "muslim entrepreneur planner",
        "islamic business finance template"
    ],
    "enabled": False
},
{
    "name": "Masjid Themed Nursery Art",
    "keywords": [
        "masjid nursery print", "cute mosque art kids", "islamic nursery decor",
        "moon star nursery print", "muslim baby room art", "masjid illustration print"
    ],
    "enabled": False
},
{
    "name": "Islamic Motivational Quotes",
    "keywords": [
        "islamic quote printable", "muslim motivational poster",
        "islamic office wall art", "quran quote print", "hadith quote poster",
        "islamic study room decor"
    ],
    "enabled": False
},
{
    "name": "Dervish & Tasawwuf Art",
    "keywords": [
        "whirling dervish art", "sufi art print", "dervish silhouette",
        "tasawwuf wall art", "dhikr art print", "islamic spiritual art"
    ],
    "enabled": False
},
{
    "name": "Islamic Funeral & Janazah Checklists",
    "keywords": [
        "janazah checklist", "islamic funeral planner", "islamic burial checklist",
        "janazah dua printable", "muslim funeral preparation", "ghusl checklist"
    ],
    "enabled": False
},
```

### ADD new niches — DISABLED (seasonal, enable when season approaches)

```python
{
    "name": "Kids Ramadan Activity Books",
    "keywords": [
        "ramadan activity book kids", "ramadan coloring pages", "ramadan maze kids",
        "ramadan good deed chart", "ramadan daily hadith kids",
        "ramadan printable activities children"
    ],
    "enabled": False  # Enable ~6 weeks before Ramadan
},
{
    "name": "Last 10 Nights Qadr Planner",
    "keywords": [
        "laylatul qadr planner", "last 10 nights ramadan", "last ten nights ibadah",
        "qadr night dua list", "ramadan last 10 nights schedule",
        "laylatul qadr worship planner"
    ],
    "enabled": False  # Enable ~4 weeks before Ramadan
},
{
    "name": "Ramadan Business Owners Planner",
    "keywords": [
        "ramadan business planner", "ramadan marketing calendar",
        "iftar event planner", "ramadan campaign planner",
        "islamic business ramadan", "ramadan charity campaign planner"
    ],
    "enabled": False  # Enable ~8 weeks before Ramadan
},
```

---

## Implementation

### Step 1: Update the seed script

Modify `app/seed.py` (or wherever the niche seeding logic lives) to:

1. Check if each niche already exists by name (case-insensitive match)
2. If it exists: merge new keywords into the existing keyword list (no duplicates), update `enabled` status as specified above
3. If it doesn't exist: create it with the keywords and enabled status specified
4. Log what was added, updated, or skipped

Make the niche seeding **idempotent** — running it multiple times should not create duplicates or lose data.

### Step 2: Run the seed script

```bash
docker-compose exec app python -m app.seed
```

### Step 3: Verify

After running, verify in the database or via the dashboard:
- Total niches: should be around 30 (8 original minus merges + new additions)
- Enabled niches: approximately 16-18 (the high-priority ones plus non-seasonal existing ones)
- Disabled niches: approximately 12-14 (medium priority + seasonal + Ramadan/Eid)
- No duplicate niches
- Existing niches have their keywords expanded, not overwritten
- The `/research` page shows the updated niche list with correct enabled/disabled badges

---

## Files to Modify

- `app/seed.py` — Update niche seeding logic with all new niches and merge logic
- `PROJECT.md` — Add changelog entry

## Final Step: Documentation & Git Push

1. Update `PROJECT.md`:
   - Add changelog entry: `| 2026-04-12 | Extended niche library to 30+ Islamic digital product niches. High-priority enabled, seasonal/lower-priority disabled for later activation. |`
   - Add to Notes & Decisions Log: `- **2026-04-12:** Expanded from 8 to 30+ niches. Seasonal niches (Ramadan, Eid) disabled post-season. Strategy: enable ~6-8 weeks before each season. Lower-priority niches disabled until research data validates demand.`

2. Commit and push:
```bash
git add .
git commit -m "Add extended Islamic niche library — 30+ niches with keyword bundles"
git push
```
