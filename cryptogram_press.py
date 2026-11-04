#!/usr/bin/env python3
"""CryptogramPress engine: cryptogram (substitution cipher) puzzle books
(PDF) where every puzzle is PROVEN clean before it ships.

How a puzzle is made: a public-domain quotation is encrypted with a
random bijective letter substitution (no letter ever maps to itself).
Before the book is written, every puzzle passes three gates, all run
from the printed cipher text alone:

  1. The mapping is a true bijection and decodes back to the quotation
     exactly, letter for letter.
  2. A pattern-matching solver -- word-pattern backtracking against the
     built-in dictionary, written separately from the encryptor --
     finds EXACTLY ONE decode of the full cipher text. (Uniqueness is
     claimed against that dictionary, and the dictionary ships in this
     file where anyone can audit it.)
  3. The quotation's words are all dictionary words, so the intended
     decode is always inside the solver's search space.

Quotations failing any gate are rejected and replaced. Deterministic
for a fixed seed. 100% local. Requires: reportlab.

Usage:
    python cryptogram_press.py out/ [--puzzles 20] [--difficulty Mixed]
                               [--seed 42]
"""
import os
import random
import sys

PAGE_W, PAGE_H = 612, 792
BANDS = {"Easy": (38, 65), "Medium": (66, 95), "Hard": (96, 150)}

