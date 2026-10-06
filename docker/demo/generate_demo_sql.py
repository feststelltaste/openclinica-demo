#!/usr/bin/env python3
"""Generate deterministic, non-medical demo data for OpenClinica."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


DEMO_PASSWORD = "openclinica"

STUDIES = (
    ("COFFEE", "Coffee and Morning Energy", "Does morning coffee make the day feel easier?", 20, "2024-01-01", "2026-12-31", "2024-02-05", 30),
    ("WALK", "Daily Walk and Mood", "Does a short daily walk improve mood?", 25, "2024-06-01", "2027-05-31", "2024-07-08", 60),
    ("MUSIC", "Music While Working", "Does background music help people focus?", 32, "2025-01-01", "2027-12-31", "2025-02-03", 90),
    ("PLANTS", "Indoor Plants and Wellbeing", "Do desk plants make a room feel better?", 40, "2025-03-01", "2026-11-30", "2025-04-07", 120),
    ("PUZZLE", "Puzzle Break and Focus", "Does a short puzzle break help concentration?", 50, "2025-09-01", "2027-08-31", "2025-10-06", 180),
    ("TEA", "Herbal Tea and Relaxation", "Does evening herbal tea help people relax?", 67, "2026-01-01", "2027-12-31", "2026-02-02", 240),
    ("READ", "Reading Before Bed", "Does reading before bed improve sleep?", 100, "2026-04-01", "2028-03-31", "2026-05-04", 300),
    ("SCREEN", "Screen-Free Evening", "Does one hour without screens improve sleep?", 200, "2026-07-01", "2028-06-30", "2026-07-06", 365),
)

ITEMS = {
    1: ("checkin_start", "Check-in start date"),
    2: ("checkin_end", "Check-in end date"),
    3: ("entry_date", "Entry date"),
    4: ("entry_time", "Entry time"),
    5: ("main_activity", "Main activity today"),
    6: ("energy_score", "Energy score from 1 to 10"),
    7: ("had_coffee", "Did you drink coffee?"),
    8: ("coffee_cups", "Number of coffee cups"),
    9: ("took_walk", "Did you take a walk?"),
    10: ("walk_date", "Walk date"),
    11: ("walk_notes", "Short walk notes"),
    12: ("heard_music", "Did you listen to music?"),
    13: ("music_date", "Music date"),
    14: ("favorite_song", "Favorite song today"),
    15: ("read_book", "Did you read a book?"),
    16: ("reading_date", "Reading date"),
    17: ("minutes_read", "Minutes spent reading"),
    18: ("book_type", "Type of book"),
    19: ("sleep_hours", "Hours of sleep"),
    20: ("screen_minutes", "Screen time in minutes"),
    21: ("step_count", "Approximate step count"),
    22: ("water_glasses", "Glasses of water"),
    23: ("good_mood", "Were you in a good mood?"),
    24: ("mood_notes", "Short mood notes"),
    25: ("watered_plant", "Did you water a plant?"),
    26: ("plant_count", "Number of plants nearby"),
    27: ("daily_comment", "Daily comment"),
    28: ("habit_name", "Habit name"),
    29: ("habit_start", "Habit start date"),
    30: ("habit_end", "Habit end date"),
    31: ("continue_habit", "Do you want to continue this habit?"),
    32: ("habit_reason", "Why did you choose this habit?"),
    33: ("habit_place", "Where did you do this habit?"),
    34: ("habit_frequency", "How often did you do this habit?"),
}

METADATA_TABLES = {
    "crf", "crf_version", "item", "response_set", "section",
    "item_form_metadata", "item_group", "item_group_metadata", "versioning_map",
}


def qi(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def qv(value: object) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def insert(table: str, values: dict[str, object]) -> None:
    columns = ", ".join(qi(column) for column in values)
    literals = ", ".join(qv(value) for value in values.values())
    print(f"INSERT INTO {qi(table)} ({columns}) VALUES ({literals});")


def prepare_metadata(table: str, values: dict[str, str]) -> dict[str, str]:
    values = values.copy()
    if table == "crf":
        if int(values["crf_id"]) == 1:
            values.update(name="Daily Check-In", description="Simple daily questions about mood and habits", oc_oid="F_DAILY_CHECKIN")
        else:
            values.update(name="Weekly Habits", description="Simple weekly habit summary", oc_oid="F_WEEKLY_HABITS")
    elif table == "crf_version":
        version_id = int(values["crf_version_id"])
        values.update(name="v1.0", description="Synthetic demo form", revision_notes="Generated for local testing", oc_oid="F_DAILY_CHECKIN_V10" if version_id == 1 else "F_WEEKLY_HABITS_V10")
    elif table == "item":
        item_id = int(values["item_id"])
        name, description = ITEMS[item_id]
        values.update(name=name, description=description, oc_oid=f"I_DEMO_{name.upper()}")
    elif table == "item_form_metadata":
        values["left_item_text"] = ITEMS[int(values["item_id"])][1]
        values["header"] = "Everyday habits"
        values["subheader"] = ""
    elif table == "section":
        title = {1: "Daily activity", 2: "Sleep and focus", 3: "Comments", 4: "Weekly habits"}[int(values["section_id"])]
        values.update(label=title.replace(" ", ""), title=title, subtitle="Simple synthetic demo questions", instructions="Enter demo values only.")
    elif table == "item_group":
        group_id = int(values["item_group_id"])
        name = {1: "Daily answers", 2: "Activity details", 3: "Weekly answers", 4: "Habit details"}[group_id]
        values.update(name=name, oc_oid=f"IG_DEMO_{group_id}")
    elif table == "item_group_metadata":
        values["header"] = "Everyday habits"
        values["subheader"] = ""
    elif table == "response_set":
        response_type = int(values["response_type_id"])
        if response_type in {5, 6}:
            values.update(label="Simple yes or no", options_text="No,Yes,Not sure" if response_type == 6 else "Yes,No", options_values="0,1,2" if response_type == 6 else "1,0")
        else:
            values["label"] = "Simple text"
    return values


def study_json(study_number: int, code: str, name: str, summary: str, expected_enrollment: int,
               planned_start: str, planned_end: str) -> str:
    created = dt.date.fromisoformat(planned_start) - dt.timedelta(days=90)
    payload = {
        "study_id": 1000 + study_number,
        "parent_study_id": None,
        "unique_identifier": f"DEMO-{code}-001",
        "secondary_identifier": f"FUN-{study_number:02d}",
        "name": name,
        "summary": summary + " Synthetic data only.",
        "owner_id": 1,
        "update_id": 1,
        "status_id": 1,
        "official_title": name,
        "expected_total_enrollment": expected_enrollment,
        "date_planned_start": planned_start,
        "date_planned_end": planned_end,
        "protocol_date_verification": (created + dt.timedelta(days=30)).isoformat(),
        "principal_investigator": "Dr. Demo",
        "facility_name": "OpenClinica Demo Center",
        "facility_city": "Berlin",
        "facility_country": "Germany",
        "sponsor": "OpenClinica Local Test",
        "oc_oid": f"S_DEMO_{code}",
        "date_created": created.isoformat(),
        "date_updated": created.isoformat(),
    }
    return json.dumps(payload, separators=(",", ":"))


def value_for_item(item_id: int, person: int, visit: int, theme: str, event_date: dt.date) -> str:
    if item_id in {1, 3, 10, 13, 16, 29}:
        return event_date.strftime("%m/%d/%Y")
    if item_id in {2, 30}:
        return (event_date + dt.timedelta(days=7)).strftime("%m/%d/%Y")
    values = {
        4: "09:00",
        5: f"{theme.title()} activity",
        6: str(4 + (person + visit) % 7),
        7: str((person + visit) % 2),
        8: str(person % 4),
        9: str((person + 1) % 2),
        11: "A comfortable short walk",
        12: str(person % 2),
        14: ("Happy Tune", "Quiet Piano", "Morning Beat")[person % 3],
        15: str((person + visit) % 2),
        17: str(10 + (person % 6) * 5),
        18: ("Novel", "History", "Science", "Comic")[person % 4],
        19: str(6 + person % 3),
        20: str(30 + (person % 8) * 15),
        21: str(3000 + (person % 10) * 700),
        22: str(4 + person % 6),
        23: str((person + visit) % 2),
        24: ("Calm day", "Busy but good", "A little tired")[person % 3],
        25: str(person % 2),
        26: str(1 + person % 5),
        27: f"Synthetic note for person {person:03d}",
        28: f"{theme.title()} habit",
        31: str(1 if person % 5 else 0),
        32: f"I want to learn about {theme}.",
        33: ("Home", "Office", "Park", "Library")[person % 4],
        34: ("Daily", "Three times a week", "Weekly")[person % 3],
    }
    return values.get(item_id, "")


def sync_sequences() -> None:
    print(r"""
