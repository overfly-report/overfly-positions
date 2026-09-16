"""Aircraft type enrichment from ICAO 4-letter type designator codes.

This module encodes domain knowledge as a lookup table — no LLM calls, no
external dependencies. The ICAO designators come from standard aviation
type-registry and ADS-B sources.

Architecture (Simon): this is a *nearly decomposable* enrichment layer.
- Strong coupling WITHIN: type → characteristics is a coherent unit
- Weak coupling BETWEEN: callers get back a dict; don't need this module to use overfly

Noise profile scale (1-5):
  1 = Barely audible at low altitude — high-bypass commercial jets at cruise
  2 = Noticeable — business jets at moderate altitude
  3 = Clearly audible — turboprops, helicopters, high jets on approach
  4 = Loud — pistons at pattern altitude (~1000-2000ft AGL), large turboprops
  5 = Very loud — pistons doing touch-and-goes directly overhead, helicopters hovering

Key insight for Pennington NJ: the aircraft at noise_profile=4-5 doing continuous
circuits over 39N (Princeton Airport) and KTTN are the main source of complaint.
A C172 at 1500ft doing pattern work is audible for ~3-5 minutes per pass.
"""

from typing import TypedDict


class AircraftTypeInfo(TypedDict):
    category: str          # human-readable category
    engine_type: str       # "piston", "turboprop", "turbofan", "turboshaft", "electric"
    engine_count: int      # typical number of engines
    noise_profile: int     # 1-5 scale (see module docstring)
    typical_cruise_ft: int # typical cruise altitude in feet
    max_seats: int         # approximate max seating capacity (0 for cargo/military)
    notes: str             # additional context useful for noise analysis


