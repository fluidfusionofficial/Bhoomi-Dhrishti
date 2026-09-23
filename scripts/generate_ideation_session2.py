"""
Generate Ideation Session 2 report for Bhoomi Dhrishti
Covers: Additional Ideas + Semantic Interoperability + LRES
"""

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
import os


def set_cell_shading(cell, color_hex):
    from docx.oxml.ns import qn
    from lxml import etree
    shading = etree.SubElement(cell._tc.get_or_add_tcPr(), qn('w:shd'))
    shading.set(qn('w:fill'), color_hex)
    shading.set(qn('w:val'), 'clear')


def add_styled_table(doc, headers, rows, col_widths=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = header
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.bold = True
                run.font.size = Pt(9)
                run.font.color.rgb = RGBColor(255, 255, 255)
        set_cell_shading(cell, '1B4F72')

    for r_idx, row in enumerate(rows):
        for c_idx, val in enumerate(row):
            cell = table.rows[r_idx + 1].cells[c_idx]
            cell.text = str(val)
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(9)
            if r_idx % 2 == 0:
                set_cell_shading(cell, 'EBF5FB')

    if col_widths:
        for i, w in enumerate(col_widths):
            for row in table.rows:
                row.cells[i].width = Cm(w)
    return table


def add_bullet(doc, text, bold_prefix=None):
    p = doc.add_paragraph(style='List Bullet')
    if bold_prefix:
        run = p.add_run(bold_prefix)
        run.bold = True
        p.add_run(text)
    else:
        p.add_run(text)
    return p


def create_report():
    doc = Document()

    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)
    style.paragraph_format.space_after = Pt(6)

    for level in range(1, 4):
        hs = doc.styles[f'Heading {level}']
        hs.font.color.rgb = RGBColor(27, 79, 114)

    # ================================================================
    # TITLE PAGE
    # ================================================================
    for _ in range(6):
        doc.add_paragraph()

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run('BHOOMI DHRISHTI')
    run.bold = True
    run.font.size = Pt(36)
    run.font.color.rgb = RGBColor(27, 79, 114)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run(
        'Ideation Session 2\n'
        'Semantic Interoperability + LRES + Advanced Features'
    )
    run.font.size = Pt(18)
    run.font.color.rgb = RGBColor(86, 101, 115)

    doc.add_paragraph()

    line = doc.add_paragraph()
    line.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = line.add_run('FROM SYNTACTIC TO SEMANTIC: THE MISSING BRIDGE')
    run.bold = True
    run.font.size = Pt(16)

    line2 = doc.add_paragraph()
    line2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = line2.add_run('SIH 2026 | PS-26014 | Ministry of Rural Development / DoLR')
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor(86, 101, 115)

    doc.add_paragraph()
    date_p = doc.add_paragraph()
    date_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = date_p.add_run('September 2026')
    run.font.size = Pt(12)

    doc.add_page_break()

    # ================================================================
    # TABLE OF CONTENTS
    # ================================================================
    doc.add_heading('Table of Contents', level=1)
    toc_items = [
        '1. Context: Where We Left Off',
        '2. Six Additional Architecture Ideas',
        '   2.1 Agentic Land Verification (AI Due Diligence)',
        '   2.2 Real-Time Land Activity Alerts',
        '   2.3 Crowdsourced Ground Truth (Citizens = RL Reward Signal)',
        '   2.4 Multi-Modal Rural Access (Voice + Image + WhatsApp)',
        '   2.5 Satellite Change Detection Pipeline',
        '   2.6 Event Sourcing / Temporal Graph',
        '3. The Healthcare Insight: Syntactic vs Semantic Interoperability',
        '   3.1 The FHIR Parallel',
        '   3.2 Why DILRMP Failed',
        '4. LRES: Land Record Exchange Standard',
        '   4.1 What LRES Contains',
        '   4.2 Land Tenure Concepts',
        '   4.3 Land Classification Ontology',
        '   4.4 Administrative Hierarchy Mapping',
        '   4.5 Transaction Type Ontology',
        '   4.6 Unit & Measurement Ontology',
        '5. The Three-Layer Interoperability Stack',
        '6. How LRES Changes the Product',
        '   6.1 Before vs After LRES',
        '   6.2 LRES + Knowledge Graph',
        '   6.3 LRES + RL Agent',
        '   6.4 LRES + LLM',
        '   6.5 LRES + Trust Engine',
        '   6.6 LRES + Natural Language Query',
        '7. The Complete System Flow',
        '8. Pitch Lines & SIH Positioning',
    ]
    for item in toc_items:
        p = doc.add_paragraph(item)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.space_before = Pt(0)
        for run in p.runs:
            run.font.size = Pt(10)

    doc.add_page_break()

    # ================================================================
    # 1. CONTEXT
    # ================================================================
    doc.add_heading('1. Context: Where We Left Off', level=1)

    doc.add_paragraph(
        'In Session 1, we established the core architecture for Bhoomi Dhrishti:'
    )

    add_bullet(doc, 'MCP-like federated architecture with RL Host connecting to 28 state + 8 UT Servers', 'Core Idea: ')
    add_bullet(doc, 'No centralized database — data stays with states, platform owns identity (BDPR) and standards', 'Data Philosophy: ')
    add_bullet(doc, 'LLM (schema matching) + RL (optimization, routing, trust) + Rules Engine (deterministic validation)', 'Three-Tier Intelligence: ')
    add_bullet(doc, 'EU sovereign data space concept applied to India — states are sovereign data providers', 'Land Data Space: ')
    add_bullet(doc, 'Neo4j/Neptune graph for parcels, owners, departments, transactions', 'Knowledge Graph: ')
    add_bullet(doc, 'Virtual representation of every parcel with time-travel capability', 'Parcel Digital Twin: ')
    add_bullet(doc, 'Citizens ask questions in natural language, LLM decomposes into multi-department queries', 'GraphRAG Queries: ')
    add_bullet(doc, 'ML models train on state data without data leaving state jurisdiction', 'Federated Learning: ')
    add_bullet(doc, 'RL-optimized per-state adapters with retry strategies and graceful degradation', 'Self-Healing Connectors: ')

    doc.add_paragraph(
        'This session extends the architecture with six new ideas and, most importantly, '
        'introduces the concept of semantic interoperability through LRES — the missing piece '
        'that transforms Bhoomi Dhrishti from a data connector into a true understanding engine.'
    )

    doc.add_page_break()

    # ================================================================
    # 2. SIX ADDITIONAL IDEAS
    # ================================================================
    doc.add_heading('2. Six Additional Architecture Ideas', level=1)

    # 2.1
    doc.add_heading('2.1 Agentic Land Verification (AI Due Diligence)', level=2)

    doc.add_paragraph(
        'Instead of a citizen manually checking 5 departments, deploy an autonomous AI agent '
        'that performs complete due diligence on any parcel. Think of it as a CIBIL score for land — '
        'one query, complete picture.'
    )

    doc.add_paragraph(
        'Example interaction:'
    )

    p = doc.add_paragraph()
    run = p.add_run(
        'Citizen: "Is it safe to buy parcel BD-TN-0042781?"\n\n'
        'Agent autonomously:\n'
        '  → Checks ownership chain (Registration service)\n'
        '  → Verifies no encumbrances/mortgages (Revenue)\n'
        '  → Confirms no court cases pending (e-Courts integration)\n'
        '  → Validates boundaries match survey (Geospatial)\n'
        '  → Checks zoning compliance (Planning)\n'
        '  → Scans for FRA/forest overlap (Forest dept)\n'
        '  → Runs Trust Engine scoring\n\n'
        '  Returns: "MEDIUM RISK — survey area differs by 12% from revenue record. '
        'No other issues found."'
    )
    run.font.size = Pt(10)
    run.font.name = 'Consolas'

    doc.add_paragraph(
        'Revenue model: Banks would pay for this service for loan verification against land collateral. '
        'This creates a sustainable business model for the platform.'
    )

    # 2.2
    doc.add_heading('2.2 Real-Time Land Activity Alerts', level=2)

    doc.add_paragraph(
        'When ANY activity happens on your land in ANY department — you get notified instantly. '
        'Like UPI notifications, but for land.'
    )

    add_styled_table(doc,
        ['Event', 'Alert to Owner'],
        [
            ['Registration attempt on your parcel', '"Registration attempt detected on BD-TN-0042781"'],
            ['Revenue mutation initiated', '"Mutation request filed — verify within 15 days"'],
            ['Survey boundary updated', '"Survey department updated boundaries"'],
            ['Court case filed involving parcel', '"Legal proceeding detected"'],
            ['Zoning change affects area', '"Zoning reclassification in your village"'],
            ['Trust score drops', '"Cross-department conflict detected on your land"'],
        ],
        col_widths=[6, 10]
    )

    doc.add_paragraph()
    doc.add_paragraph(
        'This prevents fraud proactively. The Karnataka Bhoomi breach (19 acres illegally transferred in 2024) '
        'would have been caught instantly if the actual owner received an alert. No state system does this today '
        'because alerts require cross-department visibility — exactly what Bhoomi Dhrishti provides.'
    )

    # 2.3
    doc.add_heading('2.3 Crowdsourced Ground Truth (Citizens = RL Reward Signal)', level=2)

    doc.add_paragraph(
        'This elegantly solves the RL reward signal problem. Citizens can report discrepancies between '
        'digital records and ground reality:'
    )

    add_bullet(doc, '"My land shows 2 acres in records but I actually own 1.5 acres"')
    add_bullet(doc, '"This parcel is shown as agricultural but there\'s a building on it"')
    add_bullet(doc, '"The boundary shown on the map doesn\'t match the actual fence line"')

    doc.add_paragraph(
        'These reports become the reward signal for the RL agent. Over time, the system learns which '
        'types of record mismatches are real discrepancies vs administrative lag. This is like '
        'Google Maps corrections but for land records.'
    )

    doc.add_paragraph('The feedback loop:')
    p = doc.add_paragraph()
    run = p.add_run(
        'State Data → Knowledge Graph → Trust Score → Citizen Report\n'
        '     ↑                                           |\n'
        '     └───── RL agent learns from reports ─────────┘'
    )
    run.font.size = Pt(10)
    run.font.name = 'Consolas'

    # 2.4
    doc.add_heading('2.4 Multi-Modal Rural Access (Voice + Image + WhatsApp)', level=2)

    doc.add_paragraph(
        '85% of Indian landowners are small/marginal farmers. They won\'t use a web app. '
        'The system needs multiple access channels:'
    )

    add_styled_table(doc,
        ['Channel', 'How It Works', 'Target User'],
        [
            ['Voice (Regional Languages)',
             'Speech-to-text → NL query engine → Text-to-speech response. '
             'Supports Tamil, Hindi, Telugu, Kannada, Bengali, etc.',
             'Illiterate/semi-literate farmers'],
            ['Image/Photo Input',
             'Farmer photographs physical patta document → OCR extracts details '
             '→ System matches to digital records',
             'Anyone with a paper document'],
            ['WhatsApp Bot',
             'Like Telangana\'s "Medha" but works across ALL departments, not just DHARANI. '
             'Most popular messaging app in rural India.',
             'Smartphone users (majority)'],
            ['USSD (Feature Phones)',
             '*123*BDPR# → basic parcel status menu. Works without internet.',
             'Feature phone users in low-connectivity areas'],
            ['IVR (Phone Call)',
             'Call a number, speak your BDPR/survey number, hear status via automated voice.',
             'Anyone with any phone'],
        ],
        col_widths=[4, 8, 4]
    )

    doc.add_paragraph()
    doc.add_paragraph(
        'This directly addresses PS-26014\'s requirement for citizen-facing features AND gives '
        'massive points for inclusivity at SIH judging.'
    )

    # 2.5
    doc.add_heading('2.5 Satellite Change Detection Pipeline', level=2)

    doc.add_paragraph(
        'Connect ISRO Bhuvan / Google Earth Engine satellite imagery to the Knowledge Graph '
        'for automated encroachment and land use change detection:'
    )

    p = doc.add_paragraph()
    run = p.add_run(
        'Satellite Image (T1) vs Satellite Image (T2)\n'
        '         ↓\n'
        '  Change Detection ML Model\n'
        '         ↓\n'
        '  "New construction detected on parcel BD-TN-0042781"\n'
        '         ↓\n'
        '  Cross-check: Is this parcel zoned for construction?\n'
        '         ↓\n'
        '  NO → Flag as potential encroachment\n'
        '         ↓\n'
        '  Alert sent to officer + trust score updated'
    )
    run.font.size = Pt(10)
    run.font.name = 'Consolas'

    doc.add_paragraph()
    doc.add_paragraph(
        'This feeds the Trust Engine with physical ground truth — not just what departments say, '
        'but what satellites can actually see. Uses Google Open Buildings (1.8B buildings globally) as baseline. '
        'The RL agent learns which change patterns matter: new road = government project (ignore), '
        'new building on agricultural land = encroachment (flag).'
    )

    # 2.6
    doc.add_heading('2.6 Event Sourcing / Temporal Graph (Complete History)', level=2)

    doc.add_paragraph(
        'Instead of storing "current state of parcel", store every event that ever happened. '
        'This makes the Knowledge Graph temporal — edges have timestamps, so you can traverse '
        'the graph at any point in history.'
    )

    doc.add_paragraph('Example event chain for a single parcel:')
    add_styled_table(doc,
        ['Year', 'Event', 'Source Department'],
        [
            ['1985', 'Survey established parcel, area = 2.0 acres', 'Survey & Settlement'],
            ['1992', 'Father died, mutation to son in revenue record', 'Revenue'],
            ['2005', 'Registration of sale to Buyer A', 'Registration'],
            ['2005', 'Mutation STILL PENDING (20 years!)', 'Revenue'],
            ['2020', 'Buyer A sells to Buyer B (registered)', 'Registration'],
            ['2020', 'Survey resurvey, area = 1.8 acres (discrepancy!)', 'Survey'],
            ['2025', 'SVAMITVA drone survey, area = 1.82 acres', 'SVAMITVA'],
        ],
        col_widths=[2, 9, 5]
    )

    doc.add_paragraph()
    doc.add_paragraph('Benefits:')
    add_bullet(doc, 'Show me this parcel\'s state on any date', 'Time travel: ')
    add_bullet(doc, 'Complete chain of events admissible in court', 'Dispute evidence: ')
    add_bullet(doc, 'ML can spot suspicious event sequences (rapid flipping, backdated registrations)', 'Pattern detection: ')
    add_bullet(doc, 'Event log = audit trail (aligns with existing hash-chain audit service)', 'Immutable: ')

    doc.add_paragraph()
    doc.add_paragraph('How all six ideas connect:')
    p = doc.add_paragraph()
    run = p.add_run(
        'SATELLITE IMAGERY ──→ CHANGE DETECTION ──→ TRUST ENGINE\n'
        '                                              ↑\n'
        'CITIZEN REPORTS ───→ GROUND TRUTH ────→ RL REWARD SIGNAL\n'
        '                                              ↑\n'
        'STATE SYSTEMS ─────→ KNOWLEDGE GRAPH ──→ CONFLICT DETECTION\n'
        '                          ↓\n'
        '                    PARCEL DIGITAL TWIN\n'
        '                          ↓\n'
        '         ┌────────────────┼────────────────┐\n'
        '         ↓                ↓                ↓\n'
        '   NL QUERY (web)   WHATSAPP BOT    VOICE (IVR)\n'
        '         ↓                ↓                ↓\n'
        '      CITIZEN          FARMER         FEATURE PHONE\n'
        '         ↓                ↓                ↓\n'
        '   LAND ALERTS     LAND ALERTS      LAND ALERTS'
    )
    run.font.size = Pt(9)
    run.font.name = 'Consolas'

    doc.add_page_break()

    # ================================================================
    # 3. HEALTHCARE INSIGHT
    # ================================================================
    doc.add_heading('3. The Healthcare Insight: Syntactic vs Semantic Interoperability', level=1)

    doc.add_paragraph(
        'A critical insight emerged from studying healthcare interoperability (specifically the HL7/FHIR journey) '
        'that directly applies to land records. Healthcare distinguishes between two levels of interoperability:'
    )

    doc.add_heading('Syntactic Interoperability', level=3)
    doc.add_paragraph(
        'Focuses on the structure of data exchange. Ensures different systems can successfully send and receive '
        'messages in a compatible format (e.g., moving data between HL7 V2 and FHIR). This level addresses '
        'the FORMAT of the data, but not its actual meaning.'
    )

    doc.add_heading('Semantic Interoperability', level=3)
    doc.add_paragraph(
        'Goes deeper to ensure that transmitted data is consistently defined and understood by the receiving system '
        'WITHOUT requiring human interpretation. The challenge: different systems may model the same information '
        'in unique ways, making it difficult for computers to recognize they are describing the exact same thing.'
    )

    doc.add_heading('3.1 The FHIR Parallel', level=2)

    add_styled_table(doc,
        ['Healthcare', 'Land Records (Bhoomi Dhrishti)'],
        [
            ['HL7 V2 → FHIR migration', 'State-specific schemas → canonical BDPR schema'],
            ['Every hospital has its own EMR format', 'Every state has its own land record format'],
            ['"Blood pressure" recorded differently across systems',
             '"Khata number" (KA) = "Patta number" (TN) = "Account number" (TS)'],
            ['FHIR profiles = machine-readable standard', 'LRES profiles = machine-readable land ontology'],
            ['Community-driven profile adoption', 'State-by-state onboarding with LLM assistance'],
            ['Trillion-dollar healthcare IT ecosystem', 'India\'s $1.4T real estate market needs this'],
        ],
        col_widths=[8, 8]
    )

    doc.add_paragraph()

    doc.add_heading('3.2 Why DILRMP Failed', level=2)

    doc.add_paragraph(
        'DILRMP (Digital India Land Records Modernization Programme) tried to standardize land records. '
        'It achieved syntactic interoperability — common formats, NIC-built APIs. But it never tackled '
        'semantic interoperability, which is why 28 states still cannot meaningfully exchange land data.'
    )

    doc.add_paragraph(
        'India solved the FORMAT problem years ago. Nobody solved the MEANING problem. That\'s the gap '
        'Bhoomi Dhrishti fills.'
    )

    doc.add_page_break()

    # ================================================================
    # 4. LRES
    # ================================================================
    doc.add_heading('4. LRES: Land Record Exchange Standard', level=1)

    doc.add_paragraph(
        'Inspired by FHIR, LRES (Land Record Exchange Standard) is a machine-readable ontology for land concepts. '
        'It is the Rosetta Stone for India\'s land data — the semantic bridge that turns 28 isolated databases '
        'into one coherent knowledge system without centralizing a single byte.'
    )

    doc.add_heading('4.1 What LRES Contains', level=2)

    doc.add_paragraph(
        'LRES is a structured dictionary with five sections, each addressing a different dimension '
        'of the semantic interoperability problem:'
    )

    add_bullet(doc, 'Maps patta/khata/RoR/jamabandi to canonical ownership concepts', 'Land Tenure Concepts — ')
    add_bullet(doc, 'Maps punjai/dry/sona/barani to canonical land use types', 'Land Classification Ontology — ')
    add_bullet(doc, 'Maps taluk/tehsil/mandal/block to canonical administrative levels', 'Administrative Hierarchy — ')
    add_bullet(doc, 'Breaks "mutation" into canonical sub-types (transfer, succession, partition, etc.)', 'Transaction Type Ontology — ')
    add_bullet(doc, 'Handles acres, guntha, biswa, bigha, kanal with jurisdiction-aware conversion', 'Unit & Measurement Ontology — ')

    # 4.2
    doc.add_heading('4.2 Land Tenure Concepts', level=2)

    doc.add_paragraph(
        'India has three historical land tenure families, and every state\'s terminology traces back to one of them. '
        'LRES maps all state-specific terms to canonical concepts:'
    )

    add_styled_table(doc,
        ['Canonical Concept', 'Ryotwari States\n(TN, KA, AP, TS)', 'Zamindari States\n(WB, Bihar, Odisha)',
         'Mahalwari States\n(UP, MP, Punjab)'],
        [
            ['Individual freehold right', 'Patta / A-Khata', 'Record of Rights (RoR)', 'Jamabandi'],
            ['The land record document', 'Chitta / Adangal', 'Khatian / Porcha', 'Khatauni / Khasra'],
            ['Ownership transfer process', 'Mutation (Patta Transfer)', 'Mutation (Khatian update)', 'Mutation (Jamabandi entry)'],
            ['Land survey number', 'Survey No / Subdivision', 'Plot No / Dag No', 'Khasra No / Gata No'],
            ['Revenue village boundary', 'Firka → Village', 'Mouza → JL No', 'Patwari circle → Village'],
        ],
        col_widths=[4, 4, 4, 4]
    )

    doc.add_paragraph()
    doc.add_paragraph(
        'Same legal reality, completely different words. LRES creates the Rosetta Stone so that '
        'a system can understand that "Patta" in TN, "A-Khata" in Karnataka, and "RoR" in West Bengal '
        'all represent the same fundamental concept: an individual\'s recognized right over land.'
    )

    # 4.3
    doc.add_heading('4.3 Land Classification Ontology', level=2)

    doc.add_paragraph(
        '"Agricultural land" is not one thing — it has state-specific subcategories that map to different '
        'canonical concepts:'
    )

    add_styled_table(doc,
        ['Canonical', 'Tamil Nadu', 'Karnataka', 'West Bengal', 'Punjab'],
        [
            ['Irrigated cropland', 'Nanjai', 'Wet / Tari', 'Sali', 'Nehri'],
            ['Rain-fed cropland', 'Punjai', 'Dry / Khushki', 'Sona', 'Barani'],
            ['Garden/plantation', 'Manavari', 'Garden / Tota', 'Bagani', 'Bagh'],
            ['Wasteland', 'Poramboke (govt)', 'Gomala / Kharab', 'Khas', 'Banjar'],
        ],
        col_widths=[3.5, 3, 3, 3, 3]
    )

    doc.add_paragraph()
    doc.add_paragraph(
        'A system without LRES sees "Punjai" from TN and "Khushki" from Karnataka and has no idea '
        'they\'re the same. With LRES, the system knows both map to canonical code LU_AGR_RAINFED '
        'and can compare them meaningfully.'
    )

    # 4.4
    doc.add_heading('4.4 Administrative Hierarchy Mapping', level=2)

    doc.add_paragraph(
        'Every state structures its administrative geography differently. Some have extra levels, '
        'some skip levels entirely:'
    )

    p = doc.add_paragraph()
    run = p.add_run(
        'CANONICAL:        State → District → Sub-District → Village → Parcel\n\n'
        'Tamil Nadu:       State → District → Taluk      → Village → Survey No\n'
        'Karnataka:        State → District → Taluk      → Hobli   → Village → Sy No\n'
        'West Bengal:      State → District → Block      → Mouza   → Plot No (Dag)\n'
        'Telangana:        State → District → Mandal     → Village → Survey No\n'
        'Punjab:           State → District → Tehsil     → Village → Khasra No\n'
        'NE States:        State → District → Circle     → Village → (often no survey)'
    )
    run.font.size = Pt(10)
    run.font.name = 'Consolas'

    doc.add_paragraph()
    doc.add_paragraph(
        'Notice Karnataka has an extra level (Hobli) between Taluk and Village. NE states often have '
        'no formal survey numbers at all. LRES handles this by defining a canonical hierarchy and mapping '
        'each state\'s structure onto it — including where levels are missing or extra.'
    )

    # 4.5
    doc.add_heading('4.5 Transaction Type Ontology', level=2)

    doc.add_paragraph(
        'This is where "same word, different meaning" becomes dangerous. "Mutation" sounds simple, but:'
    )

    add_bullet(doc, 'means ONLY ownership transfer recording in revenue records', 'In TN/KA: ')
    add_bullet(doc, 'means ANY change to the RoR — transfer, partition, inheritance, correction, all of it', 'In WB: ')
    add_bullet(doc, 'includes agricultural land conversion decisions', 'In Rajasthan: ')

    doc.add_paragraph(
        'If the system treats all "mutations" as the same transaction type, cross-state analytics become '
        'meaningless. LRES breaks "mutation" into canonical sub-types:'
    )

    add_styled_table(doc,
        ['Canonical Code', 'Definition', 'TN/KA Maps To', 'WB Maps To'],
        [
            ['MUTATION_TRANSFER', 'Ownership change (sale/gift)', 'Yes (only type)', 'One of many types'],
            ['MUTATION_SUCCESSION', 'Inheritance/death transfer', 'Separate process', 'Included in "mutation"'],
            ['MUTATION_PARTITION', 'Single parcel → multiple parcels', 'Separate process', 'Included in "mutation"'],
            ['MUTATION_CORRECTION', 'Error correction in records', 'Separate process', 'Included in "mutation"'],
            ['MUTATION_CONVERSION', 'Land use change (agri → non-agri)', 'Separate (NA order)', 'Separate process'],
        ],
        col_widths=[4, 4, 4, 4]
    )

    doc.add_paragraph()

    # 4.6
    doc.add_heading('4.6 Unit & Measurement Ontology', level=2)

    doc.add_paragraph(
        'Area measurements in India are a mess. Some units don\'t even have fixed values — '
        'they vary by district:'
    )

    add_styled_table(doc,
        ['Unit', 'Where Used', 'Hectare Equivalent', 'Notes'],
        [
            ['Acre', 'Most states', '0.4047 ha', 'Standard but not metric'],
            ['Cent', 'Kerala, TN (colloquial)', '0.00405 ha', '1/100 of an acre'],
            ['Guntha', 'Karnataka, Maharashtra', '0.01012 ha', '33 feet x 33 feet'],
            ['Biswa', 'UP, Rajasthan', 'VARIES by district', 'No single standard!'],
            ['Kanal', 'J&K, HP, Punjab', '0.0506 ha', 'Used in hill states'],
            ['Bigha', 'Bihar, WB, Assam', 'VARIES by state', 'Bihar Bigha ≠ WB Bigha'],
            ['Katha/Kattha', 'Bihar, Jharkhand', 'VARIES by district', 'Sub-unit of Bigha'],
        ],
        col_widths=[3, 4, 3.5, 5.5]
    )

    doc.add_paragraph()
    doc.add_paragraph(
        'Biswa and Bigha don\'t even have fixed values. LRES must encode not just conversion factors '
        'but the jurisdiction where each factor applies. A "Bigha" in Bihar = 0.2529 ha, but a "Bigha" '
        'in West Bengal = 0.1338 ha — nearly half the size. Without jurisdiction-aware conversion, '
        'area comparisons across states are meaningless.'
    )

    doc.add_page_break()

    # ================================================================
    # 5. THREE-LAYER STACK
    # ================================================================
    doc.add_heading('5. The Three-Layer Interoperability Stack', level=1)

    doc.add_paragraph(
        'LRES gives Bhoomi Dhrishti a clean three-layer interoperability architecture. Each layer '
        'maps to an existing component:'
    )

    p = doc.add_paragraph()
    run = p.add_run(
        'Layer 3: SEMANTIC (meaning)\n'
        '  "Land FHIR" ontology — LRES profiles\n'
        '  LLM assists when new state joins (suggests mappings)\n'
        '  Human expert validates and locks mappings\n'
        '  \n'
        'Layer 2: SYNTACTIC (format)\n'
        '  Current mapping.yaml system\n'
        '  JSON/XML/CSV → canonical Pydantic schema\n'
        '  Unit conversions, date format normalization\n'
        '  \n'
        'Layer 1: TRANSPORT (connectivity)\n'
        '  MCP-like adapter per state\n'
        '  API / SFTP / scraper / manual upload\n'
        '  RL agent optimizes routing and retry'
    )
    run.font.size = Pt(10)
    run.font.name = 'Consolas'

    doc.add_paragraph()

    add_styled_table(doc,
        ['Layer', 'Problem Solved', 'Component', 'Intelligence'],
        [
            ['Layer 1: Transport', 'Can we REACH the data?', 'MCP + RL Connectors', 'RL Agent (routing, retry, optimization)'],
            ['Layer 2: Syntactic', 'Can we READ the data?', 'Interoperability Service + mapping.yaml', 'Rules Engine (deterministic conversion)'],
            ['Layer 3: Semantic', 'Can we UNDERSTAND the data?', 'LRES Ontology + Knowledge Graph', 'LLM (semantic matching) + Human validation'],
        ],
        col_widths=[3, 3.5, 5, 5]
    )

    doc.add_paragraph()
    doc.add_paragraph(
        'This is the key framing for SIH: Layer 1 and Layer 2 are what everyone else will build. '
        'Layer 3 is what only Bhoomi Dhrishti has. It\'s the difference between connecting systems '
        'and making systems understand each other.'
    )

    doc.add_page_break()

    # ================================================================
    # 6. HOW LRES CHANGES THE PRODUCT
    # ================================================================
    doc.add_heading('6. How LRES Changes the Product', level=1)

    doc.add_heading('6.1 Before vs After LRES', level=2)

    doc.add_heading('Before LRES (what everyone else will build)', level=3)

    p = doc.add_paragraph()
    run = p.add_run(
        'TN says "Punjai, 2.5 acres"\n'
        'KA says "Dry, 1.01 hectares"\n\n'
        'System: "These are different. Possible conflict."\n'
        'Officer: "No, those are the same thing, you just don\'t\n'
        '          understand Tamil Nadu terminology."'
    )
    run.font.size = Pt(10)
    run.font.name = 'Consolas'

    doc.add_paragraph()
    doc.add_paragraph('False conflicts everywhere. Officers lose trust. System becomes a burden.')

    doc.add_heading('After LRES (what Bhoomi Dhrishti does)', level=3)

    p = doc.add_paragraph()
    run = p.add_run(
        'TN says "Punjai, 2.5 acres"\n'
        'LRES: Punjai → LU_AGR_RAINFED, 2.5 acres → 1.012 ha\n\n'
        'KA says "Dry, 1.01 hectares"\n'
        'LRES: Dry → LU_AGR_RAINFED, 1.01 ha → 1.01 ha\n\n'
        'System: "Same land use. Area difference: 0.002 ha\n'
        '         (within survey tolerance). Records CONSISTENT."'
    )
    run.font.size = Pt(10)
    run.font.name = 'Consolas'

    doc.add_paragraph()
    doc.add_paragraph('Real conflicts get flagged. False conflicts disappear. Officers trust the system.')

    # 6.2 - 6.6
    doc.add_heading('6.2 LRES + Knowledge Graph', level=2)
    doc.add_paragraph(
        'Graph edges become semantically meaningful. Instead of connecting raw state-specific strings, '
        'you connect canonical concepts. A query like "find all rainfed agricultural parcels across India" '
        'actually works — it matches Punjai in TN, Dry in KA, Sona in WB, Barani in Punjab. '
        'Without LRES, this query is impossible because the graph doesn\'t know these terms are equivalent.'
    )

    doc.add_heading('6.3 LRES + RL Agent', level=2)
    doc.add_paragraph(
        'The RL agent uses LRES confidence scores as a signal. If a mapping has confidence: 0.95 '
        '(like WB\'s "Raiyat" which usually but not always means freehold), the RL agent knows '
        'to flag those cases for human review rather than auto-accepting. High confidence mappings '
        'flow through automatically; low confidence ones get routed to domain experts. Over time, '
        'the RL agent learns which edge cases actually cause problems and adjusts routing accordingly.'
    )

    doc.add_heading('6.4 LRES + LLM', level=2)
    doc.add_paragraph(
        'When a new state onboards, the LLM reads their schema and proposes LRES mappings by understanding '
        'context. For example: "This field is called \'dag_no\' and appears alongside area measurements — '
        'it\'s likely the survey number equivalent." A domain expert approves or corrects, and the ontology grows. '
        'This is how FHIR grew too — community-driven profiles, not top-down mandates. The LLM accelerates '
        'what would otherwise be months of manual mapping work to days.'
    )

    doc.add_heading('6.5 LRES + Trust Engine', level=2)
    doc.add_paragraph(
        'The Trust Engine stops comparing raw values and starts comparing canonical concepts. This eliminates '
        'an entire class of false positives. When TN says "Punjai" and KA says "Dry", the Trust Engine knows '
        'these are equivalent — no false conflict flagged. But when TN says "Nanjai" (irrigated) and the '
        'survey says "Dry", the Trust Engine correctly identifies a real discrepancy. LRES makes the trust '
        'score actually reliable.'
    )

    doc.add_heading('6.6 LRES + Natural Language Query', level=2)
    doc.add_paragraph(
        'A citizen asks "do I own farmland?" The system knows to search for Patta in TN, RoR in WB, '
        'Jamabandi in Punjab — all mapped to the same canonical ownership concept. One question, '
        '28 states, one coherent answer. Without LRES, the NL query engine would need hardcoded '
        'per-state logic. With LRES, it\'s a single ontology lookup.'
    )

    doc.add_page_break()

    # ================================================================
    # 7. COMPLETE SYSTEM FLOW
    # ================================================================
    doc.add_heading('7. The Complete System Flow', level=1)

    doc.add_paragraph(
        'Putting together ALL ideas from both brainstorming sessions, here is how the complete '
        'Bhoomi Dhrishti system works end-to-end:'
    )

    doc.add_heading('Four Pillars of Bhoomi Dhrishti', level=2)

    add_styled_table(doc,
        ['Pillar', 'What It Does', 'Components'],
        [
            ['BDPR (Identity)',
             'Every parcel gets a unique ID. Answers: "Which parcel?"',
             'Parcel Identity Service + ULPIN alignment'],
            ['LRES (Understanding)',
             'Semantic ontology. Answers: "What does the data mean?"',
             'Land tenure + classification + hierarchy + transaction + unit ontologies'],
            ['Three-Tier Intelligence',
             'LLM + RL + Rules. Answers: "How do we process the data?"',
             'Schema matching (LLM), routing/optimization (RL), validation (Rules)'],
            ['Knowledge Graph + Digital Twin',
             'Unified data layer. Answers: "What is the state of reality?"',
             'Temporal graph, event sourcing, satellite verification, citizen ground truth'],
        ],
        col_widths=[3, 5, 8]
    )

    doc.add_paragraph()

    doc.add_heading('End-to-End Flow: Citizen Asks About a Parcel', level=2)

    steps = [
        ('1. Access', 'Citizen asks via web, WhatsApp, voice, USSD, or IVR'),
        ('2. NL Understanding', 'LLM decomposes question into structured queries'),
        ('3. Routing', 'RL agent determines which state systems to query and optimal route'),
        ('4. Transport', 'MCP adapters connect to state systems (API/SFTP/scraper)'),
        ('5. Syntactic Mapping', 'Interoperability Service converts format (mapping.yaml)'),
        ('6. Semantic Mapping', 'LRES translates meaning (punjai → LU_AGR_RAINFED)'),
        ('7. Graph Integration', 'Data flows into Knowledge Graph with temporal edges'),
        ('8. Trust Scoring', 'Trust Engine compares across departments using canonical concepts'),
        ('9. Response', 'Citizen receives answer with provenance and trust score'),
        ('10. Alert', 'If anything changes later, citizen gets real-time notification'),
        ('11. Feedback', 'Citizen can report discrepancies → feeds RL reward signal'),
    ]

    for step_label, step_desc in steps:
        add_bullet(doc, step_desc, step_label + ': ')

    doc.add_heading('End-to-End Flow: New State Onboarding', level=2)

    steps2 = [
        ('1. Discovery', 'LLM reads new state\'s schema/API/documents'),
        ('2. Proposal', 'LLM proposes LRES mappings with confidence scores'),
        ('3. Review', 'Domain expert validates, corrects, and locks mappings'),
        ('4. Connector', 'RL agent configures MCP adapter for the state\'s transport layer'),
        ('5. Testing', 'Self-healing connector tests queries and learns retry strategies'),
        ('6. Trust Baseline', 'Trust Engine establishes baseline scores for the state\'s data quality'),
        ('7. Go Live', 'State data flows into Knowledge Graph, queryable by citizens'),
    ]

    for step_label, step_desc in steps2:
        add_bullet(doc, step_desc, step_label + ': ')

    doc.add_page_break()

    # ================================================================
    # 8. PITCH LINES
    # ================================================================
    doc.add_heading('8. Pitch Lines & SIH Positioning', level=1)

    doc.add_heading('The Core Pitch', level=2)

    p = doc.add_paragraph()
    run = p.add_run(
        '"India digitized its land records department by department, state by state. '
        'Nobody built the bridge between them. That bridge is Bhoomi Dhrishti."'
    )
    run.italic = True
    run.font.size = Pt(12)

    doc.add_heading('The Semantic Pitch', level=2)

    p = doc.add_paragraph()
    run = p.add_run(
        '"We don\'t just translate formats — we translate meaning. When Karnataka says '
        '\'A Khata\' and Tamil Nadu says \'Ryotwari Patta\', our system knows these represent '
        'the same legal concept. This is the difference between syntactic and semantic interoperability, '
        'and it\'s the reason existing systems like DILRMP haven\'t achieved true cross-state data exchange."'
    )
    run.italic = True
    run.font.size = Pt(12)

    doc.add_heading('The FHIR Pitch', level=2)

    p = doc.add_paragraph()
    run = p.add_run(
        '"FHIR did this for healthcare — turned incompatible hospital systems into a trillion-dollar '
        'interoperable ecosystem. LRES does the same for land records. India\'s $1.4 trillion real estate '
        'market deserves the same semantic infrastructure that healthcare got."'
    )
    run.italic = True
    run.font.size = Pt(12)

    doc.add_heading('The DPI Pitch', level=2)

    p = doc.add_paragraph()
    run = p.add_run(
        '"BDPR is the Aadhaar for land parcels. LRES is the UPI for land data. '
        'Purpose-bound access tokens are DEPA consent for property information. '
        'Bhoomi Dhrishti is India Stack for land governance."'
    )
    run.italic = True
    run.font.size = Pt(12)

    doc.add_heading('The Completeness Pitch (Full Feature List)', level=2)

    features = [
        'Federated architecture — no centralized database, data stays with states',
        'BDPR universal parcel identity (like Aadhaar for land)',
        'LRES semantic ontology (like FHIR for land records)',
        'Three-tier intelligence: LLM + RL + Rules Engine',
        'Land Knowledge Graph with temporal event sourcing',
        'Parcel Digital Twin with time-travel capability',
        'Trust Engine with cross-department conflict detection',
        'Self-healing adaptive connectors (MCP + RL)',
        'Agentic land verification (CIBIL score for land)',
        'Real-time land activity alerts (UPI notifications for land)',
        'Satellite change detection pipeline (ISRO Bhuvan + Google Earth Engine)',
        'Crowdsourced ground truth (Google Maps corrections for land)',
        'Multi-modal access: Web + WhatsApp + Voice + USSD + IVR',
        'Federated learning (privacy-preserving ML across states)',
        'Natural language queries via GraphRAG',
        'Hash-chain audit trail (immutable, append-only)',
        'Purpose-bound access tokens (DEPA consent model)',
        'Bronze/Silver/Gold conformance tiers for state onboarding',
    ]

    for feat in features:
        add_bullet(doc, feat)

    doc.add_paragraph()

    doc.add_heading('Key Differentiators vs Competition', level=2)

    add_styled_table(doc,
        ['What Others Will Build', 'What Bhoomi Dhrishti Has'],
        [
            ['Centralized database', 'Federated — data stays with states'],
            ['Static API connectors', 'Self-healing RL-optimized adaptive connectors'],
            ['Format conversion (syntactic)', 'Meaning translation (semantic via LRES)'],
            ['Dashboard on top of data', 'Knowledge Graph + Digital Twin'],
            ['Manual state onboarding', 'LLM-assisted onboarding in days, not months'],
            ['Web-only interface', 'WhatsApp + Voice + USSD + IVR for rural access'],
            ['Passive data display', 'Proactive alerts + agentic verification'],
            ['Single data snapshot', 'Temporal graph with full event history'],
        ],
        col_widths=[8, 8]
    )

    # Save
    output_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(output_dir, 'Bhoomi_Dhrishti_Ideation_Session2.docx')
    doc.save(output_path)
    print(f'Saved: {output_path}')
    print(f'Size: {os.path.getsize(output_path) / 1024:.1f} KB')


if __name__ == '__main__':
    create_report()
