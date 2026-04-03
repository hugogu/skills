# Compliance Analysis Templates and Prompts
# This file contains all text content used by the ComplianceAnalyzer
# Separated from the main code to avoid Python formatting issues

WEBSITE_TYPE_DEFINITIONS = {
    "ecommerce": {
        "name": "E-commerce",
        "description": "Online retail or marketplace for selling goods/services",
        "keywords": ["shop", "store", "cart", "checkout", "product", "buy", "purchase", "price", "order", "payment", "shipping", "discount", "coupon", "wishlist", "basket"],
        "key_features": ["product listings", "shopping cart", "payment processing", "user accounts"],
        "compliance_requirements": {
            "GDPR": "Customer data protection, consent management",
            "PCI DSS": "Payment card data security (if handling card data)",
            "Consumer Protection": "Clear pricing, return policies, terms of service",
            "Accessibility": "WCAG compliance for product pages and checkout",
            "Tax Compliance": "VAT/sales tax calculation and collection"
        },
        "risk_level": "high"
    },
    "social_media": {
        "name": "Social Media",
        "description": "Platform for user-generated content and social networking",
        "keywords": ["social", "community", "profile", "friend", "follow", "post", "share", "like", "comment", "feed", "timeline", "messenger", "chat"],
        "key_features": ["user profiles", "content sharing", "social graph", "messaging"],
        "compliance_requirements": {
            "GDPR/CCPA": "User data rights, data portability, deletion",
            "DMCA": "Copyright infringement reporting and takedown",
            "Section 230": "Platform liability limitations (US)",
            "Age Verification": "COPPA compliance for users under 13",
            "Content Moderation": "Illegal content detection and removal"
        },
        "risk_level": "critical"
    },
    "saas_platform": {
        "name": "SaaS Platform",
        "description": "Software-as-a-Service offering cloud-based applications",
        "keywords": ["app", "dashboard", "login", "account", "subscription", "plan", "trial", "api", "integration", "workspace", "team", "collaboration"],
        "key_features": ["user authentication", "subscription management", "API access", "data storage"],
        "compliance_requirements": {
            "SOC 2": "Security, availability, confidentiality controls",
            "GDPR": "Data processing agreements, breach notification",
            "SLA": "Service level agreements and uptime guarantees",
            "Data Residency": "Geographic data storage requirements",
            "Backup/DR": "Business continuity and disaster recovery"
        },
        "risk_level": "high"
    },
    "educational": {
        "name": "Educational",
        "description": "Learning management system or educational content platform",
        "keywords": ["course", "lesson", "learn", "education", "student", "teacher", "class", "enrollment", "certificate", "curriculum", "quiz", "assignment"],
        "key_features": ["course content", "student progress tracking", "assessments", "certificates"],
        "compliance_requirements": {
            "FERPA": "Student educational record privacy (US)",
            "GDPR": "Student data protection",
            "COPPA": "Parental consent for under-13 users",
            "Accessibility": "WCAG AA compliance required",
            "Copyright": "Educational fair use compliance"
        },
        "risk_level": "medium"
    },
    "healthcare": {
        "name": "Healthcare",
        "description": "Medical services, telehealth, or health information platform",
        "keywords": ["health", "medical", "doctor", "patient", "appointment", "prescription", "clinic", "hospital", "symptom", "diagnosis", "treatment", "portal"],
        "key_features": ["patient portals", "appointment booking", "medical records", "secure messaging"],
        "compliance_requirements": {
            "HIPAA": "Protected health information security (US)",
            "GDPR": "Health data special category protection (EU)",
            "HITECH": "Breach notification requirements (US)",
            "FDA": "If providing medical device software",
            "State Laws": "Medical board regulations and telehealth licensing"
        },
        "risk_level": "critical"
    },
    "financial": {
        "name": "Financial Services",
        "description": "Banking, investment, insurance, or fintech platform",
        "keywords": ["bank", "finance", "invest", "money", "transfer", "payment", "loan", "credit", "debit", "account", "balance", "transaction", "trading", "crypto"],
        "key_features": ["financial transactions", "account management", "investment tracking", "regulatory reporting"],
        "compliance_requirements": {
            "PCI DSS": "Payment card industry standards",
            "SOX": "Financial reporting accuracy (public companies)",
            "AML/KYC": "Anti-money laundering and know your customer",
            "GDPR": "Financial data protection",
            "Banking Regulations": "OCC, FDIC, or relevant banking authority compliance",
            "SEC": "If offering investment services (US)"
        },
        "risk_level": "critical"
    },
    "marketplace": {
        "name": "Online Marketplace",
        "description": "Multi-vendor platform connecting buyers and sellers",
        "keywords": ["marketplace", "seller", "vendor", "listing", "commission", "seller account", "payout", "market", "bazaar", "classified"],
        "key_features": ["vendor management", "commission tracking", "multi-party transactions", "dispute resolution"],
        "compliance_requirements": {
            "Platform Liability": "Intermediary liability protections",
            "GDPR": "Data controller/processor responsibilities",
            "Consumer Protection": "Marketplace transparency requirements",
            "Tax Reporting": "1099-K or equivalent reporting",
            "Anti-Counterfeit": "Brand protection and IP enforcement"
        },
        "risk_level": "high"
    },
    "gaming": {
        "name": "Gaming",
        "description": "Online games, gambling, or esports platforms",
        "keywords": ["game", "play", "score", "level", "casino", "bet", "gambling", "poker", "slot", "esports", "tournament", "loot", "in-app purchase"],
        "key_features": ["user accounts", "virtual currency", "leaderboards", "matchmaking"],
        "compliance_requirements": {
            "Age Rating": "ESRB, PEGI, or equivalent content ratings",
            "Gambling Laws": "If real money gambling: strict licensing",
            "COPPA": "Children's privacy for games",
            "Loot Box": "Disclosure requirements in some jurisdictions",
            "GDPR": "Player data and right to deletion"
        },
        "risk_level": "high"
    },
    "content_platform": {
        "name": "Content Platform",
        "description": "Media streaming, publishing, or content distribution",
        "keywords": ["news", "blog", "article", "video", "stream", "media", "publish", "subscribe", "content", "media", "watch", "listen", "podcast", "subscribe"],
        "key_features": ["content delivery", "user subscriptions", "content management", "analytics"],
        "compliance_requirements": {
            "DMCA": "Copyright safe harbor compliance",
            "GDPR": "User data and content ownership rights",
            "Defamation": "Content liability and takedown procedures",
            "Accessibility": "Captioning and accessibility requirements",
            "Age Verification": "Adult content age restrictions"
        },
        "risk_level": "medium"
    }
}