# ICAO type code → aircraft characteristics
# Sources: ICAO Doc 8643, Jane's All the World's Aircraft, personal knowledge
# Focus on types common in the Trenton/Princeton NJ airspace
_TYPE_DATABASE: dict[str, AircraftTypeInfo] = {

    # ─── Cessna Piston Singles ──────────────────────────────────────────────
    "C150": {"category": "small-piston-single", "engine_type": "piston", "engine_count": 1,
             "noise_profile": 4, "typical_cruise_ft": 5_000, "max_seats": 2,
             "notes": "Cessna 150/152 trainer, very common at flight schools"},
    "C140": {"category": "small-piston-single", "engine_type": "piston", "engine_count": 1,
             "noise_profile": 4, "typical_cruise_ft": 5_000, "max_seats": 2,
             "notes": "Cessna 140 (1946-1951 vintage). Continental C-85/C-90, 85-90hp. "
                      "Distinctive older engine sound. Flown by vintage aircraft enthusiasts. "
                      "N89033 observed over Pennington 2026-03-29."},
    "C152": {"category": "small-piston-single", "engine_type": "piston", "engine_count": 1,
             "noise_profile": 4, "typical_cruise_ft": 5_000, "max_seats": 2,
             "notes": "Cessna 152 trainer, common at Raritan Valley Flying School (39N) "
                      "and other local flight schools"},
    "C172": {"category": "small-piston-single", "engine_type": "piston", "engine_count": 1,
             "noise_profile": 4, "typical_cruise_ft": 8_000, "max_seats": 4,
             "notes": "Cessna Skyhawk — most common aircraft in US. The primary source of "
                      "pattern noise at 39N and KTTN. Audible for 3-5 min per pass at 1500ft AGL."},
    "C172S": {"category": "small-piston-single", "engine_type": "piston", "engine_count": 1,
              "noise_profile": 4, "typical_cruise_ft": 8_000, "max_seats": 4,
              "notes": "Cessna Skyhawk SP (fuel injected), same noise as C172"},
    "C182": {"category": "small-piston-single", "engine_type": "piston", "engine_count": 1,
             "noise_profile": 4, "typical_cruise_ft": 10_000, "max_seats": 4,
             "notes": "Cessna Skylane, heavier/louder than C172"},
    "C182T": {"category": "small-piston-single", "engine_type": "piston", "engine_count": 1,
              "noise_profile": 4, "typical_cruise_ft": 10_000, "max_seats": 4,
              "notes": "Cessna Skylane T (turbocharged)"},
    "C206": {"category": "small-piston-single", "engine_type": "piston", "engine_count": 1,
             "noise_profile": 5, "typical_cruise_ft": 10_000, "max_seats": 6,
             "notes": "Cessna Stationair, workhorse utility aircraft"},
    "C210": {"category": "large-piston-single", "engine_type": "piston", "engine_count": 1,
             "noise_profile": 4, "typical_cruise_ft": 12_000, "max_seats": 6,
             "notes": "Cessna Centurion, retractable gear"},

    # ─── Piper Piston Singles ───────────────────────────────────────────────
    "PA28": {"category": "small-piston-single", "engine_type": "piston", "engine_count": 1,
             "noise_profile": 4, "typical_cruise_ft": 7_000, "max_seats": 4,
             "notes": "Piper Cherokee/Warrior/Archer family, second-most common trainer"},
    "P28A": {"category": "small-piston-single", "engine_type": "piston", "engine_count": 1,
             "noise_profile": 4, "typical_cruise_ft": 7_000, "max_seats": 4,
             "notes": "Piper Archer (Cherokee 180). Very common at 39N/KTTN flight schools."},
    "P28B": {"category": "small-piston-single", "engine_type": "piston", "engine_count": 1,
             "noise_profile": 4, "typical_cruise_ft": 7_000, "max_seats": 4,
             "notes": "Piper Warrior II"},
    "P28R": {"category": "large-piston-single", "engine_type": "piston", "engine_count": 1,
             "noise_profile": 4, "typical_cruise_ft": 12_000, "max_seats": 4,
             "notes": "Piper Arrow, retractable gear"},
    "P46T": {"category": "large-piston-single", "engine_type": "turboprop", "engine_count": 1,
             "noise_profile": 3, "typical_cruise_ft": 25_000, "max_seats": 6,
             "notes": "Piper Malibu Meridian, turboprop"},

    # ─── Piper Multi-Engine ─────────────────────────────────────────────────
    "PA44": {"category": "small-piston-twin", "engine_type": "piston", "engine_count": 2,
             "noise_profile": 5, "typical_cruise_ft": 10_000, "max_seats": 4,
             "notes": "Piper Seminole, multi-engine trainer. Noticeably louder than singles."},
    "PA34": {"category": "small-piston-twin", "engine_type": "piston", "engine_count": 2,
             "noise_profile": 5, "typical_cruise_ft": 10_000, "max_seats": 6,
             "notes": "Piper Seneca, light twin"},

    # ─── Beechcraft Piston ──────────────────────────────────────────────────
    "BE33": {"category": "small-piston-single", "engine_type": "piston", "engine_count": 1,
             "noise_profile": 4, "typical_cruise_ft": 10_000, "max_seats": 4,
             "notes": "Beechcraft Bonanza 33"},
    "BE35": {"category": "small-piston-single", "engine_type": "piston", "engine_count": 1,
             "noise_profile": 4, "typical_cruise_ft": 10_000, "max_seats": 4,
             "notes": "Beechcraft Bonanza V-tail"},
    "BE36": {"category": "small-piston-single", "engine_type": "piston", "engine_count": 1,
             "noise_profile": 4, "typical_cruise_ft": 11_000, "max_seats": 6,
             "notes": "Beechcraft Bonanza A36"},
    "BE58": {"category": "large-piston-twin", "engine_type": "piston", "engine_count": 2,
             "noise_profile": 5, "typical_cruise_ft": 12_000, "max_seats": 6,
             "notes": "Beechcraft Baron, common at regional airports"},

    # ─── Cirrus ─────────────────────────────────────────────────────────────
    "SR20": {"category": "small-piston-single", "engine_type": "piston", "engine_count": 1,
             "noise_profile": 3, "typical_cruise_ft": 10_000, "max_seats": 4,
             "notes": "Cirrus SR20, modern composite airframe, slightly quieter than Cessna"},
    "SR22": {"category": "small-piston-single", "engine_type": "piston", "engine_count": 1,
             "noise_profile": 3, "typical_cruise_ft": 17_500, "max_seats": 5,
             "notes": "Cirrus SR22, best-selling single-engine piston in the US. "
                      "Higher cruise altitude than trainers."},
    "SR22T": {"category": "small-piston-single", "engine_type": "piston", "engine_count": 1,
              "noise_profile": 3, "typical_cruise_ft": 25_000, "max_seats": 5,
              "notes": "Cirrus SR22T (turbocharged), can cruise at FL250"},

    # ─── Diamond ────────────────────────────────────────────────────────────
    "DA40": {"category": "small-piston-single", "engine_type": "piston", "engine_count": 1,
             "noise_profile": 3, "typical_cruise_ft": 10_000, "max_seats": 4,
             "notes": "Diamond DA40, glass cockpit trainer, very common at Princeton 39N"},
    "DA42": {"category": "small-piston-twin", "engine_type": "piston", "engine_count": 2,
             "noise_profile": 3, "typical_cruise_ft": 18_000, "max_seats": 4,
             "notes": "Diamond DA42 Twin Star, diesel engines, relatively quiet"},

    # ─── Light Sport / Ultralight ───────────────────────────────────────────
    "ULAC": {"category": "ultralight", "engine_type": "piston", "engine_count": 1,
             "noise_profile": 3, "typical_cruise_ft": 3_000, "max_seats": 2,
             "notes": "Ultralight/light sport aircraft"},

    # ─── Business Jets — Light ──────────────────────────────────────────────
    "C25A": {"category": "business-jet-light", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 41_000, "max_seats": 8,
             "notes": "Cessna CJ2, very common at KTTN (corporate NJ traffic)"},
    "C25B": {"category": "business-jet-light", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 45_000, "max_seats": 9,
             "notes": "Cessna CJ3"},
    "C25C": {"category": "business-jet-light", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 45_000, "max_seats": 10,
             "notes": "Cessna CJ4"},
    "C510": {"category": "business-jet-light", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 41_000, "max_seats": 5,
             "notes": "Cessna Citation Mustang, very light jet"},
    "C525": {"category": "business-jet-light", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 41_000, "max_seats": 7,
             "notes": "Cessna CitationJet (CJ1)"},
    "C55B": {"category": "business-jet-medium", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 43_000, "max_seats": 8,
             "notes": "Cessna Citation Bravo"},
    "C560": {"category": "business-jet-medium", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 45_000, "max_seats": 9,
             "notes": "Cessna Citation V/Ultra/Encore"},
    "C680": {"category": "business-jet-medium", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 45_000, "max_seats": 12,
             "notes": "Cessna Citation Sovereign"},
    "C700": {"category": "business-jet-large", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 45_000, "max_seats": 12,
             "notes": "Cessna Citation Longitude"},
    "C750": {"category": "business-jet-large", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 51_000, "max_seats": 12,
             "notes": "Cessna Citation X, one of fastest biz jets"},
    "BE40": {"category": "business-jet-light", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 41_000, "max_seats": 8,
             "notes": "Beechcraft Premier I"},

    # ─── Business Jets — Bombardier/Learjet ────────────────────────────────
    "LJ35": {"category": "business-jet-light", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 3, "typical_cruise_ft": 45_000, "max_seats": 8,
             "notes": "Learjet 35, older design, louder than modern jets"},
    "LJ45": {"category": "business-jet-medium", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 51_000, "max_seats": 10,
             "notes": "Learjet 45"},
    "LJ60": {"category": "business-jet-large", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 51_000, "max_seats": 10,
             "notes": "Learjet 60"},
    "CL30": {"category": "business-jet-large", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 45_000, "max_seats": 14,
             "notes": "Bombardier Challenger 300/350, very common at KTTN"},
    "CL60": {"category": "business-jet-heavy", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 41_000, "max_seats": 19,
             "notes": "Bombardier Challenger 600/601/604/605"},
    "GL5T": {"category": "business-jet-heavy", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 1, "typical_cruise_ft": 51_000, "max_seats": 19,
             "notes": "Bombardier Global 5000"},
    "GLEX": {"category": "business-jet-heavy", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 1, "typical_cruise_ft": 51_000, "max_seats": 17,
             "notes": "Bombardier Global Express/6000. Spotted over Pennington 2026-03-27."},
    "GL7T": {"category": "business-jet-heavy", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 1, "typical_cruise_ft": 51_000, "max_seats": 17,
             "notes": "Bombardier Global 7500, ultra-long-range"},

    # ─── Business Jets — Gulfstream ─────────────────────────────────────────
    "G150": {"category": "business-jet-medium", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 45_000, "max_seats": 8,
             "notes": "Gulfstream G150"},
    "G280": {"category": "business-jet-medium", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 45_000, "max_seats": 10,
             "notes": "Gulfstream G280"},
    "G450": {"category": "business-jet-heavy", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 1, "typical_cruise_ft": 45_000, "max_seats": 16,
             "notes": "Gulfstream G450"},
    "G550": {"category": "business-jet-heavy", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 1, "typical_cruise_ft": 51_000, "max_seats": 18,
             "notes": "Gulfstream G550"},
    "G650": {"category": "business-jet-heavy", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 1, "typical_cruise_ft": 51_000, "max_seats": 18,
             "notes": "Gulfstream G650/G650ER, top of market"},
    "GALX": {"category": "business-jet-heavy", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 1, "typical_cruise_ft": 45_000, "max_seats": 19,
             "notes": "IAI Gulfstream Galaxy / Bombardier Challenger 600 variant"},

    # ─── Business Jets — Embraer ────────────────────────────────────────────
    "E50P": {"category": "business-jet-light", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 41_000, "max_seats": 7,
             "notes": "Embraer Phenom 100"},
    "E55P": {"category": "business-jet-medium", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 45_000, "max_seats": 10,
             "notes": "Embraer Phenom 300, very popular light-medium jet"},
    "E135": {"category": "business-jet-large", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 37_000, "max_seats": 37,
             "notes": "Embraer ERJ-135 (also used as regional airliner)"},
    "E145": {"category": "commercial-regional", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 37_000, "max_seats": 50,
             "notes": "Embraer ERJ-145, common at regional airports"},
    "E170": {"category": "commercial-regional", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 37_000, "max_seats": 76,
             "notes": "Embraer 170"},
    "E175": {"category": "commercial-regional", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 41_000, "max_seats": 80,
             "notes": "Embraer 175, common at KTTN (Contour Airlines)"},
    "E190": {"category": "commercial-regional", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 39_000, "max_seats": 106,
             "notes": "Embraer 190"},

    # ─── Business Jets — Dassault ───────────────────────────────────────────
    "F2TH": {"category": "business-jet-large", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 47_000, "max_seats": 10,
             "notes": "Dassault Falcon 2000"},
    "F7X":  {"category": "business-jet-heavy", "engine_type": "turbofan", "engine_count": 3,
             "noise_profile": 1, "typical_cruise_ft": 51_000, "max_seats": 16,
             "notes": "Dassault Falcon 7X, trijet"},
    "F900": {"category": "business-jet-large", "engine_type": "turbofan", "engine_count": 3,
             "noise_profile": 2, "typical_cruise_ft": 51_000, "max_seats": 14,
             "notes": "Dassault Falcon 900, trijet"},

    # ─── Hawker / Raytheon / BAE ─────────────────────────────────────────────
    "H25B": {"category": "business-jet-medium", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 41_000, "max_seats": 8,
             "notes": "Hawker 800 (BAe 125-800 / Raytheon 800). Very common at KTTN "
                      "for corporate NJ traffic. Spotted over Pennington 2026-03-27."},
    "H25C": {"category": "business-jet-medium", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 41_000, "max_seats": 9,
             "notes": "Hawker 900XP"},

    # ─── Pilatus ─────────────────────────────────────────────────────────────
    "PC12": {"category": "turboprop-single", "engine_type": "turboprop", "engine_count": 1,
             "noise_profile": 3, "typical_cruise_ft": 30_000, "max_seats": 9,
             "notes": "Pilatus PC-12, extremely versatile turboprop. Very common at KTTN."},
    "PC24": {"category": "business-jet-light", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 45_000, "max_seats": 10,
             "notes": "Pilatus PC-24, business jet"},

    # ─── Turboprops ─────────────────────────────────────────────────────────
    "TBM7": {"category": "turboprop-single", "engine_type": "turboprop", "engine_count": 1,
             "noise_profile": 3, "typical_cruise_ft": 31_000, "max_seats": 5,
             "notes": "TBM 700, fast single turboprop"},
    "TBM8": {"category": "turboprop-single", "engine_type": "turboprop", "engine_count": 1,
             "noise_profile": 3, "typical_cruise_ft": 31_000, "max_seats": 5,
             "notes": "TBM 850/900/940"},
    "TBM9": {"category": "turboprop-single", "engine_type": "turboprop", "engine_count": 1,
             "noise_profile": 3, "typical_cruise_ft": 31_000, "max_seats": 6,
             "notes": "TBM 960"},
    "M600": {"category": "turboprop-single", "engine_type": "turboprop", "engine_count": 1,
             "noise_profile": 3, "typical_cruise_ft": 30_000, "max_seats": 6,
             "notes": "Piper M600 SLS, modern turboprop"},
    "C208": {"category": "turboprop-single", "engine_type": "turboprop", "engine_count": 1,
             "noise_profile": 3, "typical_cruise_ft": 12_000, "max_seats": 14,
             "notes": "Cessna Caravan, utility turboprop, FedEx/Amazon feeder"},
    "C90": {"category": "turboprop-twin", "engine_type": "turboprop", "engine_count": 2,
            "noise_profile": 3, "typical_cruise_ft": 25_000, "max_seats": 7,
            "notes": "Beechcraft King Air C90"},
    "B350": {"category": "turboprop-twin", "engine_type": "turboprop", "engine_count": 2,
             "noise_profile": 3, "typical_cruise_ft": 35_000, "max_seats": 11,
             "notes": "Beechcraft King Air 350, also used medevac/survey"},
    "P180": {"category": "turboprop-twin", "engine_type": "turboprop", "engine_count": 2,
             "noise_profile": 3, "typical_cruise_ft": 41_000, "max_seats": 9,
             "notes": "Piaggio Avanti, distinctive pusher turboprop — very recognizable sound"},

    # ─── Commercial Narrow-body ─────────────────────────────────────────────
    "A319": {"category": "commercial-narrowbody", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 37_000, "max_seats": 160,
             "notes": "Airbus A319, Allegiant Air uses at KTTN (FLL/PIE routes)"},
    "A320": {"category": "commercial-narrowbody", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 37_000, "max_seats": 186,
             "notes": "Airbus A320 family, Spirit Airlines (NKS) overflies Pennington"},
    "A20N": {"category": "commercial-narrowbody", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 1, "typical_cruise_ft": 39_000, "max_seats": 194,
             "notes": "Airbus A320neo (new engine option), quieter than classic A320. "
                      "Frontier/Allegiant at KTTN."},
    "A21N": {"category": "commercial-narrowbody", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 1, "typical_cruise_ft": 39_000, "max_seats": 220,
             "notes": "Airbus A321neo"},
    "B737": {"category": "commercial-narrowbody", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 35_000, "max_seats": 140,
             "notes": "Boeing 737 Classic (older, louder engine)"},
    "B738": {"category": "commercial-narrowbody", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 37_000, "max_seats": 189,
             "notes": "Boeing 737-800, Southwest/United"},
    "B38M": {"category": "commercial-narrowbody", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 1, "typical_cruise_ft": 41_000, "max_seats": 200,
             "notes": "Boeing 737 MAX 8, quieter CFM LEAP engines. Allegiant at KTTN."},
    "B739": {"category": "commercial-narrowbody", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 41_000, "max_seats": 215,
             "notes": "Boeing 737-900, United/Alaska/Delta"},
    "B737": {"category": "commercial-narrowbody", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 35_000, "max_seats": 149,
             "notes": "Boeing 737-700"},
    "B752": {"category": "commercial-narrowbody", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 39_000, "max_seats": 200,
             "notes": "Boeing 757-200, still common in US"},
    "B763": {"category": "commercial-widebody", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 43_000, "max_seats": 269,
             "notes": "Boeing 767-300"},
    "B77W": {"category": "commercial-widebody", "engine_type": "turbofan", "engine_count": 2,
             "noise_profile": 1, "typical_cruise_ft": 43_000, "max_seats": 396,
             "notes": "Boeing 777-300ER, high altitude transit over NJ"},

    # ─── Helicopters ─────────────────────────────────────────────────────────
    "R44": {"category": "helicopter-light", "engine_type": "piston", "engine_count": 1,
            "noise_profile": 4, "typical_cruise_ft": 5_000, "max_seats": 4,
            "notes": "Robinson R44, very common light helicopter"},
    "R66": {"category": "helicopter-light", "engine_type": "turboshaft", "engine_count": 1,
            "noise_profile": 4, "typical_cruise_ft": 7_000, "max_seats": 5,
            "notes": "Robinson R66, turbine version"},
    "H125": {"category": "helicopter-medium", "engine_type": "turboshaft", "engine_count": 1,
             "noise_profile": 4, "typical_cruise_ft": 8_000, "max_seats": 6,
             "notes": "Airbus H125 (AS350 Écureuil), extremely common utility helo"},
    "AS50": {"category": "helicopter-light", "engine_type": "turboshaft", "engine_count": 1,
             "noise_profile": 3, "typical_cruise_ft": 5_000, "max_seats": 5,
             "notes": "Airbus AS350"},
    "EC35": {"category": "helicopter-medium", "engine_type": "turboshaft", "engine_count": 2,
             "noise_profile": 3, "typical_cruise_ft": 10_000, "max_seats": 5,
             "notes": "Airbus EC135, EMS/police helicopter"},
    "B06": {"category": "helicopter-medium", "engine_type": "turboshaft", "engine_count": 1,
            "noise_profile": 3, "typical_cruise_ft": 8_000, "max_seats": 5,
            "notes": "Bell 206 JetRanger. NJ State Police uses this. The N4NJ spotted "
                     "repeatedly at KTTN/N51/N87 is the NJ State Police helicopter."},
    "B407": {"category": "helicopter-medium", "engine_type": "turboshaft", "engine_count": 1,
             "noise_profile": 3, "typical_cruise_ft": 10_000, "max_seats": 6,
             "notes": "Bell 407, law enforcement / utility"},
    "B429": {"category": "helicopter-heavy", "engine_type": "turboshaft", "engine_count": 2,
             "noise_profile": 3, "typical_cruise_ft": 10_000, "max_seats": 9,
             "notes": "Bell 429, EMS / corporate"},
    "S76": {"category": "helicopter-heavy", "engine_type": "turboshaft", "engine_count": 2,
            "noise_profile": 3, "typical_cruise_ft": 10_000, "max_seats": 13,
            "notes": "Sikorsky S-76, corporate / EMS"},
    "S92": {"category": "helicopter-heavy", "engine_type": "turboshaft", "engine_count": 2,
            "noise_profile": 3, "typical_cruise_ft": 10_000, "max_seats": 19,
            "notes": "Sikorsky S-92, offshore / heavy lift"},
    "A139": {"category": "helicopter-heavy", "engine_type": "turboshaft", "engine_count": 2,
             "noise_profile": 3, "typical_cruise_ft": 10_000, "max_seats": 16,
             "notes": "AgustaWestland AW139. Spotted over Pennington 2026-03-27. "
                      "Often used for EMS, police, or VIP transport."},
    "H160": {"category": "helicopter-heavy", "engine_type": "turboshaft", "engine_count": 2,
             "noise_profile": 2, "typical_cruise_ft": 10_000, "max_seats": 12,
             "notes": "Airbus H160, modern quieter design with Blue Edge rotor blades"},

    # ─── Military (common in NJ airspace near McGuire AFB) ──────────────────
    "C17":  {"category": "military-transport", "engine_type": "turbofan", "engine_count": 4,
             "noise_profile": 5, "typical_cruise_ft": 28_000, "max_seats": 0,
             "notes": "Boeing C-17 Globemaster, Joint Base McGuire-Dix-Lakehurst nearby"},
    "C130": {"category": "military-transport", "engine_type": "turboprop", "engine_count": 4,
             "noise_profile": 5, "typical_cruise_ft": 28_000, "max_seats": 0,
             "notes": "Lockheed C-130, very loud turboprops, JBMDL"},
    "F16": {"category": "military-fighter", "engine_type": "turbofan", "engine_count": 1,
            "noise_profile": 5, "typical_cruise_ft": 50_000, "max_seats": 1,
            "notes": "F-16 Fighting Falcon, occasionally out of JBMDL"},
    "P8": {"category": "military-patrol", "engine_type": "turbofan", "engine_count": 2,
           "noise_profile": 2, "typical_cruise_ft": 37_000, "max_seats": 0,
           "notes": "Boeing P-8 Poseidon maritime patrol, NAS Lakehurst nearby"},
}

