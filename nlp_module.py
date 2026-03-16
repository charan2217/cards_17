import re
import spacy
from typing import Dict, List, Tuple
from difflib import SequenceMatcher

try:
    nlp = spacy.load("en_core_web_sm")
except Exception:
    nlp = spacy.blank("en")

# Enhanced business patterns
COMPANY_PATTERNS = [
    r'^[A-Z][A-Z\s&]{2,}$',  # All caps companies
    r'.*\b(SOLUTIONS|TECHNOLOGIES|GLOBAL|MOBILE|DIGITAL)\b.*',  # Tech companies
    r'.*\b(LTD|PVT|INC|LLC|CORP|COMPANY|CO)\b.*',  # Company suffixes
]

PERSON_PATTERNS = [
    r'^[A-Z][a-z]+\s+[A-Z][a-z]+$',  # First Last
    r'^[A-Z]+\s+[A-Z]+$',  # ALL CAPS names
    r'^[A-Z][a-z]+\s+[A-Z]\.\s+[A-Z][a-z]+$',  # First M. Last
    r'^[A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+$',  # First Middle Last
    r'^[A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z]+$',  # First Last SURNAME
]

DESIGNATION_PATTERNS = [
    r'.*\b(CEO|CTO|CFO|Director|Manager|Engineer|Developer|Consultant|Analyst|Specialist|Coordinator|Administrator|President|Vice\s+President|VP|Founder|Co-?founder|Owner|Partner|Associate|Senior|Junior|Sr|Jr|Dr|Prof|Mr|Mrs|Ms|Miss|Sir|Madam)\b.*',
    r'.*\b(Executive|Officer|Supervisor|Team\s+Lead|Lead|Head|Chief|Principal|Senior|Junior|General\s+Manager|Assistant|Deputy)\b.*'
]

PHONE_PATTERNS = [
    r'\+91[-\s]?(\d{5})[-\s]?(\d{5})',  # Indian: +91-88888-88888
    r'\+91[-\s]?(\d{4})[-\s]?(\d{6})',  # Indian variant
    r'(\d{3})[-\s]?(\d{3})[-\s]?(\d{4})',  # US: 888-888-8888
    r'\+?1?[-\s]?(\d{3})[-\s]?(\d{3})[-\s]?(\d{4})',  # US with country
    r'(\d{10})',  # Simple 10-digit
    r'(\d{4})[-\s]?(\d{7})',  # Some formats
]

EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
WEBSITE_PATTERN = r'(?i)(?<!@)\b(?:https?://)?(?:www\.)?([a-z0-9][a-z0-9.-]+\.[a-z]{2,})(?:/[^\s]*)?\b'

# Indian address patterns
AREA_PATTERNS = [
    r'.*\b(Block|Sector|Phase|Area|Colony|Nagar|Pur|Ganj|Bagh|Vihar|Enclave|Park|Garden|Complex|Plaza|Market|Bazaar|Chowk|Square|Circle|Point|Junction)\b.*',
    r'.*\d+\s*\/\s*\d+.*',  # Pattern like 55/5
]

CITY_PATTERNS = [
    r'\b(?:Delhi|New Delhi|NCR|Noida|Gurgaon|Faridabad|Ghaziabad|Mumbai|Bangalore|Hyderabad|Chennai|Kolkata|Pune|Ahmedabad|Jaipur|Lucknow|Kanpur|Nagpur|Indore|Thane|Bhopal|Visakhapatnam|Patna|Vadodara|Ludhiana|Agra|Nashik|Meerut|Rajkot|Varanasi|Srinagar|Aurangabad|Amritsar|Allahabad|Ranchi|Coimbatore|Jabalpur|Gwalior|Vijayawada|Jodhpur|Madurai|Raipur|Kota|Guwahati|Chandigarh|Mysore|Tiruchirappalli|Bareilly|Aligarh|Solapur|Moradabad|Gurgaon|Jalandhar|Tiruppur|Bhubaneswar|Salem|Mira-Bhayandar|Thiruvananthapuram|Bhiwandi|Saharanpur|Guntur|Amravati|Bikaner|Jamshedpur|Bhilai|Cuttack|Firozabad|Kochi|Nellore|Bhavnagar|Dehradun|Durg|Asansol|Rourkela|Nanded|Kolhapur|Ajmer|Akola|Gulbarga|Jamnagar|Ujjain|Loni|Siliguri|Jhansi|Ulhasnagar|Jammu|Sangli|Mangalore|Erode|Belgaum|Ambattur|Tirunelveli|Malegaon|Gaya|Jalgaon|Udaipur)\b',
    r'\b[A-Z][a-z]+\s*(?:City|Town)\b'
]