# Risk level descriptions
RISK_LEVEL_DESCRIPTIONS = {
    "low": {
        "level": "Low Risk",
        "description": "Standard compliance measures sufficient",
        "action": "Follow standard best practices"
    },
    "medium": {
        "level": "Medium Risk", 
        "description": "Specific industry compliance requirements apply",
        "action": "Implement industry-specific controls"
    },
    "high": {
        "level": "High Risk",
        "description": "Significant regulatory oversight, requires dedicated compliance program",
        "action": "Establish formal compliance team and regular audits"
    },
    "critical": {
        "level": "Critical Risk",
        "description": "Heavily regulated industry with severe penalties for non-compliance",
        "action": "Engage legal counsel, implement comprehensive compliance framework"
    }
}

# General recommendations based on risk level
GENERAL_RECOMMENDATIONS = {
    "low": [
        "Implement basic privacy policy and terms of service",
        "Enable HTTPS across the entire site",
        "Set up basic cookie consent banner",
        "Ensure contact information is easily accessible"
    ],
    "medium": [
        "Conduct privacy impact assessment",
        "Implement data retention policies",
        "Set up user rights request process (access, deletion)",
        "Regular security audits recommended",
        "Consider cyber insurance coverage"
    ],
    "high": [
        "Engage compliance consultant or legal counsel",
        "Implement comprehensive data governance program",
        "Regular penetration testing and vulnerability assessments",
        "Establish incident response plan",
        "Obtain relevant certifications (SOC 2, ISO 27001, etc.)",
        "Document all compliance procedures"
    ],
    "critical": [
        "Mandatory legal review of all data practices",
        "Implement enterprise-grade security controls",
        "Regular third-party compliance audits",
        "Board-level oversight of compliance program",
        "Crisis communication plan for breaches",
        "Regulatory relationship management"
    ]
}