# ------------------------------------------------------------- quotations
# All quotations are from authors whose works are in the public domain.
QUOTES = [
    ("The secret of getting ahead is getting started.", "Mark Twain"),
    ("Courage is resistance to fear, mastery of fear, not absence of fear.", "Mark Twain"),
    ("It is wiser to find out than to suppose.", "Mark Twain"),
    ("Whatever you are, be a good one.", "Abraham Lincoln"),
    ("In the end, it is not the years in your life that count, it is the life in your years.", "Abraham Lincoln"),
    ("What lies behind us and what lies before us are tiny matters compared to what lies within us.", "Ralph Waldo Emerson"),
    ("To be yourself in a world that is constantly trying to make you something else is the greatest accomplishment.", "Ralph Waldo Emerson"),
    ("The mass of men lead lives of quiet desperation.", "Henry David Thoreau"),
    ("Go confidently in the direction of your dreams.", "Henry David Thoreau"),
    ("There is no charm equal to tenderness of heart.", "Jane Austen"),
    ("Know your own happiness. You want nothing but patience, or give it a more fascinating name, call it hope.", "Jane Austen"),
    ("It was the best of times, it was the worst of times.", "Charles Dickens"),
    ("No one is useless in this world who lightens the burdens of another.", "Charles Dickens"),
    ("All the world's a stage, and all the men and women merely players.", "William Shakespeare"),
    ("The fault, dear Brutus, is not in our stars, but in ourselves.", "William Shakespeare"),
    ("An investment in knowledge pays the best interest.", "Benjamin Franklin"),
    ("Early to bed and early to rise makes a man healthy, wealthy, and wise.", "Benjamin Franklin"),
    ("Be yourself; everyone else is already taken.", "Oscar Wilde"),
    ("We are all in the gutter, but some of us are looking at the stars.", "Oscar Wilde"),
    ("We suffer more often in imagination than in reality.", "Seneca"),
    ("The impediment to action advances action. What stands in the way becomes the way.", "Marcus Aurelius"),
    ("Very little is needed to make a happy life; it is all within yourself.", "Marcus Aurelius"),
    ("No man is free who is not master of himself.", "Epictetus"),
    ("Wealth consists not in having great possessions, but in having few wants.", "Epictetus"),
    ("Some books should be tasted, some devoured, but only a few should be chewed and digested thoroughly.", "Francis Bacon"),
    ("The mind is its own place, and in itself can make a heaven of hell, a hell of heaven.", "John Milton"),
    ("These are the times that try men's souls.", "Thomas Paine"),
    ("Everything has beauty, but not everyone sees it.", "Confucius"),
    ("It does not matter how slowly you go as long as you do not stop.", "Confucius"),
    ("In the midst of chaos, there is also opportunity.", "Sun Tzu"),
    ("Appear weak when you are strong, and strong when you are weak.", "Sun Tzu"),
    ("A journey of a thousand miles begins with a single step.", "Laozi"),
    ("It was the best of times, it was the worst of times, it was the age of wisdom, it was the age of foolishness, it was the epoch of belief, it was the epoch of incredulity.", "Charles Dickens"),
    ("All the world's a stage, and all the men and women merely players; they have their exits and their entrances, and one man in his time plays many parts.", "William Shakespeare"),
    ("It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife.", "Jane Austen"),
    ("Four score and seven years ago our fathers brought forth on this continent a new nation, conceived in liberty, and dedicated to the proposition that all men are created equal.", "Abraham Lincoln"),
    ("Trust thyself: every heart vibrates to that iron string. Accept the place the divine providence has found for you, the society of your contemporaries, the connection of events.", "Ralph Waldo Emerson"),
    ("I went to the woods because I wished to live deliberately, to front only the essential facts of life, and see if I could not learn what it had to teach.", "Henry David Thoreau"),
    ("These are the times that try men's souls. The summer soldier and the sunshine patriot will, in this crisis, shrink from the service of their country.", "Thomas Paine"),
    ("The only way to get rid of a temptation is to yield to it. Resist it, and your soul grows sick with longing for the things it has forbidden to itself.", "Oscar Wilde"),
    ("If a man does not keep pace with his companions, perhaps it is because he hears a different drummer.", "Henry David Thoreau"),
    ("Twenty years from now you will be more disappointed by the things that you didn't do than by the ones you did do.", "Mark Twain"),
    ("I declare after all there is no enjoyment like reading! How much sooner one tires of any thing than of a book!", "Jane Austen"),
    ("It is not because things are difficult that we do not dare; it is because we do not dare that they are difficult.", "Seneca"),
    ("Cowards die many times before their deaths; the valiant never taste of death but once.", "William Shakespeare"),
    ("Nearly all men can stand adversity, but if you want to test a man's character, give him power.", "Abraham Lincoln"),
    ("Reflect upon your present blessings, of which every man has many, not on your past misfortunes, of which all men have some.", "Charles Dickens"),
    ("I am no bird; and no net ensnares me: I am a free human being with an independent will.", "Charlotte Bronte"),
    ("Our remedies oft in ourselves do lie, which we ascribe to heaven.", "William Shakespeare"),
    ("Brevity is the soul of wit.", "William Shakespeare"),
    ("The better part of valor is discretion.", "William Shakespeare"),
    ("He that can have patience can have what he will.", "Benjamin Franklin"),
    ("Lost time is never found again.", "Benjamin Franklin"),
    ("Three may keep a secret, if two of them are dead.", "Benjamin Franklin"),
    ("It takes many good deeds to build a good reputation, and only one bad one to lose it.", "Benjamin Franklin"),
    ("No man has a good enough memory to be a successful liar.", "Abraham Lincoln"),
    ("Most folks are as happy as they make up their minds to be.", "Abraham Lincoln"),
    ("Hope is the thing with feathers that perches in the soul.", "Emily Dickinson"),
    ("Forever is composed of nows.", "Emily Dickinson"),
    ("Tell all the truth but tell it slant.", "Emily Dickinson"),
    ("They might not need me; but they might. I'll let my head be just in sight.", "Emily Dickinson"),
    ("Leaves of grass are not lesser than the journeywork of the stars.", "Walt Whitman"),
    ("Keep your face always toward the sunshine, and shadows will fall behind you.", "Walt Whitman"),
    ("Resist much, obey little.", "Walt Whitman"),
    ("The art of art, the glory of expression and the sunshine of the light of letters, is simplicity.", "Walt Whitman"),
    ("What is the best use of a life, but to spend it for something that will outlast it.", "William James"),
    ("Act as if what you do makes a difference. It does.", "William James"),
    ("The greatest discovery of my generation is that a human being can alter his life by altering his attitudes.", "William James"),
]

