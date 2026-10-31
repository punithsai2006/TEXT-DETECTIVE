import json
import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.models.schemas import DocumentType
from app.services.ingestion.preprocessor import process_uploaded_file
from app.storage.case_store import case_store

BASE_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SAMPLE_DIR = BASE_DATA_DIR / "sample_cases"
GROUND_TRUTH_DIR = BASE_DATA_DIR / "ground_truth"


def create_case_2_blackwood():
    case_id = "case_02_blackwood"
    case_name = "The Blackwood Manor Art Heist"
    case_folder = SAMPLE_DIR / case_id
    case_folder.mkdir(parents=True, exist_ok=True)

    docs = {
        "interview_curator_clara.txt": (
            "INTERVIEW TRANSCRIPT: CLARA STERLING\n"
            "Case: Blackwood Manor Art Heist\n"
            "Interviewer: Detective Reynolds\n"
            "Interviewee: Clara Sterling, Gallery Curator\n\n"
            "[09:00 AM] REYNOLDS: State your name and position.\n"
            "[09:00 AM] STERLING: Clara Sterling, chief curator at Blackwood Manor Gallery.\n"
            "[09:01 AM] REYNOLDS: When did you last see the Vermeer canvas 'The Silent Witness'?\n"
            "[09:01 AM] STERLING: I personally inspected the vault at 6:00 PM on Friday and locked the biometric vault safe.\n"
            "[09:02 AM] REYNOLDS: Did anyone else have the emergency override code?\n"
            "[09:02 AM] STERLING: No, only Lord Blackwood and I possess the vault keys. The security guard, Julian Vance, has no safe access.\n"
            "[09:03 AM] REYNOLDS: What time did you leave the estate?\n"
            "[09:03 AM] STERLING: I drove through the front gates at 6:30 PM and attended a charity dinner in town until midnight.\n"
        ),
        "interview_guard_julian.txt": (
            "INTERVIEW TRANSCRIPT: JULIAN VANCE\n"
            "Case: Blackwood Manor Art Heist\n"
            "Interviewer: Detective Reynolds\n"
            "Interviewee: Julian Vance, Night Guard\n\n"
            "[10:30 AM] REYNOLDS: Julian, describe your patrol route on Friday night.\n"
            "[10:30 AM] VANCE: I began my shift at 7:00 PM. I stayed in the security control booth until 11:00 PM.\n"
            "[10:31 AM] REYNOLDS: Did you hear the basement motion alarm at 10:15 PM?\n"
            "[10:31 AM] VANCE: The motion alarm never sounded in the booth. The control panel showed green all night.\n"
            "[10:32 AM] REYNOLDS: Did anyone visit the estate during your watch?\n"
            "[10:32 AM] VANCE: The courier van from Apex Deliveries arrived at 9:50 PM with conservatory plants, and drove off at 10:30 PM.\n"
            "[10:33 AM] REYNOLDS: Did you leave your desk at all?\n"
            "[10:33 AM] VANCE: I remained at the security console continuously from 7:00 PM to midnight without leaving.\n"
        ),
        "interview_cleaner_marta.txt": (
            "INTERVIEW TRANSCRIPT: MARTA GOMEZ\n"
            "Case: Blackwood Manor Art Heist\n"
            "Interviewer: Detective Reynolds\n"
            "Interviewee: Marta Gomez, Evening Housekeeper\n\n"
            "[11:15 AM] REYNOLDS: Marta, where were you working between 9:00 PM and 11:00 PM?\n"
            "[11:15 AM] GOMEZ: I was cleaning the second-floor gallery and dining room.\n"
            "[11:16 AM] REYNOLDS: Did you see Julian Vance during that time?\n"
            "[11:16 AM] GOMEZ: Yes. Julian was not at the security desk. I saw Julian walking near the basement service elevator carrying a heavy black duffel bag around 10:15 PM.\n"
            "[11:17 AM] REYNOLDS: Did the gallery motion sensors go off?\n"
            "[11:17 AM] GOMEZ: Yes, the loud acoustic chime in the hallway buzzed at 10:15 PM, but it shut off after thirty seconds.\n"
        ),
        "alarm_system_telemetry.txt": (
            "[2024-10-18 19:00:00] SYSTEM: Main security grid armed by Operator #04 [Julian Vance]\n"
            "[2024-10-18 21:50:12] GATE_SENSOR: Rear estate delivery gate opened by remote buzzer\n"
            "[2024-10-18 22:15:02] MOTION_SENSOR: Zone 4 (Basement Vault Corridor) - ALARM TRIGGERED (Duration: 34s)\n"
            "[2024-10-18 22:15:36] CONSOLE: Alarm in Zone 4 manually silenced and acknowledged by local console\n"
            "[2024-10-18 22:28:19] VAULT_SENSOR: Safe door magnetic contact broken - MANUAL KEY OVERRIDE USED\n"
            "[2024-10-18 22:31:00] GATE_SENSOR: Rear delivery gate closed - Vehicle departed\n"
        ),
        "curator_appraisal_email.txt": (
            "From: Clara Sterling <c.sterling@blackwoodestate.co.uk>\n"
            "To: Arthur Blackwood <arthur@blackwoodholdings.com>\n"
            "Date: October 17, 2024 04:15 PM\n"
            "Subject: Insurance revaluation and vault arrangement\n\n"
            "Lord Blackwood,\n\n"
            "Following yesterday's appraisal, 'The Silent Witness' has been valued at 14.5 million GBP. "
            "As requested, the second physical vault key was placed in the unlocked desk drawer inside the security guard station.\n"
            "Please ensure Julian is reminded not to touch the key.\n\n"
            "Clara Sterling\n"
        ),
        "police_initial_report.txt": (
            "METROPOLITAN POLICE - INCIDENT REPORT\n"
            "Incident: Burglary / Theft of High-Value Cultural Property\n"
            "Location: Blackwood Manor, Surrey\n"
            "Officer: DI Thomas Reynolds, Badge #8841\n"
            "Date of Incident: October 18, 2024\n\n"
            "1. SYNOPSIS: At 06:15 AM on October 19, curator Clara Sterling discovered the basement vault door open. "
            "The 17th-century Vermeer canvas was cut from its gilded frame and missing.\n"
            "2. FORCED ENTRY: No external doors, windows, or gates showed forced entry. Entry was executed via the rear delivery gate and physical vault key.\n"
            "3. FORENSICS: Tire tracks in the gravel courtyard match standard commercial light transport vehicles.\n"
        ),
        "courier_delivery_log.txt": (
            "APEX DELIVERIES - DAILY VEHICLE TELEMETRY & RUN SHEET\n"
            "Driver: Marcus Finch | Vehicle: Ford Transit (Reg: LK68 YTR)\n"
            "2024-10-18 21:50:00 - Arrived Blackwood Manor Rear Delivery Gate\n"
            "2024-10-18 22:05:00 - Consignment offloaded at Greenhouse\n"
            "2024-10-18 22:30:45 - Vehicle cleared gate and departed towards A3 motorway\n"
            "Driver Statement: 'The security guard walked down to the van around 10:20 PM and asked if we could transport a boxed package to London. I refused and left.'\n"
        ),
        "estate_cctv_audit_report.txt": (
            "BLACKWOOD MANOR SECURITY AUDIT\n"
            "Forensic review of CCTV Hard Drive Unit #1:\n"
            "- Cameras 1 through 3 (Front Driveway) functioned continuously.\n"
            "- Camera 5 (Basement Corridor) was disabled between 22:10 and 22:35 PM due to an unplugged video feed cable.\n"
            "- Gate Camera showed Lord Blackwood's vehicle did not return to the estate until Saturday afternoon.\n"
        )
    }

    for fn, content in docs.items():
        with open(case_folder / fn, "w", encoding="utf-8") as f:
            f.write(content)

    gt_data = {
        "case_id": case_id,
        "case_name": case_name,
        "document_count": len(docs),
        "true_entities": {
            "persons": ["Clara Sterling", "Julian Vance", "Marta Gomez", "Thomas Reynolds", "Marcus Finch", "Arthur Blackwood"],
            "organizations": ["Blackwood Manor Gallery", "Metropolitan Police", "Apex Deliveries"],
            "locations": ["Basement Vault", "Zone 4", "Greenhouse", "Surrey", "Second-Floor Gallery"],
            "objects": ["The Silent Witness", "Vault Safe Key", "Black Duffel Bag", "Ford Transit LK68 YTR"]
        },
        "planted_contradictions": [
            {
                "id": "c2_01",
                "entity": "Julian Vance",
                "topic": "Presence at desk vs basement elevator with duffel bag",
                "doc_a": "interview_guard_julian.txt",
                "statement_a": "I remained at the security console continuously from 7:00 PM to midnight without leaving.",
                "doc_b": "interview_cleaner_marta.txt",
                "statement_b": "I saw Julian walking near the basement service elevator carrying a heavy black duffel bag around 10:15 PM.",
                "type": "confirmed_contradiction"
            },
            {
                "id": "c2_02",
                "entity": "Motion Alarm",
                "topic": "Alarm sounding vs never sounding",
                "doc_a": "interview_guard_julian.txt",
                "statement_a": "The motion alarm never sounded in the booth. The control panel showed green all night.",
                "doc_b": "alarm_system_telemetry.txt",
                "statement_b": "[2024-10-18 22:15:02] MOTION_SENSOR: Zone 4 (Basement Vault Corridor) - ALARM TRIGGERED (Duration: 34s)",
                "type": "confirmed_contradiction"
            },
            {
                "id": "c2_03",
                "entity": "Vault Key Security",
                "topic": "Only Lord Blackwood and Clara have keys vs spare in unlocked desk drawer",
                "doc_a": "interview_curator_clara.txt",
                "statement_a": "No, only Lord Blackwood and I possess the vault keys. The security guard, Julian Vance, has no safe access.",
                "doc_b": "curator_appraisal_email.txt",
                "statement_b": "As requested, the second physical vault key was placed in the unlocked desk drawer inside the security guard station.",
                "type": "confirmed_contradiction"
            }
        ],
        "correct_hypothesis": {
            "title": "Insider Theft by Security Guard Julian Vance",
            "description": "Julian Vance retrieved the spare vault key from the unlocked desk drawer, unplugged camera 5, entered the basement vault at 10:15 PM, silenced the alarm, cut the Vermeer painting from its frame, and attempted to stash it in a duffel bag.",
            "is_correct": True
        },
        "decoy_hypotheses": [
            {
                "title": "External Delivery Driver Intrusion by Apex Courier",
                "description": "Courier Marcus Finch breached the greenhouse and entered the basement vault without guard knowledge.",
                "is_correct": False
            },
            {
                "title": "Insurance Fraud Orchestrated by Curator Clara Sterling",
                "description": "Clara Sterling returned after midnight and removed the painting to claim the 14.5 million GBP policy.",
                "is_correct": False
            }
        ]
    }

    with open(GROUND_TRUTH_DIR / f"{case_id}_ground_truth.json", "w", encoding="utf-8") as f:
        json.dump(gt_data, f, indent=2)