STATE_PATTERNS = [
    r'\b(?:Delhi|NCT of Delhi|Maharashtra|Uttar Pradesh|Karnataka|Tamil Nadu|West Bengal|Gujarat|Rajasthan|Andhra Pradesh|Odisha|Telangana|Kerala|Madhya Pradesh|Punjab|Haryana|Jharkhand|Chhattisgarh|Assam|Bihar|Uttarakhand|Himachal Pradesh|Jammu & Kashmir|Goa|Sikkim|Meghalaya|Manipur|Tripura|Mizoram|Nagaland|Arunachal Pradesh)\b'
]

PINCODE_PATTERNS = [
    r'\b(\d{6})\b',  # Indian 6-digit pincode
    r'\b(\d{3}\s+\d{3})\b',  # spaced pincode like 641 012
    r'.*-\s*(\d{6})',  # City - Pincode format
]

ADDRESS_PATTERNS = [
    r'.*\d+.*,\s*.*,\s*.*',  # Number, Street, City
    r'.*\d+\s+.*(?:Street|St|Road|Rd|Avenue|Ave|Lane|Ln).*',
    r'.*Block\s+\d+.*',
    r'.*Sector\s+\d+.*',
    r'.*,\s*[A-Za-z]+\s*-\s*\d+',  # City - Pincode
]

# Business keywords for classification
BUSINESS_KEYWORDS = {
    'mobile': ['mobile', 'cellular', 'smartphone', 'phone', 'wireless'],
    'technology': ['technology', 'software', 'digital', 'tech', 'it'],
    'solutions': ['solutions', 'services', 'consulting', 'support'],
    'accessories': ['accessories', 'parts', 'components', 'equipment'],
    'dealership': ['dealer', 'dealership', 'distributor', 'retail'],
}

def extract_entities(text: str) -> Dict[str, str]:
    """Ultimate high-accuracy entity extraction with specific fields"""
    
    # Clean and preprocess
    text = clean_text(text)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    print("=== ULTIMATE ACCURACY EXTRACTION ===")
    print(f"Input text: {text}")
    print(f"Lines: {lines}")
    
    result = {
        "Card Holder": "",      # Person name
        "Company Name": "",     # Company
        "Designation": "",      # Job title
        "Mobile Number": "",    # Phone
        "Email": "",
        "Website": "",
        "Area": "",             # Locality/area
        "City": "",
        "State": "",
        "Pincode": "",
        "Address": "",          # Full address
        "Services/Products": "",
        "Other Info": ""
    }
    
    # Extract in order of confidence
    extract_email(text, result)
    extract_phone(text, result)
    extract_website(text, result)
    extract_designation(lines, result)
    extract_company_name(lines, result)
    extract_card_holder(lines, result)
    extract_address_components(lines, result)
    extract_full_address(lines, result)
    extract_services(lines, result)
    extract_other_info(lines, result)
    
    auto_correct_result(text, lines, result)
    
    print("=== FINAL RESULTS ===")
    for k, v in result.items():
        print(f"{k}: '{v}'")
    print("=" * 50)
    
    return result

def clean_text(text: str) -> str:
    """Advanced text cleaning"""
    # OCR corrections
    corrections = {
        'gmai1': 'gmail', 'corn': 'com', 'co rn': 'com', 'c0m': 'com',
        '@gmai1': '@gmail', 'gm ail': 'gmail', 'outl00k': 'outlook',
        'yah00': 'yahoo', 'inb0x': 'inbox', 'rnessage': 'message',
        'cont act': 'contact', 'ph0ne': 'phone', 'm0bile': 'mobile',
        'soiutions': 'solutions', 'technoiogies': 'technologies'
    }
    
    for old, new in corrections.items():
        text = text.replace(old, new)

    # Preserve line breaks for downstream line-based extraction.
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    cleaned_lines: List[str] = []
    for raw_line in text.split('\n'):
        line = raw_line.strip()
        if not line:
            continue
        line = re.sub(r'[\t\f\v]+', ' ', line)
        line = re.sub(r' {2,}', ' ', line)
        line = re.sub(r'([.,;:])\s*', r'\1 ', line)
        cleaned_lines.append(line.strip())

    return '\n'.join(cleaned_lines)

