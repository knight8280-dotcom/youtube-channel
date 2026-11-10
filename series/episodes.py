"""Scripts for episodes 2-11 of the plant-operators Shorts series.

    python3 series/episodes.py      # (re)writes videos/<episode>/script.json for every episode

Each episode is a list of beats (one shot each). Lines are voiced with the
characters in engine/cast.json; frames are generated from the prompts below
using the shared character descriptions, so the cast looks the same every episode.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

STYLE = ("Vertical 9:16 still from a glossy 3D animated family movie (modern CGI animation studio style, big expressive eyes, "
         "stylized proportions, soft subsurface skin, highly detailed render, cinematic lighting).")
END = "Comedic. No text, no words, no logos, no captions."
CAMO = ("a stocky young plant operator with a round face, light stubble and brown hair, wearing a camo trucker hat with tan mesh back "
        "and a dark leather American flag patch, an olive-brown camo quarter-zip pullover with a black two-way radio clipped on his chest, "
        "navy work pants and muddy brown work boots")
STACHE = ("a lean young plant operator with a thin mustache and dark brown hair, black baseball cap, light blue button-up work shirt "
          "with sleeves rolled up, colorful tattoo sleeve on his forearm, black smartwatch, navy work pants and white sneakers")
MAINT = "a gruff big-bellied maintenance mechanic in his 50s with a gray goatee, scuffed white hard hat and grease-stained gray coveralls"
ENG = "a skinny nervous young process engineer with big round glasses, a spotless white hard hat, a tucked-in teal polo shirt and khakis"
MGR = "a plant manager in his 40s with neat gelled hair, a crisp white dress shirt, red tie and a spotless white hard hat"
DAY = "a cheerful female day-shift plant operator in her 30s with a ponytail, white hard hat and an orange high-visibility vest over a navy work shirt"
NEW = ("a skinny wide-eyed young new hire in spotless brand-new navy coveralls, shiny new boots, an oversized brand-new white hard hat "
       "with a green sticker, and a huge backpack")
ROOM = ("an industrial plant control room with a whiteboard covered in yellow caution tags, teal window blinds, desks with glowing "
        "monitors and charging two-way radios")
BOTH = f"LEFT: {CAMO}. RIGHT: {STACHE}."


def frames(**prompts):
    return {k: {"file": f"{k.lower()}.jpg", "prompt": f"{STYLE} {p} {END}"} for k, p in prompts.items()}


def say(who, text, **kw):
    return {"who": who, "text": text, **kw}


EPISODES = {}

# ------------------------------------------------------------------ 02
EPISODES["02-shift-turnover"] = {
    "title": "Shift Turnover",
    "frames": frames(
        A=f"Inside {ROOM}. In the doorway stands {DAY}, with a huge sunny smile and a thumbs up. Through the big window behind her the "
          f"process unit is clearly in trouble: black smoke billowing, a flare roaring, orange flashing lights. In the foreground two operators "
          f"sit in black mesh office chairs seen from behind: one in a camo trucker hat and camo pullover, one in a black cap and light blue work shirt.",
        B=f"Close two-shot inside {ROOM}. Two operators sitting in black mesh office chairs squint with deep suspicion, side-eye, one eyebrow raised. {BOTH}",
        C="Close-up of an industrial plant control board: a whole wall of computer monitors and panels covered in flashing red and yellow "
          "alarm boxes, blinking warning lights everywhere, absurdly many alarms, lit up like a Christmas tree, dark room.",
        D=f"{DAY} sprinting out of a plant gate toward the parking lot at golden sunset, lunchbox in hand, ponytail flying, a big cartoon dust "
          "cloud behind her, joyful face, extreme speed.",
        E=f"Night inside {ROOM}. Two operators both facepalming at the same time, slumped in their office chairs. {BOTH}",
    ),
    "danger": ["2019."],
    "beats": [
        {"shot": "A", "dur": 2.6, "zoom": [1.05, 1.12], "music": "comedy",
         "texts": [{"style": "title", "lines": ["SHIFT TURNOVER", "BE LIKE"], "emoji": "🙃"}]},
        {"shot": "A", "flash": True, "zoom": [1.3, 1.45], "cx": [0.5, 0.5], "cy": [0.3, 0.32],
         "chip": {"text": "☀️ DAY SHIFT", "bg": "#ffd400", "fg": "#111"},
         "lines": [say("day", "Everything's good! Nothing to report!")]},
        {"shot": "B", "zoom": [1.0, 1.12], "cy": [0.4, 0.38],
         "lines": [say("stache", "Then why is the board lit up like a Christmas tree?")]},
        {"shot": "C", "fx": ["alarm"], "zoom": [1.0, 1.15], "amb": [{"name": "beeps", "gain": 0.08}],
         "lines": [say("day", "Oh, those? Those have been in alarm since 2019.")]},
        {"shot": "D", "flash": True, "fx": ["shake_small"], "music": "fast", "zoom": [1.05, 1.2], "min": 2.0,
         "sfx": [{"name": "whoosh", "after_line": 0, "offset": 0.05, "gain": 0.4}],
         "lines": [say("day", "Okay, bye!")], "post": 0.9},
        {"shot": "E", "music": "comedy", "zoom": [1.0, 1.1],
         "lines": [say("camo", "She's gone."), say("stache", "And she took the good radio.")],
         "texts": [{"style": "note", "header": "DAY SHIFT LOG:", "lines": ["all good :)"], "after_line": 1, "offset": 0.2, "y": 860}]},
    ],
    "cta": ["TAG YOUR", "DAY SHIFT"],
}

# ------------------------------------------------------------------ 03
EPISODES["03-work-orders"] = {
    "title": "Work Orders",
    "frames": frames(
        A=f"Inside {ROOM}. {CAMO} sits at a computer typing with one finger, smug and proud of himself, face lit by the monitor.",
        B=f"Daytime inside an industrial pump house. {MAINT} kneels next to a large quiet blue industrial pump with his ear pressed "
          "against it, puzzled, shrugging with one hand.",
        C=f"Night inside an industrial pump house. A large blue industrial pump shaking violently, screeching, sparks and steam spraying "
          f"from it. Two operators in white hard hats cover their ears with pained faces. {BOTH}",
        D=f"Bright morning inside an industrial pump house. {MAINT} stands next to a calm, quiet blue pump holding a coffee thermos, "
          "relaxed, smiling and shrugging.",
        E=f"Inside an industrial pump house. Two operators in white hard hats stare straight at the camera with dead-eyed, totally "
          f"unimpressed blank expressions. {BOTH}",
    ),
    "danger": ["night."],
    "beats": [
        {"shot": "A", "dur": 2.6, "music": "comedy", "zoom": [1.05, 1.1],
         "texts": [{"style": "title", "lines": ["HOW OPERATORS", "WRITE WORK ORDERS"], "emoji": "✍️"}]},
        {"shot": "A", "flash": True, "zoom": [1.2, 1.35], "cy": [0.35, 0.35],
         "lines": [say("camo", "Pump's making a noise. Fix it. Submit.")],
         "texts": [{"style": "note", "header": "WORK ORDER #4471", "lines": ["PUMP MAKING", "NOISE. FIX."], "size": 96, "at_line": 0, "offset": 0.4, "y": 900}]},
        {"shot": "B", "flash": True, "zoom": [1.05, 1.15], "chip": {"text": "🔧 MAINTENANCE", "bg": "#ff8a00", "fg": "#111"},
         "lines": [say("maint", "Ran it for five minutes. Could not duplicate.")],
         "texts": [{"style": "stamp", "lines": ["CLOSED:", "COULD NOT", "DUPLICATE"], "after_line": 0, "offset": 0.1, "y": 820}],
         "post": 1.2},
        {"card": "2:00 AM", "sub": "THAT NIGHT...", "music": "none"},
        {"shot": "C", "fx": ["shake", "sparks", "steam"], "music": "action", "zoom": [1.05, 1.15],
         "sfx": [{"name": "bang", "at": 0.05, "gain": 0.45}], "amb": [{"name": "hiss", "gain": 0.18}],
         "lines": [say("stache", "Is this loud enough to duplicate?!", delay=0.4)]},
        {"card": "8:00 AM", "sub": "THE NEXT MORNING", "color": "#ffb347", "music": "none"},
        {"shot": "D", "music": "comedy", "zoom": [1.05, 1.12], "amb": [{"name": "birds", "gain": 0.06}],
         "lines": [say("maint", "Sounds fine to me.")]},
        {"shot": "E", "zoom": [1.0, 1.1],
         "lines": [say("camo", "It only does it at night."), say("maint", "Then put in a work order.")],
         "sfx": [{"name": "sad_trombone", "after_line": 1, "offset": 0.15, "gain": 0.3}],
         "texts": [{"style": "label", "lines": ["THE CYCLE", "CONTINUES"], "after_line": 1, "offset": 0.1, "y": 300}], "post": 1.6},
    ],
    "cta": ["TAG A MECHANIC WHO", "\"COULD NOT DUPLICATE\""],
}

# ------------------------------------------------------------------ 04
EPISODES["04-safety-meeting"] = {
    "title": "The Safety Meeting",
    "frames": frames(
        A=f"A plant break room with folding tables. At the front, {MGR} proudly presents a projector screen showing a pie chart. "
          "A crew of plant operators sits at the tables with coffee and donuts, already bored, including a stocky guy in a camo trucker hat "
          "and camo pullover and a lean mustached guy in a black cap and light blue work shirt.",
        B=f"The same plant break room hours later: every operator slumped asleep, cobwebs hanging off them, a skeleton wearing a hard hat in "
          f"one chair. {CAMO} props his eyes open with toothpicks. {STACHE} is asleep, drooling. The plant manager in a red tie still "
          "presents energetically at the projector.",
        C=f"{ENG} sits at the back of a plant break room eagerly raising his hand high with a big hopeful smile, a notepad in his other hand.",
        D=f"Inside a plant break room, every operator has turned around in their seat to glare at the camera with furious, murderous, "
          f"glowing red eyes, dramatic dark lighting. In the front: {CAMO} and {STACHE}.",
        E=f"{CAMO} and {STACHE} walk out of a plant break room happily, each carrying a whole box of donuts, big satisfied grins.",
    ),
    "danger": ["NOT", "question!"],
    "beats": [
        {"shot": "A", "dur": 3.0, "music": "comedy", "zoom": [1.05, 1.1],
         "texts": [{"style": "title", "lines": ["THE SAFETY MEETING", "ABOUT THE", "SAFETY MEETING"], "emoji": "🦺"}]},
        {"shot": "A", "flash": True, "zoom": [1.2, 1.35], "cx": [0.5, 0.5], "cy": [0.3, 0.32],
         "chip": {"text": "👔 MANAGEMENT", "bg": "#8e44ff", "fg": "#fff"},
         "lines": [say("mgr", "Alright everybody, this'll be quick.")],
         "texts": [{"style": "label", "lines": ["SLIDE 1 OF 87"], "at_line": 0, "offset": 0.6, "y": 420, "size": 70}]},
        {"card": "2 HOURS LATER", "sub": "", "color": "#ffffff", "music": "none"},
        {"shot": "B", "music": "chill", "zoom": [1.0, 1.12], "amb": [{"name": "snore", "gain": 0.12}],
         "lines": [say("mgr", "Slide forty-three. Ladders."), say("mgr", "Do NOT stand on the top rung.", say="Do not stand on the top rung.")],
         "texts": [{"style": "label", "lines": ["SLIDE 43 OF 87"], "y": 260, "size": 70}]},
        {"shot": "C", "music": "none", "zoom": [1.05, 1.18],
         "texts": [{"style": "label", "lines": ["6:59 AM"], "y": 260, "color": "#ffe135"}],
         "lines": [say("eng", "Quick question!", delay=0.4)],
         "sfx": [{"name": "record_scratch", "after_line": 0, "offset": 0.05, "gain": 0.35}], "post": 0.4},
        {"shot": "D", "punch": [0.05], "fx": ["darken"], "zoom": [1.0, 1.05], "amb": [{"name": "crickets", "gain": 0.1}],
         "sfx": [{"name": "boom", "at": 0.05, "gain": 0.4}],
         "lines": [say("camo", "Nobody has questions, Kevin.", delay=0.4)]},
        {"shot": "E", "music": "comedy", "zoom": [1.0, 1.1],
         "lines": [say("stache", "Worth it for the donuts."), say("camo", "Every time.")]},
    ],
    "cta": ["TAG THE GUY WHO", "ASKS QUESTIONS AT 6:59"],
}

# ------------------------------------------------------------------ 05
EPISODES["05-new-hire"] = {
    "title": "The New Hire",
    "frames": frames(
        A=f"Inside {ROOM}. In the doorway stands {NEW}, beaming with excitement, waving hello and hugging a giant three-ring binder.",
        B=f"Inside {ROOM}. Two operators in black mesh office chairs side-eye each other with knowing smirks. {BOTH}",
        C=f"Daytime in an industrial process unit. A pressure relief valve blasts a huge cloud of white steam with a bang. {NEW} dives "
          f"face-first onto the ground screaming in terror. Behind him {CAMO} and {STACHE} stand calmly sipping coffee, totally unbothered.",
        D=f"Inside {ROOM}. {CAMO} and {STACHE} scream in absolute horror, hands on their cheeks, staring at an empty glass coffee pot on "
          "the coffee maker. The new hire in brand-new coveralls stands behind them calm and confused.",
    ),
    "danger": ["die!", "last", "cup?!"],
    "beats": [
        {"shot": "A", "dur": 2.6, "music": "comedy", "zoom": [1.05, 1.1],
         "texts": [{"style": "title", "lines": ["THE NEW HIRE'S", "FIRST DAY"], "emoji": "🐣"}]},
        {"shot": "A", "flash": True, "zoom": [1.25, 1.4], "cy": [0.3, 0.32], "chip": {"text": "🐣 NEW HIRE", "bg": "#3ddc84", "fg": "#111"},
         "lines": [say("new", "Hi! I read the entire operating manual last night!")]},
        {"shot": "B", "zoom": [1.0, 1.1],
         "lines": [say("camo", "All of it?"), say("new", "All four thousand pages!"), say("stache", "Cute.")]},
        {"shot": "C", "flash": True, "fx": ["shake", "steam"], "music": "none", "zoom": [1.05, 1.15],
         "sfx": [{"name": "bang", "at": 0.05, "gain": 0.5}], "amb": [{"name": "hiss", "gain": 0.2}],
         "lines": [say("new", "We're all gonna die!", delay=0.3), say("stache", "That's just Tuesday.", delay=0.3)]},
        {"shot": "D", "flash": True, "music": "comedy", "punch": [0.1], "zoom": [1.0, 1.08],
         "sfx": [{"name": "sting", "at": 0.05, "gain": 0.4}],
         "lines": [say("camo", "Who drank the last cup?!", delay=1.6)],
         "texts": [{"style": "banner", "lines": ["THE ONLY THING", "OPERATORS FEAR"], "at": 0.1, "y": 330}], "post": 1.2},
    ],
    "cta": ["TAG THE", "NEW GUY"],
}

# ------------------------------------------------------------------ 06
EPISODES["06-july-vs-january"] = {
    "title": "Rounds: July vs January",
    "frames": frames(
        A=f"An industrial chemical plant under a blazing summer sun, heat waves shimmering off the pipes. Two operators in white hard hats "
          f"doing rounds, drenched in sweat, wilting, one fanning himself with a clipboard. {BOTH}",
        B=f"Summer heat in an industrial plant. {CAMO} fries an egg on a hot steel steam pipe with a big proud grin while {STACHE} watches "
          "in disbelief, both dripping sweat.",
        C=f"The same industrial plant in a freezing winter: snow, ice and icicles everywhere. Two operators bundled in heavy jackets and "
          f"beanies under hard hats shiver, frosty breath; the mustached one has his mustache frozen solid with little icicles. {BOTH}",
        D="Winter night in an industrial plant, snow falling. Two operators in heavy jackets and hard hats whack a valve encased in thick "
          "ice with a big hammer, ice shards flying. One wears a camo trucker hat under his hard hat, the other has a thin mustache.",
        E=f"Inside {ROOM}. {CAMO} and {STACHE} fight over a wall thermostat, both grabbing the dial in a comedic tug-of-war, angry faces.",
    ),
    "beats": [
        {"shot": "A", "dur": 3.0, "music": "comedy", "fx": ["heat"], "zoom": [1.05, 1.1],
         "texts": [{"style": "title", "lines": ["ROUNDS IN JULY", "vs", "ROUNDS IN JANUARY"], "emoji": "🥵🥶"}]},
        {"shot": "A", "flash": True, "fx": ["heat"], "zoom": [1.15, 1.3], "chip": {"text": "☀️ JULY", "bg": "#ff8a00", "fg": "#111"},
         "lines": [say("camo", "It's a dry heat."), say("stache", "It's ninety-nine percent humidity.")],
         "texts": [{"style": "stamp", "lines": ["107°F"], "at": 0.3, "y": 560, "size": 130, "rot": 0.08}]},
        {"shot": "B", "fx": ["heat"], "zoom": [1.05, 1.18], "amb": [{"name": "sizzle", "gain": 0.12}],
         "lines": [say("camo", "Breakfast is served.", delay=0.4)]},
        {"shot": "C", "flash": True, "fx": ["snow"], "zoom": [1.05, 1.2], "chip": {"text": "❄️ JANUARY", "bg": "#7fd3ff", "fg": "#111"},
         "amb": [{"name": "wind", "gain": 0.14}],
         "lines": [say("stache", "I can't feel my face."), say("camo", "Your mustache froze.")],
         "texts": [{"style": "stamp", "lines": ["8°F"], "at": 0.3, "y": 560, "size": 130, "color": "#2f80ff", "rot": 0.08}]},
        {"shot": "D", "fx": ["snow", "shake_small"], "zoom": [1.05, 1.15], "amb": [{"name": "wind", "gain": 0.12}],
         "sfx": [{"name": "clang", "at": 0.25, "gain": 0.3}, {"name": "clang", "at": 0.9, "gain": 0.3}],
         "lines": [say("camo", "Steam trace froze again!", delay=0.9)]},
        {"shot": "E", "flash": True, "music": "fast", "zoom": [1.0, 1.1],
         "texts": [{"style": "label", "lines": ["ALSO OPERATORS:"], "at": 0.1, "y": 260}],
         "lines": [say("camo", "Turn the heat up!"), say("stache", "Turn the AC on!", say="Turn the A. C. on!")]},
    ],
    "cta": ["TAG YOUR", "THERMOSTAT ENEMY"],
}

# ------------------------------------------------------------------ 07
EPISODES["07-3am-overtime-call"] = {
    "title": "The 3 AM Overtime Call",
    "frames": frames(
        A=f"Night, a dark blue bedroom at home. {CAMO.replace('wearing a camo trucker hat with tan mesh back and a dark leather American flag patch, ', '')} "
          "is fast asleep in bed under a camo blanket, snoring, mouth open. His phone glows and vibrates on the nightstand.",
        B="Night, dark bedroom. A stocky young man with a round face and light stubble sits up in bed groggy under a camo blanket. On one "
          "shoulder stands a tiny angel version of himself with a halo, white robe and little wings wearing a camo trucker hat; on the other "
          "shoulder a tiny red devil version of himself with horns and a pitchfork wearing a camo trucker hat.",
        C="Night, dark bedroom lit only by a phone screen. A stocky young man with a round face, light stubble and messy brown hair holds "
          "the phone to his ear in bed with half-closed sleepy eyes.",
        D=f"Night outside a small house. {CAMO}, fully dressed for work with a white hard hat, bursts out of his front door at cartoon "
          "speed with a coffee thermos and car keys, motion blur and speed lines, determined grin.",
        E=f"Inside {ROOM} at 4 AM. {STACHE} sits in a black mesh office chair with a coffee cup, looking up tiredly at {CAMO} walking in "
          "the door.",
    ),
    "beats": [
        {"shot": "A", "dur": 2.6, "music": "none", "zoom": [1.05, 1.1], "amb": [{"name": "snore", "gain": 0.14}],
         "texts": [{"style": "title", "lines": ["WHEN THE PLANT", "CALLS AT 3 AM"], "emoji": "📞"}]},
        {"shot": "A", "zoom": [1.15, 1.3], "cy": [0.55, 0.6], "dur": 3.0,
         "sfx": [{"name": "phone_ring", "at": 0.1, "gain": 0.3}],
         "texts": [{"style": "phone", "name": "THE PLANT", "sub": "incoming call...", "at": 0.1, "y": 620}]},
        {"shot": "B", "flash": True, "music": "dreamy", "zoom": [1.0, 1.1],
         "lines": [say("angel", "Don't answer. You're on your days off."), say("devil", "It's double time."),
                   say("angel", "Okay, that's fair.", delay=0.3)]},
        {"shot": "C", "music": "none", "zoom": [1.05, 1.15],
         "lines": [say("board", "Hey bud, any chance you can come in?", filter="phone"), say("camo", "How long?"),
                   say("board", "Sixteen hours.", filter="phone")]},
        {"shot": "D", "flash": True, "music": "fast", "fx": ["shake_small"], "zoom": [1.05, 1.2],
         "sfx": [{"name": "whoosh", "at": 0.2, "gain": 0.4}],
         "lines": [say("camo", "On my way!", delay=0.3)],
         "texts": [{"style": "banner", "lines": ["DOUBLE TIME", "HITS DIFFERENT"], "after_line": 0, "offset": 0.2, "y": 330}], "post": 1.4},
        {"shot": "E", "music": "comedy", "zoom": [1.0, 1.1],
         "lines": [say("stache", "They called you too?"), say("camo", "They called everybody.")]},
    ],
    "cta": ["TAG SOMEONE WHO", "NEVER SAYS NO TO OT"],
}

# ------------------------------------------------------------------ 08
EPISODES["08-plant-manager-visit"] = {
    "title": "When the Plant Manager Visits",
    "frames": frames(
        A=f"Inside a messy {ROOM}: open pizza boxes, energy drink cans everywhere. {CAMO} has his feet up on the desk; {STACHE} eats a slice of pizza.",
        B=f"Inside {ROOM}, total chaos: {STACHE} frantically tosses pizza boxes in the trash, {CAMO} frantically pulls on safety goggles "
          "and a hard hat, papers flying, motion blur, panic.",
        C=f"A spotless, shining {ROOM}. {CAMO} and {STACHE} stand at stiff attention wearing absurd amounts of safety gear: hard hats, face "
          f"shields, goggles, ear muffs, gloves, harnesses and high-visibility vests. {MGR} walks in looking impressed.",
        D=f"The same {ROOM} seconds later: the manager is gone, safety gear piled on the floor, pizza back out, {CAMO} and {STACHE} "
          "collapsed back in their chairs with their feet up.",
    ),
    "beats": [
        {"shot": "A", "dur": 2.8, "music": "chill", "zoom": [1.05, 1.1],
         "texts": [{"style": "title", "lines": ["WHEN THE PLANT MANAGER", "VISITS THE UNIT"], "emoji": "👀"}]},
        {"shot": "A", "zoom": [1.15, 1.25], "lines": [say("board", "Heads up! Plant manager's walking over!")], "post": 0.3},
        {"shot": "B", "flash": True, "music": "fast", "fx": ["shake_small"], "zoom": [1.05, 1.15],
         "lines": [say("camo", "Hide the pizza!"), say("stache", "Where are my safety glasses?!")]},
        {"shot": "C", "flash": True, "music": "none", "zoom": [1.0, 1.08], "chip": {"text": "👔 MANAGEMENT", "bg": "#8e44ff", "fg": "#fff"},
         "sfx": [{"name": "ding", "at": 0.1, "gain": 0.3}],
         "lines": [say("mgr", "Wow. Very impressive, gentlemen.", delay=0.3), say("camo", "Safety first, sir.")]},
        {"shot": "D", "flash": True, "music": "comedy", "zoom": [1.0, 1.1],
         "lines": [say("camo", "Is he gone?"), say("stache", "He's gone.")],
         "texts": [{"style": "stamp", "lines": ["TOTAL TIME OF", "COMPLIANCE:", "4 MINUTES"], "after_line": 1, "offset": 0.2, "y": 760, "size": 80}],
         "post": 1.4},
    ],
    "cta": ["TAG YOUR", "UNIT'S PPE POLICE"],
}

# ------------------------------------------------------------------ 09
EPISODES["09-radio-calls"] = {
    "title": "Radio Calls",
    "frames": frames(
        A=f"Inside {ROOM}. {STACHE} leans back at the control board talking casually into a handheld two-way radio.",
        B=f"Daytime in an industrial process unit. {CAMO}, radio in hand, stands in front of an enormous wall of hundreds of identical "
          "valves and pipes, completely confused.",
        C=f"Daytime in an industrial pump area with dozens of identical pumps in rows in every direction. {CAMO} spins around confused and dizzy, radio in hand.",
        D=f"Daytime in an industrial process unit. {CAMO} stares blankly straight into the camera, deadpan and unamused, radio in hand.",
        E=f"Inside {ROOM}. {STACHE} mumbles into a handheld radio with half a donut stuffed in his mouth.",
    ),
    "beats": [
        {"shot": "A", "dur": 2.6, "music": "comedy", "zoom": [1.05, 1.1],
         "texts": [{"style": "title", "lines": ["OPERATOR RADIO", "CALLS BE LIKE"], "emoji": "📻"}]},
        {"shot": "A", "zoom": [1.15, 1.3], "cy": [0.35, 0.35], "lines": [say("stache", "Board to outside. Open the valve.")]},
        {"shot": "B", "flash": True, "zoom": [1.0, 1.12],
         "lines": [say("camo", "Which valve?", filter="radio"), say("stache", "The one by the pump.", filter="radio")]},
        {"shot": "C", "fx": ["shake_small"], "zoom": [1.0, 1.12],
         "lines": [say("camo", "Which pump?", filter="radio"), say("stache", "The one by the valve.", filter="radio")]},
        {"shot": "D", "music": "none", "zoom": [1.1, 1.25], "dur": 2.6, "amb": [{"name": "crickets", "gain": 0.12}],
         "texts": [{"style": "action", "lines": ["*stares into camera*"], "at": 0.3}]},
        {"shot": "E", "music": "comedy", "zoom": [1.0, 1.12],
         "lines": [say("stache", "Mmph... pump... mmph... go.", say="Mm, pump, mm, go.", filter="radio"), say("camo", "Copy.", filter="radio")],
         "texts": [{"style": "stamp", "lines": ["HE DID NOT", "COPY"], "after_line": 1, "offset": 0.3, "y": 760}], "post": 1.4},
    ],
    "cta": ["TAG YOUR", "RADIO PARTNER"],
}

# ------------------------------------------------------------------ 10
EPISODES["10-turnaround-season"] = {
    "title": "Turnaround Season",
    "frames": frames(
        A="A huge industrial chemical plant swarming with hundreds of contractors in different colored hard hats, scaffolding covering "
          "every tower, cranes, chaos, bright daytime.",
        B=f"Sunrise at an industrial plant covered in scaffolding. {CAMO} and {STACHE}, fresh, clean and optimistic, smile holding coffee cups.",
        C=f"Night at an industrial plant covered in scaffolding. {CAMO} and {STACHE} are exhausted zombies leaning against the scaffolding, "
          "dark bags under their eyes, grimy, clothes torn, the mustached one asleep standing up.",
        D=f"An absurdly long line of contractors in hard hats waiting for a single portable toilet, the line stretching into the distance "
          f"at an industrial plant. Near the back of the line, {CAMO} does a pained, desperate dance.",
        E=f"Inside {ROOM}. {MGR} beams with two thumbs up next to a wall calendar. In the foreground {CAMO} and {STACHE} scream in despair.",
    ),
    "danger": ["two", "more", "weeks!"],
    "beats": [
        {"shot": "A", "dur": 2.6, "music": "comedy", "zoom": [1.05, 1.12], "amb": [{"name": "crowd", "gain": 0.1}],
         "texts": [{"style": "title", "lines": ["TURNAROUND", "SEASON BE LIKE"], "emoji": "🏗️"}]},
        {"shot": "B", "flash": True, "zoom": [1.0, 1.1], "texts": [{"style": "label", "lines": ["DAY 1"], "y": 260}],
         "lines": [say("camo", "Thirty days of twelve-hour shifts. Easy money."), say("stache", "We got this.")]},
        {"shot": "C", "flash": True, "music": "tense", "zoom": [1.0, 1.12],
         "texts": [{"style": "label", "lines": ["DAY 23"], "y": 260, "color": "#ff3b30"}],
         "lines": [say("stache", "What day is it?"), say("camo", "Turnaround.")]},
        {"shot": "D", "flash": True, "music": "comedy", "zoom": [1.0, 1.15], "amb": [{"name": "crowd", "gain": 0.1}],
         "texts": [{"style": "label", "lines": ["THE PORTA-JOHN LINE"], "y": 260}],
         "sfx": [{"name": "sad_trombone", "at": 0.3, "gain": 0.28}],
         "lines": [say("camo", "I've been in this line since Tuesday.", delay=1.6)]},
        {"shot": "E", "flash": True, "music": "none", "zoom": [1.0, 1.08], "texts": [{"style": "label", "lines": ["DAY 30"], "y": 260}],
         "lines": [say("mgr", "Great news! We're extending turnaround two more weeks!"), say("camo", "No!", delay=0.4), say("stache", "No no no no!")],
         "sfx": [{"name": "sting", "after_line": 0, "offset": 0.1, "gain": 0.4}], "post": 0.8},
    ],
    "cta": ["TAG YOUR", "TURNAROUND CREW"],
}

# ------------------------------------------------------------------ 11
EPISODES["11-4am-night-shift"] = {
    "title": "Night Shift at 4 AM",
    "frames": frames(
        A=f"Night inside {ROOM}. {CAMO} and {STACHE} sit upright, alert and professional, focused on the monitors with coffee, determined.",
        B=f"4 AM inside {ROOM}. {CAMO} and {STACHE} lie on the floor laughing uncontrollably with tears streaming down their faces, clutching their stomachs.",
        C=f"4 AM in a dark industrial hallway. {CAMO} stands frozen in front of a glowing vending machine with a blank zombie stare.",
        D=f"Night inside {ROOM}. {STACHE} gazes out the window at a glowing orange flare stack in the night sky, deep in thought, "
          f"philosophical, moody lighting. {CAMO} stands beside him looking out too.",
        E=f"Morning inside {ROOM}. {CAMO} and {STACHE} sit perfectly upright with stiff, forced professional smiles as {DAY} walks in the door.",
    ),
    "beats": [
        {"shot": "B", "dur": 2.6, "music": "comedy", "zoom": [1.05, 1.12],
         "texts": [{"style": "title", "lines": ["NIGHT SHIFT", "AT 4 AM"], "emoji": "🫠"}]},
        {"card": "8:00 PM", "sub": "START OF SHIFT", "color": "#7fd3ff", "music": "none", "dur": 1.3},
        {"shot": "A", "music": "chill", "zoom": [1.0, 1.1],
         "lines": [say("camo", "Alright. Let's have a productive night."), say("stache", "Focused. Professional.")]},
        {"card": "4:00 AM", "sub": "", "color": "#b388ff", "music": "none", "dur": 1.2},
        {"shot": "B", "music": "fast", "zoom": [1.0, 1.12],
         "lines": [say("stache", "He said... pump."), say("camo", "Ha! Pump!")],
         "texts": [{"style": "action", "lines": ["*nobody knows why", "this is funny*"], "after_line": 1, "offset": 0.2, "y": 1580}], "post": 1.2},
        {"shot": "C", "music": "none", "zoom": [1.05, 1.25], "dur": 2.8, "amb": [{"name": "room", "gain": 0.05}],
         "texts": [{"style": "action", "lines": ["*has been staring at the", "vending machine for 11 minutes*"], "at": 0.3}]},
        {"shot": "D", "music": "dreamy", "zoom": [1.0, 1.1],
         "lines": [say("stache", "Do you think the flare gets lonely?"), say("camo", "Every night, man.", delay=0.4)]},
        {"card": "6:45 AM", "sub": "DAY SHIFT ARRIVES", "color": "#ffb347", "music": "none", "dur": 1.3},
        {"shot": "E", "music": "comedy", "zoom": [1.0, 1.1], "chip": {"text": "☀️ DAY SHIFT", "bg": "#ffd400", "fg": "#111"},
         "lines": [say("camo", "Quiet night. Nothing to report."), say("stache", "Very professional.")]},
    ],
    "cta": ["TAG YOUR", "4 AM PARTNER"],
}


if __name__ == "__main__":
    for name, ep in EPISODES.items():
        d = ROOT / "videos" / name
        (d / "frames").mkdir(parents=True, exist_ok=True)
        (d / "script.json").write_text(json.dumps(ep, indent=1, ensure_ascii=False))
        print(f"{name}: {len(ep['beats'])} beats, {len(ep['frames'])} frames, {sum(len(b.get('lines', [])) for b in ep['beats'])} lines")
