"""
Compliance Analyzer - Analyzes website for compliance requirements
"""
import re
from typing import Dict, List, Optional
from urllib.parse import urlparse

# Import templates from separate file
from compliance_templates import (
    WEBSITE_TYPE_DEFINITIONS,
    RISK_LEVEL_DESCRIPTIONS,
    GENERAL_RECOMMENDATIONS
)


class ComplianceAnalyzer:
    """Analyze website for compliance requirements based on type detection"""
    
    def __init__(self):
        self.website_types = WEBSITE_TYPE_DEFINITIONS
        self.risk_descriptions = RISK_LEVEL_DESCRIPTIONS
        self.general_recommendations = GENERAL_RECOMMENDATIONS
    
    def analyze(self, content_analysis: Dict, url: str, domain: str) -> Dict:
        """
        Analyze website and return compliance assessment
        
        Args:
            content_analysis: Content analysis results from ContentAnalyzer
            url: Full website URL
            domain: Domain name
            
        Returns:
            Dictionary with compliance analysis results
        """
        result = {
            "detected_types": [],
            "primary_type": None,
            "confidence": 0,
            "risk_level": "low",
            "compliance_requirements": {},
            "recommendations": [],
            "jurisdictions": []
        }
        
        # Detect website types
        detected = self._detect_website_types(content_analysis, url)
        result["detected_types"] = detected
        
        if detected:
            # Get primary type (highest confidence)
            primary = max(detected, key=lambda x: x["confidence"])
            result["primary_type"] = primary
            result["confidence"] = primary["confidence"]
            
            # Determine risk level based on primary type
            type_key = primary["type"]
            risk_level = self.website_types[type_key]["risk_level"]
            result["risk_level"] = risk_level
            
            # Get compliance requirements for detected types
            result["compliance_requirements"] = self._get_compliance_requirements(detected)
            
            # Get recommendations
            result["recommendations"] = self._get_recommendations(detected, risk_level)
            
            # Detect likely jurisdictions
            result["jurisdictions"] = self._detect_jurisdictions(content_analysis, domain)
        
        return result
    
    def _detect_website_types(self, content_analysis: Dict, url: str) -> List[Dict]:
        """Detect website types based on content analysis"""
        detected = []
        
        # Combine all text content for analysis
        text_content = ""
        text_content += content_analysis.get("title", "") or ""
        text_content += " "
        text_content += content_analysis.get("description", "") or ""
        text_content += " "
        
        # Get link texts if available
        links = content_analysis.get("links", {})
        text_content += " ".join(links.get("all_texts", []))
        
        text_content = text_content.lower()
        
        # Score each website type
        for type_key, type_def in self.website_types.items():
            score = 0
            matched_keywords = []
            
            # Check keywords
            for keyword in type_def["keywords"]:
                if keyword.lower() in text_content:
                    score += 10
                    matched_keywords.append(keyword)
            
            # Check URL patterns
            url_lower = url.lower()
            for keyword in type_def["keywords"]:
                if keyword.lower() in url_lower:
                    score += 5
            
            # Calculate confidence (cap at 100)
            confidence = min(score, 100)
            
            if confidence > 20:  # Threshold for detection
                detected.append({
                    "type": type_key,
                    "name": type_def["name"],
                    "confidence": confidence,
                    "description": type_def["description"],
                    "matched_keywords": matched_keywords[:5],  # Top 5 matches
                    "risk_level": type_def["risk_level"]
                })
        
        # Sort by confidence
        detected.sort(key=lambda x: x["confidence"], reverse=True)
        return detected
    
    def _get_compliance_requirements(self, detected_types: List[Dict]) -> Dict:
        """Get consolidated compliance requirements for detected types"""
        requirements = {}
        
        for detected in detected_types:
            type_key = detected["type"]
            type_def = self.website_types[type_key]
            
            for regulation, description in type_def["compliance_requirements"].items():
                if regulation not in requirements:
                    requirements[regulation] = {
                        "description": description,
                        "applies_to": []
                    }
                requirements[regulation]["applies_to"].append(type_def["name"])
        
        return requirements
    
    def _get_recommendations(self, detected_types: List[Dict], risk_level: str) -> List[str]:
        """Get compliance recommendations"""
        recommendations = []
        
        # Add general recommendations based on risk level
        if risk_level in self.general_recommendations:
            recommendations.extend(self.general_recommendations[risk_level])
        
        # Add type-specific recommendations
        type_specific = {
            "ecommerce": [
                "Implement secure payment processing (PCI DSS compliance)",
                "Display clear return and refund policies",
                "Provide accurate product descriptions and pricing",
                "Implement customer review moderation"
            ],
            "social_media": [
                "Implement robust content moderation tools",
                "Provide clear community guidelines",
                "Enable user reporting mechanisms",
                "Implement age verification where required"
            ],
            "saas_platform": [
                "Draft comprehensive Terms of Service and SLA",
                "Implement data backup and disaster recovery",
                "Provide data export functionality",
                "Document API usage policies"
            ],
            "healthcare": [
                "Execute Business Associate Agreements (BAAs)",
                "Implement end-to-end encryption for all data",
                "Conduct regular HIPAA risk assessments",
                "Train all staff on HIPAA requirements"
            ],
            "financial": [
                "Engage regulatory counsel before launch",
                "Implement multi-factor authentication",
                "Establish transaction monitoring systems",
                "Maintain detailed audit logs"
            ],
            "educational": [
                "Obtain proper parental consent for minors",
                "Implement FERPA-compliant record keeping",
                "Provide accessible learning materials",
                "Document data retention for student records"
            ]
        }
        
        for detected in detected_types[:2]:  # Top 2 types
            type_key = detected["type"]
            if type_key in type_specific:
                recommendations.extend(type_specific[type_key])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)
        
        return unique_recommendations[:10]  # Limit to top 10
    
    def _detect_jurisdictions(self, content_analysis: Dict, domain: str) -> List[str]:
        """Detect likely jurisdictions based on content and domain"""
        jurisdictions = []
        
        text_content = ""
        text_content += content_analysis.get("title", "") or ""
        text_content += " "
        text_content += content_analysis.get("description", "") or ""
        text_content = text_content.lower()
        
        # Country-specific indicators
        indicators = {
            "United States": ["usa", "united states", "america", "us ", " fda", " hipaa", " ferpa", "ccpa"],
            "European Union": ["eu ", "european", "gdpr", "europe", "vat"],
            "United Kingdom": ["uk", "united kingdom", "britain", "england", "ico"],
            "Canada": ["canada", "canadian", "pipeda"],
            "Australia": ["australia", "australian", "oaic"],
            "Singapore": ["singapore", "singaporean", "pdpc"],
            "China": ["china", "chinese", "网络安全法", "个人信息保护法"],
            "Japan": ["japan", "japanese", "apPI"],
        }
        
        for country, keywords in indicators.items():
            for keyword in keywords:
                if keyword.lower() in text_content:
                    jurisdictions.append(country)
                    break
        
        # Domain-based detection
        domain_indicators = {
            ".com": "United States (likely)",
            ".co.uk": "United Kingdom",
            ".de": "Germany",
            ".fr": "France",
            ".eu": "European Union",
            ".au": "Australia",
            ".ca": "Canada",
            ".jp": "Japan",
            ".cn": "China",
            ".sg": "Singapore",
        }
        
        for suffix, country in domain_indicators.items():
            if domain.endswith(suffix):
                if country not in jurisdictions:
                    jurisdictions.append(country)
                break
        
        # Default if nothing detected
        if not jurisdictions:
            jurisdictions.append("United States (default)")
        
        return jurisdictions[:3]  # Top 3 likely jurisdictions
    
    def get_risk_description(self, risk_level: str) -> Dict:
        """Get description for a risk level"""
        return self.risk_descriptions.get(risk_level, self.risk_descriptions["low"])