def create_case_3_helios():
    case_id = "case_03_helios"
    case_name = "The Helios Pharma Clinical Trial Discrepancy"
    case_folder = SAMPLE_DIR / case_id
    case_folder.mkdir(parents=True, exist_ok=True)

    docs = {
        "interview_dr_kaufman.txt": (
            "INTERVIEW TRANSCRIPT: DR. ARLO KAUFMAN\n"
            "Case: Helios Pharma Trial HL-902\n"
            "Interviewer: Regulatory Auditor Sarah Jenkins\n"
            "Interviewee: Dr. Arlo Kaufman, Principal Investigator\n\n"
            "[09:00 AM] JENKINS: Dr. Kaufman, were all Phase 2 sample vials kept at minus 80 Celsius continuously?\n"
            "[09:00 AM] KAUFMAN: Yes, absolutely. Freezer Unit 4 maintained strict minus 80 Celsius throughout the August testing window.\n"
            "[09:01 AM] JENKINS: Did any power outage affect the cold storage?\n"
            "[09:01 AM] KAUFMAN: There was zero temperature excursion. The backup diesel generator kicked in seamlessly during the August 14 storm.\n"
            "[09:02 AM] JENKINS: When were the efficacy blood draws sent to the central reference lab?\n"
            "[09:02 AM] KAUFMAN: They were dispatched via CryoExpress courier on August 16 at 08:00 AM under dry ice.\n"
        ),
        "interview_lab_tech_priya.txt": (
            "INTERVIEW TRANSCRIPT: PRIYA SHARMA\n"
            "Case: Helios Pharma Trial HL-902\n"
            "Interviewer: Regulatory Auditor Sarah Jenkins\n"
            "Interviewee: Priya Sharma, Senior Laboratory Technician\n\n"
            "[10:30 AM] JENKINS: Priya, tell us about the condition of Freezer Unit 4 on August 14.\n"
            "[10:30 AM] SHARMA: The backup generator failed to engage for nearly six hours. The digital display on Freezer Unit 4 rose to plus 4 Celsius between 2:00 AM and 7:45 AM.\n"
            "[10:31 AM] JENKINS: Did you report this excursion to Dr. Kaufman?\n"
            "[10:31 AM] SHARMA: Yes, I sent an urgent email at 08:15 AM on August 14 and logged it in the paper deviation binder.\n"
            "[10:32 AM] JENKINS: What did Dr. Kaufman instruct you to do?\n"
            "[10:32 AM] SHARMA: He told me to discard the paper binder page and proceed with patient dosing as scheduled.\n"
        ),
        "freezer_iot_telemetry_log.txt": (
            "HELIOS BIOMEDICAL - CRYOGENIC FREEZER TELEMETRY (UNIT 4)\n"
            "2024-08-14 01:45:00 - Temp: -80.2 C - Status: NORMAL\n"
            "2024-08-14 02:10:00 - POWER FAULT: Mains disconnected - Generator: OFFLINE\n"
            "2024-08-14 04:30:00 - Temp: -22.5 C - CRITICAL WARMING ALARM\n"
            "2024-08-14 06:15:00 - Temp: +4.1 C - PRODUCT VIABILITY COMPROMISED\n"
            "2024-08-14 07:45:00 - Mains power restored - Compressor active\n"
            "2024-08-14 11:00:00 - Temp: -78.9 C - Status: RECOVERED\n"
        ),
        "urgent_tech_email.txt": (
            "From: Priya Sharma <p.sharma@heliospharma.org>\n"
            "To: Arlo Kaufman <a.kaufman@heliospharma.org>\n"
            "Date: August 14, 2024 08:15 AM\n"
            "Subject: CRITICAL: Unit 4 Thawing overnight - Batch HL-902B\n\n"
            "Dr. Kaufman,\n\n"
            "Freezer Unit 4 lost power at 2:10 AM and warmed up to +4.1 C. "
            "The active peptide conjugate in Batch HL-902B degrades rapidly above -20 C. "
            "These vials must be quarantined immediately per GCP protocols.\n\n"
            "Priya\n"
        ),
        "courier_shipping_manifest.txt": (
            "CRYOEXPRESS COURIER SERVICES - WAYBILL #CX-889012\n"
            "Sender: Helios Pharma Clinical Research Site 03\n"
            "Pickup Timestamp: 2024-08-16 14:30:00 (Delayed from morning due to missing dry ice replenishment)\n"
            "Package Temperature on Receipt: -12.0 C (Non-compliant with ultra-cold standard)\n"
            "Driver: Raymond Vance | Signee: Dr. Arlo Kaufman\n"
        ),
        "patient_safety_adverse_event_report.txt": (
            "CLINICAL SAFETY BOARD - EXPEDITED AE SUMMARY\n"
            "Trial: HL-902-ONC | Drug: Velocept-4\n"
            "Date: August 22, 2024\n"
            "Findings: Five patients enrolled in Cohort 3 developed severe injection-site necrosis and acute fever within 12 hours of receiving doses from Batch HL-902B.\n"
            "Analysis: Chemical degradation of hydrolyzed adjuvant occurred due to thermal excursion.\n"
        ),
        "sponsor_audit_findings.txt": (
            "GLOBAL HEALTH REGULATORY AUDIT\n"
            "Helios Pharma Site 03 Inspection Report\n"
            "Lead Inspector: Sarah Jenkins\n\n"
            "Violations Noted:\n"
            "1. Major protocol non-compliance: Failure to report 5.5-hour cryogenic failure on August 14.\n"
            "2. Intentional falsification of trial records by Principal Investigator Dr. Arlo Kaufman.\n"
            "3. Administering degraded clinical trial material to human research subjects.\n"
        ),
        "internal_memo_coverup.txt": (
            "CONFIDENTIAL MEMORANDUM\n"
            "Date: August 15, 2024\n"
            "From: Dr. Arlo Kaufman\n"
            "To: Clinical Supply Operations\n\n"
            "Subject: Batch HL-902B clearance\n"
            "I have personally re-verified the cold chain records. All vials in Freezer 4 remained within acceptable specifications. Proceed with patient administration for Friday morning cohort.\n"
        )
    }

    for fn, content in docs.items():
        with open(case_folder / fn, "w", encoding="utf-8") as f:
            f.write(content)

    gt_data = {
        "case_id": case_id,
        "case_name": case_name,
        "document_count": len(docs),
        "is_held_out": True,
        "true_entities": {
            "persons": ["Arlo Kaufman", "Priya Sharma", "Sarah Jenkins", "Raymond Vance"],
            "organizations": ["Helios Pharma", "CryoExpress", "Clinical Safety Board"],
            "locations": ["Site 03", "Freezer Unit 4", "Cold Storage Vault"],
            "objects": ["Batch HL-902B", "Freezer Unit 4", "Dry Ice", "Waybill CX-889012"]
        },
        "planted_contradictions": [
            {
                "id": "c3_01",
                "entity": "Freezer Unit 4 Temperature",
                "topic": "Continuous minus 80 C vs warming to plus 4 C",
                "doc_a": "interview_dr_kaufman.txt",
                "statement_a": "Yes, absolutely. Freezer Unit 4 maintained strict minus 80 Celsius throughout the August testing window.",
                "doc_b": "freezer_iot_telemetry_log.txt",
                "statement_b": "2024-08-14 06:15:00 - Temp: +4.1 C - PRODUCT VIABILITY COMPROMISED",
                "type": "confirmed_contradiction"
            },
            {
                "id": "c3_02",
                "entity": "Power and Backup Generator",
                "topic": "Generator kicked in seamlessly vs generator failed for nearly six hours",
                "doc_a": "interview_dr_kaufman.txt",
                "statement_a": "The backup diesel generator kicked in seamlessly during the August 14 storm.",
                "doc_b": "interview_lab_tech_priya.txt",
                "statement_b": "The backup generator failed to engage for nearly six hours. The digital display on Freezer Unit 4 rose to plus 4 Celsius between 2:00 AM and 7:45 AM.",
                "type": "confirmed_contradiction"
            },
            {
                "id": "c3_03",
                "entity": "Courier Dispatch Time",
                "topic": "Dispatched at 08:00 AM vs delayed pickup at 14:30 PM",
                "doc_a": "interview_dr_kaufman.txt",
                "statement_a": "They were dispatched via CryoExpress courier on August 16 at 08:00 AM under dry ice.",
                "doc_b": "courier_shipping_manifest.txt",
                "statement_b": "Pickup Timestamp: 2024-08-16 14:30:00 (Delayed from morning due to missing dry ice replenishment)",
                "type": "confirmed_contradiction"
            }
        ],
        "correct_hypothesis": {
            "title": "Deliberate Concealment of Temperature Excursion by Principal Investigator",
            "description": "Dr. Arlo Kaufman knowingly concealed the 5.5-hour cryogenic failure of Freezer Unit 4, ordered the paper logs suppressed, and administered degraded Batch HL-902B to patients to avoid milestone delays.",
            "is_correct": True
        },
        "decoy_hypotheses": [
            {
                "title": "Courier Handling Failure During CryoExpress Transit",
                "description": "The drug degraded exclusively during shipping because driver Raymond Vance failed to replenish dry ice.",
                "is_correct": False
            },
            {
                "title": "Unforeseeable Biological Idiosyncrasy in Cohort 3 Patients",
                "description": "Patient adverse reactions were caused by unexpected genetic hypersensitivity rather than drug degradation.",
                "is_correct": False
            }
        ]
    }

    with open(GROUND_TRUTH_DIR / f"{case_id}_ground_truth.json", "w", encoding="utf-8") as f:
        json.dump(gt_data, f, indent=2)