DO $demo$
DECLARE sequence_row record; max_value bigint;
BEGIN
    FOR sequence_row IN
        SELECT namespace.nspname AS schema_name, table_class.relname AS table_name,
               column_info.attname AS column_name, sequence_class.relname AS sequence_name
        FROM pg_class sequence_class
        JOIN pg_depend dependency ON dependency.objid = sequence_class.oid AND dependency.deptype = 'a'
        JOIN pg_class table_class ON table_class.oid = dependency.refobjid
        JOIN pg_namespace namespace ON namespace.oid = table_class.relnamespace
        JOIN pg_attribute column_info ON column_info.attrelid = table_class.oid AND column_info.attnum = dependency.refobjsubid
        WHERE sequence_class.relkind = 'S' AND namespace.nspname = 'public'
    LOOP
        EXECUTE format('SELECT max(%I) FROM %I.%I', sequence_row.column_name, sequence_row.schema_name, sequence_row.table_name) INTO max_value;
        IF max_value IS NOT NULL THEN
            PERFORM setval(format('%I.%I', sequence_row.schema_name, sequence_row.sequence_name)::regclass, max_value, true);
        END IF;
    END LOOP;
END
$demo$;
""")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    fixture = repo_root / "core/src/test/resources/org/akaza/openclinica/dao/rule/testdata/RuleDaoTest.xml"
    source_rows = [(element.tag, dict(element.attrib)) for element in ET.parse(fixture).getroot()]
    metadata_rows = [(table, prepare_metadata(table, values)) for table, values in source_rows if table in METADATA_TABLES]
    event_template = next(values for table, values in source_rows if table == "study_event")
    event_crf_templates = [values for table, values in source_rows if table == "event_crf"][:2]
    item_templates: dict[int, dict[str, str]] = {}
    for table, values in source_rows:
        if table == "item_data":
            item_templates.setdefault(int(values["item_id"]), values)
    default_item_template = next(iter(item_templates.values()))

    print(r"\set ON_ERROR_STOP on")
    print("BEGIN;")
    print("SET client_min_messages TO WARNING;")
    print("TRUNCATE crf, subject, study_event_definition RESTART IDENTITY CASCADE;")
    print("DELETE FROM study_user_role WHERE study_id <> 1;")
    print("DELETE FROM study_parameter_value WHERE study_id <> 1;")
    print("DELETE FROM study WHERE study_id <> 1;")
    print("UPDATE configuration SET value = '0' WHERE key IN ('pwd.change.required', 'pwd.expiration.days');")

    for study_number, (code, name, summary, expected_enrollment, planned_start, planned_end,
                       _enrollment_start, _follow_up_days) in enumerate(STUDIES, 1):
        study_id = 1000 + study_number
        payload = study_json(study_number, code, name, summary, expected_enrollment, planned_start, planned_end)
        print(f"INSERT INTO study SELECT (json_populate_record(base_study, {qv(payload)}::json)).* FROM study base_study WHERE study_id = 1;")
        print("INSERT INTO study_parameter_value (study_parameter_value_id, study_id, value, parameter) "
              f"SELECT {study_id} * 100 + row_number() OVER (ORDER BY parameter), {study_id}, value, parameter "
              "FROM study_parameter_value WHERE study_id = 1;")
        print("INSERT INTO study_user_role (role_name, study_id, status_id, owner_id, date_created, date_updated, update_id, user_name) "
              f"SELECT role_name, {study_id}, status_id, owner_id, date_created, date_updated, update_id, user_name "
              "FROM study_user_role WHERE study_id = 1;")

    for table, values in metadata_rows:
        insert(table, values)

    item_data_id = 0
    for study_number, (code, _name, _summary, _expected_enrollment, _planned_start, _planned_end,
                       enrollment_start, follow_up_days) in enumerate(STUDIES, 1):
        study_id = 1000 + study_number
        first_enrollment = dt.date.fromisoformat(enrollment_start)
        definition_ids = (study_id * 10 + 1, study_id * 10 + 2)
        for visit, definition_id in enumerate(definition_ids, 1):
            insert("study_event_definition", {
                "study_event_definition_id": definition_id, "study_id": study_id,
                "name": "First Check-In" if visit == 1 else "Follow-Up Visit",
                "description": "Simple synthetic demo visit", "repeating": "false" if visit == 1 else "true",
                "type": "scheduled", "category": "Everyday habits", "owner_id": 1,
                "status_id": 1, "date_created": "2025-01-01", "ordinal": visit,
                "oc_oid": f"SE_{code}_{visit}",
            })
            for crf_id in (1, 2):
                insert("event_definition_crf", {
                    "event_definition_crf_id": study_id * 100 + visit * 10 + crf_id,
                    "study_event_definition_id": definition_id, "study_id": study_id,
                    "crf_id": crf_id, "required_crf": "true", "double_entry": "false",
                    "require_all_text_filled": "false", "decision_conditions": "false",
                    "null_values": "", "default_version_id": crf_id, "status_id": 1,
                    "owner_id": 1, "date_created": "2025-01-01", "ordinal": crf_id,
                    "electronic_signature": "false",
                })

        for local_person in range(1, 21):
            person = (study_number - 1) * 20 + local_person
            subject_id = 10000 + person
            enrollment = first_enrollment + dt.timedelta(days=(local_person - 1) * 3)
            insert("subject", {
                "subject_id": subject_id, "status_id": 1,
                "date_of_birth": f"{1960 + person % 35:04d}-{person % 12 + 1:02d}-{person % 25 + 1:02d}",
                "gender": "f" if person % 2 else "m",
                "unique_identifier": f"SYN-{code}-{local_person:03d}",
                "date_created": enrollment.isoformat(), "owner_id": 1, "dob_collected": "true",
            })
            insert("study_subject", {
                "study_subject_id": subject_id, "label": f"{code}-{local_person:03d}",
                "secondary_label": f"Demo person {local_person:03d}", "subject_id": subject_id,
                "study_id": study_id, "status_id": 1, "enrollment_date": enrollment.isoformat(),
                "date_created": enrollment.isoformat(), "owner_id": 1,
                "oc_oid": f"SS_{code}_{local_person:03d}",
            })

            for visit, definition_id in enumerate(definition_ids, 1):
                event_id = person * 10 + visit
                event_date = enrollment + dt.timedelta(days=0 if visit == 1 else follow_up_days)
                event_values = event_template.copy()
                event_values.update(study_event_id=str(event_id), study_event_definition_id=str(definition_id),
                                    study_subject_id=str(subject_id),
                                    location=("Berlin" if person % 2 else "Hamburg") + " Demo Center",
                                    sample_ordinal="1", date_start=f"{event_date.isoformat()} 09:00:00",
                                    date_end=f"{event_date.isoformat()} 10:00:00",
                                    date_created=event_date.isoformat(), date_updated=event_date.isoformat())
                insert("study_event", event_values)

                for crf_id, template in enumerate(event_crf_templates, 1):
                    event_crf_id = person * 100 + visit * 10 + crf_id
                    event_crf_values = template.copy()
                    event_crf_values.update(event_crf_id=str(event_crf_id), study_event_id=str(event_id),
                                            crf_version_id=str(crf_id), study_subject_id=str(subject_id),
                                            date_interviewed=event_date.isoformat(),
                                            interviewer_name="Demo Coordinator",
                                            date_created=event_date.isoformat(), date_updated=event_date.isoformat())
                    insert("event_crf", event_crf_values)
                    for item_id in (range(1, 28) if crf_id == 1 else range(28, 35)):
                        item_data_id += 1
                        item_values = item_templates.get(item_id, default_item_template).copy()
                        item_values.update(item_data_id=str(item_data_id), item_id=str(item_id),
                                           event_crf_id=str(event_crf_id), status_id="2",
                                           value=value_for_item(item_id, person, visit, code.lower(), event_date),
                                           date_created=event_date.isoformat(), owner_id="1", ordinal="1")
                        insert("item_data", item_values)

    print("UPDATE user_account SET active_study = 1001 WHERE user_name = 'root';")
    root_passwd = hashlib.sha1(DEMO_PASSWORD.encode()).hexdigest()
    print(f"UPDATE user_account SET passwd = '{root_passwd}' WHERE user_name = 'root';")
    sync_sequences()
    print("COMMIT;")
    return 0


if __name__ == "__main__":
    sys.exit(main())
