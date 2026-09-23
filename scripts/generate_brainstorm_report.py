"""
Generate brainstorming report for Bhoomi Dhrishti architecture evolution
as a Word document (.docx)
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
    run = subtitle.add_run('Architecture Evolution Brainstorm\nRL + LLM + Knowledge Graph + Land Data Space')
    run.font.size = Pt(18)
    run.font.color.rgb = RGBColor(86, 101, 115)

    doc.add_paragraph()

    line = doc.add_paragraph()
    line.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = line.add_run('IDEATION & RESEARCH-BACKED IMPROVEMENTS')
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
        '1. The Core Insight',
        '2. Original Idea: MCP + RL Federated Architecture',
        '   2.1 What You Proposed',
        '   2.2 Academic Validation',
        '   2.3 Strengths',
        '   2.4 Gaps to Address',
        '3. Improvement 1: LLM + RL Hybrid (Three-Tier Intelligence)',
        '   3.1 Why Not Pure RL',
        '   3.2 The Three-Tier Stack',
        '   3.3 Research Backing',
        '4. Improvement 2: Land Data Space (GAIA-X Model)',
        '   4.1 What Are Data Spaces',
        '   4.2 Why This Framing Wins',
        '   4.3 India Stack Alignment',
        '5. Improvement 3: Knowledge Graph as Semantic Bridge',
        '   5.1 Nodes, Edges, and Cross-State Links',
        '   5.2 Natural Conflict Detection',
        '   5.3 Graph-Based Fraud Detection',
        '6. Improvement 4: Federated Learning for Privacy-Preserving ML',
        '7. Improvement 5: Self-Healing Adaptive Connectors',
        '8. New Idea 1: Parcel Digital Twin',
        '9. New Idea 2: Natural Language Land Query (GraphRAG)',
        '10. New Idea 3: Conflict Resolution Workflow',
        '11. The Complete Evolved Architecture',
        '12. SIH Demo Priorities',
        '13. Research Papers & Sources',
    ]
    for item in toc_items:
        p = doc.add_paragraph(item)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.space_before = Pt(0)
        for run in p.runs:
            run.font.size = Pt(10)

    doc.add_page_break()

    # ================================================================
    # 1. THE CORE INSIGHT
    # ================================================================
    doc.add_heading('1. The Core Insight', level=1)

    p = doc.add_paragraph()
    run = p.add_run('"India digitized its land records department by department, state by state. '
                     'Nobody built the bridge between them. That bridge is Bhoomi Dhrishti."')
    run.italic = True
    run.font.size = Pt(12)

    doc.add_paragraph(
        'The central problem is interoperability across 28 states, 8 union territories, '
        '3-5 departments per state, and 1,000+ land laws. Each state has digitized its own '
        'silo — 99.90% of Records of Rights are computerized — but there is almost zero '
        'integration between systems.'
    )

    doc.add_paragraph(
        'The proposed solution: use an MCP-like (Model Context Protocol) architecture where '
        'an intelligent agent (the Host) connects to all state systems (the Servers) to retrieve '
        'and reconcile data in real-time, without creating a centralized database. States keep '
        'their data and authority. The platform provides the bridge.'
    )

    doc.add_page_break()

    # ================================================================
    # 2. ORIGINAL IDEA
    # ================================================================
    doc.add_heading('2. Original Idea: MCP + RL Federated Architecture', level=1)

    doc.add_heading('2.1 What You Proposed', level=2)
    doc.add_paragraph(
        'An MCP-like architecture where:'
    )
    items = [
        'Host = A custom Reinforcement Learning algorithm sitting on the central Bhoomi Dhrishti server',
        'Servers = Each of the 28 states + 8 UTs land record systems, connected via adapters',
        'No centralized database — data stays with states, queried in real-time',
        'The RL agent learns how to retrieve, translate, and reconcile data across heterogeneous systems',
    ]
    for item in items:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_heading('2.2 Academic Validation', level=2)

    p = doc.add_paragraph()
    run = p.add_run('This idea has direct academic backing. ')
    run.bold = True

    doc.add_paragraph(
        'Mequanenit, Nibret & Herrero-Martin (2025), "A Multi-Agent Deep Reinforcement Learning '
        'System for Governmental Interoperability", Applied Sciences 15(6):3146. Cited by 21.'
    )

    doc.add_paragraph('Key results from the paper:')
    add_styled_table(doc,
        ['Metric', 'Result'],
        [
            ['Framework', 'JADE (Java Agent Development Framework) + Deep RL'],
            ['Task Completion Rate', '95%'],
            ['Decision Accuracy', '96%'],
            ['Communication Latency', '120 ms'],
            ['Problem Addressed', 'Fragmented operations, incompatible data formats, rigid communication protocols'],
            ['Departments Tested', 'Treasury, Event Management, Public Safety'],
            ['Key Innovation', 'Agents leverage historical + real-time data to adapt to environmental changes'],
        ]
    )

    doc.add_paragraph()
    p = doc.add_paragraph()
    run = p.add_run('Implication: ')
    run.bold = True
    p.add_run(
        'Your instinct about RL for governmental interoperability is validated by peer-reviewed '
        'research with strong results. The paper demonstrates this is feasible and effective.'
    )

    doc.add_heading('2.3 Strengths of the Original Idea', level=2)
    add_styled_table(doc,
        ['Strength', 'Why It Matters'],
        [
            ['Politically perfect', 'States keep their data — no sovereignty conflict. No state government can object to "we just ask your system questions."'],
            ['Legally correct', 'No centralized copy = no liability for stale/wrong data. You are a bridge, not a mirror.'],
            ['MCP pattern is right abstraction', 'A host orchestrating multiple tool-providing servers is exactly what this problem needs.'],
            ['Novel for SIH', 'Nobody else will propose an RL-based federated query agent. Judges will notice.'],
            ['Aligns with India Stack', 'DPI philosophy: public infrastructure, private innovation, population-scale adoption.'],
        ]
    )

    doc.add_heading('2.4 Gaps to Address', level=2)
    add_styled_table(doc,
        ['Gap', 'The Problem', 'Solution (See Section)'],
        [
            ['Why RL specifically?', 'If the task is "get RoR for parcel X" — that is a deterministic API call, not an RL problem. RL needs a reward signal.', 'Section 3: Three-Tier Intelligence'],
            ['Pure real-time is fragile', 'When AP Mee Bhoomi is down for maintenance, citizens get nothing.', 'Section 7: Self-Healing Connectors'],
            ['State systems lack APIs', 'Most portals are web-only (HTML), not API-first. You need adapters/scrapers.', 'Section 4: Land Data Space Protocol'],
            ['Schema heterogeneity', 'TN "patta" = MH "khata" = WB "plot" — field names, formats, and semantics differ.', 'Section 3: LLM for schema matching'],
            ['No semantic layer', 'API calls return rows, not meaning. You need to understand relationships.', 'Section 5: Knowledge Graph'],
        ]
    )

    doc.add_page_break()

    # ================================================================
    # 3. IMPROVEMENT 1: LLM + RL HYBRID
    # ================================================================
    doc.add_heading('3. Improvement 1: LLM + RL Hybrid (Three-Tier Intelligence)', level=1)

    doc.add_heading('3.1 Why Not Pure RL', level=2)
    doc.add_paragraph(
        'Reinforcement Learning needs three things: an action space (what can the agent do?), '
        'a reward signal (how does it know it did well?), and an environment that changes based '
        'on actions. For simple data retrieval ("get RoR for parcel X from Tamil Nadu"), this is '
        'a deterministic API call — RL adds no value.'
    )
    doc.add_paragraph('But RL IS the right tool for:')
    items = [
        'Optimizing which source to trust when revenue says 2 acres and survey says 1.8 acres (reward = ground truth alignment)',
        'Learning optimal query strategies across flaky state systems (retry timing, fallback order, degradation)',
        'Conflict resolution patterns — learning that certain disagreement types are benign vs. fraud indicators',
        'Cache refresh optimization — when is cached data stale enough to re-query?',
    ]
    for item in items:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_paragraph(
        'What RL cannot do well: understanding that Tamil Nadu\'s "patta_number" is semantically '
        'equivalent to Maharashtra\'s "khata_number" or West Bengal\'s "plot_number". That requires '
        'language understanding — which is what LLMs excel at.'
    )

    doc.add_heading('3.2 The Three-Tier Intelligence Stack', level=2)

    add_styled_table(doc,
        ['Tier', 'Technology', 'What It Does', 'Examples'],
        [
            ['Tier 3 (Top)', 'Large Language Model', 'Understands semantics, translates schemas, resolves entity ambiguity',
             'patta_number → khata_number mapping; "Raju S/O Venkat" = "S. Raju son of Venkatesh"'],
            ['Tier 2 (Middle)', 'Reinforcement Learning Agent', 'Optimizes strategies over time based on feedback',
             'Query routing, cache refresh timing, trust scoring, conflict resolution prioritization'],
            ['Tier 1 (Base)', 'Deterministic Rules Engine', 'Hard constraints that never change — no ML drift allowed',
             'BDPR format validation, provenance enforcement, audit chain integrity, SRID 4326'],
        ]
    )

    doc.add_paragraph()
    p = doc.add_paragraph()
    run = p.add_run('Why three tiers instead of one: ')
    run.bold = True
    p.add_run(
        'Land records are high-stakes — a wrong mapping can mislabel ownership. You need the LLM\'s '
        'intelligence for understanding, but the Rules Engine\'s determinism for safety, and the RL '
        'agent\'s adaptability for optimization. No single approach handles all three needs.'
    )

    doc.add_heading('3.3 Research Backing', level=2)

    add_styled_table(doc,
        ['Paper', 'Year', 'Key Finding', 'Relevance'],
        [
            ['Dehghani, "LLM-assisted schema matching and deterministic normalization"',
             '2026', 'LLM + RL hybrid for heterogeneous environmental permitting data',
             'Directly validates LLM for schema matching + deterministic pipeline'],
            ['Zheng et al., "Distributed data governance with local LLM coordination"',
             '2026', 'Java probe agents in 69 source systems + local LLM for semantic fragmentation',
             'Shows LLM-based coordination of government data at scale'],
            ['Israel & Paul, "Reinforcement Learning for Adaptive ETL Workflows"',
             '2026', 'RL for automatic schema mapping, self-healing pipelines',
             'Validates RL for the optimization layer of data integration'],
            ['Deng et al., "LLM-Driven Deterministic Data Governance"',
             '2026', 'Explicit data object models + multi-agent adaptive approach',
             'Shows LLM + deterministic rules coexisting for data governance'],
            ['Ali et al., "Talk to Open Data: LLM agent using Langchain"',
             '2025', 'LLM agent for cross-domain ontology alignment in government data',
             'Validates LLM for government data schema alignment'],
        ]
    )

    doc.add_paragraph()
    doc.add_heading('3.4 How This Replaces mapping.yaml', level=2)
    doc.add_paragraph('Current approach (static):')
    items = [
        'Each state has a mapping.yaml that manually maps field names to canonical schema',
        'Adding a new state requires a human to write the mapping',
        'If a state changes its schema, the mapping breaks silently',
    ]
    for item in items:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_paragraph('Evolved approach (LLM-assisted):')
    items = [
        'LLM analyzes a state\'s data schema and proposes mappings to canonical Bhoomi Dhrishti schema',
        'Human reviews and confirms (human-in-the-loop for safety)',
        'Once confirmed, mapping becomes a deterministic rule (Tier 1)',
        'RL agent monitors mapping quality over time and flags drift',
        'New state onboarding goes from days of manual work to hours of review',
    ]
    for item in items:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_page_break()

    # ================================================================
    # 4. IMPROVEMENT 2: LAND DATA SPACE
    # ================================================================
    doc.add_heading('4. Improvement 2: Land Data Space (GAIA-X Model)', level=1)

    doc.add_heading('4.1 What Are Data Spaces', level=2)
    doc.add_paragraph(
        'The EU\'s GAIA-X initiative creates sovereign data spaces where data stays with its '
        'owner but becomes interoperable through standardized connectors. Each participant '
        'maintains data sovereignty while enabling controlled, audited data exchange.'
    )
    doc.add_paragraph('Core principles of data spaces:')
    items = [
        'Data sovereignty: Data stays with its owner (the state government)',
        'Standardized connectors: A common protocol for data exchange',
        'Trust framework: Participants are authenticated and authorized',
        'Audit trail: Every data access is logged and traceable',
        'Interoperability: Common semantic model across participants',
        'Decentralization: No single point of control or failure',
    ]
    for item in items:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_heading('4.2 Why This Framing Wins', level=2)
    add_styled_table(doc,
        ['Framing', 'How Judges Perceive It', 'Political Feasibility'],
        [
            ['"We built an app"', 'Yet another hackathon project', 'States may resist adoption'],
            ['"We built a platform"', 'Interesting but who maintains it?', 'Centralization concerns'],
            ['"We built India\'s Land Data Space"', 'This is Digital Public Infrastructure', 'States are sovereign participants, not subordinates'],
        ]
    )

    doc.add_paragraph()
    p = doc.add_paragraph()
    run = p.add_run('The key insight: ')
    run.bold = True
    p.add_run(
        'Bhoomi Dhrishti is not an application or a platform. It is infrastructure — like UPI is '
        'infrastructure for payments. States participate voluntarily because the infrastructure '
        'makes their own systems more valuable, not because it replaces them.'
    )

    doc.add_heading('4.3 India Stack Alignment', level=2)
    doc.add_paragraph(
        'India has already proven the DPI model works at scale:'
    )
    add_styled_table(doc,
        ['Layer', 'India Stack Example', 'Bhoomi Dhrishti Equivalent'],
        [
            ['Identity', 'Aadhaar (1.4B IDs)', 'BDPR / ULPIN (408.5M parcels)'],
            ['Payments', 'UPI (federated, bank-to-bank)', 'Land Data Space (federated, state-to-state)'],
            ['Data', 'DigiLocker / Account Aggregator', 'Provenance-tracked land records with consent'],
            ['Consent', 'DEPA framework', 'Purpose-bound tokens (LOAN_VERIFICATION, LEGAL_USE)'],
        ]
    )

    doc.add_paragraph()
    p = doc.add_paragraph()
    run = p.add_run('Research backing: ')
    run.bold = True
    p.add_run(
        'Yellasiri (2025, TechRxiv) specifically compares EU (GAIA-X, FAIR Data Spaces) and India '
        'sovereignty movements. Schmeling (2026, Universitat Konstanz) studied government collaboration '
        'in sovereign data spaces. Burnard (2026, SSRN) analyzes GAIA-X as digital sovereignty infrastructure.'
    )

    doc.add_page_break()

    # ================================================================
    # 5. IMPROVEMENT 3: KNOWLEDGE GRAPH
    # ================================================================
    doc.add_heading('5. Improvement 3: Knowledge Graph as Semantic Bridge', level=1)

    doc.add_heading('5.1 Nodes, Edges, and Cross-State Links', level=2)
    doc.add_paragraph(
        'Instead of just API calls returning rows of data, build a Land Knowledge Graph where '
        'entities and their relationships are explicitly modeled:'
    )

    add_styled_table(doc,
        ['Node Type', 'Examples', 'Properties'],
        [
            ['Parcel', 'BD-TN-0000001, BD-MH-0045782', 'BDPR, area, geometry, ULPIN status'],
            ['Owner', 'Person or organization', 'Name variants, Aadhaar linkage, gender'],
            ['Department', 'Revenue, Registration, Survey, Forest', 'State, system name, data freshness'],
            ['Transaction', 'Sale, mutation, mortgage, partition', 'Date, type, parties, value'],
            ['Law/Regulation', 'TN Patta Act, MH MLRC 1966', 'Jurisdiction, applicability'],
            ['Zone', 'Residential, commercial, forest, CRZ', 'Restrictions, permitted uses'],
        ]
    )

    doc.add_paragraph()
    doc.add_paragraph('Edge types (relationships):')
    add_styled_table(doc,
        ['Edge', 'From', 'To', 'Meaning'],
        [
            ['OWNED_BY', 'Parcel', 'Owner', 'Revenue department says this person owns this land'],
            ['REGISTERED_AT', 'Transaction', 'Department', 'This transaction was registered here'],
            ['CONFLICTS_WITH', 'Record A', 'Record B', 'Two departments disagree on this parcel'],
            ['ADJACENT_TO', 'Parcel', 'Parcel', 'Spatial adjacency (from geospatial service)'],
            ['GOVERNED_BY', 'Parcel', 'Law', 'Which laws/regulations apply'],
            ['ZONED_AS', 'Parcel', 'Zone', 'Planning/zoning classification'],
            ['TRANSFERRED_VIA', 'Parcel', 'Transaction', 'Ownership chain / lineage'],
        ]
    )

    doc.add_heading('5.2 Natural Conflict Detection', level=2)
    doc.add_paragraph(
        'With a knowledge graph, conflicts become structural patterns rather than '
        'rule-based checks:'
    )
    items = [
        'Two OWNED_BY edges for the same parcel from different departments = ownership dispute',
        'OWNED_BY edge contradicts REGISTERED_AT transaction chain = mutation lag',
        'Parcel ZONED_AS residential but GOVERNED_BY Forest Rights Act = jurisdiction conflict',
        'TRANSFERRED_VIA chain has a gap = missing mutation in revenue records',
        'Owner node has multiple name variants across departments = entity resolution needed',
    ]
    for item in items:
        doc.add_paragraph(item, style='List Bullet')

    p = doc.add_paragraph()
    run = p.add_run('Advantage over current Trust Engine: ')
    run.bold = True
    p.add_run(
        'The current trust engine runs deterministic rule checks against DB tables. A knowledge graph '
        'makes conflict detection emergent — new conflict types are discovered by graph traversal '
        'patterns, not hardcoded rules. The RL agent can learn which graph patterns indicate fraud '
        'vs. benign administrative lag.'
    )

    doc.add_heading('5.3 Graph-Based Fraud Detection', level=2)
    doc.add_paragraph('Fraud patterns visible in graph structure:')
    add_styled_table(doc,
        ['Pattern', 'Graph Structure', 'What It Indicates'],
        [
            ['Circular ownership', 'A→B→C→A ownership chain', 'Potential benami (fictitious ownership)'],
            ['Star pattern', 'One owner → many parcels transferred in short time', 'Land grabbing or consolidation'],
            ['Orphan parcels', 'Parcel node with no OWNED_BY edge', 'Unrecorded or disputed land'],
            ['Department island', 'Parcel exists in one dept but not others', 'Silo gap — registration without mutation'],
            ['Temporal anomaly', 'TRANSFERRED_VIA date before previous transfer completes', 'Double sale fraud'],
        ]
    )

    doc.add_paragraph()
    doc.add_paragraph(
        'Research backing: Jeong et al. (2026, ISPRS) demonstrated a Geographical Scene Knowledge '
        'Graph integrating cadastral polygon data with building spatial data for urban digital twins. '
        'Lee et al. (2026, IEEE Access) built a Declarative Geographic Knowledge Graph for district-scale '
        'infrastructure analysis.'
    )

    doc.add_page_break()

    # ================================================================
    # 6. IMPROVEMENT 4: FEDERATED LEARNING
    # ================================================================
    doc.add_heading('6. Improvement 4: Federated Learning for Privacy-Preserving ML', level=1)

    doc.add_paragraph(
        'The Trust Engine currently runs deterministic rules. With federated learning, you can '
        'train ML models across state data without the data ever leaving the state.'
    )

    add_styled_table(doc,
        ['Component', 'Current (Rules)', 'Evolved (Federated Learning)'],
        [
            ['Fraud detection', 'Hardcoded patterns (CRITICAL/HIGH/MEDIUM/LOW)', 'ML models trained on real state data, detecting novel patterns'],
            ['Entity resolution', 'String matching on names', 'Federated NER model trained across states\' name variants'],
            ['Trust scoring', 'Deterministic penalty scores', 'ML-based scoring that learns from resolution outcomes'],
            ['Data quality', 'Schema validation only', 'Anomaly detection trained on state-specific data distributions'],
            ['Privacy', 'Data cached on central server', 'Only model weights leave the state, never raw data'],
        ]
    )

    doc.add_paragraph()
    doc.add_paragraph('How it works:')
    items = [
        'Each state runs a local ML model on their land record data',
        'Only model gradients/weights are sent to the central Bhoomi Dhrishti server',
        'Central server aggregates weights using federated averaging (FedAvg)',
        'Updated global model is sent back to states',
        'Result: ML intelligence from ALL states\' data, but no state\'s data leaves their jurisdiction',
    ]
    for item in items:
        doc.add_paragraph(item, style='List Bullet')

    p = doc.add_paragraph()
    run = p.add_run('Research backing: ')
    run.bold = True
    p.add_run(
        'Zhang (2024, Government Information Quarterly) demonstrated "A more secure framework for '
        'open government data sharing based on federated learning" with horizontal, vertical, and '
        'federated transfer learning variants. Cited by 16. Schumacher et al. (2026, Elsevier) showed '
        'federated learning for environmental monitoring where data confidentiality is critical.'
    )

    doc.add_page_break()

    # ================================================================
    # 7. IMPROVEMENT 5: SELF-HEALING CONNECTORS
    # ================================================================
    doc.add_heading('7. Improvement 5: Self-Healing Adaptive Connectors', level=1)

    doc.add_paragraph(
        'Each state\'s MCP server/adapter must handle the reality that government portals are '
        'unreliable, change without notice, and have wildly different performance characteristics.'
    )

    add_styled_table(doc,
        ['Capability', 'What the RL Agent Learns', 'Reward Signal'],
        [
            ['Retry strategy', 'Odisha ASP.NET is slow (5s avg), AP is fast (200ms) — different retry timing per state',
             'Successful response within latency budget'],
            ['Scraper resilience', 'Detects when a state portal\'s HTML structure changes and flags for adapter update',
             'Continued data extraction accuracy'],
            ['Graceful degradation', 'Automatically drops from Gold (real-time) to Silver (hourly) to Bronze (daily) when state is partially down',
             'Service availability maintained'],
            ['Cache refresh', 'Tamil Nadu updates daily so cache for 23h; Odisha updates monthly so cache for 29d',
             'Freshness vs. cost optimization'],
            ['Schema drift', 'Detects when a state adds new fields or changes value enumerations',
             'Mapping accuracy over time'],
        ]
    )

    doc.add_paragraph()
    p = doc.add_paragraph()
    run = p.add_run('Research backing: ')
    run.bold = True
    p.add_run(
        'Israel & Paul (2026), "Reinforcement Learning for Adaptive ETL Workflows" — demonstrates '
        'self-healing pipelines that detect failure modes and adjust execution. Directly applicable '
        'to state portal connectivity.'
    )

    doc.add_page_break()

    # ================================================================
    # 8. NEW IDEA 1: PARCEL DIGITAL TWIN
    # ================================================================
    doc.add_heading('8. New Idea 1: Parcel Digital Twin', level=1)

    doc.add_paragraph(
        'Nobody in Indian land governance talks about digital twins yet. But the concept fits '
        'perfectly — a virtual representation of every land parcel in India, continuously updated '
        'from state systems.'
    )

    add_styled_table(doc,
        ['Aspect', 'Physical Parcel', 'Digital Twin'],
        [
            ['Geometry', 'Physical boundary on ground', '3D visualization in MapLibre GL with satellite overlay'],
            ['Ownership', 'Paper records in multiple offices', 'All departments\' views shown simultaneously'],
            ['Conflicts', 'Discovered in court after 20 years', 'Trust Engine flags conflicts in real-time'],
            ['History', 'Scattered across mutation registers', 'Time-travel: view parcel state at any date'],
            ['Neighbors', 'Walk the boundary', 'Spatial query: adjacent parcels, disputes, easements'],
            ['Regulations', 'Check with 3-4 departments manually', 'All applicable zones/restrictions overlaid'],
        ]
    )

    doc.add_paragraph()
    doc.add_paragraph('What makes this compelling for SIH judges:')
    items = [
        '"Digital Twin" is a buzzword they will recognize from Industry 4.0 — applying it to land governance is novel',
        'Visualizing a parcel from all departments\' perspectives simultaneously is the Trust Engine made tangible',
        'Time-travel feature is unique — "show me this parcel in 2015 vs today"',
        'Directly maps to PS-26014 requirement: "Parcel-based decision-support dashboards"',
    ]
    for item in items:
        doc.add_paragraph(item, style='List Bullet')

    p = doc.add_paragraph()
    run = p.add_run('Research backing: ')
    run.bold = True
    p.add_run(
        'Jeong et al. (2026, ISPRS) built an "Urban Digital Twin Based on Geospatial Data" using '
        'Geographical Scene Knowledge Graph integrated with cadastral polygon information. '
        'Xue et al. (2025, Taylor & Francis) surveyed "Advances when GIS meets Digital Twin."'
    )

    doc.add_page_break()

    # ================================================================
    # 9. NEW IDEA 2: NATURAL LANGUAGE LAND QUERY
    # ================================================================
    doc.add_heading('9. New Idea 2: Natural Language Land Query (GraphRAG)', level=1)

    doc.add_paragraph(
        'Citizens should not need to know which department to ask, which form to fill, or which '
        'portal to visit. With the Knowledge Graph + LLM, they can ask in natural language:'
    )

    doc.add_paragraph()
    p = doc.add_paragraph()
    run = p.add_run('Example query: ')
    run.bold = True
    run = p.add_run('"Show me land near Velachery, Chennai that has no disputes, is residential '
                     'zoned, and was last sold in the past 5 years"')
    run.italic = True

    doc.add_paragraph()
    doc.add_paragraph('How the system decomposes this:')

    add_styled_table(doc,
        ['Query Component', 'Service Hit', 'Knowledge Graph Traversal'],
        [
            ['"near Velachery, Chennai"', 'Geospatial (8002)', 'Spatial query: parcels within radius of Velachery centroid'],
            ['"no disputes"', 'Trust Engine (8008)', 'Filter: trust_score > threshold AND no CONFLICTS_WITH edges'],
            ['"residential zoned"', 'Planning-Zoning (8005)', 'Filter: parcel ZONED_AS residential'],
            ['"last sold in past 5 years"', 'Registration (8004)', 'Traverse: TRANSFERRED_VIA edges with date > 2021'],
        ]
    )

    doc.add_paragraph()
    p = doc.add_paragraph()
    run = p.add_run('The citizen never knows 4 departments were queried. ')
    run.bold = True
    p.add_run(
        'They get a map with matching parcels, each with provenance data showing which department '
        'provided what information and when.'
    )

    doc.add_paragraph()
    doc.add_paragraph('Additional NL query capabilities:')
    items = [
        '"What is the ownership history of parcel BD-TN-0000042?" → lineage graph visualization',
        '"Are there any forest rights claims overlapping with my land?" → FRA + revenue cross-check',
        '"What would be the stamp duty for purchasing this 2-acre plot?" → fiscal + registration calculation',
        '"Show me all parcels in this village where revenue and survey areas disagree by more than 10%" → trust engine analytics',
        '"Who are my neighbors and do any of them have boundary disputes?" → spatial + trust graph query',
    ]
    for item in items:
        doc.add_paragraph(item, style='List Bullet')

    p = doc.add_paragraph()
    run = p.add_run('Technology: ')
    run.bold = True
    p.add_run(
        'GraphRAG (Retrieval-Augmented Generation over Knowledge Graphs). The LLM translates '
        'natural language to graph queries (Cypher/SPARQL), executes them across the Knowledge Graph, '
        'and presents results in human-readable format with full provenance.'
    )

    doc.add_page_break()

    # ================================================================
    # 10. NEW IDEA 3: CONFLICT RESOLUTION WORKFLOW
    # ================================================================
    doc.add_heading('10. New Idea 3: Conflict Resolution Workflow', level=1)

    doc.add_paragraph(
        'When the Trust Engine detects a conflict between departments, currently someone has to '
        'manually investigate and resolve it. A structured digital workflow can accelerate this:'
    )

    add_styled_table(doc,
        ['Step', 'Action', 'Actor'],
        [
            ['1. Detection', 'Trust Engine flags conflict (e.g., area mismatch between revenue and survey)', 'Automated'],
            ['2. Classification', 'RL agent classifies conflict type and severity based on historical patterns', 'Automated'],
            ['3. Assignment', 'Conflict routed to appropriate officer(s) based on type and jurisdiction', 'Automated'],
            ['4. Evidence', 'System assembles all relevant records from all departments automatically', 'Automated'],
            ['5. Review', 'Officers from relevant departments review assembled evidence', 'Human'],
            ['6. Resolution', 'Officers submit resolution with justification', 'Human'],
            ['7. Audit', 'Resolution recorded on hash-chained audit log with all officer signatures', 'Automated'],
            ['8. Learning', 'RL agent learns from resolution to improve future classification and routing', 'Automated'],
        ]
    )

    doc.add_paragraph()
    p = doc.add_paragraph()
    run = p.add_run('Why this matters: ')
    run.bold = True
    p.add_run(
        '95% of land disputes arise from administrative non-compliance. A structured resolution '
        'workflow catches these at the administrative level BEFORE they become court cases. '
        'Average court resolution: 20 years. Average workflow resolution target: 25 days '
        '(matching Maharashtra\'s e-Hakk mutation guarantee).'
    )

    doc.add_page_break()

    # ================================================================
    # 11. THE COMPLETE EVOLVED ARCHITECTURE
    # ================================================================
    doc.add_heading('11. The Complete Evolved Architecture', level=1)

    doc.add_paragraph(
        'The following table maps each architectural component to its role, the technology choice, '
        'and the section where it was justified:'
    )

    add_styled_table(doc,
        ['Layer', 'Component', 'Technology', 'Section'],
        [
            ['User Interface', 'Citizen PWA', 'Next.js + NL query input', 'Section 9'],
            ['User Interface', 'Officer Console', 'MapLibre + Digital Twin visualization', 'Section 8'],
            ['User Interface', 'Admin Console', 'State onboarding + monitoring dashboard', 'Existing'],
            ['Intelligence', 'LLM Layer (Tier 3)', 'Claude/GPT for schema matching, NL→query, entity resolution', 'Section 3'],
            ['Intelligence', 'RL Orchestrator (Tier 2)', 'Multi-agent DRL for query routing, trust scoring, cache optimization', 'Section 3'],
            ['Intelligence', 'Rules Engine (Tier 1)', 'Deterministic validation: BDPR format, provenance, audit integrity', 'Section 3'],
            ['Semantic', 'Land Knowledge Graph', 'Neo4j / Amazon Neptune + GraphRAG', 'Section 5'],
            ['Semantic', 'Parcel Digital Twin', 'Knowledge Graph + temporal dimension + 3D viz', 'Section 8'],
            ['Privacy', 'Federated Learning', 'PySyft / Flower framework + FedAvg aggregation', 'Section 6'],
            ['Connectivity', 'Land Data Space Protocol', 'Standardized connector spec per state', 'Section 4'],
            ['Connectivity', 'Self-Healing Adapters', 'RL-optimized per-state connectors', 'Section 7'],
            ['Connectivity', 'State MCP Servers', '36 adapters (one per state/UT)', 'Section 2'],
            ['Governance', 'Conflict Resolution Workflow', 'Automated detection + human-in-loop resolution', 'Section 10'],
            ['Governance', 'Hash-Chained Audit Log', 'Append-only, SHA-256 chain (existing)', 'Existing'],
            ['Governance', 'Purpose-Bound Access', 'Keycloak JWT + role/purpose scoping (existing)', 'Existing'],
        ]
    )

    doc.add_paragraph()
    doc.add_heading('11.1 Architecture Diagram (Text)', level=2)
    p = doc.add_paragraph()
    run = p.add_run(
        '                    CITIZEN / OFFICER UI\n'
        '                   Natural Language + MapLibre\n'
        '                            |\n'
        '                   LAND KNOWLEDGE GRAPH\n'
        '                (Neo4j/Neptune + GraphRAG)\n'
        '              Parcels x Owners x Depts x Laws\n'
        '                            |\n'
        '         +------------------+------------------+\n'
        '         |                  |                  |\n'
        '    LLM LAYER         RL ORCHESTRATOR    RULES ENGINE\n'
        '  Schema matching    Query routing       BDPR validation\n'
        '  NL->structured     Cache refresh       Provenance\n'
        '  Entity resolution  Conflict scoring    Audit chain\n'
        '         |                  |                  |\n'
        '         +------------------+------------------+\n'
        '                            |\n'
        '                LAND DATA SPACE PROTOCOL\n'
        '               (Standardized connectors)\n'
        '                            |\n'
        '    +-------+-------+-------+-------+-------+-------+\n'
        '    |       |       |       |       |       |       |\n'
        '   TN      MH      AP      WB      KA      CH     ...\n'
        '  Server  Server  Server  Server  Server  Server   36\n'
        '    |       |       |       |       |       |       |\n'
        ' TNREGI  MahaBhu  MeeBho  Banglar Bhoomi  CH-LRC  State\n'
        '  NET    lekh     omi     bhumi   KA             Systems'
    )
    run.font.name = 'Consolas'
    run.font.size = Pt(8)

    doc.add_page_break()

    # ================================================================
    # 12. SIH DEMO PRIORITIES
    # ================================================================
    doc.add_heading('12. SIH Demo Priorities', level=1)

    doc.add_paragraph('If building for SIH demo (15-minute presentation), prioritize these 3 features:')

    doc.add_heading('12.1 Priority 1: Natural Language Land Query (Biggest Wow Factor)', level=2)
    doc.add_paragraph(
        'Citizen types a question in natural language. The system queries 4 departments transparently '
        'and returns results on a map with full provenance. This is the single most impressive feature '
        'you can demo — it makes the interoperability tangible and citizen-facing.'
    )
    doc.add_paragraph('Build time estimate: 2-3 weeks (LLM query decomposition + Knowledge Graph + UI)')

    doc.add_heading('12.2 Priority 2: Live Schema Auto-Mapping (Technical Differentiator)', level=2)
    doc.add_paragraph(
        'Show the LLM analyzing a new state\'s data schema and proposing mappings to the canonical '
        'Bhoomi Dhrishti schema — live, on stage. Then show the human confirming the mapping. Then '
        'show data flowing through immediately. This replaces weeks of manual mapping.yaml work.'
    )
    doc.add_paragraph('Build time estimate: 1-2 weeks (LLM integration + mapping UI)')

    doc.add_heading('12.3 Priority 3: Trust Engine Visualization / Digital Twin (Visual Impact)', level=2)
    doc.add_paragraph(
        'A specific parcel with a real conflict — revenue says 2.3 acres, survey says 1.8 acres, '
        'registration shows a 2020 sale but mutation is still pending. Show all three department '
        'views side by side on the map, with trust score breakdown and conflict resolution workflow.'
    )
    doc.add_paragraph('Build time estimate: 1 week (mostly frontend visualization)')

    doc.add_paragraph()
    doc.add_heading('12.4 Demo Flow (15 Minutes)', level=2)
    add_styled_table(doc,
        ['Time', 'Segment', 'What to Show'],
        [
            ['0-2 min', 'Problem Statement', 'The 4 axes of fragmentation + key statistics (66% civil cases, Rs 18.5L crore)'],
            ['2-5 min', 'Citizen Demo', 'Natural language query → multi-department results on map → provenance visible'],
            ['5-9 min', 'Officer Demo', 'Digital Twin view of conflict parcel → Trust Engine scoring → Resolution workflow'],
            ['9-12 min', 'Technical Deep Dive', 'Architecture diagram → LLM schema auto-mapping demo → Knowledge Graph visualization'],
            ['12-14 min', 'Scalability & Impact', 'Show TN + CH configs → explain Bronze/Silver/Gold tiers → Land Data Space framing'],
            ['14-15 min', 'Closing', 'Key numbers + "We are not building an app, we are building India\'s Land Data Space"'],
        ]
    )

    doc.add_page_break()

    # ================================================================
    # 13. RESEARCH PAPERS
    # ================================================================
    doc.add_heading('13. Research Papers & Sources', level=1)

    doc.add_heading('13.1 Directly Relevant (Validate Core Architecture)', level=2)
    sources = [
        'Mequanenit, Nibret & Herrero-Martin (2025). "A Multi-Agent Deep Reinforcement Learning System '
        'for Governmental Interoperability." Applied Sciences 15(6):3146. Cited by 21. '
        'https://www.mdpi.com/2076-3417/15/6/3146',

        'Dehghani (2026). "Integrating heterogeneous environmental permitting spreadsheets through '
        'LLM-assisted schema matching and deterministic normalization." UBC Thesis. '
        'https://open.library.ubc.ca/soa/cIRcle/collections/ubctheses/24/items/1.0451952',

        'Israel & Paul (2026). "Reinforcement Learning for Adaptive ETL Workflows." ResearchGate. '
        'https://www.researchgate.net/publication/404314126',

        'Zheng, Miao, Yi, Fan, Zhuo & Wang (2026). "A distributed data governance architecture for '
        'smart cities based on data unified registration, dynamic catalog, and local LLM data '
        'coordination." Urban Informatics. Springer. '
        'https://link.springer.com/article/10.1007/s44212-026-00114-1',

        'Deng, Liu, Yang, Chen & Li (2026). "LLM-Driven Deterministic Data Governance: A Decoupled '
        'Standardization Architecture." IEEE Intelligence and Data. '
        'https://ieeexplore.ieee.org/abstract/document/11676170/',

        'Zhang (2024). "A more secure framework for open government data sharing based on federated '
        'learning." Government Information Quarterly. Cited by 16. '
        'https://www.sciencedirect.com/science/article/pii/S0740624X2400073X',
    ]
    for s in sources:
        doc.add_paragraph(s, style='List Bullet')

    doc.add_heading('13.2 Knowledge Graph & Digital Twin', level=2)
    sources = [
        'Jeong, Jeong & Kim (2026). "Development of an Urban Digital Twin Based on Geospatial Data: '
        'A Case Study of Busan, South Korea." ISPRS Int. J. Geo-Information. '
        'https://www.mdpi.com/2220-9964/15/6/247',

        'Lee (2026). "A Declarative Geographic Knowledge Graph Framework for District-Scale Urban '
        'Infrastructure Analysis." IEEE Access. https://ieeexplore.ieee.org/abstract/document/11573884/',

        'Xue, Li, Liu et al. (2025). "Advances, challenges and prospective research when GIS meets '
        'digital twin." Digital Twin, Taylor & Francis. '
        'https://www.tandfonline.com/doi/abs/10.1080/27525783.2025.2610851',

        'Wahlberg (2026). "Towards Data-Centric Geospatial Applications: A Knowledge Graph Approach '
        'to Road Maintenance in Stockholm." Lund University MSc Thesis.',
    ]
    for s in sources:
        doc.add_paragraph(s, style='List Bullet')

    doc.add_heading('13.3 Data Spaces & Digital Sovereignty', level=2)
    sources = [
        'Schmeling (2026). "Investigating government collaboration in sovereign data spaces." '
        'Universitat Konstanz PhD. https://kops.uni-konstanz.de/',

        'Yellasiri (2025). "Sovereignty movements in EU, India — GAIA-X, FAIR Data Spaces." TechRxiv.',

        'Burnard (2026). "Foundations of Digital Sovereignty: Definitions, Drivers, and a Reference '
        'Framework for National Digital Infrastructure." SSRN. '
        'https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7355801',

        'Ford, Dell\'Aquila, Grabova, Munoz & Renda (2025). "Building the European Digital Public '
        'Infrastructure: Rationale, Options, and Roadmap." CEPS. https://cdn.ceps.eu/',

        'Marojevikj & Stojanov (2025). "Navigating the Data Space Landscape: Concepts, Applications, '
        'and Future Directions." arXiv:2509.06983.',
    ]
    for s in sources:
        doc.add_paragraph(s, style='List Bullet')

    doc.add_heading('13.4 LLM Agents for Government Data', level=2)
    sources = [
        'Ali, Alexopoulos & Charalabidis (2025/2026). "Talk to Open Data: Enabling User Interaction '
        'with Open Government Data Using LLMs, RAG and Smart Agent Technologies" / "Unlocking '
        'Government Open Data: Harnessing Open-Source LLMs." IntechOpen / Springer.',

        'Hossain et al. (2026). "Safe and Scalable Collaboration in Multiagent LLM Systems: '
        'A Comprehensive Review." IEEE. https://ieeexplore.ieee.org/abstract/document/11598769/',

        'Renney et al. (2026). "LLM-Enabled Multi-Agent Systems: Empirical Evaluation and Insights '
        'into Emerging Design Patterns & Paradigms." arXiv:2601.03328.',

        'Malik, Mittal, Mavaluru & Narapureddy (2023). "Building a secure platform for digital '
        'governance interoperability and data exchange using blockchain and deep learning-based '
        'frameworks." IEEE Access. Cited by 102.',
    ]
    for s in sources:
        doc.add_paragraph(s, style='List Bullet')

    # ================================================================
    # SAVE
    # ================================================================
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(os.path.dirname(output_dir), 'Bhoomi_Dhrishti_Brainstorm.docx')
    doc.save(output_path)
    print(f"Report saved to: {output_path}")
    return output_path


if __name__ == '__main__':
    path = create_report()
