"""
Multi-language notification templates.
Channels: IN_APP (always), EMAIL (if available), SMS_OTP (critical only).
"""
from __future__ import annotations

NOTIFICATION_TEMPLATES: dict = {
    "MUTATION_SUBMITTED": {
        "en": "Your mutation request for parcel {ulpin} has been submitted. Reference: {ref_id}",
        "hi": "भूखण्ड {ulpin} के लिए आपका म्यूटेशन अनुरोध सबमिट कर दिया गया है। संदर्भ: {ref_id}",
        "ta": "{ulpin} நிலத்திற்கான மாற்றம் சமர்ப்பிக்கப்பட்டது. குறிப்பு: {ref_id}",
        "te": "{ulpin} భూమికి మ్యూటేషన్ దరఖాస్తు సమర్పించబడింది. రిఫరెన్స్: {ref_id}",
        "critical": False,
        "channels": ["IN_APP", "EMAIL"],
    },
    "MUTATION_APPROVED": {
        "en": "Mutation request {ref_id} for parcel {ulpin} has been APPROVED.",
        "hi": "भूखण्ड {ulpin} के लिए म्यूटेशन अनुरोध {ref_id} को स्वीकृत किया गया है।",
        "ta": "மாற்றம் {ref_id} ஒப்புதல் அளிக்கப்பட்டது.",
        "te": "మ్యూటేషన్ {ref_id} ఆమోదించబడింది.",
        "critical": True,
        "channels": ["IN_APP", "EMAIL", "SMS_OTP"],
    },
    "MUTATION_REJECTED": {
        "en": "Mutation request {ref_id} for parcel {ulpin} has been REJECTED. Reason: {reason}",
        "hi": "भूखण्ड {ulpin} के लिए म्यूटेशन अनुरोध {ref_id} अस्वीकृत कर दिया गया। कारण: {reason}",
        "ta": "மாற்றம் {ref_id} நிராகரிக்கப்பட்டது. காரணம்: {reason}",
        "te": "మ్యూటేషన్ {ref_id} తిరస్కరించబడింది. కారణం: {reason}",
        "critical": True,
        "channels": ["IN_APP", "EMAIL", "SMS_OTP"],
    },
    "PARCEL_ACCESSED": {
        "en": "Your parcel {ulpin} was accessed by a government officer on {date}.",
        "hi": "आपके भूखण्ड {ulpin} को {date} को एक सरकारी अधिकारी द्वारा देखा गया।",
        "ta": "உங்கள் நிலம் {ulpin} அரசு அதிகாரியால் {date} அன்று அணுகப்பட்டது.",
        "te": "{date} న ప్రభుత్వ అధికారి మీ భూమి {ulpin} ని యాక్సెస్ చేశారు.",
        "critical": False,
        "channels": ["IN_APP"],
    },
    "CONFLICT_DETECTED": {
        "en": "A data inconsistency has been detected on parcel {ulpin}. Please verify records.",
        "hi": "भूखण्ड {ulpin} पर डेटा असंगतता पाई गई है। कृपया रिकॉर्ड सत्यापित करें।",
        "ta": "{ulpin} நிலத்தில் தரவு முரண்பாடு கண்டறியப்பட்டது. பதிவுகளை சரிபார்க்கவும்.",
        "te": "{ulpin} భూమిలో డేటా అసమ్మతి గుర్తించబడింది. రికార్డులను ధృవీకరించండి.",
        "critical": True,
        "channels": ["IN_APP", "EMAIL", "SMS_OTP"],
    },
    "TAX_OVERDUE": {
        "en": "Property tax for {ulpin} is overdue. Amount: ₹{amount}",
        "hi": "भूखण्ड {ulpin} का संपत्ति कर बकाया है। राशि: ₹{amount}",
        "ta": "{ulpin} சொத்து வரி நிலுவையில் உள்ளது. தொகை: ₹{amount}",
        "te": "{ulpin} ఆస్తి పన్ను నిలువు ఉంది. మొత్తం: ₹{amount}",
        "critical": True,
        "channels": ["IN_APP", "EMAIL", "SMS_OTP"],
    },
    "BUILDING_PERMIT_APPROVED": {
        "en": "Building permit {ref_id} for parcel {ulpin} has been approved.",
        "hi": "भूखण्ड {ulpin} के लिए भवन अनुमति {ref_id} स्वीकृत कर दी गई है।",
        "ta": "கட்டிட அனுமதி {ref_id} ஒப்புதல் அளிக்கப்பட்டது.",
        "te": "బిల్డింగ్ పర్మిట్ {ref_id} ఆమోదించబడింది.",
        "critical": False,
        "channels": ["IN_APP", "EMAIL"],
    },
    "ENCUMBRANCE_CERTIFICATE_READY": {
        "en": "Your Encumbrance Certificate (Ref: {ref_id}) for parcel {ulpin} is ready for download.",
        "hi": "भूखण्ड {ulpin} का भार प्रमाणपत्र (संदर्भ: {ref_id}) डाउनलोड के लिए तैयार है।",
        "ta": "அடமான சான்றிதழ் {ref_id} பதிவிறக்கத்திற்கு தயாராக உள்ளது.",
        "te": "ఎన్కంబ్రెన్స్ సర్టిఫికేట్ {ref_id} డౌన్‌లోడ్‌కు సిద్ధంగా ఉంది.",
        "critical": False,
        "channels": ["IN_APP", "EMAIL"],
    },
}


def render_template(template_key: str, lang: str, variables: dict) -> str:
    """Render a notification template with given variables."""
    tmpl = NOTIFICATION_TEMPLATES.get(template_key)
    if not tmpl:
        return f"Notification: {template_key}"
    text = tmpl.get(lang) or tmpl.get("en", f"Notification: {template_key}")
    try:
        return text.format(**variables)
    except KeyError:
        return text
