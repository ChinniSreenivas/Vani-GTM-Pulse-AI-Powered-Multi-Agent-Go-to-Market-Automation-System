"""Vani-specific four-agent GTM workflow.

The app deliberately drafts outreach only. Public search results are evidence candidates,
not proof of buying intent; a human must verify sources and approve any outreach.
"""
from datetime import datetime, timezone
import asyncio
import re
from urllib.parse import urlparse

from .context_client import search_web


VANI_POSITIONING = (
    "Vani helps organizations build communication fitness through personalized "
    "practice, AI-supported feedback, and coaching."
)


def _clean(value):
    return str(value or "").strip()


def _source_is_valid(url):
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("https", "http") and bool(parsed.netloc)
    except Exception:
        return False


def _research_relevance(item):
    text = f"{item.get('title', '')} {item.get('description', '')}".lower()
    keywords = (
        "learning and development", "communication", "sales enablement",
        "customer experience", "client-facing", "client facing",
        "leadership development", "training", "coaching", "sales team",
        "consultant", "frontline", "workforce", "hiring", "careers",
        "customer success", "relationship manager",
    )
    matches = [word for word in keywords if word in text]
    return matches


def run_pipeline(p):
    events = []

    def log(agent, message, status="info"):
        events.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": agent,
            "message": message,
            "status": status,
        })

    pains = [_clean(x) for x in (p.pain_points or []) if _clean(x)]
    signals = [_clean(x) for x in (p.signals or []) if _clean(x)]
    pains = pains or ["communication consistency across customer-facing teams"]
    signals = signals or ["no prospect-specific buying signal supplied"]

    # Agent 1: Demand Sensing
    log("Demand Sensing", "Searching for public signals relevant to Vani's communication-coaching use cases")
    query = (
        f'"{p.company}" {p.industry} {p.location} '
        '(hiring OR "learning and development" OR "sales enablement" OR '
        '"customer experience" OR communication OR coaching OR training)'
    )
    research_results = []
    research_error = None
    try:
        data = asyncio.run(search_web(query, num_results=8))
        raw_results = data.get("results", []) if isinstance(data, dict) else []
        for item in raw_results:
            if not isinstance(item, dict):
                continue
            url = _clean(item.get("url"))
            result = {
                "title": _clean(item.get("title")),
                "url": url,
                "description": _clean(item.get("description")),
            }
            result["source_url_valid"] = _source_is_valid(url)
            result["relevance_matches"] = _research_relevance(result)
            result["vani_relevance"] = (
                "potentially_relevant" if result["relevance_matches"] else "needs_manual_review"
            )
            if result["title"] or result["url"] or result["description"]:
                research_results.append(result)
        log(
            "Demand Sensing",
            f"Collected {len(research_results)} public research candidates; relevance and freshness require review",
            "success" if research_results else "warning",
        )
    except Exception as exc:
        research_error = str(exc)
        log(
            "Demand Sensing",
            "Live research unavailable; supplied signals are treated as unverified hypotheses",
            "warning",
        )

    relevant_results = [
        item for item in research_results
        if item.get("source_url_valid") and item.get("relevance_matches")
    ]
    user_signal_cards = [
        {
            "signal": signal,
            "evidence_status": "user_supplied_unverified",
            "source_url": None,
        }
        for signal in signals
    ]
    web_signal_cards = [
        {
            "signal": item["title"] or item["description"][:160],
            "evidence_status": "public_search_candidate_needs_verification",
            "source_url": item["url"],
            "description": item["description"],
            "relevance_matches": item["relevance_matches"],
        }
        for item in relevant_results[:5]
    ]
    all_signal_cards = web_signal_cards + user_signal_cards

    demand = {
        "agent": "Demand Sensing Agent",
        "status": "completed" if research_results else "needs_review",
        "research_query": query,
        "research_source": "Context.dev public web search",
        "research_results": research_results,
        "relevant_research_results": relevant_results,
        "research_error": research_error,
        "signals": [item["signal"] for item in all_signal_cards],
        "signal_evidence": all_signal_cards,
        "opportunities": [
            {
                "title": f"Explore {pains[0]}",
                "rationale": (
                    f"Potential Vani use case for {p.company}: assess whether "
                    f"{pains[0]} is a current, measurable challenge."
                ),
                "evidence": "Prospect input; validate with buyer",
                "status": "hypothesis",
            },
            {
                "title": "Assess communication coaching needs",
                "rationale": (
                    f"Explore whether {p.company}'s {p.industry} teams would benefit "
                    "from personalized communication practice, AI-supported feedback, and coaching."
                ),
                "evidence": (
                    "Vani product positioning; prospect need not yet confirmed"
                ),
                "status": "hypothesis",
            },
        ],
        "market_summary": (
            f"Demand-sensing candidates for {p.company}. Public search results and "
            "user-provided signals are not proof of buying intent; verify each source."
        ),
        "source_verification_required": True,
    }

    # Agent 2: Customer Profiling
    log("Customer Profiling", "Scoring fit against Vani's enterprise communication-coaching ICP")
    company_size = _clean(p.company_size).lower()
    industry = _clean(p.industry).lower()
    target_role = _clean(p.target_role).lower()
    text_signals = " ".join(signals + [r.get("title", "") + " " + r.get("description", "") for r in relevant_results]).lower()
    communication_role_fit = 85 if any(k in text_signals for k in [
        "client-facing", "client facing", "customer", "sales", "consultant",
        "relationship", "frontline", "communication"
    ]) else 55
    trigger_strength = 80 if relevant_results else (55 if signals and signals[0] != "no prospect-specific buying signal supplied" else 35)
    vertical_fit = 80 if any(k in industry for k in [
        "bank", "bfsi", "pharma", "consult", "manufactur", "professional service",
        "saas", "software", "sales", "financial", "insurance"
    ]) else 65
    role_fit = 85 if any(k in target_role for k in [
        "learning", "development", "chro", "people", "talent", "sales",
        "enablement", "customer", "operations", "business"
    ]) else 65
    scale_fit = 85 if any(k in company_size for k in ["enterprise", "large"]) else (
        75 if "mid" in company_size else 60
    )
    evidence_quality = 80 if relevant_results else 40
    components = {
        "communication_intensive_role_fit": {"weight": 0.25, "score": communication_role_fit},
        "trigger_strength": {"weight": 0.25, "score": trigger_strength},
        "industry_use_case_fit": {"weight": 0.15, "score": vertical_fit},
        "target_persona_fit": {"weight": 0.15, "score": role_fit},
        "organization_scale_fit": {"weight": 0.10, "score": scale_fit},
        "evidence_quality": {"weight": 0.10, "score": evidence_quality},
    }
    score = round(sum(x["weight"] * x["score"] for x in components.values()))
    fit_label = "High" if score >= 75 else "Moderate" if score >= 60 else "Needs research"
    disposition = (
        "priority_for_human_review" if score >= 75 and relevant_results
        else "research_or_nurture" if score >= 55
        else "hold_for_more_evidence"
    )
    profile = {
        "agent": "Customer Profiling Agent",
        "status": "completed",
        "ideal_customer_fit": fit_label,
        "lead_score": score,
        "score_breakdown": components,
        "profiling_disposition": disposition,
        "target_persona": p.target_role,
        "persona_verified": False,
        "company_profile": {
            "company": p.company,
            "industry": p.industry,
            "location": p.location,
            "company_size": p.company_size,
            "product_fit": "Vani communication fitness and coaching platform",
        },
        "pain_points": pains,
        "intent_signals": signals,
        "research_result_count": len(research_results),
        "relevant_research_result_count": len(relevant_results),
        "evidence_sources": [
            {"title": x.get("title"), "url": x.get("url"), "description": x.get("description")}
            for x in relevant_results
        ],
        "use_case_hypothesis": (
            "Personalized communication practice and coaching for customer-facing, "
            "sales, consulting, or leadership teams."
        ),
        "score_note": (
            "Transparent heuristic, not a validated prediction. A high score is not "
            "proof of buying intent; public source and buyer need must be verified."
        ),
    }
    log("Customer Profiling", f"Calculated explainable ICP fit score: {score}/100 ({fit_label})",
        "success" if relevant_results else "warning")

    # Agent 3: Outbound Strategy
    log("Outbound Strategy", "Creating Vani-specific, evidence-aware outreach draft")
    first_evidence = relevant_results[0] if relevant_results else None
    if first_evidence:
        trigger_sentence = (
            f"I came across this public information about {p.company}: "
            f"{first_evidence.get('title') or first_evidence.get('description')}. "
            "I wanted to check whether communication development is a current priority "
            "for your team, rather than assume it is."
        )
        personalization_basis = {
            "type": "public_search_candidate",
            "summary": first_evidence.get("title") or first_evidence.get("description"),
            "source_url": first_evidence.get("url"),
            "verification_status": "requires_human_verification",
        }
    else:
        trigger_sentence = (
            f"Given your work in {p.industry}, I wondered whether improving "
            f"{pains[0]} is a current priority for {p.company}. I have not independently "
            "verified this as an active challenge."
        )
        personalization_basis = {
            "type": "user_supplied_hypothesis",
            "summary": pains[0],
            "source_url": None,
            "verification_status": "unverified",
        }

    subject = "Exploring communication coaching for your team"
    body = (
        f"Hi [Name],\n\n"
        f"{trigger_sentence}\n\n"
        f"{VANI_POSITIONING} Depending on your team's goals, this may be relevant "
        "for customer-facing conversations, presentations, or stakeholder communication.\n\n"
        "Would a brief conversation be useful to understand your team's priorities and "
        "see whether Vani could be a fit?\n\n"
        "Best regards,\n[Your Name]"
    )
    outbound = {
        "agent": "Outbound Strategy Agent",
        "status": "completed",
        "subject": subject,
        "body": body,
        "personalization_basis": personalization_basis,
        "evidence_source_url": personalization_basis.get("source_url"),
        "recommended_cta": "Brief discovery conversation",
        "follow_up_plan": [
            {"day": 0, "action": "Human-review the source and approve/edit the initial draft"},
            {"day": 4, "action": "If sent and no reply/opt-out, consider one useful follow-up"},
            {"day": 10, "action": "If appropriate, share a relevant resource or close the loop"},
        ],
        "send_status": "Draft only — not sent",
        "approval_required": True,
    }
    log("Outbound Strategy", "Personalized draft generated; no message sent", "success")

    # Agent 4: Managing Agent
    log("Managing Agent", "Validating evidence, score, draft, and approval requirements")
    source_urls = [x.get("url", "") for x in relevant_results]
    checks = {
        "company_present": bool(_clean(p.company)),
        "lead_score_in_range": 0 <= score <= 100,
        "outreach_has_subject_and_body": bool(subject.strip() and body.strip()),
        "research_status_reported": bool(research_results or research_error),
        "public_source_candidate_available": bool(relevant_results),
        "source_urls_look_valid": all(_source_is_valid(url) for url in source_urls) if source_urls else False,
        "persona_verified": False,
        "duplicate_check": "not_run_no_crm_connector",
        "suppression_check": "not_run_no_email_connector",
        "human_approval": "pending",
        "external_message_sent": False,
    }
    ready_for_review = all([
        checks["company_present"],
        checks["lead_score_in_range"],
        checks["outreach_has_subject_and_body"],
        checks["public_source_candidate_available"],
    ])
    manager_status = "pending_human_review" if ready_for_review else "needs_review"
    manager = {
        "agent": "Managing Agent",
        "status": manager_status,
        "decision": "pending_human_review" if ready_for_review else "blocked_needs_research",
        "validation_checks": checks,
        "all_checks_passed": ready_for_review and bool(relevant_results),
        "summary": (
            f"Prepared a Vani GTM brief for {p.company}; ICP heuristic {score}/100; "
            f"{len(research_results)} research candidates, {len(relevant_results)} relevant candidates. "
            "Draft is not sent and requires human review."
        ),
        "next_action": (
            "Open and verify the source, validate the target persona and buyer need, "
            "check duplicates/suppression through approved systems, then approve or edit the draft."
            if ready_for_review else
            "Collect a relevant public source and verify the prospect signal before approving outreach."
        ),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    log("Managing Agent", "Final quality gate completed; human approval remains pending",
        "warning" if not relevant_results else "success")

    return {
        "company": p.company,
        "demand_sensing": demand,
        "customer_profiling": profile,
        "outbound": outbound,
        "manager": manager,
        "events": events,
    }