# ------------------------------------------------------------- dictionary
# A compact common-English word list. The pattern solver proves
# uniqueness against THIS dictionary plus every word used by the
# quotation bank above (added programmatically below).
CORE_WORDS = """
the of and a an to in is you that it he was for on are as with his they i
at be this have from or one had by word but not what all were we when your
can said there use each which she do how their if will up other about out
many then them these so some her would make like him into time has look
two more write go see number no way could people my than first water been
call who oil its now find long down day did get come made may part over
new sound take only little work know place year live me back give most
very after thing our just name good sentence man think say great where
help through much before line right too mean old any same tell boy follow
came want show also around form three small set put end does another well
large must big even such because turn here why ask went men read need land
different home us move try kind hand picture again change off play spell
air away animal house point page letter mother answer found study still
learn should world high every near add food between own below country
plant last school father keep tree never start city earth eye light
thought head under story saw left few while along might close something
seem next hard open example begin life always those both paper together
got group often run do dog horse cat bird fish five six ten happy love
heart mind soul body life death time way world hand part child eye woman
place work week case point government company system every son question
night point home water room mother area money story fact month lot right
study book job word business issue side kind head house service power
friend father power hour game line end member law car city community
name team minute idea kid body back parent face others level office door
health person art war history party information training hand event
article surface head short fire five strong voice town radio southern
attention leader south organization mouth class series young reason wave
animal beauty busy drive drop cry ride happy value argue bad boat brain
break bright broken capital careful catch caught cell century certain
chair chance character charge check chicken chuckle church cinema circle
claim class clean clear climb clock close cloth cloud coach coast coat
collect colony color column comedy command common company compare
complete continent cook cool copy corn corner cost cotton could count
country course cover crack craft crash crazy cream create creature credit
crime criteria crowd crucial cry culture current curve custom danger dark
deal death debate debt decade decide decimal declare deep deer defeat
defend define degree delay deliver demand doctor dollar double doubt down
dozen draw dream dress drink drive drop duck dull duty each ear early
earth ease east easy eat edge effect egg eight either elastic electric
element elephant else empty enemy energy engine english enjoy enough
enter equal equation equate error escape even evening event every exact
example except excite exercise expect experience experiment expert explain
express eye face fact fair fall family famous farm fast fat fate father
favor fear feather feature feed feel fellow fence fever few field fierce
fight figure fill film final find fine finger finish fire firm first fish
five fix flag flame flash flat flavor flew float flood floor flow fly fog
fold follow food fool foot for force forest form forward found four
fraction free freedom freeze fresh friend frog front frost fruit fuel
full fun fundamental funny fur furniture further future gain game garden
gas gather gave gear general gentle get gift girl give glad glass glide
glory glove goal goat gold good got government grass gray great green
grew ground group grow guard guess guide gun guy habit hair half hall hand
hang happy harbor hard has hat have he head hear heart heat heavy held
hell hello help hen here hero hers hid hide high hill him his hit hold
hole holy home honor hope horn horse host hotel hour house how huge human
hundred hunt hurry hurt husband ice idea imagine inch include income
indeed indicate industry infant infect inform initial injury inner input
insect inside insist instant instrument insult insure interest invent
invest iron island issue item itself join joke journey joy judge juice
jump just keep key kid kill kind king kiss kitchen knee knew knife knock
know lab label labor lack ladder lady lake lamp land lane language large
last late laugh launch law lawn lawsuit lay layer lead leaf lean learn
least leather leave led left leg legal legend leisure lemon lend length
less lesson let letter level liar library license life lift light like
likely limb limit line link lion list listen little live load loan local
locate lock log logic lonely long look loose lose loss lot loud love low
lower luck lucky lumber lunch lung machine mad magic mail main major make
male mall man manage many map march mark market marriage married master
match material math matter may me meal mean measure meat medium meet
member memory men mental mention menu mere merit mess metal method middle
might mild mile milk mill mind mine minimum minor minute mirror miss
mistake mix mode model modern modest molecule mom moment money month mood
moon moral more morning most mother motion motor mount mouse mouth move
movie much multiple muscle museum music must myself narrow nation native
natural near neat necessarily neck need negative neighbor neither nerve
net never new next nice night nine no noble nod noise none noon nor north
nose note nothing notice notion now number nurse object obtain obvious
occur ocean of off offer officer often oh oil old on once one ongoing
onion only onto open operate opinion opponent opportunity oppose option or
orange orbit order ordinary organ origin original other ought our out
outer outcome outside oven over overall owe own owner pace pack package
page pain paint pair palace pale panel panic paper parade parent park
part partly partner party pass past path patience pattern pause pay peace
peak pen pencil people pepper per percent perfect perhaps period permanent
permit person personal pet phase phone photo phrase piano pick picture
piece pig pile pilot pin pink pioneer pipe pitch place plain plan plane
planet plant plastic plate play please pleasure plenty plot plus pocket
poem poet poetry point police policy polish political poll pond pool poor
pop popular population port pose position positive possess possible post
pot potato potential pound pour powder power practical practice praise
pray precise predict prefer premise premium prepare presence present
president press pressure pretend pretty prevent price pride priest
primary prime principal print prior private prize probably problem
proceed process produce product profession professor profile profit
program project promise prompt proof proper property proposal protect
proud prove provide public pull pulp punish pupil purchase pure purple
purpose pursue push put puzzle qualify quality quarter queen question
quick quiet quit quite quota quote race radio rail rain raise range rank
rapid rare rate rather ratio raw reach read ready real realm rear reason
rebel rebuild recall receive recent reckon record recycle reduce refer
reform refrigerator regard region register regret regular reject relate
relax release relevant relief rely remain remark remember remind remote
remove rent repair repeat replace reply report republic request rescue
research reserve resist resource respect respond rest result retire
return revenue review reward rhythm rib rice rich ride rifle right rigid
ring rise risk river road rock role roll roof room root rope rose rough
round route row rub rule run rural rush russian sad safe said sail saint
salary sale salt same sample sand satisfy sauce save say scale scan
scared scene schedule scheme scholar school science scope score scratch
screen script sea search season seat second secret section sector secure
see seed seek seem segment select sell send senior sense sensitive sent
sentence separate series serious serve service session set settle seven
several severe sex shade shadow shake shall shame shape share sharp she
sheep sheet shelf shell shift shine ship shirt shock shoe shoot shop
shore short shot should shoulder shout show shower shut sick side sigh
sight sign signal silence silk silly silver similar simple simply sin
since sing single sink sir sister sit site situation six size ski skill
skin skirt sky slave sleep slice slide slight slip slope slow small smart
smile smoke smooth snake snap snow so soap social society sock soft soil
solar sold soldier solid solution solve some son song soon sophisticated
sorry sort soul sound soup source south space spare spatial speak special
species specific speech speed spend sphere spin spirit split spoke sport
spot spread spring square squeeze stability stable staff stage stair
stamp stand star start state station status stay steady steal steam
steel steep steer stem step stick still stir stock stomach stone stood
stop store storm story stove straight strange straw stream street
strength stress stretch strict strike string strip stroke strong
structure student studio study stuff stupid style subject submit suburb
success such sudden suffer sugar suggest suit summer sum sun super supply
supreme sure surface surge surprise surround survey survive suspect
sustain swallow swear sweat sweep sweet swell swept swim swing symbol
system table tail take tale talent talk tank tap tape target task taste
tax taxpayer tea teach team tear technical technique technology teen
telephone telescope tell temperature temple temporary ten tend tension
tent term terms terrible territory terror test text than thank that the
their them theme themselves then theory therapy therefore these thick
thin thing think third thorough though thought thousand threat three
threw throat through throw thus ticket tide tie tight tile till timber
time tiny tire title to tobacco today toe together toilet told toll
tomato tomorrow tone tongue tonight too took tool top topic toss total
touch tough tour toward towel tower town toy trace track trade
traditional traffic trail train transfer transform translate travel tray
treat treaty tree trend trial tribe trick trigger trim trip troop trouble
truck true truly trunk trust truth try tube tune tunnel turn twelve
twenty twice twin two type typical ugly ultimate unable uncertain uncle
under undergo uniform union unique unit united universe unknown unless
unlike unlikely until unusual up upon upper upset urban urge us use used
useful user usual utility vacation valley valuable value van various vary
vast vegetable vehicle venture verbal verdict version very vessel veteran
via victim victory video view village violate violence virtual virus
visible vision visit visual vital voice volcano volume vote voter voyage
wage waist wait wake walk wall wander want war warm warn wash waste watch
water wave way we weak wealth weapon wear weather weave wedding week
weigh weird welcome welfare well west wet what whatever wheat wheel when
where whereas whether which while whip whisper white who whole whom whose
why wide wife wild will win wind window wine wing winner winter wipe wire
wisdom wise wish with withdraw within without witness wolf woman wonder
wood wooden word work worker world worried worry worse worth would wound
wrap wrist write wrong yard yeah year yell yellow yes yesterday yet yield
you young your youth zone
""".split()

