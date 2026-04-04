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

DISTRICT_SOCIO_ECON = {
    "the_crown": {"income": (9000, 18000), "rent": (3400, 6800), "employment": 0.96, "night_bias": 0.15},
    "glass_harbor": {"income": (6200, 14000), "rent": (2700, 5200), "employment": 0.93, "night_bias": 0.24},
    "old_meridian": {"income": (4200, 9200), "rent": (1600, 3600), "employment": 0.9, "night_bias": 0.18},
    "southline": {"income": (3400, 7800), "rent": (1200, 2600), "employment": 0.88, "night_bias": 0.34},
    "north_vale": {"income": (4600, 9800), "rent": (1500, 3000), "employment": 0.91, "night_bias": 0.16},
    "highgarden": {"income": (11000, 22000), "rent": (4200, 7600), "employment": 0.97, "night_bias": 0.08},
    "ember_district": {"income": (2200, 5200), "rent": (950, 2200), "employment": 0.79, "night_bias": 0.22},
    "ironwood_fringe": {"income": (3000, 6600), "rent": (900, 2100), "employment": 0.85, "night_bias": 0.2},
    "riverwake": {"income": (4400, 10400), "rent": (1500, 3200), "employment": 0.92, "night_bias": 0.18},
    "neon_market": {"income": (3200, 8700), "rent": (1400, 3400), "employment": 0.87, "night_bias": 0.42},
}


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
                activity_profile={"peak_hour": self.rng.choice([8, 9, 12, 18, 22]), "rhythm": self.rng.choice(["steady", "spiky", "night"])},
            ))
            locations.extend(self._district_locations(district_id, name, center))

        district_locations = defaultdict(list)
        for loc in locations:
            district_locations[loc.district_id].append(loc)

        person_index = 0
        for district in districts:
            target = district.population_count
            created = 0
            econ = DISTRICT_SOCIO_ECON[district.district_id]
            while created < target:
                household_size = min(self.rng.choice([1, 2, 2, 3, 4]), target - created)
                h_id = f"hh_{district.district_id}_{created:03d}"
                homes = [x for x in district_locations[district.district_id] if x.type == "home"]
                home = homes[(created // max(1, household_size)) % len(homes)]
                member_ids = []
                income_total = round(self.rng.uniform(*econ["income"]), 2)
                rent_total = round(self.rng.uniform(*econ["rent"]), 2)
                burden = round(min(0.95, rent_total / max(income_total, 500.0)), 3)
                pressure_index = round(min(1.0, burden + self.rng.uniform(0.02, 0.2)), 3)

                for _ in range(household_size):
                    p_id = f"p_{person_index:04d}"
                    person_index += 1
                    member_ids.append(p_id)
                    age = self.rng.randint(18, 78)
                    employment_roll = self.rng.random()
                    employed = employment_roll <= econ["employment"] and age <= 68
                    employment_status = "employed" if employed else ("student" if age <= 24 and self.rng.random() > 0.4 else "underemployed")

                    work_locations = [x for x in district_locations[district.district_id] if x.type in ["work", "service", "leisure"]]
                    work = self.rng.choice(work_locations) if employed else None
                    shift_window = self._sample_shift_window(district.district_id)
                    routine_type = self._routine_from_shift(shift_window, employment_status)
                    wage = round(self.rng.uniform(16, 82), 2) if employed else 0.0
                    burden_share = round(burden * self.rng.uniform(0.7, 1.15), 3)

                    persons.append(AuralitePerson(
                        person_id=p_id,
                        name=f"{self.rng.choice(NAMES)} {self.rng.choice(['Lee', 'Kim', 'Smith', 'Garcia', 'Patel', 'Nguyen'])}",
                        age=age,
                        district_id=district.district_id,
                        household_id=h_id,
                        occupation=self.rng.choice(OCCUPATIONS),
                        home_location_id=home.location_id,
                        work_location_id=work.location_id if work else None,
                        current_location_id=home.location_id,
                        current_activity="home",
                        routine_type=routine_type,
                        employment_status=employment_status,
                        hourly_wage=wage,
                        housing_burden_share=burden_share,
                        shift_window=shift_window,
                        state_summary={
                            "mood": self.rng.choice(["steady", "strained", "optimistic"]),
                            "energy": self.rng.randint(40, 90),
                            "stress": round(min(1.0, pressure_index * self.rng.uniform(0.7, 1.2)), 3),
                        },
                    ))

                households.append(AuraliteHousehold(
                    household_id=h_id,
                    district_id=district.district_id,
                    home_location_id=home.location_id,
                    member_ids=member_ids,
                    household_type=self.rng.choice(["single", "couple", "family", "shared"]),
                    monthly_income=income_total,
                    monthly_rent=rent_total,
                    housing_cost_burden=burden,
                    pressure_level="high" if burden >= 0.46 else "medium" if burden >= 0.31 else "low",
                    pressure_index=pressure_index,
                    context={
                        "dependents": max(0, household_size - 2),
                        "commute_sensitivity": round(self.rng.uniform(0.2, 0.95), 2),
                        "savings_buffer_weeks": self.rng.randint(1, 24),
                    },
                ))
                created += household_size

        city = AuraliteCity(
            city_id=city_id,
            name="Auralite Metro One",
            district_ids=[d.district_id for d in districts],
            population_count=len(persons),
            world_metrics={
                "employment_rate": 0.0,
                "avg_hourly_wage": 0.0,
                "avg_housing_burden": 0.0,
                "household_pressure_index": 0.0,
            },
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

    def _sample_shift_window(self, district_id: str) -> str:
        night_bias = DISTRICT_SOCIO_ECON[district_id]["night_bias"]
        roll = self.rng.random()
        if roll < night_bias:
            return "night"
        if roll < night_bias + 0.18:
            return "swing"
        return "day"

    @staticmethod
    def _routine_from_shift(shift_window: str, employment_status: str) -> str:
        if employment_status != "employed":
            return "local"
        if shift_window == "night":
            return "shift"
        if shift_window == "swing":
            return "mixed"
        return "commuter"
