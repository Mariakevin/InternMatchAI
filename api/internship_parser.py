import re
from typing import Optional

from api.models import (
    EligibilityCondition,
    InternshipDetail,
    RiskIndicator,
    WorkMode,
)
from api.taxonomy import (
    SKILL_ALIASES,
    normalize_currency,
    normalize_degree,
    normalize_discipline,
)


AMBIGUOUS_SKILL_ALIASES = {
    "go",
    "express",
    "react",
    "node",
    "ts",
    "ml",
    "py",
    "js",
    "r",
}
PREF_EXPLICIT_LINE_PATTERN = re.compile(
    r"(?i)\b(?:preferred|nice\s+to\s+have|bonus|good\s+to\s+have|plus|desired)\b"
)
REQ_EXPLICIT_LINE_PATTERN = re.compile(
    r"(?i)\b(?:required|requirements?|qualifications?|must\s+have|skills?|"
    r"technologies|tech\s+stack|stack|tools?)\b"
)


def extract_skills_from_text(text: str) -> tuple[list[str], list[str]]:
    """
    Returns (required_skills, preferred_skills) normalized.

    Short aliases that are also ordinary English words are only trusted inside
    explicit skill blocks/lines so prose such as "go through onboarding" is not
    mistaken for a requirement.
    """
    required: set[str] = set()
    preferred: set[str] = set()

    pref_patterns = [
        r"(?i)(?:preferred|nice to have|bonus|good to have|plus|desired)[:\n](.*?)(?=\n[A-Z][a-z]+|\Z)",
    ]
    req_patterns = [
        r"(?i)(?:required|qualifications|must have|requirements|skills)[:\n](.*?)(?=\n[A-Z][a-z]+|\Z)",
    ]

    pref_block = ""
    for pat in pref_patterns:
        m = re.search(pat, text, re.DOTALL)
        if m:
            pref_block += " " + m.group(1)

    req_block = ""
    for pat in req_patterns:
        m = re.search(pat, text, re.DOTALL)
        if m:
            req_block += " " + m.group(1)

    pref_lines = "\n".join(
        line for line in text.splitlines() if PREF_EXPLICIT_LINE_PATTERN.search(line)
    )
    req_lines = "\n".join(
        line for line in text.splitlines() if REQ_EXPLICIT_LINE_PATTERN.search(line)
    )

    norm_text = text.casefold()
    pref_norm = pref_block.casefold()
    req_norm = req_block.casefold()
    pref_explicit_norm = pref_lines.casefold()
    req_explicit_norm = req_lines.casefold()
    explicit_norm = "\n".join((pref_block, req_block, pref_lines, req_lines)).casefold()

    for alias, canonical in SKILL_ALIASES.items():
        alias_norm = alias.casefold()
        pattern = rf"(?<!\w){re.escape(alias_norm)}(?!\w)"
        is_ambiguous = alias_norm in AMBIGUOUS_SKILL_ALIASES
        search_text = explicit_norm if is_ambiguous else norm_text
        if not re.search(pattern, search_text):
            continue

        if pref_norm and re.search(pattern, pref_norm):
            preferred.add(canonical)
        elif req_norm and re.search(pattern, req_norm):
            required.add(canonical)
        elif is_ambiguous:
            if pref_explicit_norm and re.search(pattern, pref_explicit_norm):
                preferred.add(canonical)
            elif req_explicit_norm and re.search(pattern, req_explicit_norm):
                required.add(canonical)
        else:
            sent_match = re.search(
                rf"([^.!?\n]*?{re.escape(alias_norm)}[^.!?\n]*)", norm_text
            )
            sentence = sent_match.group(1) if sent_match else ""
            if any(
                w in sentence
                for w in ("preferred", "plus", "bonus", "nice to have", "good to have")
            ):
                preferred.add(canonical)
            else:
                required.add(canonical)

    for skill in required:
        preferred.discard(skill)

    return sorted(list(required)), sorted(list(preferred))


def _first_non_negated(pattern: str, text: str) -> Optional[re.Match[str]]:
    for match in re.finditer(pattern, text):
        prefix = text[max(0, match.start() - 25) : match.start()]
        if not re.search(r"(?i)\b(?:not|no|never|without)\b", prefix):
            return match
    return None