def extract_email(text: str, result: Dict[str, str]):
    """Extract email with high accuracy"""
    # Normalize common OCR spacing issues inside emails
    normalized = text
    normalized = re.sub(r'\s*@\s*', '@', normalized)
    normalized = re.sub(r'\s*\.\s*', '.', normalized)
    normalized = re.sub(r'\s*,\s*', '.', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)

    # Aggressive compact form for OCR that inserts spaces inside emails
    compact = re.sub(r'\s+', '', normalized)
    compact = re.sub(r'\(dot\)|\[dot\]|\{dot\}', '.', compact, flags=re.IGNORECASE)
    compact = re.sub(r'\(at\)|\[at\]|\{at\}', '@', compact, flags=re.IGNORECASE)

    emails = re.findall(EMAIL_PATTERN, normalized, re.IGNORECASE)
    if not emails:
        emails = re.findall(EMAIL_PATTERN, compact, re.IGNORECASE)
    if emails:
        # Choose the most professional email
        professional_domains = ['gmail.com', 'outlook.com', 'yahoo.com', 'hotmail.com']
        for email in emails:
            domain = email.split('@')[-1].lower()
            if any(prof in domain for prof in professional_domains):
                result["Email"] = email.lower()
                print(f"Email found: {email}")
                return
        result["Email"] = emails[0].lower()
        print(f"Email found: {emails[0]}")

def extract_phone(text: str, result: Dict[str, str]):
    """Extract phone with multiple format support"""
    print("\n=== PHONE EXTRACTION ===")
    
    for i, pattern in enumerate(PHONE_PATTERNS):
        matches = re.findall(pattern, text, re.IGNORECASE)
        print(f"Pattern {i+1}: {pattern} -> {matches}")
        
        if matches:
            if isinstance(matches[0], tuple):
                phone = ''.join(matches[0])
            else:
                phone = matches[0]
            
            # Clean and format
            phone = re.sub(r'[^\d+]', '', phone)
            
            if len(phone) >= 10 and len(phone) <= 15:
                if phone.startswith('+'):
                    result["Mobile Number"] = phone
                elif len(phone) == 10:
                    result["Mobile Number"] = f"+91-{phone[:5]}-{phone[5:]}"
                else:
                    result["Mobile Number"] = phone
                
                print(f"Phone extracted: {result['Mobile Number']}")
                return

def extract_website(text: str, result: Dict[str, str]):
    """Extract website information"""
    emails = re.findall(EMAIL_PATTERN, text, re.IGNORECASE)
    email_domains = {e.split('@')[-1].lower() for e in emails}

    # Prefer explicit www/http occurrences to avoid picking domains from emails.
    candidates = re.findall(WEBSITE_PATTERN, text)
    filtered: List[str] = []
    for domain in candidates:
        d = domain.lower().strip('.').strip()
        if not d or '@' in d:
            continue
        # If website domain matches email domain, keep it only when explicitly presented as a website.
        if d in email_domains:
            explicit = bool(re.search(rf'(?i)(?:website|web|www\.|https?://)\s*[:\-]?\s*(?:https?://)?(?:www\.)?{re.escape(d)}', text))
            if not explicit:
                continue
        filtered.append(d)

    if not filtered:
        return

    # Prefer domains that appear next to explicit website markers.
    preferred = None
    for d in filtered:
        if re.search(rf'(?i)(?:website|web|www\.|https?://)\s*[:\-]?\s*(?:https?://)?(?:www\.)?{re.escape(d)}', text):
            preferred = d
            break
    if preferred is None:
        preferred = filtered[0]

    result["Website"] = f"www.{preferred}"
    print(f"Website found: {result['Website']}")