def create_case_4_apex_robotics():
    case_id = "case_04_apex_robotics"
    case_name = "The Apex Robotics Drone Sabotage"
    case_folder = SAMPLE_DIR / case_id
    case_folder.mkdir(parents=True, exist_ok=True)

    docs = {
        "interview_lead_eng_derek.txt": (
            "INTERVIEW TRANSCRIPT: DEREK COLE\n"
            "Case: Apex Robotics Tactical Drone Crash\n"
            "Interviewer: Agent Vance\n"
            "Interviewee: Derek Cole, Lead Firmware Engineer\n\n"
            "[09:00 AM] VANCE: State your name and role at Apex Robotics.\n"
            "[09:00 AM] COLE: Derek Cole, lead embedded firmware engineer for SkyHarrier-9.\n"
            "[09:01 AM] VANCE: Did you modify the flight controller firmware before yesterday's live demonstration?\n"
            "[09:01 AM] COLE: Absolutely not. I approved the final stable build v2.4 at 18:00 UTC and signed off the checksum.\n"
            "[09:02 AM] VANCE: Where were you between 20:00 and 21:30 UTC last night?\n"
            "[09:02 AM] COLE: I left the facility at 19:45 UTC. I was at dinner at Bistro Laurent in town until 21:30 UTC.\n"
            "[09:03 AM] VANCE: Did you have any communication with Vanguard Aero or outside aerospace recruiters?\n"
            "[09:03 AM] COLE: No, none whatsoever. My exclusive contract is with Apex Robotics.\n"
        ),
        "interview_test_pilot_elena.txt": (
            "INTERVIEW TRANSCRIPT: ELENA ROSTOVA\n"
            "Case: Apex Robotics Tactical Drone Crash\n"
            "Interviewer: Agent Vance\n"
            "Interviewee: Elena Rostova, Chief Flight Test Pilot\n\n"
            "[10:30 AM] VANCE: Elena, what did you observe prior to the 21:00 UTC test flight?\n"
            "[10:30 AM] ROSTOVA: I conducted the visual pre-flight inspection of SkyHarrier-9 at 20:00 UTC. The airframe was pristine.\n"
            "[10:31 AM] VANCE: Did you see anyone approach the drone in Hangar 3?\n"
            "[10:31 AM] ROSTOVA: Yes. Around 20:15 UTC, I walked back toward Assembly Bay to grab my checklist. I saw Derek Cole standing by the drone's avionics bay with a laptop and a flashing blue USB dongle.\n"
            "[10:32 AM] VANCE: What happened during the test flight at 21:05 UTC?\n"
            "[10:32 AM] ROSTOVA: At altitude 400 meters, all four brushless motors cut out simultaneously. It wasn't stall or battery drain; it was an abrupt software cutoff.\n"
        ),
        "interview_qa_tech_liam.txt": (
            "INTERVIEW TRANSCRIPT: LIAM VANCE\n"
            "Case: Apex Robotics Tactical Drone Crash\n"
            "Interviewer: Agent Vance\n"
            "Interviewee: Liam Vance, QA Safety Specialist\n\n"
            "[11:45 AM] VANCE: Liam, describe the firmware validation telemetry.\n"
            "[11:45 AM] LIAM: Standard protocol requires two-engineer authorization before flashing firmware.\n"
            "[11:46 AM] VANCE: Did the automated build pipeline trigger an alert?\n"
            "[11:46 AM] LIAM: Yes. At 20:18 UTC, our QA dashboard flashed a red banner: 'MANUAL FLASH OVERRIDE DETECTED ON AIRFRAME #09'. It bypassed the standard cryptographic verification.\n"
        ),
        "hangar_rfid_access_log.txt": (
            "APEX ROBOTICS - HANGAR 3 SECURITY ACCESS LOG\n"
            "Facility: Test Range Alpha | Assembly Hangar 3\n"
            "Date: 2024-10-25\n\n"
            "[2024-10-25 18:02:11] CARD #1088 [Elena Rostova] - AUTH_GRANTED (Main Bay Entry)\n"
            "[2024-10-25 19:42:00] CARD #4412 [Derek Cole] - AUTH_GRANTED (Exit Front Turnstile)\n"
            "[2024-10-25 20:12:44] CARD #4412 [Derek Cole] - AUTH_GRANTED (Rear Hangar 3 Service Door Entry)\n"
            "[2024-10-25 20:25:19] CARD #4412 [Derek Cole] - AUTH_GRANTED (Rear Hangar 3 Service Door Exit)\n"
            "[2024-10-25 20:55:00] CARD #1088 [Elena Rostova] - AUTH_GRANTED (Flight Deck Entry)\n"
        ),
        "drone_flight_recorder_telemetry.log": (
            "SKYHARRIER-9 BLACK BOX FLASH MEMORY TELEMETRY\n"
            "Hardware UUID: SH9-00891-TX\n\n"
            "[2024-10-25 18:00:00] BOOT: Firmware v2.4 (SHA256: e88a91b... VERIFIED)\n"
            "[2024-10-25 20:17:33] USB_HOST: Device Attached [VID: 0x0781 PID: 0x5581 SanDisk Cruzer]\n"
            "[2024-10-25 20:18:02] FLASH_OVERWRITE: Block 0x000F4000 overwritten with custom binary [PAYLOAD: KILL_OVERRIDE_0x99]\n"
            "[2024-10-25 20:20:11] USB_HOST: Device Ejected\n"
            "[2024-10-25 21:00:15] FLIGHT: Motors Spooled Up - Launch\n"
            "[2024-10-25 21:05:42] EXEC: Trigger condition reached [ALTITUDE > 350m]. KILL_OVERRIDE executed. Motor PWM disabled.\n"
        ),
        "slack_export_engineering.txt": (
            "SLACK CHANNEL: #firmware-core (Internal Apex Workspace)\n"
            "Date: October 25, 2024\n\n"
            "20:05 Derek Cole: Hey team, grabbing dinner. Won't be back until late. Good luck on the 21:00 flight.\n"
            "20:07 Liam Vance: Thanks Derek, enjoy dinner.\n"
            "20:19 BOT-ALARM: Warning - Hardware Debug Port JTAG connected on Airframe 9.\n"
            "20:20 Liam Vance: Did someone leave the debug cable plugged in?\n"
            "20:21 Elena Rostova: Derek was just in the bay a minute ago.\n"
        ),
        "incident_investigation_report.txt": (
            "APEX ROBOTICS - SECURITY FORENSICS REPORT\n"
            "Incident: Catastrophic Loss of SkyHarrier-9 Prototype\n"
            "Investigator: Marcus Stone, Chief Security Officer\n"
            "Date: October 26, 2024\n\n"
            "1. EXECUTIVE SUMMARY: SkyHarrier-9 crashed at 21:05 UTC. Root-cause forensic memory analysis confirms deliberate firmware sabotage.\n"
            "2. ATTRIBUTION: Physical access to Hangar 3 required badge authentication. Card #4412 (Derek Cole) accessed the hangar at 20:12 UTC.\n"
            "3. CODE RECOVERY: The injected firmware payload contained a timer triggered when altitude exceeded 350 meters, cutting power to all electronic speed controllers.\n"
        ),
        "competitor_consulting_email.txt": (
            "CONFIDENTIAL CONSULTING AGREEMENT - VANGUARD AERO\n"
            "From: hiring@vanguard-aero.com\n"
            "To: d.cole.personal@fastmail.com\n"
            "Date: October 24, 2024 18:30 UTC\n"
            "Subject: Retention Fee and Demonstration Milestone\n\n"
            "Derek,\n\n"
            "We have deposited the initial 75,000 USD consulting retainer into your overseas account. "
            "Our offer for the Principal Flight Architect position remains contingent on the upcoming Apex government trial failing to achieve flight certification this Friday.\n"
            "Please confirm once the milestone is concluded.\n\n"
            "Vanguard Aero Talent Acquisition\n"
        ),
    }

    for filename, content in docs.items():
        with open(case_folder / filename, "w", encoding="utf-8") as f:
            f.write(content)

    gt_data = {
        "case_id": case_id,
        "case_name": case_name,
        "document_count": len(docs),
        "is_held_out": True,
        "true_entities": {
            "persons": ["Derek Cole", "Elena Rostova", "Liam Vance", "Marcus Stone"],
            "organizations": ["Apex Robotics", "Vanguard Aero", "Federal Aviation Board"],
            "locations": ["Hangar 3", "Telemetry Bunker", "Test Range Alpha", "Assembly Bay"],
            "objects": ["SkyHarrier-9", "Firmware v2.4", "USB Dongle", "Kill Switch Payload"]
        },
        "planted_contradictions": [
            {
                "id": "c4_01",
                "entity": "Derek Cole Alibi at 20:15",
                "topic": "Dinner in town vs inside Hangar 3",
                "doc_a": "interview_lead_eng_derek.txt",
                "statement_a": "I left the facility at 19:45 UTC. I was at dinner at Bistro Laurent in town until 21:30 UTC.",
                "doc_b": "hangar_rfid_access_log.txt",
                "statement_b": "[2024-10-25 20:12:44] CARD #4412 [Derek Cole] - AUTH_GRANTED (Rear Hangar 3 Service Door Entry)",
                "type": "confirmed_contradiction"
            },
            {
                "id": "c4_02",
                "entity": "Firmware Modification",
                "topic": "No modifications approved v2.4 vs manual flash overwrite",
                "doc_a": "interview_lead_eng_derek.txt",
                "statement_a": "Absolutely not. I approved the final stable build v2.4 at 18:00 UTC and signed off the checksum.",
                "doc_b": "drone_flight_recorder_telemetry.log",
                "statement_b": "[2024-10-25 20:18:02] FLASH_OVERWRITE: Block 0x000F4000 overwritten with custom binary [PAYLOAD: KILL_OVERRIDE_0x99]",
                "type": "confirmed_contradiction"
            },
            {
                "id": "c4_03",
                "entity": "Competitor Affiliation",
                "topic": "No communication with Vanguard Aero vs wire payment agreement",
                "doc_a": "interview_lead_eng_derek.txt",
                "statement_a": "No, none whatsoever. My exclusive contract is with Apex Robotics.",
                "doc_b": "competitor_consulting_email.txt",
                "statement_b": "We have deposited the initial 75,000 USD consulting retainer into your overseas account.",
                "type": "confirmed_contradiction"
            }
        ],
        "correct_hypothesis": {
            "title": "Insider Firmware Sabotage by Derek Cole for Competitor Payoff",
            "description": "Derek Cole returned to Hangar 3 at 20:12 UTC, physically connected a USB dongle to SkyHarrier-9, and flashed a malicious altitude-triggered motor kill routine to ensure the trial failed in exchange for a 75,000 USD retainer from Vanguard Aero.",
            "is_correct": True
        },
        "decoy_hypotheses": [
            {
                "title": "External RF Jamming and Anti-Drone Countermeasure Interference",
                "description": "An adversary operating high-powered RF jamming equipment from outside the facility flooded the 2.4 GHz control frequency, forcing motor shutdown.",
                "is_correct": False
            },
            {
                "title": "Lithium Polymer Battery Thermal Runaway and Low Voltage Cutoff",
                "description": "Defective battery cells in the power distribution board overheated upon reaching 400m altitude, triggering standard BMS safety shutdown.",
                "is_correct": False
            }
        ]
    }

    with open(GROUND_TRUTH_DIR / f"{case_id}_ground_truth.json", "w", encoding="utf-8") as f:
        json.dump(gt_data, f, indent=2)


def main():
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating Case 2 (Blackwood Manor Art Heist)...")
    create_case_2_blackwood()

    print("Generating Case 3 (Helios Pharma Clinical Trial Discrepancy - Held-Out)...")
    create_case_3_helios()

    print("Generating Case 4 (Apex Robotics Drone Sabotage - Additional Held-Out)...")
    create_case_4_apex_robotics()

    print("Successfully created sample cases and ground truth files.")


if __name__ == "__main__":
    main()