def _mode_from_fragment(fragment: str) -> WorkMode:
    lower = fragment.casefold()

    hybrid_match = _first_non_negated(r"\bhybrid\b", lower)
    remote_match = _first_non_negated(r"\b(?:remote|work from home|wfh)\b", lower)
    onsite_match = _first_non_negated(
        r"\b(?:on-?site|in-?office|at office|office)\b", lower
    )

    if hybrid_match:
        return WorkMode.HYBRID
    if remote_match and onsite_match:
        # Both mentioned: the keyword appearing first describes the primary mode.
        return (
            WorkMode.REMOTE
            if remote_match.start() < onsite_match.start()
            else WorkMode.ONSITE
        )
    if remote_match:
        return WorkMode.REMOTE
    if onsite_match:
        return WorkMode.ONSITE
    return WorkMode.ANY


def extract_work_mode(text: str) -> tuple[WorkMode, str]:
    # An explicit "Work mode:"/"Mode:" label is authoritative over prose mentions.
    explicit_match = re.search(r"(?im)\b(?:work\s+mode|mode)\s*[:=]\s*([^\n.;]+)", text)
    mode = (
        _mode_from_fragment(explicit_match.group(1)) if explicit_match else WorkMode.ANY
    )
    if mode == WorkMode.ANY:
        mode = _mode_from_fragment(text)

    is_remote = mode == WorkMode.REMOTE

    location = ""
    loc_match = re.search(
        r"\b(?:location|city|based in|stationed at|office in)\s*[:=]?\s*([A-Za-z\s,]+?)(?=[.\n;]|\b(?:mode|stipend|duration)\b)",
        text,
        re.IGNORECASE,
    )
    if loc_match:
        location = loc_match.group(1).strip()
    elif not is_remote:
        city_match = re.search(
            r"\b(Bangalore|Bengaluru|Mumbai|Delhi|Hyderabad|Pune|Chennai|New York|San Francisco|London|Seattle|Austin)\b",
            text,
            re.IGNORECASE,
        )
        if city_match:
            location = city_match.group(1)

    return mode, location


MONEY_PATTERN = re.compile(
    r"(?:(?P<cur1>\$|₹|€|£|\brs\.?|\binr\b|\busd\b|\beur\b|\bgbp\b|\bpounds?\b)\s*"
    r"(?P<amt1>[0-9][0-9,]*(?:\.[0-9]+)?)"
    r"|(?P<amt2>[0-9][0-9,]*(?:\.[0-9]+)?)\s*"
    r"(?P<cur2>inr|usd|eur|rupees|gbp|pounds?))"
    r"\s*(?:(?:per|/|-)\s*(?P<period>month|mo|week|wk|hour|hr|year|yr|total|lump\s+sum)"
    r"|(?P<period_bare>total|lump\s+sum))?",
    re.IGNORECASE,
)
EXCLUDED_STIPEND_CONTEXT = re.compile(
    r"(?i)\b(?:fee|deposit|registration|application|processing|"
    r"training|security|equipment|insurance)\b"
)


def extract_stipend_and_compensation(
    text: str,
) -> tuple[Optional[float], str, str, bool, bool, list[str]]:
    lower = text.casefold()
    contradictions: list[str] = []

    is_unpaid = bool(
        re.search(
            r"\b(?:unpaid|non-?paid|volunteer|no stipend|without stipend|0 stipend)\b",
            lower,
        )
    )

    money_matches = list(MONEY_PATTERN.finditer(text))

    amount: Optional[float] = None
    currency = "USD"
    period = "monthly"
    disclosed = False
    amounts_found: list[tuple[float, str]] = []

    for m in money_matches:
        cur1 = m.group("cur1")
        amt1 = m.group("amt1")
        amt2 = m.group("amt2")
        cur2 = m.group("cur2")
        prd = m.group("period") or m.group("period_bare")
        amt_str = (amt1 or amt2 or "").replace(",", "")
        if not amt_str:
            continue
        try:
            val = float(amt_str)
        except ValueError:
            continue

        # Fee/deposit/training amounts are costs, never stipends. Restrict the
        # exclusion check to the current clause so a nearby fee does not mask a
        # legitimate stipend in the next sentence.
        prefix = text[max(0, m.start() - 40) : m.start()]
        clause_start = max(prefix.rfind("."), prefix.rfind(";"), prefix.rfind("\\n"))
        if clause_start >= 0:
            prefix = prefix[clause_start + 1 :]
        if EXCLUDED_STIPEND_CONTEXT.search(prefix):
            continue

        if not (cur1 or cur2):
            # A bare number is ambiguous; only 1900-2100 could be a year and is
            # never treated as a stipend amount.
            continue

        cur = normalize_currency(cur1 or cur2 or "USD")

        p_raw = (prd or "month").lower()
        if "hr" in p_raw or "hour" in p_raw:
            p = "hourly"
        elif "wk" in p_raw or "week" in p_raw:
            p = "weekly"
        elif "yr" in p_raw or "year" in p_raw:
            p = "yearly"
        elif "total" in p_raw or "lump" in p_raw:
            p = "total"
        else:
            p = "monthly"

        amounts_found.append((val, f"{cur} {val} / {p}"))
        if amount is None:
            amount = val
            currency = cur
            period = p
            disclosed = True

    if is_unpaid and amount is not None and amount > 0:
        contradictions.append(
            f"Listing states both 'unpaid' and specifies a stipend of {currency} {amount}."
        )

    if len(set(a[1] for a in amounts_found)) > 1:
        details = ", ".join(sorted(set(a[1] for a in amounts_found)))
        contradictions.append(
            f"Multiple inconsistent stipend amounts mentioned: {details}"
        )

    if not is_unpaid and amount is None:
        disclosed = False

    return amount, currency, period, disclosed, is_unpaid, contradictions