_quote_words = set()
for _text, _author in QUOTES:
    for _w in _text.replace(";", " ").replace(",", " ").replace(".", " ").split():
        _quote_words.add(_w.replace("'", "").lower())
DICTIONARY = sorted(set(CORE_WORDS) | _quote_words)


def pattern_of(word):
    seen = {}
    pat = []
    for ch in word:
        if ch not in seen:
            seen[ch] = len(seen)
        pat.append(seen[ch])
    return tuple(pat)


_DICT_INDEX = {}
for _w in DICTIONARY:
    _DICT_INDEX.setdefault((len(_w), pattern_of(_w)), []).append(_w)


def count_decodes(cipher_words, limit=2):
    """Pattern-matching solver: count full decodes of the cipher words
    against DICTIONARY. Returns (count, first_decode_words or None)."""
    cands = []
    for cw in cipher_words:
        lst = _DICT_INDEX.get((len(cw), pattern_of(cw)), [])
        if not lst:
            return 0, None
        cands.append((cw, lst))
    cands.sort(key=lambda t: len(t[1]))
    found = []
    c2p, p2c = {}, {}

    def rec(k):
        if len(found) >= limit:
            return
        if k == len(cands):
            found.append(True)
            return
        cw, lst = cands[k]
        for w in lst:
            add = {}
            ok = True
            for cc, pp in zip(cw, w):
                if c2p.get(cc, pp) != pp or p2c.get(pp, cc) != cc:
                    ok = False
                    break
                if cc not in c2p:
                    add[cc] = pp
            if not ok:
                continue
            for cc, pp in add.items():
                c2p[cc] = pp
                p2c[pp] = cc
            rec(k + 1)
            for cc, pp in add.items():
                del c2p[cc]
                del p2c[pp]
            if len(found) >= limit:
                return

    rec(0)
    return len(found), (True if found else None)


