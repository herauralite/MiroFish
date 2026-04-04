import random
from collections import defaultdict

from ..models.auralite_city import AuraliteCity
from ..models.auralite_district import AuraliteDistrict
from ..models.auralite_household import AuraliteHousehold
from ..models.auralite_institution import AuraliteInstitution
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
        institutions: list[AuraliteInstitution] = []

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
            institutions.extend(self._district_institutions(district_id, name))

        district_locations = defaultdict(list)
        for loc in locations:
            district_locations[loc.district_id].append(loc)

        district_institutions = defaultdict(list)
        for institution in institutions:
            district_institutions[institution.district_id].append(institution)

        person_index = 0
        for district in districts:
            target = district.population_count
            created = 0
            econ = DISTRICT_SOCIO_ECON[district.district_id]
            district_employers = [i for i in district_institutions[district.district_id] if i.institution_type == 'employer']
            district_landlords = [i for i in district_institutions[district.district_id] if i.institution_type == 'landlord']
            district_transit = [i for i in district_institutions[district.district_id] if i.institution_type == 'transit']
            district_services = [i for i in district_institutions[district.district_id] if i.institution_type in {'healthcare', 'service_access'}]

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
                landlord = self.rng.choice(district_landlords) if district_landlords else None
                eviction_risk = round(min(1.0, pressure_index * self.rng.uniform(0.5, 1.15)), 3)

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
                    employer = self.rng.choice(district_employers) if employed and district_employers else None
                    transit_service = self.rng.choice(district_transit) if district_transit else None
                    service_provider = self.rng.choice(district_services) if district_services else None

                    shift_window = self._sample_shift_window(district.district_id)
                    routine_type = self._routine_from_shift(shift_window, employment_status)
                    wage = round(self.rng.uniform(16, 82), 2) if employed else 0.0
                    burden_share = round(burden * self.rng.uniform(0.7, 1.15), 3)
                    service_access_score = round(self.rng.uniform(0.35, 0.95), 3)
                    commute_reliability = round(self.rng.uniform(0.4, 0.95), 3)

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
                        employer_id=employer.institution_id if employer else None,
                        transit_service_id=transit_service.institution_id if transit_service else None,
                        service_provider_id=service_provider.institution_id if service_provider else None,
                        service_access_score=service_access_score,
                        state_summary={
                            "mood": self.rng.choice(["steady", "strained", "optimistic"]),
                            "energy": self.rng.randint(40, 90),
                            "stress": round(min(1.0, pressure_index * self.rng.uniform(0.7, 1.2)), 3),
                            "commute_reliability": commute_reliability,
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
                    landlord_id=landlord.institution_id if landlord else None,
                    eviction_risk=eviction_risk,
                    context={
                        "dependents": max(0, household_size - 2),
                        "commute_sensitivity": round(self.rng.uniform(0.2, 0.95), 2),
                        "savings_buffer_weeks": self.rng.randint(1, 24),
                        "landlord_pressure": round(landlord.pressure_index, 3) if landlord else 0.0,
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
                "service_access_score": 0.0,
                "social_support_score": 0.0,
            },
        )

        social_graph = self._build_social_graph_scaffolding(
            persons=persons,
            households=households,
            institutions=institutions,
        )

        return {
            "city": city.to_dict(),
            "districts": [d.to_dict() for d in districts],
            "locations": [l.to_dict() for l in locations],
            "persons": [p.to_dict() for p in persons],
            "households": [h.to_dict() for h in households],
            "institutions": [i.to_dict() for i in institutions],
            "social_graph": social_graph,
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

    def _district_institutions(self, district_id: str, district_name: str) -> list[AuraliteInstitution]:
        return [
            AuraliteInstitution(
                institution_id=f"inst_{district_id}_employer_1",
                district_id=district_id,
                name=f"{district_name} Works Cooperative",
                institution_type="employer",
                capacity=self.rng.randint(80, 240),
                access_score=round(self.rng.uniform(0.45, 0.95), 3),
                pressure_index=round(self.rng.uniform(0.15, 0.78), 3),
                metadata={"sector": self.rng.choice(["logistics", "office", "retail", "public", "health"])},
            ),
            AuraliteInstitution(
                institution_id=f"inst_{district_id}_employer_2",
                district_id=district_id,
                name=f"{district_name} Anchor Employers Guild",
                institution_type="employer",
                capacity=self.rng.randint(60, 220),
                access_score=round(self.rng.uniform(0.45, 0.95), 3),
                pressure_index=round(self.rng.uniform(0.18, 0.75), 3),
                metadata={"sector": self.rng.choice(["manufacturing", "education", "service", "media"])},
            ),
            AuraliteInstitution(
                institution_id=f"inst_{district_id}_landlord_1",
                district_id=district_id,
                name=f"{district_name} Housing Group",
                institution_type="landlord",
                capacity=self.rng.randint(50, 180),
                access_score=round(self.rng.uniform(0.35, 0.82), 3),
                pressure_index=round(self.rng.uniform(0.25, 0.88), 3),
                metadata={"portfolio_type": self.rng.choice(["mixed", "legacy", "luxury", "budget"])},
            ),
            AuraliteInstitution(
                institution_id=f"inst_{district_id}_transit_1",
                district_id=district_id,
                name=f"{district_name} Transit Loop",
                institution_type="transit",
                capacity=self.rng.randint(140, 420),
                access_score=round(self.rng.uniform(0.4, 0.9), 3),
                pressure_index=round(self.rng.uniform(0.1, 0.7), 3),
                metadata={"mode": self.rng.choice(["bus", "tram", "metro"])},
            ),
            AuraliteInstitution(
                institution_id=f"inst_{district_id}_health_1",
                district_id=district_id,
                name=f"{district_name} Community Health",
                institution_type="healthcare",
                capacity=self.rng.randint(80, 220),
                access_score=round(self.rng.uniform(0.35, 0.92), 3),
                pressure_index=round(self.rng.uniform(0.14, 0.82), 3),
                metadata={"service_level": self.rng.choice(["clinic", "urgent", "hospital"])},
            ),
            AuraliteInstitution(
                institution_id=f"inst_{district_id}_service_1",
                district_id=district_id,
                name=f"{district_name} Service Access Desk",
                institution_type="service_access",
                capacity=self.rng.randint(60, 170),
                access_score=round(self.rng.uniform(0.35, 0.88), 3),
                pressure_index=round(self.rng.uniform(0.2, 0.8), 3),
                metadata={"focus": self.rng.choice(["benefits", "job_support", "housing_support", "care_navigation"])},
            ),
        ]

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

    def _build_social_graph_scaffolding(
        self,
        persons: list[AuralitePerson],
        households: list[AuraliteHousehold],
        institutions: list[AuraliteInstitution],
    ) -> dict:
        person_by_id = {person.person_id: person for person in persons}
        household_by_id = {hh.household_id: hh for hh in households}

        people_by_employer: dict[str, list[AuralitePerson]] = defaultdict(list)
        people_by_district: dict[str, list[AuralitePerson]] = defaultdict(list)
        for person in persons:
            if person.employer_id:
                people_by_employer[person.employer_id].append(person)
            people_by_district[person.district_id].append(person)

        support_institution_ids = {
            inst.institution_id
            for inst in institutions
            if inst.institution_type in {"healthcare", "service_access"}
        }
        employers = {inst.institution_id: inst.name for inst in institutions if inst.institution_type == "employer"}

        for household in households:
            members = [person_by_id[mid] for mid in household.member_ids if mid in person_by_id]
            avg_member_service = sum(member.service_access_score for member in members) / max(1, len(members))
            support_exposure = round(
                min(
                    1.0,
                    (avg_member_service * 0.5)
                    + (0.35 if any((member.service_provider_id in support_institution_ids) for member in members) else 0.0)
                    + self.rng.uniform(0.0, 0.12),
                ),
                3,
            )
            tie_density = round(min(1.0, max(0.1, len(members) / 4.0)), 3)
            strain_index = round(min(1.0, household.pressure_index * 0.55 + (1.0 - support_exposure) * 0.45), 3)
            household.social_context = {
                "household_tie_density": tie_density,
                "support_exposure": support_exposure,
                "local_strain_index": strain_index,
                "district_support_channels": self.rng.choice(["formal_services", "kin_and_neighbors", "mixed"]),
            }

        for person in persons:
            household = household_by_id.get(person.household_id)
            household_members = [
                member_id
                for member_id in (household.member_ids if household else [])
                if member_id != person.person_id
            ]
            coworker_candidates = [
                coworker.person_id
                for coworker in people_by_employer.get(person.employer_id or "", [])
                if coworker.person_id != person.person_id
            ]
            district_candidates = [
                neighbor.person_id
                for neighbor in people_by_district.get(person.district_id, [])
                if neighbor.person_id != person.person_id and neighbor.household_id != person.household_id
            ]

            coworker_ties = self.rng.sample(coworker_candidates, k=min(2, len(coworker_candidates)))
            district_ties = self.rng.sample(district_candidates, k=min(2, len(district_candidates)))
            person.social_ties = (
                [{"person_id": tie_id, "tie_type": "household"} for tie_id in household_members]
                + [{"person_id": tie_id, "tie_type": "coworker"} for tie_id in coworker_ties]
                + [{"person_id": tie_id, "tie_type": "district_local"} for tie_id in district_ties]
            )

            support_index = round(
                min(
                    1.0,
                    0.35
                    + (0.12 * len(household_members))
                    + (0.1 * len(coworker_ties))
                    + (0.08 * len(district_ties))
                    + (0.18 if person.service_provider_id in support_institution_ids else 0.0),
                ),
                3,
            )
            strain_index = round(
                min(
                    1.0,
                    (household.pressure_index if household else 0.4) * 0.55
                    + (1.0 - support_index) * 0.32
                    + (0.1 if person.employment_status != "employed" else 0.0),
                ),
                3,
            )
            person.social_context = {
                "support_index": support_index,
                "strain_index": strain_index,
                "household_ties": len(household_members),
                "coworker_ties": len(coworker_ties),
                "district_local_ties": len(district_ties),
                "primary_support_channel": (
                    "workplace" if len(coworker_ties) > len(household_members)
                    else "household" if household_members
                    else "district"
                ),
                "employer_adjacency": employers.get(person.employer_id, "none"),
            }

        edge_counts = {"household": 0, "coworker": 0, "district_local": 0}
        for person in persons:
            for tie in person.social_ties:
                edge_counts[tie.get("tie_type", "district_local")] = edge_counts.get(tie.get("tie_type", "district_local"), 0) + 1

        return {
            "schema_version": "m08-lightweight-social-v1",
            "edge_counts": edge_counts,
            "district_neighbors": {
                "the_crown": ["glass_harbor", "old_meridian", "highgarden"],
                "glass_harbor": ["the_crown", "neon_market", "riverwake"],
                "old_meridian": ["the_crown", "riverwake", "ember_district", "southline"],
                "southline": ["old_meridian", "ember_district", "ironwood_fringe", "neon_market"],
                "north_vale": ["riverwake", "old_meridian", "ironwood_fringe"],
                "highgarden": ["the_crown", "glass_harbor"],
                "ember_district": ["old_meridian", "southline", "ironwood_fringe", "riverwake"],
                "ironwood_fringe": ["ember_district", "southline", "north_vale"],
                "riverwake": ["north_vale", "old_meridian", "glass_harbor", "ember_district"],
                "neon_market": ["glass_harbor", "southline", "old_meridian"],
            },
            "notes": [
                "Lightweight relationship hooks only; not a full social-memory graph.",
                "Supports household/coworker/district-local explainability contributors.",
                "District-neighbor map included for bounded ripple propagation scaffolding.",
            ],
        }