def extract_duration_and_hours(
    text: str,
) -> tuple[Optional[int], Optional[int], list[str]]:
    contradictions: list[str] = []

    duration_matches = list(
        re.finditer(
            r"\b([0-9]+)\s*(?:-|to)?\s*([0-9]+)?\s*(month|months|mo|weeks|wks)\b",
            text,
            re.IGNORECASE,
        )
    )
    duration_months: Optional[int] = None
    durations_found: list[int] = []

    for m in duration_matches:
        d1, d2, unit = m.groups()
        val = int(d1)
        if "week" in unit.lower():
            val = max(1, round(val / 4.0))
        durations_found.append(val)
        if duration_months is None:
            duration_months = val

    if len(set(durations_found)) > 1:
        contradictions.append(
            f"Inconsistent duration terms found in posting: {durations_found} months."
        )

    hours_match = re.search(
        r"\b([0-9]{1,2})\s*(?:-|to)?\s*([0-9]{1,2})?\s*(?:hours|hrs)\s*"
        r"(?:/|per|a|each)\s*(?:week|wk)\b",
        text,
        re.IGNORECASE,
    )
    weekly_hours: Optional[int] = None
    if hours_match:
        weekly_hours = int(hours_match.group(2) or hours_match.group(1))

    return duration_months, weekly_hours, contradictions