# Common aliases and alternate codes that map to canonical entries
_ALIASES: dict[str, str] = {
    "C172SP": "C172S",
    "C172N": "C172",
    "C172M": "C172",
    "C172P": "C172",
    "C172R": "C172",
    "PA28R": "P28R",
    "PA28A": "P28A",
    "PA44": "PA44",
    "BE58": "BE58",
    "B06B": "B06",
    "B206": "B06",
    "H130": "H125",
    "AS350": "H125",
    "EC135": "EC35",
    "AW139": "A139",
    "A320N": "A20N",
    "A321N": "A21N",
}

_UNKNOWN: AircraftTypeInfo = {
    "category": "unknown",
    "engine_type": "unknown",
    "engine_count": 0,
    "noise_profile": 0,
    "typical_cruise_ft": 0,
    "max_seats": 0,
    "notes": "Type code not in database",
}


def lookup(typecode: str | None) -> AircraftTypeInfo:
    """Look up aircraft type information by ICAO type designator.

    Returns an AircraftTypeInfo dict. Never raises — unknown types return
    a dict with category='unknown' and noise_profile=0.
    """
    if not typecode:
        return _UNKNOWN

    code = typecode.upper().strip()
    # Direct lookup
    if code in _TYPE_DATABASE:
        return _TYPE_DATABASE[code]
    # Alias resolution
    if code in _ALIASES:
        canonical = _ALIASES[code]
        return _TYPE_DATABASE.get(canonical, _UNKNOWN)
    return _UNKNOWN