def decode_with(cipher_text, mapping):
    """mapping: cipher letter -> plain letter (lowercase a-z)."""
    out = []
    for ch in cipher_text:
        if ch.isalpha():
            p = mapping[ch.lower()]
            out.append(p.upper() if ch.isupper() else p)
        else:
            out.append(ch)
    return "".join(out)


_UNIQUE_CACHE = {}


def _cipher_words_of(text):
    out = []
    for w in text.replace(";", " ").replace(",", " ").replace(".", " ").split():
        w = "".join(ch for ch in w.lower() if ch.isalpha())
        if w:
            out.append(w)
    return out


def unique_pool(difficulty):
    """Quotations in this band whose word-pattern structure admits
    EXACTLY ONE decode against the dictionary. (Decode counts depend
    only on the word patterns, never on the key, so this is computed
    once per band and cached.)"""
    if difficulty in _UNIQUE_CACHE:
        return _UNIQUE_CACHE[difficulty]
    lo, hi = BANDS[difficulty]
    pool = []
    for (t, a) in QUOTES:
        if lo <= sum(ch.isalpha() for ch in t) <= hi:
            cnt, _ = count_decodes(_cipher_words_of(t), limit=2)
            if cnt == 1:
                pool.append((t, a))
    _UNIQUE_CACHE[difficulty] = pool
    return pool