def extract_formal_eligibility_conditions(text: str) -> list[EligibilityCondition]:
    conditions: list[EligibilityCondition] = []

    # 1. Degree conditions
    KNOWN_DEGREES = [
        (
            "B.Tech",
            r"\b(?:B\.?Tech|B\.?E\.?|Bachelor of Technology|Bachelor of Engineering)\b",
        ),
        ("BCA", r"\b(?:BCA|Bachelor of Computer Applications)\b"),
        ("B.Sc", r"\b(?:B\.?Sc|B\.?S\.?|Bachelor of Science)\b"),
        (
            "M.Tech",
            r"\b(?:M\.?Tech|M\.?E\.?|Master of Technology|Master of Engineering)\b",
        ),
        ("MCA", r"\b(?:MCA|Master of Computer Applications)\b"),
        ("M.Sc", r"\b(?:M\.?Sc|M\.?S\.?|Master of Science)\b"),
        ("MBA", r"\b(?:MBA|Master of Business Administration)\b"),
        ("PhD", r"\b(?:Ph\.?D|Doctorate)\b"),
        ("Diploma", r"\b(?:Diploma)\b"),
    ]

    # Look for degree/qualification statements
    deg_stmt_match = re.search(
        r"(?i)\b(?:degree|qualification|qualifications|eligibility|education|course|courses)\s*[:=]?\s*([^\n;]+)",
        text,
    )
    if deg_stmt_match:
        clause = deg_stmt_match.group(1)
        found_degrees: list[str] = []
        for canonical, pattern in KNOWN_DEGREES:
            if re.search(pattern, clause, re.IGNORECASE):
                norm = normalize_degree(canonical)
                if norm not in found_degrees:
                    found_degrees.append(norm)

        # Check if "only" or "mandatory" is present
        is_only = bool(re.search(r"\b(?:only|mandatory)\b", clause, re.IGNORECASE))

        if len(found_degrees) > 1:
            conditions.append(
                EligibilityCondition(
                    condition_id=f"cond_{len(conditions) + 1}",
                    condition_type="degree",
                    operator="in",
                    value=found_degrees,
                    logic_group="degree_req",
                    is_mandatory=True,
                    original_text=deg_stmt_match.group(0),
                    source_reference="Degree requirement clause",
                    extraction_confidence=0.95,
                )
            )
        elif len(found_degrees) == 1:
            conditions.append(
                EligibilityCondition(
                    condition_id=f"cond_{len(conditions) + 1}",
                    condition_type="degree",
                    operator="==",
                    value=found_degrees[0],
                    logic_group="degree_req",
                    is_mandatory=True,
                    original_text=deg_stmt_match.group(0),
                    source_reference="Degree requirement clause",
                    extraction_confidence=1.0 if is_only else 0.9,
                )
            )
    else:
        # Check if a single degree + only appears anywhere, e.g. "B.Tech only"
        only_match = re.search(
            r"\b(B\.?Tech|B\.?E\.?|BCA|B\.?Sc|M\.?Tech|MCA)\s+(?:only|mandatory)\b",
            text,
            re.IGNORECASE,
        )
        if only_match:
            deg = normalize_degree(only_match.group(1))
            conditions.append(
                EligibilityCondition(
                    condition_id=f"cond_{len(conditions) + 1}",
                    condition_type="degree",
                    operator="==",
                    value=deg,
                    logic_group="degree_req",
                    is_mandatory=True,
                    original_text=only_match.group(0),
                    source_reference="Degree clause",
                    extraction_confidence=1.0,
                )
            )

    # 2. Level conditions (e.g. "postgraduate student", "enrolled postgraduate")
    pg_match = re.search(
        r"\b(?:enrolled\s+)?(postgraduate|post-graduate|masters?|graduate student)\b",
        text,
        re.IGNORECASE,
    )
    if pg_match:
        conditions.append(
            EligibilityCondition(
                condition_id=f"cond_{len(conditions) + 1}",
                condition_type="level",
                operator="==",
                value="postgraduate",
                logic_group="level_req",
                is_mandatory=True,
                original_text=pg_match.group(0),
                source_reference="Academic level requirement",
                extraction_confidence=0.95,
            )
        )

    # 3. Enrolment status
    enrolment_match = re.search(
        r"\b(currently enrolled|currently pursuing|must be enrolled|current student)\b",
        text,
        re.IGNORECASE,
    )
    if enrolment_match:
        conditions.append(
            EligibilityCondition(
                condition_id=f"cond_{len(conditions) + 1}",
                condition_type="enrolment",
                operator="==",
                value="enrolled",
                logic_group="enrolment_req",
                is_mandatory=True,
                original_text=enrolment_match.group(0),
                source_reference="Enrolment clause",
                extraction_confidence=1.0,
            )
        )

    # 4. Discipline conditions (e.g. "Computer Science or IT", "B.Tech in CS").
    # "in" alone is too broad (matches "assist in building it"), so only use it
    # when it follows a degree token.
    disc_match = re.search(
        r"(?i)\b(?:branch|discipline|major|stream)\s*[:=]?\s*([^\n.;]+)",
        text,
    )
    if not disc_match:
        disc_match = re.search(
            r"(?i)\b(?:degree|bachelor(?:'s)?|master(?:'s)?|b\.?tech|bca|m\.?tech|mca|b\.?sc|m\.?sc)\b[^\n.;]*?\bin\s+([^\n.;]+)",
            text,
        )
    if disc_match:
        raw_disc = disc_match.group(1)
        found_discs: list[str] = []
        for disc, pat in [
            ("Computer Science", r"(?i)\b(?:Computer Science|CS|CSE)\b"),
            ("Information Technology", r"\b(?:Information Technology)\b|\bIT\b"),
            ("Data Science", r"(?i)\b(?:Data Science|AI|Artificial Intelligence)\b"),
            ("Electronics and Communication", r"(?i)\b(?:Electronics|ECE)\b"),
            ("Electrical Engineering", r"(?i)\b(?:Electrical|EEE)\b"),
            ("Mechanical Engineering", r"(?i)\b(?:Mechanical)\b"),
            ("Civil Engineering", r"(?i)\b(?:Civil)\b"),
        ]:
            if disc == "Information Technology":
                matched = bool(
                    re.search(r"(?i)\bInformation Technology\b", raw_disc)
                    or re.search(r"\bIT\b", raw_disc)
                )
            else:
                matched = bool(re.search(pat, raw_disc))
            if matched:
                norm = normalize_discipline(disc)
                if norm not in found_discs:
                    found_discs.append(norm)

        if found_discs:
            conditions.append(
                EligibilityCondition(
                    condition_id=f"cond_{len(conditions) + 1}",
                    condition_type="discipline",
                    operator="in" if len(found_discs) > 1 else "==",
                    value=found_discs if len(found_discs) > 1 else found_discs[0],
                    logic_group="discipline_req",
                    is_mandatory=True,
                    original_text=disc_match.group(0),
                    source_reference="Discipline clause",
                    extraction_confidence=0.9,
                )
            )

    # 5. Marks / CGPA conditions
    marks_match = re.search(
        r"\b(?:minimum\s+)?(?:cgpa|gpa|aggregate|marks|percentage)\s*(?:of|:|>=|at least)?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:/\s*([0-9]+(?:\.[0-9]+)?)|%)?",
        text,
        re.IGNORECASE,
    )
    if marks_match:
        val = float(marks_match.group(1))
        scale_grp = marks_match.group(2)
        scale = (
            float(scale_grp)
            if scale_grp
            else (4.0 if val <= 4.0 else (10.0 if val <= 10.0 else 100.0))
        )
        conditions.append(
            EligibilityCondition(
                condition_id=f"cond_{len(conditions) + 1}",
                condition_type="marks",
                operator=">=",
                value={"min_value": val, "scale": scale},
                logic_group="marks_req",
                is_mandatory=True,
                original_text=marks_match.group(0),
                source_reference="Academic marks requirement",
                extraction_confidence=1.0,
            )
        )

    # 6. Graduation window conditions (e.g. "Graduating between 2024 and 2026", "Batch of 2025")
    grad_range_match = re.search(
        r"\b(?:graduating|graduation|batch)\s*(?:between|from|in)?\s*(20[2-3][0-9])\s*(?:and|to|-)\s*(20[2-3][0-9])\b",
        text,
        re.IGNORECASE,
    )
    if grad_range_match:
        start_yr = int(grad_range_match.group(1))
        end_yr = int(grad_range_match.group(2))
        conditions.append(
            EligibilityCondition(
                condition_id=f"cond_{len(conditions) + 1}",
                condition_type="graduation_date",
                operator="between",
                value=[start_yr, end_yr],
                logic_group="grad_req",
                is_mandatory=True,
                original_text=grad_range_match.group(0),
                source_reference="Graduation window clause",
                extraction_confidence=1.0,
            )
        )
    else:
        grad_single_match = re.search(
            r"\b(?:batch of|graduating in)\s*(20[2-3][0-9])\b",
            text,
            re.IGNORECASE,
        )
        if grad_single_match:
            yr = int(grad_single_match.group(1))
            conditions.append(
                EligibilityCondition(
                    condition_id=f"cond_{len(conditions) + 1}",
                    condition_type="graduation_date",
                    operator="==",
                    value=yr,
                    logic_group="grad_req",
                    is_mandatory=True,
                    original_text=grad_single_match.group(0),
                    source_reference="Graduation year clause",
                    extraction_confidence=1.0,
                )
            )

    # 7. Year / Semester conditions (e.g. "3rd year or 4th year students", "minimum 5th semester")
    sem_match = re.search(
        r"\b(?:minimum\s+)?([1-8])(?:st|nd|rd|th)?\s*(?:semester|sem)\b",
        text,
        re.IGNORECASE,
    )
    if not sem_match:
        sem_match = re.search(
            r"\b(?:semester|sem)\s*[:=]?\s*([1-8])\b",
            text,
            re.IGNORECASE,
        )
    if sem_match:
        num = int(sem_match.group(1))
        conditions.append(
            EligibilityCondition(
                condition_id=f"cond_{len(conditions) + 1}",
                condition_type="semester",
                operator=">=",
                value=num,
                logic_group="sem_req",
                is_mandatory=True,
                original_text=sem_match.group(0),
                source_reference="Academic semester requirement",
                extraction_confidence=0.9,
            )
        )

    # Academic year context only: an ordinal year, "students in 3rd year", or
    # "year of study". A bare "2 year contract" is not an academic condition.
    year_context_patterns = (
        r"\b([1-4])(?:st|nd|rd|th)\s+year\b",
        r"\b(?:student|students)\s+in\s+(?:the\s+)?([1-4])(?:st|nd|rd|th)?\s+year\b",
        r"\byear\s+of\s+study\s*[:=]?\s*([1-4])\b",
    )
    year_exclude = re.compile(r"(?i)\b(?:contract|program|programme|duration)\b")

    yr_match = None
    for pattern in year_context_patterns:
        candidate = re.search(pattern, text, re.IGNORECASE)
        if candidate and not year_exclude.search(
            text[candidate.end() : candidate.end() + 20]
        ):
            yr_match = candidate
            break

    if yr_match and not sem_match:
        num = int(yr_match.group(1))
        conditions.append(
            EligibilityCondition(
                condition_id=f"cond_{len(conditions) + 1}",
                condition_type="year",
                operator=">=",
                value=num,
                logic_group="year_req",
                is_mandatory=True,
                original_text=yr_match.group(0),
                source_reference="Academic year requirement",
                extraction_confidence=0.9,
            )
        )

    return conditions