def extract_designation(lines: List[str], result: Dict[str, str]):
    """Extract job designation with ultra-enhanced patterns"""
    print("\n=== DESIGNATION EXTRACTION ===")
    
    # Ultra-enhanced designation patterns - more comprehensive
    designation_keywords = [
        'CEO', 'CTO', 'CFO', 'Director', 'Manager', 'Engineer', 'Developer',
        'Consultant', 'Analyst', 'Specialist', 'Coordinator', 'Administrator',
        'President', 'Vice President', 'VP', 'Founder', 'Co-founder', 'Owner',
        'Partner', 'Associate', 'Senior', 'Junior', 'Sr', 'Jr', 'Dr', 'Prof',
        'Executive', 'Officer', 'Supervisor', 'Team Lead', 'Lead', 'Head',
        'Chief', 'Principal', 'Senior', 'Junior', 'General Manager', 'Assistant', 'Deputy',
        'Sales', 'Marketing', 'Finance', 'HR', 'Operations', 'Technical',
        'Business', 'Product', 'Project', 'Account', 'Regional', 'National',
        'Prop.', 'Proprietor', 'prop', 'owner', 'partner', 'dealer', 'distributor',
        'representative', 'executive', 'consultant', 'advisor', 'expert', 'specialist',
        'manager', 'head', 'lead', 'chief', 'director', 'president', 'founder'
    ]
    
    # Also check for position indicators
    position_indicators = ['position', 'designation', 'title', 'role']
    
    for line in lines:
        line_lower = line.lower()
        line_stripped = line.strip()
        
        print(f"Checking line for designation: '{line_stripped}'")
        
        # Check for designation keywords
        for keyword in designation_keywords:
            if keyword.lower() in line_lower:
                result["Designation"] = line_stripped
                print(f"Designation found (keyword): {line}")
                return
        
        # Check for position indicators
        for indicator in position_indicators:
            if indicator in line_lower:
                # Extract the designation part
                parts = line.split(':')
                if len(parts) > 1:
                    result["Designation"] = parts[1].strip()
                    print(f"Designation found (indicator): {parts[1].strip()}")
                    return
    
    # Fallback: Look for lines that might be designations based on position
    # Usually 2nd or 3rd line after company name
    for i, line in enumerate(lines):
        if i > 0 and i < 4:  # Check 2nd, 3rd, 4th lines
            line_stripped = line.strip()
            if (
                len(line_stripped) > 2
                and len(line_stripped) < 50
                and not any(char.isdigit() for char in line_stripped)
                and not is_contact_info(line_stripped)
                and not is_company_name(line_stripped)
                and not is_person_name(line_stripped)
                and is_designation_line(line_stripped)
            ):
                result["Designation"] = line_stripped
                print(f"Designation found (fallback): {line}")
                return


def extract_company_name(lines: List[str], result: Dict[str, str]):
    """Extract company name with advanced patterns"""
    print("\n=== COMPANY EXTRACTION ===")

    business_name_keywords = [
        'computers', 'computer', 'solutions', 'technology', 'technologies', 'systems', 'services',
        'enterprises', 'enterprise', 'industries', 'industrial', 'traders', 'trading', 'store',
        'suppliers', 'supplier', 'distributors', 'distributor', 'agency', 'agencies', 'marketing'
    ]

    def _looks_like_address_or_place(t: str) -> bool:
        low = t.lower()
        if any(ch.isdigit() for ch in t):
            return True
        if ',' in t:
            return True
        if any(k in low for k in ['street', 'st', 'road', 'rd', 'complex', 'floor', 'phase', 'sector', 'block']):
            return True
        for pat in CITY_PATTERNS:
            if re.search(pat, t, re.IGNORECASE):
                return True
        for pat in AREA_PATTERNS:
            if re.search(pat, t, re.IGNORECASE):
                return True
        return False

    # Strategy -1: Prefer obvious business names (e.g., 'Supreme Computers')
    for line in lines:
        t = line.strip()
        if not t:
            continue
        if is_contact_info(t) or is_website(t):
            continue
        if _looks_like_address_or_place(t):
            continue
        if any(kw in t.lower() for kw in business_name_keywords):
            result["Company Name"] = t
            print(f"Company found via business keyword: {t}")
            return

    legal_markers = [
        'pvt', 'pvt.', 'private', 'ltd', 'ltd.', 'limited', 'llp', 'llp.', 'inc', 'inc.', 'corp', 'corp.',
        'corporation', 'co', 'co.', 'company'
    ]

    # Strategy 0: Legal entity suffixes (PVT/LTD/LLP etc)
    for line in lines:
        t = line.strip()
        if not t:
            continue
        if is_contact_info(t) or is_website(t):
            continue
        low = t.lower()
        if any(re.search(rf'\b{re.escape(m)}\b', low) for m in legal_markers):
            if not is_person_name(t):
                result["Company Name"] = t
                print(f"Company found via legal marker: {t}")
                return

    # Strategy 1: Pattern matching
    for line in lines:
        t = line.strip()
        if not t:
            continue
        if is_contact_info(t) or is_website(t):
            continue
        for pattern in COMPANY_PATTERNS:
            if re.match(pattern, t, re.IGNORECASE):
                if not is_person_name(t):
                    result["Company Name"] = t
                    print(f"Company found via pattern: {t}")
                    return

    # Strategy 2: spaCy ORG entities
    doc = nlp(' '.join(lines))
    for ent in doc.ents:
        if ent.label_ == "ORG" and len(ent.text.split()) <= 6:
            cand = ent.text.strip()
            if cand and not is_contact_info(cand) and not is_website(cand) and not is_person_name(cand):
                result["Company Name"] = cand
                print(f"Company found via spaCy: {cand}")
                return


