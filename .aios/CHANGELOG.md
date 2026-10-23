# BigWork AI-OS engine changes

Plain English, newest on top. `/upgrade --check` shows the owner the entry for the version on offer.

## 0.3.12
- Your live review. Say "give me my live review" (or type `/live`) and the brain builds a page of
  everything going on: every open follow-up, every client's next step, and anything waiting for
  your OK, biggest priority first. Tick what's done, add a note to any line, ask Claude about any
  item, then send it all back. The brain files each change in the right place: the follow-up
  list, the client's folder and its history. Your notes never let it send or spend anything.
- The page wears your look, not ours. Your logo, your colours, your fonts, from one small file in
  your company folder (`company/look.json`); say "make it look like my website" and the brain fills
  it in. With nothing set it is plain and quiet. No BigWork branding anywhere on it.
- Send saves straight into your brain, the same way everything else does. No approval screens.
- Every send comes back with a receipt. The brain checks each of your decisions against your
  files: a ticked follow-up really closed, a new date is the date you asked for, a client's last
  touch really moved, a dropped item really left. A note the files cannot prove shows with your
  own words and a "Looks right" button, so you are the one who confirms it. A send that never
  gets a receipt shows as a problem, never as done.
- Where your ticks and notes live: the page is hosted by Anthropic, and what you type on it is
  stored there and kept as history after Send copies your decisions into the brain. The access
  page now says so. Put nothing on the page you would not put in the brain.
- The Friday review ends by offering the same page.
- In Codex, or in a Claude session that cannot publish pages, the page opens as a file instead and
  ticks and notes do not save; the brain says so when that happens.
- After an update, the brain points you to a "what's new" page for the version it just installed.

## 0.3.11
- Works in Codex, not only Claude. The installer picks Codex when that is what you have and never asks you to install Claude. Commands are available as `$start`, `$week` and so on. Codex cannot save by itself when a window closes, so the brain saves when you say "save" and is told to do it before every session ends.
- The guide now shows Claude and Codex side by side: how to open the brain, what to type, how saving works.

## 0.3.10
- Updates are now checked before they install. Only a release signed by BigWork's key, matching
  BigWork's published release list, and newer than the one you have, can go in. The first time, the
  brain reads you the key's fingerprint to confirm against your welcome kit; after that it is pinned.
- "Ask before upgrading" is now honoured by the updater itself, not only when a session starts, so a
  scheduled job cannot slip past it. A missing or garbled setting means ask.
- /upgrade shows the changes and waits for your yes. The Friday review offers it instead of running it.
- If an update fails partway, every file in the brain goes back exactly as it was.
- A brain can no longer push itself into BigWork's public kit, whatever its GitHub copy points at.
  (Found by a friends-week owner on 2026-10-07, and by BigWork's own rehearsal the same day.)

## 0.3.8
- Connect Xero, Stripe or your bookkeeping software and the brain will look up invoices, reports and totals for
  you. It still never changes a record there, never moves money, and never saves a card or bank
  number. Your permissions page is updated to say so.
- When a site blocks the brain (Facebook, Yellow Pages and many directories do), it tells you which
  ones and asks you to open them in your browser or save them as a PDF and drop them in, instead of
  quietly skipping them.

## 0.3.7
- A coach in the Friday review. From your follow-up list, what the brain did for you, and where
  the week's work went, it tells you two things you did well and one habit worth changing, with
  the numbers behind each. It says what it can't see (calls, texts, work outside Claude) and asks
  you before drawing a conclusion. No screen recording.

## 0.3.6
- Straight answers about what it searched. When the brain looks in your email, Drive, calendar or
  meeting recorder, it says what it searched, shows where each answer came from, and says what it
  didn't look at, so a confident answer never hides a thin search.
- A freshness check in the Friday review: facts that disagree, guesses nobody confirmed, and facts
  not checked in six months come back to you as a few quick questions, so the brain doesn't quietly
  go stale.

## 0.3.5
- Your skills show up where you'd look: type / in a new chat to see them, or just ask for one in
  your own words. Skills you taught before this update are moved there for you.
- Every new skill meets a quality bar: it reads your numbers from your files instead of guessing,
  says exactly what "tight" or "overdue" means, checks what could clash, drafts in your voice, and
  puts any date it promises on your follow-up list.
- A tidy-up check after your files and accounts are read: the same customer twice, one product with
  two prices, an old reminder for a paid invoice, a date that can't be kept. Each one is a quick
  question for you.

## 0.3.4
- Your voice is your first skill. The brain builds it from a few real samples of you writing and
  talking (emails to customers and friends, a meeting where you talk, a blog post), or starts from
  a voice guide you already have and sharpens it. It tests it on a real draft with you, and every
  draft after that sounds like you.

## 0.3.3
- PDFs are read and checked like every other file. Price lists, quotes and invoices no longer
  wait for you to vouch for them; only a photo or scan of paper is left for your yes.
- Your business numbers are welcome: sales, costs, margins, invoices, what's owed. Spreadsheets full
  of numbers no longer set off a false card-number alarm. Payroll is your call: the brain asks once.
  Bank and card numbers, passwords, ID numbers and personal matters still stay out.

## 0.3.2
- The checker never follows a shortcut. A shortcut in your documents folder can point at your
  private folder, so the checker passes over shortcuts and hidden files, names them, and reads
  none of them.
- The checker now catches bank account and routing numbers (written next to "routing",
  "bank account" or "account number"), IBANs and social security numbers, as well as cards,
  passwords and keys. A plain customer or supplier account number is left alone.
- A business name with quotes or accents installs cleanly: Café becomes cafe in the folder name,
  and upgrades keep the full name.
- A damaged download or a GitHub name that is already taken now says so plainly and leaves nothing
  half-made behind.

## 0.3.1
- The first session sounds like a person now: warmer, shorter, straight to the point. With no
  website it says it will start with your files, not ask you instead.
- Adding your files is one move: drag files or folders into the chat (or pick them with the +)
  and hit Enter, as much as you've got. The brain copies them into your documents folder, checks
  them, then sorts them.

## 0.3.0
- Your files come before the first job: after your website (or straight away if you have none),
  the brain reads your documents folder, so the first job uses your real material instead of
  asking you questions.
- You decide what the brain may do on its own. A new permissions page starts empty; say "you can
  always do that" and it adds the job, "stop doing that" and it takes it off. Money, deleting
  anything and your bank are never on it.
- Every action it takes outside the brain (a send, a booking, a change) is written to an action
  log, and the weekly review reads it back to you.

## 0.2.0
- The first session reads before it asks: after your website and the first job, it takes your
  documents folder and the accounts you choose to connect (email, Drive, calendar, meeting
  recorder), and only then asks about what is still missing. Anything it found is read back to
  you as a question instead of asked from scratch.

## 0.1.0
- First engine: kickoff interview, six commands, automatic saving, automatic meeting sweep,
  safety checks, one line of history on main.