NEGATION_PATTERN = re.compile(r"(?i)\b(?:no|not|never|without|zero)\b")
FEE_BLOCK_PATTERN = re.compile(
    r"([^.!?\n]*?\b(?:application\s+fee|registration\s+fee|fee\s+to\s+apply|"
    r"exam\s+fee|processing\s+fee|pay\s+to\s+apply)\b[^.!?\n]*)",
    re.IGNORECASE,
)
FEE_KEYWORD_PATTERN = re.compile(
    r"(?i)\b(?:application\s+fee|registration\s+fee|fee\s+to\s+apply|"
    r"exam\s+fee|processing\s+fee|pay\s+to\s+apply)\b"
)
DEPOSIT_BLOCK_PATTERN = re.compile(
    r"([^.!?\n]*?\b(?:security\s+deposit|refundable\s+deposit|"
    r"equipment\s+deposit|laptop\s+fee|deposit\s+required)\b[^.!?\n]*)",
    re.IGNORECASE,
)
DEPOSIT_KEYWORD_PATTERN = re.compile(
    r"(?i)\b(?:security\s+deposit|refundable\s+deposit|equipment\s+deposit|"
    r"laptop\s+fee|deposit\s+required)\b"
)
TRAINING_BLOCK_PATTERN = re.compile(
    r"([^.!?\n]*?\b(?:paid\s+training|training\s+fee|"
    r"must\s+purchase\s+training|training\s+charges)\b[^.!?\n]*)",
    re.IGNORECASE,
)
TRAINING_KEYWORD_PATTERN = re.compile(
    r"(?i)\b(?:paid\s+training|training\s+fee|must\s+purchase\s+training|"
    r"training\s+charges)\b"
)