def extract_card_holder(lines: List[str], result: Dict[str, str]):
    """Extract person name with high accuracy"""
    print("\n=== CARD HOLDER EXTRACTION ===")
    company = (result.get("Company Name") or "").strip().lower()

    for line in lines:
        t = line.strip()
        if not t:
            continue
        if t.lower() == company:
            continue
        if is_contact_info(t) or is_designation_line(t) or is_company_name(t) or is_website(t):
            continue
        for pattern in PERSON_PATTERNS:
            if re.match(pattern, t):
                result["Card Holder"] = t
                print(f"Card holder found via pattern: {t}")
                return

    doc = nlp(' '.join(lines))
    for ent in doc.ents:
        if ent.label_ == "PERSON" and len(ent.text.split()) <= 4:
            cand = ent.text.strip()
            if cand and cand.lower() != company and not is_contact_info(cand) and not is_designation_line(cand):
                result["Card Holder"] = cand
                print(f"Card holder found via spaCy: {cand}")
                return


def extract_address_components(lines: List[str], result: Dict[str, str]):
    """Extract address components: Area, City, State, Pincode"""
    print("\n=== ADDRESS COMPONENTS EXTRACTION ===")
    text = ' '.join(lines)

    for pattern in PINCODE_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            pin = matches[0][0] if isinstance(matches[0], tuple) else matches[0]
            result["Pincode"] = re.sub(r'\s+', '', str(pin))
            break

    for pattern in CITY_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            result["City"] = matches[0]
            break

    for pattern in STATE_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            result["State"] = matches[0]
            break

    for line in lines:
        t = line.strip()
        if not t:
            continue
        if is_contact_info(t) or is_website(t):
            continue
        for pattern in AREA_PATTERNS:
            if re.search(pattern, t, re.IGNORECASE):
                area = re.sub(r',.*$', '', t)
                area = re.sub(r'\b\d{6}\b', '', area).strip()
                if 2 < len(area) < 60:
                    result["Area"] = area
                    return


def extract_full_address(lines: List[str], result: Dict[str, str]):
    """Extract full address information"""
    print("\n=== FULL ADDRESS EXTRACTION ===")
    for line in lines:
        t = line.strip()
        if not t:
            continue
        if is_contact_info(t) or is_website(t):
            continue
        for pattern in ADDRESS_PATTERNS:
            if re.match(pattern, t, re.IGNORECASE):
                if not is_company_name(t) and not is_person_name(t):
                    result["Address"] = t
                    return


def extract_services(lines: List[str], result: Dict[str, str]):
    """Extract services and products"""
    services: List[str] = []
    for line in lines:
        t = line.strip()
        if not t or t in result.values():
            continue
        low = t.lower()
        if any(k in low for k in ['deal in', 'we deal', 'manufacturer', 'supplier', 'distributor', 'dealer', 'services', 'products']):
            if not is_contact_info(t) and not is_website(t):
                services.append(t)
    result["Services/Products"] = " | ".join(services)


def extract_other_info(lines: List[str], result: Dict[str, str]):
    """Collect remaining information"""
    other: List[str] = []
    for line in lines:
        t = line.strip()
        if not t or t in result.values() or len(t) <= 2:
            continue
        other.append(t)
    result["Other Info"] = " | ".join(other)