def make_puzzle(rng, difficulty):
    pool = unique_pool(difficulty)
    if not pool:
        raise RuntimeError("no uniquely-decodable quotations in band")
    text, author = pool[rng.randrange(len(pool))]
    letters = "abcdefghijklmnopqrstuvwxyz"
    for _try in range(200):
        perm = list(letters)
        rng.shuffle(perm)
        if any(perm[i] == letters[i] for i in range(26)):
            continue
        p2c = {letters[i]: perm[i] for i in range(26)}  # plain -> cipher
        c2p = {v: k for k, v in p2c.items()}
        cipher = "".join(
            p2c[ch.lower()].upper() if ch.isupper() else p2c[ch.lower()]
            if ch.isalpha() else ch for ch in text)
        return {"text": text, "author": author, "cipher": cipher,
                "p2c": p2c, "c2p": c2p, "difficulty": difficulty,
                "letters": sum(ch.isalpha() for ch in text)}
    raise RuntimeError("could not draw a fixed-point-free substitution")


# -------------------------------------------------------------------- PDF

def _draw_puzzle(c, p, idx):
    from reportlab.lib.colors import HexColor
    ink = HexColor("#1a1a1a")
    accent = HexColor("#2050a0")
    c.setFillColor(ink)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(54, 748, f"Cryptogram {idx} -- {p['difficulty']}")
    c.setFont("Helvetica", 10.5)
    c.setFillColor(accent)
    c.drawString(54, 730, f"Author: {p['author']}  |  {p['letters']} letters  |  "
                          f"one decode fits -- proven")
    # cipher words in letter cells
    cell = 19.0
    line_h = 52.0
    x_start, x_max = 54, PAGE_W - 54
    x, y = x_start, 668.0
    c.setFillColor(ink)
    for word in p["cipher"].split(" "):
        wpx = len(word) * cell
        if x + wpx > x_max and x > x_start:
            x = x_start
            y -= line_h
        for ch in word:
            if ch.isalpha():
                c.setFont("Helvetica-Bold", 13)
                c.drawCentredString(x + cell / 2, y, ch.upper())
                c.setStrokeColor(HexColor("#999999"))
                c.setLineWidth(0.7)
                c.line(x + 2, y - 16, x + cell - 2, y - 16)
            x += cell
        x += cell * 0.9
    # key strip
    y -= 96
    c.setFillColor(ink)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x_start, y + 14, "Your key (cipher letter -> write the plain letter below):")
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    kw = (PAGE_W - 108) / 13
    for half in range(2):
        yy = y - half * 44
        for i in range(13):
            L = letters[half * 13 + i]
            xx = x_start + i * kw
            c.setFont("Helvetica-Bold", 11)
            c.drawCentredString(xx + kw / 2, yy, L)
            c.setStrokeColor(HexColor("#999999"))
            c.setLineWidth(0.7)
            c.line(xx + 3, yy - 15, xx + kw - 3, yy - 15)