def _is_negated_before(text: str, position: int) -> bool:
    prefix = text[max(0, position - 30) : position]
    return bool(NEGATION_PATTERN.search(prefix))


def _first_active_excerpt(
    block_pattern: re.Pattern[str],
    keyword_pattern: re.Pattern[str],
    text: str,
) -> Optional[str]:
    for match in block_pattern.finditer(text):
        excerpt = match.group(1).strip()
        keyword = keyword_pattern.search(excerpt)
        if keyword is None:
            continue
        if _is_negated_before(excerpt, keyword.start()):
            continue
        return excerpt
    return None


def analyze_listing_risks(text: str) -> list[RiskIndicator]:
    indicators: list[RiskIndicator] = []

    # 1. Application / Registration Fee
    fee_excerpt = _first_active_excerpt(FEE_BLOCK_PATTERN, FEE_KEYWORD_PATTERN, text)
    if fee_excerpt:
        indicators.append(
            RiskIndicator(
                category="application_fee",
                severity="warning",
                title="Application fee requested",
                excerpt=fee_excerpt,
                explanation="Legitimate internships rarely charge an application or registration fee. Review carefully before making any payment.",
            )
        )

    # 2. Security deposit / Equipment fee
    deposit_excerpt = _first_active_excerpt(
        DEPOSIT_BLOCK_PATTERN, DEPOSIT_KEYWORD_PATTERN, text
    )
    if deposit_excerpt:
        indicators.append(
            RiskIndicator(
                category="security_deposit",
                severity="warning",
                title="Security deposit requested",
                excerpt=deposit_excerpt,
                explanation="Requiring a deposit or equipment payment prior to starting an internship is a common warning sign.",
            )
        )

    # 3. Paid training condition
    training_excerpt = _first_active_excerpt(
        TRAINING_BLOCK_PATTERN, TRAINING_KEYWORD_PATTERN, text
    )
    if training_excerpt:
        indicators.append(
            RiskIndicator(
                category="paid_training",
                severity="warning",
                title="Paid training condition",
                excerpt=training_excerpt,
                explanation="Internships that condition placement on purchasing a paid training course warrant careful scrutiny.",
            )
        )

    # 4. Guaranteed selection / 100% job placement claims
    guarantee_match = re.search(
        r"([^.!?\n]*?\b(?:100%\s+guaranteed|guaranteed\s+selection|guaranteed\s+job|direct\s+selection\s+without\s+interview)\b[^.!?\n]*)",
        text,
        re.IGNORECASE,
    )
    if guarantee_match:
        indicators.append(
            RiskIndicator(
                category="guaranteed_job",
                severity="review_carefully",
                title="Unconditional selection claim",
                excerpt=guarantee_match.group(1).strip(),
                explanation="Claims of guaranteed job placement or selection without evaluation can be unrealistic marketing claims.",
            )
        )

    # 5. Premature sensitive data requests
    sensitive_match = re.search(
        r"([^.!?\n]*?\b(?:bank\s+account\s+details|ssn|social\s+security\s+number|passport\s+copy|aadhaar\s+card|net\s+banking)\b[^.!?\n]*)",
        text,
        re.IGNORECASE,
    )
    if sensitive_match:
        indicators.append(
            RiskIndicator(
                category="early_sensitive_data",
                severity="warning",
                title="Premature sensitive data requested",
                excerpt=sensitive_match.group(1).strip(),
                explanation="Requesting bank account details or official identity documents in the initial description is unusual before an official offer.",
            )
        )

    # 6. Vague identity or missing responsibilities. Only flag genuinely empty
    # postings; short listings that still carry extractable facts are legitimate.
    if len(text.strip()) < 100:
        required_skills, preferred_skills = extract_skills_from_text(text)
        conditions = extract_formal_eligibility_conditions(text)
        (
            stipend_amount,
            _currency,
            _period,
            _disclosed,
            is_unpaid,
            _contradictions,
        ) = extract_stipend_and_compensation(text)
        work_mode, _location = extract_work_mode(text)
        has_extractable_facts = bool(
            required_skills
            or preferred_skills
            or conditions
            or stipend_amount is not None
            or is_unpaid
            or work_mode != WorkMode.ANY
        )
        if not has_extractable_facts:
            indicators.append(
                RiskIndicator(
                    category="vague_identity",
                    severity="notice",
                    title="Brief or vague description",
                    excerpt=text[:100] + "...",
                    explanation="The listing contains very few details about duties, qualifications, or employer background.",
                )
            )

    return indicators