def auto_correct_result(text: str, lines: List[str], result: Dict[str, str]):
    normalized = text
    normalized = re.sub(r'\s*@\s*', '@', normalized)
    normalized = re.sub(r'\s*\.\s*', '.', normalized)
    normalized = re.sub(r'\s*,\s*', '.', normalized)

    # Force Email whenever we see an email-like token
    emails = re.findall(EMAIL_PATTERN, normalized, re.IGNORECASE)
    if not emails:
        emails = re.findall(EMAIL_PATTERN, re.sub(r'\s+', '', normalized), re.IGNORECASE)
    if emails:
        result["Email"] = emails[0].lower()

    # Extra safety: any line containing '@' should yield an email after compaction.
    if not (result.get("Email") or "").strip():
        for line in lines:
            if '@' not in line:
                continue
            c = re.sub(r'\s+', '', line)
            c = re.sub(r',', '.', c)
            c = re.sub(r'\(at\)|\[at\]|\{at\}', '@', c, flags=re.IGNORECASE)
            c = re.sub(r'\(dot\)|\[dot\]|\{dot\}', '.', c, flags=re.IGNORECASE)
            m = re.search(EMAIL_PATTERN, c, re.IGNORECASE)
            if m:
                result["Email"] = m.group(0).lower()
                break

    # Force Website whenever we see www/http/.tld (also handles OCR missing dots like 'www foxindia net')
    domains: List[str] = []
    spaced_www = re.compile(r'(?i)\bwww\s*\.?\s*([a-z0-9][a-z0-9-]{1,})\s*\.?\s*([a-z]{2,})\b')
    for line in lines:
        raw = line.strip()
        if not raw:
            continue
        compact_line = re.sub(r'\s+', '', raw)

        m2 = spaced_www.search(raw)
        if m2:
            domains.append(f"{m2.group(1).lower()}.{m2.group(2).lower()}".strip('.'))
            continue

        if is_website(compact_line):
            m = re.search(WEBSITE_PATTERN, compact_line)
            if m:
                domains.append(m.group(1).lower().strip('.'))

    if domains:
        result["Website"] = f"www.{domains[0]}"

    # Move misplacements out of company/name/designation/etc
    for key in ["Company Name", "Card Holder", "Designation", "Area", "Address", "Other Info"]:
        val = (result.get(key) or "").strip()
        if not val:
            continue
        compact_val = re.sub(r'\s+', '', val)
        if '@' in compact_val:
            m = re.search(EMAIL_PATTERN, compact_val, re.IGNORECASE)
            if m:
                result["Email"] = m.group(0).lower()
                result[key] = ""
                continue
        if is_website(compact_val):
            m = re.search(WEBSITE_PATTERN, compact_val)
            if m:
                result["Website"] = f"www.{m.group(1).lower().strip('.')}"
                result[key] = ""

    # Company should never be a website
    if (result.get("Company Name") or "").strip() and is_website(result["Company Name"]):
        result["Company Name"] = ""


def is_person_name(text: str) -> bool:
    return any(re.match(pattern, text.strip()) for pattern in PERSON_PATTERNS)


def is_company_name(text: str) -> bool:
    return any(re.match(pattern, text.strip(), re.IGNORECASE) for pattern in COMPANY_PATTERNS)


def is_contact_info(text: str) -> bool:
    t = text.strip()
    if not t:
        return False
    t_compact = re.sub(r'\s+', '', t)
    return bool(
        re.search(EMAIL_PATTERN, t_compact, re.IGNORECASE)
        or re.match(r'\+?\d', t_compact)
        or is_website(t_compact)
    )


def is_website(text: str) -> bool:
    t = text.strip()
    if not t:
        return False
    t_compact = re.sub(r'\s+', '', t)
    if '@' in t_compact:
        return False
    if t_compact.lower().startswith('www'):
        return True
    if re.search(r'(?i)\bhttps?://', t_compact) or re.search(r'(?i)\bwww\.', t_compact):
        return True
    return bool(re.search(r'(?i)\.[a-z]{2,}(?:/|$)', t_compact))


def is_designation_line(text: str) -> bool:
    t = text.strip()
    if not t:
        return False
    return any(re.match(pat, t, re.IGNORECASE) for pat in DESIGNATION_PATTERNS) or any(
        kw in t.lower() for kw in [
            'sales', 'manager', 'engineer', 'director', 'executive', 'officer', 'lead', 'head',
            'asst', 'assistant', 'sr', 'jr', 'marketing',
            'authorised stockist', 'authorized stockist', 'stockist', 'distributor', 'dealer', 'reseller',
            'partner'
        ]
    )