def icao_hex_country(hex_id: str | None) -> str | None:
    """Decode country of registration from ICAO 24-bit Mode S hex address.

    The most significant bits of the hex identify the country, which in turn
    determines the registration format (N- for US, C- for Canada, F- for France, etc.)
    This works for any aircraft regardless of whether we have registry data.

    Source: ICAO Doc 9303 / Annex 10, public allocation table.
    Returns: country name string, or None if hex is None/unknown.
    """
    if not hex_id:
        return None
    try:
        val = int(hex_id.replace(" ", ""), 16)
    except ValueError:
        return None

    # ICAO 24-bit address allocation by country (selected ranges most relevant
    # to US Northeast airspace — can be extended as needed)
    # ICAO Annex 10 authoritative allocations.
    # Regression fix 2026-03-30: France and Germany were swapped in original
    # code. Caught when Airbus H160 demo aircraft (German D-Hxxx registration,
    # hex prefix 3E = 0x3E0000 in Germany range) was misidentified as French.
    # Correct per ICAO Doc 9303: France=0x380000-0x3BFFFF, Germany=0x3C0000-0x3FFFFF
    _RANGES = [
        (0xA00000, 0xAFFFFF, "United States"),
        (0xC00000, 0xC3FFFF, "Canada"),
        (0x380000, 0x3BFFFF, "France"),         # F- prefix
        (0x3C0000, 0x3FFFFF, "Germany"),        # D- prefix (was wrong: had France here)
        (0x400000, 0x43FFFF, "United Kingdom"),
        (0x440000, 0x447FFF, "Austria"),
        (0x448000, 0x44FFFF, "Belgium"),
        (0x450000, 0x457FFF, "Bulgaria"),
        (0x458000, 0x45FFFF, "Denmark"),
        (0x460000, 0x467FFF, "Finland"),
        (0x480000, 0x487FFF, "Greece"),
        (0x4C0000, 0x4CFFFF, "Italy"),
        (0x500000, 0x5003FF, "Cayman Islands"),
        (0x0D0000, 0x0FFFFF, "Mexico"),          # XA/XB/XC prefix (was 0x710000 — wrong)
        (0x720000, 0x727FFF, "Brazil"),
        (0xE00000, 0xE3FFFF, "Spain"),
        (0xE40000, 0xE7FFFF, "Portugal"),
        (0x4D0000, 0x4DFFFF, "Luxembourg"),
        (0x4B0000, 0x4B7FFF, "Ireland"),
        (0x4A0000, 0x4A7FFF, "Iceland"),
        (0x700000, 0x700FFF, "Bermuda"),
        (0x7C0000, 0x7FFFFF, "Australia"),
        (0x600000, 0x6FFFFF, "Japan"),
    ]
    for lo, hi, country in _RANGES:
        if lo <= val <= hi:
            return country
    return "Unknown"