def parse_internship(
    title: str,
    description: str,
    company: str = "",
    source_url: Optional[str] = None,
    internship_id: str = "0",
) -> InternshipDetail:
    work_mode, location = extract_work_mode(description)
    (
        stipend_amount,
        stipend_currency,
        stipend_period,
        stipend_disclosed,
        is_unpaid,
        stipend_contradictions,
    ) = extract_stipend_and_compensation(description)
    duration_months, weekly_hours, duration_contradictions = extract_duration_and_hours(
        description
    )
    conditions = extract_formal_eligibility_conditions(description)
    required_skills, preferred_skills = extract_skills_from_text(description)

    contradictions = stipend_contradictions + duration_contradictions

    return InternshipDetail(
        id=internship_id,
        title=title.strip() or "Internship Position",
        company=company.strip() or "Organization Not Specified",
        source_url=source_url,
        description=description.strip(),
        domain="",
        responsibilities=[],
        work_mode=work_mode,
        location=location,
        duration_months=duration_months,
        weekly_hours=weekly_hours,
        stipend_amount=stipend_amount,
        stipend_currency=stipend_currency,
        stipend_period=stipend_period,
        stipend_disclosed=stipend_disclosed,
        is_unpaid=is_unpaid,
        eligibility_conditions=conditions,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        tools_and_tech=[],
        has_contradictions=bool(contradictions),
        contradiction_details=contradictions,
    )
