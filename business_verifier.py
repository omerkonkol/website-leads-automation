# Redirect — actual code in analysis/business_verifier.py
from analysis.business_verifier import *  # noqa: F401,F403
from analysis.business_verifier import (  # explicit re-exports
    verify_business, verify_business_quick, verify_phone,
    verify_google_presence, verify_whatsapp, verify_website_alive,
    verify_facebook, deep_research_business,
)
