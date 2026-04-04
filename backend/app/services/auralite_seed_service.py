import random
from collections import defaultdict

DISTRICT_BLUEPRINT = [
    ("the_crown", "The Crown", "finance_prestige", "Finance, politics, and media prestige core.", (6, 8)),
    ("glass_harbor", "Glass Harbor", "startup_speculation", "Innovation corridor with speculative growth.", (8, 8)),
    ("old_meridian", "Old Meridian", "historic_mixed_use", "Historic mixed-use neighborhoods and legacy communities.", (4, 6)),
    ("southline", "Southline", "industrial_logistics", "Industrial belt with labor and infrastructure pressure.", (5, 9)),
    ("north_vale", "North Vale", "suburban_family", "Stabilizing suburb belt focused on schools and routines.", (3, 3)),
    ("highgarden", "Highgarden", "elite_enclave", "Insulated elite enclave with donor influence.", (8, 2)),
    ("ember_district", "Ember District", "transitional_stressed", "Precarious zone with intense structural pressure.", (5, 5)),
    ("ironwood_fringe", "Ironwood Fringe", "edge_hinterland", "Outer edge where rural/suburban/industrial blur.", (1, 8)),
    ("riverwake", "Riverwake", "education_civic", "Research, civic administration, and nonprofits.", (2, 2)),
    ("neon_market", "Neon Market", "nightlife_vice", "Nightlife and fast-money district with hidden networks.", (7, 5)),
]

NAMES = [
    "Alex", "Jordan", "Taylor", "Casey", "Morgan", "Riley", "Avery", "Parker", "Skyler", "Quinn",
    "Cameron", "Reese", "Rowan", "Drew", "Hayden", "Emerson", "Kai", "Dakota", "Logan", "Harper",
]

OCCUPATIONS = ["analyst", "operator", "nurse", "teacher", "driver", "technician", "clerk", "researcher", "owner", "student"]


class AuraliteSeedService:
    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def create_seed_bundle(self, population_target: int = 240) -> dict:
        city_id = "auralite_city_01"
        districts = []
        locations = []
        persons = []
        households = []

        district_pop_alloc = self._district_population_allocation(population_target)

        for idx, (district_id, name, archetype, summary, center) in enumerate(DISTRICT_BLUEPRINT):
            pop = district_pop_alloc[district_id]
            districts.append({
                "district_id": district_id,
                "name": name,
                "archetype": archetype,
                "summary": summary,
                "map_region_key": f"region_{idx+1}",
                "population_count": pop,
                "housing_profile": {"pressure": self.rng.choice(["low", "medium", "high"]), "density": self.rng.choice(["low", "medium", "high"])},
                "activity_profile": {"peak_hour": self.rng.choice([9, 12, 18, 22]), "rhythm": self.rng.choice(["steady", "spiky", "night"])} ,
                "current_activity_level": 0.0,
            })
            locations.extend(self._district_locations(district_id, name, center))

        district_locations = defaultdict(list)
        for loc in locations:
            district_locations[loc["district_id"]].append(loc)

        person_index = 0
        for district in districts:
            target = district["population_count"]
            created = 0
            while created < target:
                household_size = min(self.rng.choice([1, 2, 3, 4]), target - created)
                h_id = f"hh_{district['district_id']}_{created:03d}"
                homes = [x for x in district_locations[district["district_id"]] if x["type"] == "home"]
                home = homes[(created // max(1, household_size)) % len(homes)]
                member_ids = []
                for _ in range(household_size):
                    p_id = f"p_{person_index:04d}"
                    person_index += 1
                    member_ids.append(p_id)
                    work_locations = [x for x in district_locations[district["district_id"]] if x["type"] in ["work", "service", "leisure"]]
                    work = self.rng.choice(work_locations)
                    age = self.rng.randint(18, 78)
                    routine_type = self.rng.choice(["commuter", "shift", "local", "student"])
                    persons.append({
                        "person_id": p_id,
                        "name": f"{self.rng.choice(NAMES)} {self.rng.choice(['Lee', 'Kim', 'Smith', 'Garcia', 'Patel', 'Nguyen'])}",
                        "age": age,
                        "district_id": district["district_id"],
                        "household_id": h_id,
                        "occupation": self.rng.choice(OCCUPATIONS),
                        "home_location_id": home["location_id"],
                        "work_location_id": work["location_id"] if age > 21 else None,
                        "current_location_id": home["location_id"],
                        "current_activity": "home",
                        "routine_type": routine_type,
                        "state_summary": {"mood": self.rng.choice(["steady", "strained", "optimistic"]), "energy": self.rng.randint(40, 90)},
                    })
                households.append({
                    "household_id": h_id,
                    "district_id": district["district_id"],
                    "home_location_id": home["location_id"],
                    "member_ids": member_ids,
                    "household_type": self.rng.choice(["single", "couple", "family", "shared"]),
                })
                created += household_size

        return {
            "city": {
                "city_id": city_id,
                "name": "Auralite Metro One",
                "district_ids": [d["district_id"] for d in districts],
                "population_count": len(persons),
                "world_metrics": {"pressure_index": 0.5, "trust_index": 0.5},
            },
            "districts": districts,
            "locations": locations,
            "persons": persons,
            "households": households,
        }

    def _district_population_allocation(self, population_target: int) -> dict:
        weights = {
            "the_crown": 0.10,
            "glass_harbor": 0.11,
            "old_meridian": 0.11,
            "southline": 0.12,
            "north_vale": 0.11,
            "highgarden": 0.07,
            "ember_district": 0.12,
            "ironwood_fringe": 0.09,
            "riverwake": 0.08,
            "neon_market": 0.09,
        }
        allocation = {k: max(10, int(population_target * v)) for k, v in weights.items()}
        diff = population_target - sum(allocation.values())
        keys = list(allocation.keys())
        i = 0
        while diff != 0:
            key = keys[i % len(keys)]
            if diff > 0:
                allocation[key] += 1
                diff -= 1
            else:
                if allocation[key] > 10:
                    allocation[key] -= 1
                    diff += 1
            i += 1
        return allocation

    def _district_locations(self, district_id: str, district_name: str, center: tuple[int, int]) -> list[dict]:
        cx, cy = center
        types = ["home", "home", "home", "work", "work", "leisure", "service", "transit"]
        locations = []
        for idx, loc_type in enumerate(types):
            locations.append({
                "location_id": f"loc_{district_id}_{idx}",
                "district_id": district_id,
                "name": f"{district_name} {loc_type.title()} {idx+1}",
                "type": loc_type,
                "capacity": self.rng.randint(30, 120),
                "x": cx + self.rng.uniform(-0.7, 0.7),
                "y": cy + self.rng.uniform(-0.7, 0.7),
            })
        return locations