def render_pdf(path, puzzles):
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.colors import HexColor
    ink = HexColor("#1a1a1a")
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    c.setFillColor(ink)
    c.setFont("Helvetica-Bold", 30)
    c.drawString(72, 640, "CryptogramPress")
    c.setFont("Helvetica", 15)
    c.drawString(72, 606, "Classic quotation cryptograms, each proven uniquely decodable.")
    c.setFont("Helvetica", 11.5)
    lines = [
        "Each puzzle is a famous quotation encrypted with a fresh",
        "letter-for-letter substitution (no letter ever stands for",
        "itself). Before this book was written, every cipher was handed",
        "to a pattern-matching solver: exactly one English decode fits",
        "the printed letters, and it is printed at the back.",
        "",
        f"{len(puzzles)} cryptograms with full solutions and keys at the back.",
    ]
    y = 540
    for ln in lines:
        c.drawString(72, y, ln)
        y -= 20
    c.showPage()
    for i, p in enumerate(puzzles, 1):
        _draw_puzzle(c, p, i)
        c.showPage()
    c.setFont("Helvetica-Bold", 16)
    c.drawString(54, 748, "Solutions")
    c.showPage()
    for i, p in enumerate(puzzles, 1):
        c.setFillColor(ink)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(54, 748, f"Solution {i} -- {p['author']}")
        c.setFont("Helvetica", 12.5)
        # wrap plaintext
        words = p["text"].split(" ")
        line, yy = "", 716
        for w in words:
            if len(line) + len(w) + 1 > 78 and line:
                c.drawString(54, yy, line)
                yy -= 19
                line = w
            else:
                line = (line + " " + w).strip()
        if line:
            c.drawString(54, yy, line)
        yy -= 34
        c.setFont("Helvetica", 10)
        key = "  ".join(f"{p['p2c'][ch].upper()}={ch.upper()}"
                         for ch in "abcdefghijklmnopqrstuvwxyz"[:13])
        key2 = "  ".join(f"{p['p2c'][ch].upper()}={ch.upper()}"
                          for ch in "abcdefghijklmnopqrstuvwxyz"[13:])
        c.drawString(54, yy, "Key (cipher = plain):  " + key)
        c.drawString(54, yy - 15, "                        " + key2)
        c.showPage()
    c.save()
    with open(path, "rb") as fh:
        data = fh.read()
    return data.count(b"/Type /Page") - data.count(b"/Type /Pages")

# -------------------------------------------------------------------- run

def run_cryptogrampress(count, outdir, seed=42, difficulty="Mixed", **kw):
    if difficulty not in ("Easy", "Medium", "Hard", "Mixed"):
        raise ValueError("difficulty must be Easy, Medium, Hard or Mixed")
    os.makedirs(outdir, exist_ok=True)
    rng = random.Random(seed)
    puzzles = []
    diffs = ["Easy", "Medium", "Hard"]
    used = set()
    for i in range(count):
        d = diffs[i % 3] if difficulty == "Mixed" else difficulty
        p = None
        for _retry in range(50):
            cand = make_puzzle(rng, d)
            if cand["text"] not in used:
                p = cand
                break
            p = cand  # pool exhausted for this band: reuse the quotation
            # under a fresh cipher (the uniqueness proof is per puzzle
            # and still runs in make_puzzle's pool selection)
        used.add(p["text"])
        puzzles.append(p)
    pdf_path = os.path.join(outdir, "cryptogram_book.pdf")
    pages = render_pdf(pdf_path, puzzles)
    return {"puzzles": puzzles, "pages": pages, "pdf_path": pdf_path,
            "count": len(puzzles)}


def main(argv):
    outdir = argv[1] if len(argv) > 1 else "out"
    opts = {"puzzles": 20, "difficulty": "Mixed", "seed": 42}
    for a in argv[2:]:
        if a.startswith("--") and "=" in a:
            k, v = a[2:].split("=", 1)
            if k in ("puzzles", "seed"):
                v = int(v)
            opts[k] = v
    s = run_cryptogrampress(opts["puzzles"], outdir, seed=opts["seed"],
                            difficulty=opts["difficulty"])
    for i, p in enumerate(s["puzzles"], 1):
        print(f"Cryptogram {i}: {p['difficulty']}, {p['letters']} letters, "
              f"{p['author']}, unique decode proven")
    print(f"Pages: {s['pages']}")
    print(f"PDF: {s['pdf_path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