def enrich(position: dict) -> dict:
    """Add aircraft_type and registration_country to a position record in-place.

    Works with any dict that has a 'typecode' field (OpenSky, ADSB.lol, or similar).
    Returns the same dict with 'aircraft_type' and 'registration_country' added.
    """
    typecode = position.get("typecode") or position.get("type_code")
    position["aircraft_type"] = lookup(typecode)
    # Decode country of registration from ICAO hex — works for foreign aircraft
    # where FAA registry has no data
    hex_id = position.get("icao24") or position.get("hex_ident")
    position["registration_country"] = icao_hex_country(hex_id)
    return position


def noise_profile(typecode: str | None) -> int:
    """Return the noise profile (1-5) for a given ICAO type code. 0 = unknown."""
    return lookup(typecode)["noise_profile"]


def is_pattern_traffic(position: dict) -> bool:
    """Heuristic: is this likely a touch-and-go / VFR pattern aircraft?

    Pattern traffic: small piston, low altitude (<3000ft), slow speed (<120kts).
    The speed threshold is the key discriminator:
    - C172 in the pattern: 65-90 kts
    - SR22 cross-country (e.g. N505MA BLM→SCE): 155-185 kts — NOT pattern
    - The original 200kt threshold falsely flagged cross-country piston flights.

    Regression: N505MA (SR22) at 4400ft/155kts was incorrectly flagged as
    pattern traffic (2026-03-27). Fix: lower speed threshold to 120kts and
    altitude threshold to 3000ft.
    """
    info = lookup(position.get("typecode"))
    alt = position.get("altitude_ft") or position.get("baro_altitude_ft") or position.get("feet")
    speed = position.get("ground_speed_kts") or position.get("velocity_kts") or position.get("kts")

    if info["engine_type"] != "piston":
        return False
    if alt is not None and alt > 3000:
        return False
    if speed is not None and speed > 120:
        return False
    return True
