import random
from collections import defaultdict

from ..models.auralite_city import AuraliteCity
from ..models.auralite_district import AuraliteDistrict
from ..models.auralite_household import AuraliteHousehold
from ..models.auralite_location import AuraliteLocation
from ..models.auralite_person import AuralitePerson

DISTRICT_BLUEPRINT = [
    ("the_crown", "The Crown", "finance_prestige", "Finance, politics, and media prestige core.", (62, 16)),
    ("glass_harbor", "Glass Harbor", "startup_speculation", "Innovation corridor with speculative growth.", (78, 20)),
    ("old_meridian", "Old Meridian", "historic_mixed_use", "Historic mixed-use neighborhoods and legacy communities.", (46, 40)),
    ("southline", "Southline", "industrial_logistics", "Industrial belt with labor and infrastructure pressure.", (52, 74)),
    ("north_vale", "North Vale", "suburban_family", "Stabilizing suburb belt focused on schools and routines.", (22, 22)),
    ("highgarden", "Highgarden", "elite_enclave", "Insulated elite enclave with donor influence.", (82, 10)),
    ("ember_district", "Ember District", "transitional_stressed", "Precarious zone with intense structural pressure.", (34, 58)),
    ("ironwood_fringe", "Ironwood Fringe", "edge_hinterland", "Outer edge where rural/suburban/industrial blur.", (16, 78)),
    ("riverwake", "Riverwake", "education_civic", "Research, civic administration, and nonprofits.", (26, 40)),
    ("neon_market", "Neon Market", "nightlife_vice", "Nightlife and fast-money district with hidden networks.", (72, 50)),
]

NAMES = ["Alex", "Jordan", "Taylor", "Casey", "Morgan", "Riley", "Avery", "Parker", "Skyler", "Quinn", "Cameron", "Reese", "Rowan", "Drew", "Hayden", "Emerson", "Kai", "Dakota", "Logan", "Harper"]
OCCUPATIONS = ["analyst", "operator", "nurse", "teacher", "driver", "technician", "clerk", "researcher", "owner", "student"]


class AuraliteSeedService:
    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def create_seed_bundle(self, population_target: int = 240) -> dict:
        city_id = "auralite_city_01"
        districts: list[AuraliteDistrict] = []
        locations: list[AuraliteLocation] = []
        persons: list[AuralitePerson] = []
        households: list[AuraliteHousehold] = []

        district_pop_alloc = self._district_population_allocation(population_target)

        for idx, (district_id, name, archetype, summary, center) in enumerate(DISTRICT_BLUEPRINT):
            pop = district_pop_alloc[district_id]
            districts.append(AuraliteDistrict(
                district_id=district_id,
                name=name,
                archetype=archetype,
                summary=summary,
                map_region_key=f"region_{idx + 1}",
                population_count=pop,
                housing_profile={"pressure": self.rng.choice(["low", "medium", "high"]), "density": self.rng.choice(["low", "medium", "high"])},
                activity_profile={"peak_hour": self.rng.choice([9, 12, 18, 22]), "rhythm": self.rng.choice(["steady", "spiky", "night"])},
                current_activity_level=0.0,
            ))
            locations.extend(self._district_locations(district_id, name, center))

        district_locations = defaultdict(list)
        for loc in locations:
            district_locations[loc.district_id].append(loc)

        person_index = 0
        for district in districts:
            target = district.population_count
            created = 0
            while created < target:
                household_size = min(self.rng.choice([1, 2, 3, 4]), target - created)
                h_id = f"hh_{district.district_id}_{created:03d}"
                homes = [x for x in district_locations[district.district_id] if x.type == "home"]
                home = homes[(created // max(1, household_size)) % len(homes)]
                member_ids = []
                for _ in range(household_size):
                    p_id = f"p_{person_index:04d}"
                    person_index += 1
                    member_ids.append(p_id)
                    work_locations = [x for x in district_locations[district.district_id] if x.type in ["work", "service", "leisure"]]
                    work = self.rng.choice(work_locations)
                    age = self.rng.randint(18, 78)
                    persons.append(AuralitePerson(
                        person_id=p_id,
                        name=f"{self.rng.choice(NAMES)} {self.rng.choice(['Lee', 'Kim', 'Smith', 'Garcia', 'Patel', 'Nguyen'])}",
                        age=age,
                        district_id=district.district_id,
                        household_id=h_id,
                        occupation=self.rng.choice(OCCUPATIONS),
                        home_location_id=home.location_id,
                        work_location_id=work.location_id if age > 21 else None,
                        current_location_id=home.location_id,
                        current_activity="home",
                        routine_type=self.rng.choice(["commuter", "shift", "local", "student"]),
                        state_summary={"mood": self.rng.choice(["steady", "strained", "optimistic"]), "energy": self.rng.randint(40, 90)},
                    ))
                households.append(AuraliteHousehold(
                    household_id=h_id,
                    district_id=district.district_id,
                    home_location_id=home.location_id,
                    member_ids=member_ids,
                    household_type=self.rng.choice(["single", "couple", "family", "shared"]),
                ))
                created += household_size

        city = AuraliteCity(
            city_id=city_id,
            name="Auralite Metro One",
            district_ids=[d.district_id for d in districts],
            population_count=len(persons),
            world_metrics={"pressure_index": 0.5, "trust_index": 0.5},
        )

        return {
            "city": city.to_dict(),
            "districts": [d.to_dict() for d in districts],
            "locations": [l.to_dict() for l in locations],
            "persons": [p.to_dict() for p in persons],
            "households": [h.to_dict() for h in households],
        }

    def _district_population_allocation(self, population_target: int) -> dict:
        weights = {
            "the_crown": 0.10, "glass_harbor": 0.11, "old_meridian": 0.11, "southline": 0.12, "north_vale": 0.11,
            "highgarden": 0.07, "ember_district": 0.12, "ironwood_fringe": 0.09, "riverwake": 0.08, "neon_market": 0.09,
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
            elif allocation[key] > 10:
                allocation[key] -= 1
                diff += 1
            i += 1
        return allocation

    def _district_locations(self, district_id: str, district_name: str, center: tuple[int, int]) -> list[AuraliteLocation]:
        cx, cy = center
        types = ["home", "home", "home", "work", "work", "leisure", "service", "transit"]
        locations = []
        for idx, loc_type in enumerate(types):
            locations.append(AuraliteLocation(
                location_id=f"loc_{district_id}_{idx}",
                district_id=district_id,
                name=f"{district_name} {loc_type.title()} {idx + 1}",
                type=loc_type,
                capacity=self.rng.randint(30, 120),
                x=round(cx + self.rng.uniform(-6, 6), 2),
                y=round(cy + self.rng.uniform(-6, 6), 2),
            ))
        return locations
