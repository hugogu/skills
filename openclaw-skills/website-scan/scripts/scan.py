#!/usr/bin/env python3
"""
Website Scanner - Comprehensive website analysis tool
Analyzes IP, DNS, content, SEO, and third-party metrics
"""

import argparse
import json
import re
import socket
import subprocess
import sys
import urllib.parse
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

import requests
from bs4 import BeautifulSoup


@dataclass
class ScanResult:
    """Container for all scan results"""
    url: str
    domain: str
    ip_info: Dict = field(default_factory=dict)
    dns_info: Dict = field(default_factory=dict)
    whois_info: Dict = field(default_factory=dict)
    content_analysis: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)
    seo_data: Dict = field(default_factory=dict)
    sitemap_data: Dict = field(default_factory=dict)
    robots_txt: str = ""
    llms_txt: str = ""
    third_party: Dict = field(default_factory=dict)
    pages_scanned: List[Dict] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    compliance_analysis: Dict = field(default_factory=dict)


class IPAnalyzer:
    """Analyze IP addresses (IPv4 and IPv6)"""
    
    @staticmethod
    def resolve_hostname(domain: str) -> Dict:
        """Resolve domain to IP addresses"""
        result = {"ipv4": [], "ipv6": [], "errors": []}
        
        # IPv4
        try:
            ipv4_info = socket.getaddrinfo(domain, None, socket.AF_INET)
            result["ipv4"] = list(set([info[4][0] for info in ipv4_info]))
        except Exception as e:
            result["errors"].append(f"IPv4 resolution failed: {e}")
        
        # IPv6
        try:
            ipv6_info = socket.getaddrinfo(domain, None, socket.AF_INET6)
            result["ipv6"] = list(set([info[4][0] for info in ipv6_info]))
        except Exception as e:
            result["errors"].append(f"IPv6 resolution failed: {e}")
        
        return result
    
    @staticmethod
    def get_ip_geolocation(ip: str) -> Dict:
        """Get geolocation data for IP"""
        try:
            response = requests.get(f"https://ipapi.co/{ip}/json/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    "ip": ip,
                    "city": data.get("city"),
                    "region": data.get("region"),
                    "country": data.get("country_name"),
                    "country_code": data.get("country_code"),
                    "latitude": data.get("latitude"),
                    "longitude": data.get("longitude"),
                    "org": data.get("org"),
                    "asn": data.get("asn"),
                    "timezone": data.get("timezone")
                }
        except Exception as e:
            return {"error": str(e)}
        return {}


class DNSAnalyzer:
    """Analyze DNS records"""
    
    RECORD_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]
    
    @classmethod
    def query_dns(cls, domain: str) -> Dict:
        """Query multiple DNS record types"""
        results = {}
        
        for record_type in cls.RECORD_TYPES:
            try:
                result = subprocess.run(
                    ["dig", "+short", "-t", record_type, domain],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                output = result.stdout.strip()
                if output:
                    results[record_type] = output.split("\n")
            except Exception as e:
                results[record_type] = [f"Error: {e}"]
        
        return results


class WHOISAnalyzer:
    """Analyze WHOIS information"""
    
    @staticmethod
    def query_whois(domain: str) -> Dict:
        """Query WHOIS data for domain"""
        try:
            result = subprocess.run(
                ["whois", domain],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            whois_text = result.stdout
            
            # Parse key fields
            parsed = {
                "registrar": WHOISAnalyzer._extract_field(whois_text, [r"Registrar:\s*(.+)", r"Sponsoring Registrar:\s*(.+)"]),
                "creation_date": WHOISAnalyzer._extract_field(whois_text, [r"Creation Date:\s*(.+)", r"created:\s*(.+)"]),
                "expiration_date": WHOISAnalyzer._extract_field(whois_text, [r"Registry Expiry Date:\s*(.+)", r"expires:\s*(.+)"]),
                "name_servers": WHOISAnalyzer._extract_list(whois_text, [r"Name Server:\s*(.+)", r"nserver:\s*(.+)"]),
                "status": WHOISAnalyzer._extract_list(whois_text, [r"Domain Status:\s*(.+)"]),
                "registrant_org": WHOISAnalyzer._extract_field(whois_text, [r"Registrant Organization:\s*(.+)", r"org:\s*(.+)"]),
                "registrant_country": WHOISAnalyzer._extract_field(whois_text, [r"Registrant Country:\s*(.+)", r"country:\s*(.+)"]),
            }
            
            return parsed
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def _extract_field(text: str, patterns: list) -> Optional[str]:
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    @staticmethod
    def _extract_list(text: str, patterns: list) -> List[str]:
        results = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            results.extend([m.strip() for m in matches])
        return list(set(results))


#!/usr/bin/env python3
"""
Website Scanner - Comprehensive website analysis tool
Analyzes IP, DNS, content, SEO, compliance and third-party metrics
"""

import argparse
import json
import re
import socket
import subprocess
import sys
import urllib.parse
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

import requests
from bs4 import BeautifulSoup


@dataclass
class ScanResult:
    """Container for all scan results"""
    url: str
    domain: str
    ip_info: Dict = field(default_factory=dict)
    dns_info: Dict = field(default_factory=dict)
    whois_info: Dict = field(default_factory=dict)
    content_analysis: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)
    seo_data: Dict = field(default_factory=dict)
    sitemap_data: Dict = field(default_factory=dict)
    robots_txt: str = ""
    llms_txt: str = ""
    third_party: Dict = field(default_factory=dict)
    pages_scanned: List[Dict] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    compliance_analysis: Dict = field(default_factory=dict)
    compliance_analysis: Dict = field(default_factory=dict)  # NEW


class IPAnalyzer:
    """Analyze IP addresses (IPv4 and IPv6)"""
    
    @staticmethod
    def resolve_hostname(domain: str) -> Dict:
        """Resolve domain to IP addresses"""
        result = {"ipv4": [], "ipv6": [], "errors": []}
        
        # IPv4
        try:
            ipv4_info = socket.getaddrinfo(domain, None, socket.AF_INET)
            result["ipv4"] = list(set([info[4][0] for info in ipv4_info]))
        except Exception as e:
            result["errors"].append(f"IPv4 resolution failed: {e}")
        
        # IPv6
        try:
            ipv6_info = socket.getaddrinfo(domain, None, socket.AF_INET6)
            result["ipv6"] = list(set([info[4][0] for info in ipv6_info]))
        except Exception as e:
            result["errors"].append(f"IPv6 resolution failed: {e}")
        
        return result
    
    @staticmethod
    def get_ip_geolocation(ip: str) -> Dict:
        """Get geolocation data for IP"""
        try:
            response = requests.get(f"https://ipapi.co/{ip}/json/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    "ip": ip,
                    "city": data.get("city"),
                    "region": data.get("region"),
                    "country": data.get("country_name"),
                    "country_code": data.get("country_code"),
                    "latitude": data.get("latitude"),
                    "longitude": data.get("longitude"),
                    "org": data.get("org"),
                    "asn": data.get("asn"),
                    "timezone": data.get("timezone")
                }
        except Exception as e:
            return {"error": str(e)}
        return {}


class ComplianceAnalyzer:
    """Analyze website for compliance requirements"""
    
    # Website type indicators
    TYPE_INDICATORS = {
        "ecommerce": {
            "keywords": ["shop", "store", "cart", "checkout", "product", "buy", "purchase", "payment", "order", "price", "shipping", "payment", "stripe", "paypal", "alipay", "wechat pay"],
            "paths": ["/cart", "/checkout", "/shop", "/product", "/order", "/payment"],
            "selectors": [".product", ".cart", ".checkout", "[data-product]", ".add-to-cart", ".price"]
        },
        "social_media": {
            "keywords": ["social", "community", "share", "follow", "friend", "post", "feed", "like", "comment", "profile", "messaging", "chat"],
            "paths": ["/feed", "/profile", "/messages", "/notifications", "/friends", "/explore"],
            "selectors": [".feed", ".post", ".comment", ".like", ".share", ".profile"]
        },
        "content_platform": {
            "keywords": ["blog", "article", "news", "publish", "content", "read", "subscribe", "newsletter", "editorial"],
            "paths": ["/blog", "/article", "/news", "/category", "/author"],
            "selectors": [".article", ".blog-post", ".news", ".content"]
        },
        "saas_platform": {
            "keywords": ["app", "dashboard", "login", "signup", "api", "service", "cloud", "software", "solution", "platform", "enterprise", "pricing", "trial"],
            "paths": ["/dashboard", "/app", "/api", "/docs", "/login", "/signup", "/pricing"],
            "selectors": [".dashboard", ".app", "[data-app]", ".pricing-table"]
        },
        "educational": {
            "keywords": ["course", "learn", "education", "training", "academy", "school", "university", "lesson", "tutorial", "certification", "degree"],
            "paths": ["/courses", "/learn", "/lessons", "/certification", "/academy"],
            "selectors": [".course", ".lesson", ".curriculum", ".instructor"]
        },
        "healthcare": {
            "keywords": ["health", "medical", "doctor", "patient", "clinic", "hospital", "pharmacy", "treatment", "diagnosis", "medicine"],
            "paths": ["/patient", "/doctor", "/appointment", "/medical-records"],
            "selectors": [".patient", ".medical", ".appointment"]
        },
        "financial": {
            "keywords": ["bank", "finance", "investment", "trading", "crypto", "bitcoin", "ethereum", "wallet", "exchange", "loan", "credit", "insurance", "mortgage"],
            "paths": ["/trading", "/wallet", "/exchange", "/invest", "/banking"],
            "selectors": [".trading", ".wallet", ".exchange", ".financial"]
        },
        "marketplace": {
            "keywords": ["marketplace", "vendor", "seller", "buyer", "listing", "auction", "bid", "classified", "freelance", "gig"],
            "paths": ["/listings", "/vendors", "/sellers", "/marketplace"],
            "selectors": [".listing", ".vendor", ".seller", ".marketplace"]
        },
        "gaming": {
            "keywords": ["game", "gaming", "play", "player", "multiplayer", "esports", "casino", "betting", "gambling", "loot", "skin"],
            "paths": ["/games", "/play", "/tournaments", "/leaderboard"],
            "selectors": [".game", ".player", ".leaderboard"]
        }
    }
    
    @classmethod
    def analyze(cls, url: str, content_analysis: Dict, html_content: str = "") -> Dict:
        """Analyze website for type, purpose and compliance requirements"""
        result = {
            "website_type": "unknown",
            "purpose": "",
            "use_cases": [],
            "compliance_requirements": [],
            "jurisdictions": [],
            "risk_level": "low",
            "recommendations": []
        }
        
        # Detect website type
        website_type = cls._detect_website_type(url, content_analysis, html_content)
        result["website_type"] = website_type["type"]
        result["confidence"] = website_type["confidence"]
        
        # Determine purpose and use cases
        purpose_data = cls._analyze_purpose(website_type["type"], content_analysis)
        result["purpose"] = purpose_data["purpose"]
        result["use_cases"] = purpose_data["use_cases"]
        
        # Analyze compliance requirements
        compliance = cls._analyze_compliance(website_type["type"], content_analysis)
        result["compliance_requirements"] = compliance["requirements"]
        result["jurisdictions"] = compliance["jurisdictions"]
        result["risk_level"] = compliance["risk_level"]
        result["recommendations"] = compliance["recommendations"]
        
        return result
    
    @classmethod
    def _detect_website_type(cls, url: str, content_analysis: Dict, html_content: str) -> Dict:
        """Detect website type based on content analysis"""
        scores = {site_type: 0 for site_type in cls.TYPE_INDICATORS}
        max_score = 0
        
        # Check keywords in title and description
        title = (content_analysis.get("title") or "").lower()
        description = (content_analysis.get("description") or "").lower()
        text_content = f"{title} {description}"
        
        # Check server indicators if available
        server = (content_analysis.get("server") or "").lower()
        
        for site_type, indicators in cls.TYPE_INDICATORS.items():
            # Keyword matching
            for keyword in indicators["keywords"]:
                if keyword in text_content:
                    scores[site_type] += 2
                if keyword in html_content.lower():
                    scores[site_type] += 1
            
            # Path matching in URL
            for path in indicators["paths"]:
                if path in url.lower():
                    scores[site_type] += 3
        
        # Special checks for HTML content
        soup = BeautifulSoup(html_content, 'html.parser') if html_content else None
        if soup:
            for site_type, indicators in cls.TYPE_INDICATORS.items():
                for selector in indicators["selectors"]:
                    try:
                        if soup.select(selector):
                            scores[site_type] += 2
                    except:
                        pass
        
        # Determine best match
        if scores:
            best_match = max(scores, key=scores.get)
            max_score = scores[best_match]
            
            # Calculate confidence
            if max_score >= 10:
                confidence = "high"
            elif max_score >= 5:
                confidence = "medium"
            else:
                confidence = "low"
                best_match = "general"
            
            return {"type": best_match, "confidence": confidence, "scores": scores}
        
        return {"type": "general", "confidence": "low", "scores": scores}
    
    @classmethod
    def _analyze_purpose(cls, website_type: str, content_analysis: Dict) -> Dict:
        """Analyze website purpose and use cases"""
        purposes = {
            "ecommerce": {
                "purpose": "在线商品销售平台，为商家和消费者提供交易服务",
                "use_cases": [
                    "B2C 零售销售",
                    "B2B 批发交易", 
                    "数字商品销售",
                    "订阅服务",
                    "跨境电子商务"
                ]
            },
            "social_media": {
                "purpose": "社交媒体平台，促进用户之间的内容分享和互动",
                "use_cases": [
                    "个人社交互动",
                    "内容创作者变现",
                    "品牌推广和营销",
                    "社群运营",
                    "实时通讯"
                ]
            },
            "content_platform": {
                "purpose": "内容发布和分发平台，提供信息、新闻或教育内容",
                "use_cases": [
                    "新闻资讯发布",
                    "博客和文章分享",
                    "教育资源分发",
                    "行业报告和研究",
                    "多媒体内容托管"
                ]
            },
            "saas_platform": {
                "purpose": "软件即服务平台，为企业提供云端软件解决方案",
                "use_cases": [
                    "企业生产力工具",
                    "数据分析和可视化",
                    "项目管理",
                    "客户关系管理 (CRM)",
                    "API 服务提供"
                ]
            },
            "educational": {
                "purpose": "在线教育平台，提供课程、培训和认证服务",
                "use_cases": [
                    "在线课程学习",
                    "职业培训",
                    "学术认证",
                    "企业内训",
                    "技能测评"
                ]
            },
            "healthcare": {
                "purpose": "医疗健康服务平台，提供医疗咨询、预约和健康管理",
                "use_cases": [
                    "在线医疗咨询",
                    "预约挂号服务",
                    "健康档案管理",
                    "远程诊疗",
                    "药品配送"
                ]
            },
            "financial": {
                "purpose": "金融服务平台，提供投资、交易、借贷等金融服务",
                "use_cases": [
                    "股票和加密货币交易",
                    "支付和转账服务",
                    "投资理财",
                    "贷款和信贷",
                    "保险服务"
                ]
            },
            "marketplace": {
                "purpose": "在线市场平台，连接买家和卖家促成交易",
                "use_cases": [
                    "C2C 个人交易",
                    "B2C 商家入驻",
                    "服务外包平台",
                    "二手物品交易",
                    "拍卖和竞价"
                ]
            },
            "gaming": {
                "purpose": "游戏娱乐平台，提供在线游戏和竞技服务",
                "use_cases": [
                    "在线多人游戏",
                    "电竞比赛",
                    "游戏直播",
                    "虚拟物品交易",
                    "社交游戏平台"
                ]
            },
            "general": {
                "purpose": "通用信息展示网站，提供企业或个人信息展示",
                "use_cases": [
                    "企业官网展示",
                    "个人作品集",
                    "信息门户",
                    "品牌推广",
                    "联系和咨询"
                ]
            }
        }
        
        return purposes.get(website_type, purposes["general"])
    
    @classmethod
    def _analyze_compliance(cls, website_type: str, content_analysis: Dict) -> Dict:
        """Analyze compliance requirements based on website type"""
        result = {
            "requirements": [],
            "jurisdictions": [],
            "risk_level": "low",
            "recommendations": []
        }
        
        # Base compliance for all websites
        base_requirements = [
            {
                "regulation": "隐私政策",
                "description": "必须提供清晰的隐私政策，说明数据收集和使用方式",
                "jurisdictions": ["全球"],
                "priority": "high"
            },
            {
                "regulation": "Cookie 合规",
                "description": "需获得用户同意后才能使用非必要 Cookie",
                "jurisdictions": ["欧盟 (GDPR)", "英国"],
                "priority": "medium"
            },
            {
                "regulation": "网站可访问性",
                "description": "遵循 WCAG 标准，确保残障用户可访问",
                "jurisdictions": ["美国 (ADA)", "欧盟"],
                "priority": "medium"
            }
        ]
        
        result["requirements"].extend(base_requirements)
        
        # Type-specific compliance
        type_compliance = {
            "ecommerce": {
                "requirements": [
                    {
                        "regulation": "消费者权益保护",
                        "description": "提供明确的退货政策、价格透明、合同条款",
                        "jurisdictions": ["欧盟", "美国", "中国"],
                        "priority": "high"
                    },
                    {
                        "regulation": "支付卡行业数据安全标准 (PCI DSS)",
                        "description": "处理信用卡数据需符合 PCI DSS 要求",
                        "jurisdictions": ["全球"],
                        "priority": "critical"
                    },
                    {
                        "regulation": "产品安全合规",
                        "description": "销售产品需符合目标市场的安全标准",
                        "jurisdictions": ["欧盟 (CE)", "美国 (FCC/UL)", "中国 (CCC)"],
                        "priority": "high"
                    }
                ],
                "jurisdictions": ["欧盟", "美国", "中国", "日本"],
                "risk_level": "high",
                "recommendations": [
                    "实施 SSL/TLS 加密保护支付数据",
                    "提供多语言用户协议和隐私政策",
                    "建立客户争议解决机制",
                    "定期进行安全漏洞扫描",
                    "保存交易记录至少 5-7 年"
                ]
            },
            "social_media": {
                "requirements": [
                    {
                        "regulation": "GDPR 数据保护",
                        "description": "用户有权删除账户和数据，数据 portability",
                        "jurisdictions": ["欧盟", "英国", "瑞士"],
                        "priority": "critical"
                    },
                    {
                        "regulation": "内容审核责任",
                        "description": "需建立内容审核机制，处理非法内容举报",
                        "jurisdictions": ["欧盟 (DSA)", "美国 (Section 230)", "中国"],
                        "priority": "high"
                    },
                    {
                        "regulation": "儿童在线隐私保护 (COPPA)",
                        "description": "收集 13 岁以下儿童数据需获得家长同意",
                        "jurisdictions": ["美国", "英国 (Age Appropriate Design Code)"],
                        "priority": "critical"
                    }
                ],
                "jurisdictions": ["欧盟", "美国", "中国", "印度"],
                "risk_level": "high",
                "recommendations": [
                    "实施年龄验证机制",
                    "建立用户内容举报系统",
                    "定期进行内容审核培训",
                    "保存用户活动日志以满足法律要求",
                    "实施数据最小化原则"
                ]
            },
            "financial": {
                "requirements": [
                    {
                        "regulation": "反洗钱 (AML)",
                        "description": "实施 KYC (了解你的客户) 程序，监控可疑交易",
                        "jurisdictions": ["美国 (FinCEN)", "欧盟 (AMLD)", "中国"],
                        "priority": "critical"
                    },
                    {
                        "regulation": "金融监管许可",
                        "description": "提供金融服务需获得相应牌照",
                        "jurisdictions": ["美国 (SEC/CFTC)", "欧盟 (MiFID II)", "新加坡 (MAS)"],
                        "priority": "critical"
                    },
                    {
                        "regulation": "数据本地化",
                        "description": "金融数据可能需要存储在特定司法管辖区",
                        "jurisdictions": ["中国", "俄罗斯", "印度"],
                        "priority": "high"
                    }
                ],
                "jurisdictions": ["美国", "欧盟", "英国", "新加坡", "香港", "中国"],
                "risk_level": "critical",
                "recommendations": [
                    "获得必要的金融服务牌照",
                    "实施强大的身份验证系统",
                    "建立交易监控系统",
                    "定期进行合规审计",
                    "实施数据加密和隔离",
                    "建立业务连续性计划"
                ]
            },
            "healthcare": {
                "requirements": [
                    {
                        "regulation": "健康数据保护 (HIPAA)",
                        "description": "保护患者健康信息的隐私和安全",
                        "jurisdictions": ["美国"],
                        "priority": "critical"
                    },
                    {
                        "regulation": "GDPR 特殊类别数据",
                        "description": "健康数据属于敏感数据，需额外保护",
                        "jurisdictions": ["欧盟", "英国"],
                        "priority": "critical"
                    },
                    {
                        "regulation": "医疗器械监管",
                        "description": "健康类 App 可能被归类为医疗器械",
                        "jurisdictions": ["美国 (FDA)", "欧盟 (MDR)"],
                        "priority": "high"
                    }
                ],
                "jurisdictions": ["美国", "欧盟", "中国", "日本"],
                "risk_level": "critical",
                "recommendations": [
                    "实施端到端加密",
                    "建立严格的访问控制",
                    "获得医疗数据保护认证",
                    "进行定期的安全评估",
                    "建立数据泄露响应计划"
                ]
            },
            "saas_platform": {
                "requirements": [
                    {
                        "regulation": "SOC 2 合规",
                        "description": "服务组织控制报告，证明安全控制有效性",
                        "jurisdictions": ["全球"],
                        "priority": "high"
                    },
                    {
                        "regulation": "ISO 27001",
                        "description": "信息安全管理体系认证",
                        "jurisdictions": ["全球"],
                        "priority": "medium"
                    },
                    {
                        "regulation": "数据跨境传输",
                        "description": "遵守数据本地化或跨境传输规则",
                        "jurisdictions": ["欧盟", "中国", "俄罗斯"],
                        "priority": "high"
                    }
                ],
                "jurisdictions": ["美国", "欧盟", "中国"],
                "risk_level": "medium",
                "recommendations": [
                    "实施零信任安全架构",
                    "建立供应商安全管理计划",
                    "定期进行渗透测试",
                    "实施数据备份和恢复策略",
                    "建立客户数据处理协议 (DPA)"
                ]
            },
            "content_platform": {
                "requirements": [
                    {
                        "regulation": "版权保护 (DMCA)",
                        "description": "建立版权投诉处理机制",
                        "jurisdictions": ["美国", "欧盟"],
                        "priority": "high"
                    },
                    {
                        "regulation": "虚假信息治理",
                        "description": "需建立事实核查和内容标注机制",
                        "jurisdictions": ["欧盟", "德国 (NetzDG)", "法国"],
                        "priority": "medium"
                    }
                ],
                "jurisdictions": ["美国", "欧盟", "中国"],
                "risk_level": "medium",
                "recommendations": [
                    "建立版权声明和投诉机制",
                    "实施内容来源标注",
                    "建立编辑政策公开透明",
                    "定期进行版权合规审查"
                ]
            },
            "educational": {
                "requirements": [
                    {
                        "regulation": "FERPA (家庭教育权利和隐私法)",
                        "description": "保护学生教育记录隐私",
                        "jurisdictions": ["美国"],
                        "priority": "high"
                    },
                    {
                        "regulation": "教育资质认证",
                        "description": "提供学位或认证需获得教育资质",
                        "jurisdictions": ["各国教育部门"],
                        "priority": "high"
                    }
                ],
                "jurisdictions": ["美国", "欧盟", "中国"],
                "risk_level": "medium",
                "recommendations": [
                    "获得相关教育资质认证",
                    "建立学生数据保护政策",
                    "实施学习成果评估体系",
                    "确保课程内容版权合规"
                ]
            },
            "gaming": {
                "requirements": [
                    {
                        "regulation": "年龄分级系统",
                        "description": "游戏内容需进行年龄分级",
                        "jurisdictions": ["美国 (ESRB)", "欧盟 (PEGI)", "中国"],
                        "priority": "high"
                    },
                    {
                        "regulation": "游戏防沉迷",
                        "description": "对未成年玩家实施游戏时间限制",
                        "jurisdictions": ["中国"],
                        "priority": "high"
                    },
                    {
                        "regulation": "博彩监管",
                        "description": "含赌博元素需获得博彩牌照",
                        "jurisdictions": ["各国博彩监管机构"],
                        "priority": "critical"
                    }
                ],
                "jurisdictions": ["美国", "欧盟", "中国", "韩国", "日本"],
                "risk_level": "high",
                "recommendations": [
                    "实施年龄验证系统",
                    "建立游戏内容分级",
                    "对未成年玩家实施限制",
                    "确保虚拟物品交易合规",
                    "建立玩家申诉机制"
                ]
            },
            "marketplace": {
                "requirements": [
                    {
                        "regulation": "平台责任",
                        "description": "对平台上的交易承担连带责任",
                        "jurisdictions": ["欧盟 (DSA/DMA)", "美国", "中国"],
                        "priority": "high"
                    },
                    {
                        "regulation": "卖家资质审核",
                        "description": "需验证平台卖家身份和资质",
                        "jurisdictions": ["美国 (INFORM Consumers Act)", "欧盟"],
                        "priority": "high"
                    }
                ],
                "jurisdictions": ["美国", "欧盟", "中国"],
                "risk_level": "medium",
                "recommendations": [
                    "建立卖家 KYC 流程",
                    "实施交易担保机制",
                    "建立争议解决系统",
                    "定期审核卖家资质",
                    "保存交易记录备查"
                ]
            }
        }
        
        if website_type in type_compliance:
            compliance = type_compliance[website_type]
            result["requirements"].extend(compliance["requirements"])
            result["jurisdictions"] = compliance["jurisdictions"]
            result["risk_level"] = compliance["risk_level"]
            result["recommendations"] = compliance["recommendations"]
        
        return result


class ContentAnalyzer:
    """Analyze website content"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
    
    def analyze_homepage(self) -> Dict:
        """Analyze homepage content"""
        try:
            response = self.session.get(self.base_url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            return {
                "status_code": response.status_code,
                "content_type": response.headers.get('Content-Type', ''),
                "server": response.headers.get('Server', ''),
                "title": soup.title.string if soup.title else None,
                "description": self._get_meta(soup, 'description'),
                "keywords": self._get_meta(soup, 'keywords'),
                "viewport": self._get_meta(soup, 'viewport'),
                "lang": soup.html.get('lang') if soup.html else None,
                "heading_structure": self._analyze_headings(soup),
                "links": self._count_links(soup),
                "images": self._count_images(soup),
                "scripts": len(soup.find_all('script')),
                "stylesheets": len(soup.find_all('link', rel='stylesheet')),
            }
        except Exception as e:
            return {"error": str(e)}
    
    def extract_json_ld(self) -> List[Dict]:
        """Extract Schema.org JSON-LD structured data"""
        try:
            response = self.session.get(self.base_url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            schemas = []
            
            for script in json_ld_scripts:
                try:
                    data = json.loads(script.string)
                    schemas.append({
                        "@context": data.get("@context"),
                        "@type": data.get("@type"),
                        "data": data
                    })
                except:
                    continue
            
            return schemas
        except Exception as e:
            return [{"error": str(e)}]
    
    def fetch_robots_txt(self) -> str:
        """Fetch and parse robots.txt"""
        try:
            parsed = urllib.parse.urlparse(self.base_url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            response = self.session.get(robots_url, timeout=10)
            
            if response.status_code == 200:
                return response.text[:2000]
            return f"Status: {response.status_code}"
        except Exception as e:
            return f"Error: {e}"
    
    def fetch_llms_txt(self) -> str:
        """Fetch and parse llms.txt"""
        try:
            parsed = urllib.parse.urlparse(self.base_url)
            llms_url = f"{parsed.scheme}://{parsed.netloc}/llms.txt"
            response = self.session.get(llms_url, timeout=10)
            
            if response.status_code == 200:
                return response.text[:2000]
            return f"Not found (Status: {response.status_code})"
        except Exception as e:
            return f"Error: {e}"
    
    def fetch_sitemap(self) -> Dict:
        """Fetch and parse sitemap.xml"""
        try:
            parsed = urllib.parse.urlparse(self.base_url)
            sitemap_url = f"{parsed.scheme}://{parsed.netloc}/sitemap.xml"
            response = self.session.get(sitemap_url, timeout=10)
            
            if response.status_code != 200:
                # Try robots.txt to find sitemap
                robots = self.fetch_robots_txt()
                sitemap_match = re.search(r'Sitemap:\s*(.+)', robots, re.IGNORECASE)
                if sitemap_match:
                    sitemap_url = sitemap_match.group(1).strip()
                    response = self.session.get(sitemap_url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'xml')
                urls = soup.find_all('url')
                
                return {
                    "found": True,
                    "url": sitemap_url,
                    "url_count": len(urls),
                    "urls": [
                        {
                            "loc": url.loc.string if url.loc else None,
                            "lastmod": url.lastmod.string if url.lastmod else None,
                        }
                        for url in urls[:10]
                    ]
                }
            
            return {"found": False, "status": response.status_code}
        except Exception as e:
            return {"found": False, "error": str(e)}
    
    def _get_meta(self, soup: BeautifulSoup, name: str) -> Optional[str]:
        tag = soup.find('meta', attrs={'name': name})
        return tag.get('content') if tag else None
    
    def _analyze_headings(self, soup: BeautifulSoup) -> Dict:
        return {f"h{i}": len(soup.find_all(f'h{i}')) for i in range(1, 7)}
    
    def _count_links(self, soup: BeautifulSoup) -> Dict:
        links = soup.find_all('a', href=True)
        internal = 0
        external = 0
        base_domain = urllib.parse.urlparse(self.base_url).netloc
        
        for link in links:
            href = link['href']
            if href.startswith('http'):
                if base_domain in href:
                    internal += 1
                else:
                    external += 1
            elif href.startswith('/'):
                internal += 1
        
        return {"internal": internal, "external": external, "total": len(links)}
    
    def _count_images(self, soup: BeautifulSoup) -> Dict:
        images = soup.find_all('img')
        with_alt = sum(1 for img in images if img.get('alt'))
        return {"total": len(images), "with_alt": with_alt, "without_alt": len(images) - with_alt}


class SEOAnalyzer:
    """Analyze SEO metrics"""
    
    @staticmethod
    def analyze(content_analysis: Dict) -> Dict:
        """Generate SEO recommendations"""
        issues = []
        score = 100
        
        if not content_analysis.get('title'):
            issues.append("Missing title tag")
            score -= 15
        
        if not content_analysis.get('description'):
            issues.append("Missing meta description")
            score -= 10
        
        if not content_analysis.get('viewport'):
            issues.append("Missing viewport meta tag")
            score -= 10
        
        images = content_analysis.get('images', {})
        if images.get('without_alt', 0) > 0:
            issues.append(f"{images['without_alt']} images missing alt text")
            score -= 5
        
        headings = content_analysis.get('heading_structure', {})
        if headings.get('h1', 0) == 0:
            issues.append("Missing H1 heading")
            score -= 10
        
        return {"score": max(0, score), "issues": issues}


class ThirdPartyAnalyzer:
    """Analyze third-party data"""
    
    @staticmethod
    def check_google_index(domain: str) -> Dict:
        """Check Google index status"""
        try:
            response = requests.get(
                f"https://www.google.com/search?q=site:{domain}",
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10
            )
            
            match = re.search(r'About ([\d,]+) results', response.text)
            if match:
                return {"indexed": True, "approx_pages": match.group(1)}
            
            if "did not match any documents" in response.text:
                return {"indexed": False, "approx_pages": 0}
            
            return {"indexed": True, "approx_pages": "Unknown"}
        except Exception as e:
            return {"error": str(e)}


class WebsiteScanner:
    """Main scanner orchestrating all analysis modules"""
    
    def __init__(self, url: str, deep_scan: bool = False, max_pages: int = 5):
        self.url = url if url.startswith('http') else f"https://{url}"
        self.domain = urllib.parse.urlparse(self.url).netloc
        self.deep_scan = deep_scan
        self.max_pages = max_pages
        self.result = ScanResult(url=self.url, domain=self.domain)
    
    def scan(self) -> ScanResult:
        """Run complete website scan"""
        print(f"🔍 Scanning {self.domain}...")
        
        # 1. IP Analysis
        print("  📍 Resolving IP addresses...")
        self.result.ip_info = IPAnalyzer.resolve_hostname(self.domain)
        if self.result.ip_info.get("ipv4"):
            print("  🌍 Getting IP geolocation...")
            self.result.ip_info["geolocation"] = IPAnalyzer.get_ip_geolocation(
                self.result.ip_info["ipv4"][0]
            )
        
        # 2. DNS Analysis
        print("  🌐 Querying DNS records...")
        self.result.dns_info = DNSAnalyzer.query_dns(self.domain)
        
        # 3. WHOIS Analysis
        print("  📋 Querying WHOIS...")
        self.result.whois_info = WHOISAnalyzer.query_whois(self.domain)
        
        # 4. Content Analysis
        print("  📄 Analyzing homepage...")
        analyzer = ContentAnalyzer(self.url)
        self.result.content_analysis = analyzer.analyze_homepage()
        self.result.metadata["json_ld_schemas"] = analyzer.extract_json_ld()
        self.result.robots_txt = analyzer.fetch_robots_txt()
        self.result.llms_txt = analyzer.fetch_llms_txt()
        self.result.sitemap_data = analyzer.fetch_sitemap()
        
        # 5. SEO Analysis
        print("  📊 Analyzing SEO...")
        self.result.seo_data = SEOAnalyzer.analyze(self.result.content_analysis)
        
        # 6. Third-party Analysis
        print("  🔎 Checking Google index...")
        self.result.third_party["google_index"] = ThirdPartyAnalyzer.check_google_index(self.domain)
        
        # 7. Compliance Analysis
        print("  ⚖️  Analyzing compliance requirements...")
        html_content = ""
        try:
            resp = requests.get(self.url, timeout=30)
            html_content = resp.text
        except:
            pass
        self.result.compliance_analysis = ComplianceAnalyzer.analyze(
            self.url, self.result.content_analysis, html_content
        )

        # 7. Deep scan
        if self.deep_scan and self.result.sitemap_data.get("urls"):
            print(f"  🔬 Deep scanning...")
            self._deep_scan(analyzer)
        
        print("✅ Scan complete!")
        return self.result
    
    def _deep_scan(self, analyzer: ContentAnalyzer):
        """Scan additional pages from sitemap"""
        urls = self.result.sitemap_data.get("urls", [])[:self.max_pages]
        
        for url_data in urls:
            url = url_data.get("loc")
            if not url or url == self.url:
                continue
            
            try:
                response = analyzer.session.get(url, timeout=15)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                self.result.pages_scanned.append({
                    "url": url,
                    "status": response.status_code,
                    "title": soup.title.string if soup.title else None,
                })
            except Exception as e:
                self.result.pages_scanned.append({"url": url, "error": str(e)})
    
    def generate_report(self) -> str:
        """Generate human-readable report"""
        r = self.result
        
        report = f"""# Website Scan Report: {r.domain}

**Scan Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Target URL:** {r.url}

---

## 📍 IP & Network Information

### IP Addresses
- **IPv4:** {', '.join(r.ip_info.get('ipv4', ['N/A']))}
- **IPv6:** {', '.join(r.ip_info.get('ipv6', ['N/A']))}

### Server Location
{r.ip_info.get('geolocation', {}).get('city', 'N/A')}, {r.ip_info.get('geolocation', {}).get('country', 'N/A')}  
**Organization:** {r.ip_info.get('geolocation', {}).get('org', 'N/A')}

### DNS Records
"""
        for record_type, values in r.dns_info.items():
            if values and not str(values[0]).startswith("Error"):
                report += f"- **{record_type}:** {', '.join(values[:3])}\n"
        
        report += f"""
---

## 📋 WHOIS Information

**Registrar:** {r.whois_info.get('registrar', 'N/A')}  
**Creation Date:** {r.whois_info.get('creation_date', 'N/A')}  
**Expiration Date:** {r.whois_info.get('expiration_date', 'N/A')}  
**Registrant:** {r.whois_info.get('registrant_org', 'N/A')}

---

## 📄 Content Analysis

### Homepage Metadata
- **Title:** {r.content_analysis.get('title', 'N/A')}
- **Description:** {r.content_analysis.get('description', 'N/A')[:100] if r.content_analysis.get('description') else 'N/A'}...
- **Language:** {r.content_analysis.get('lang', 'N/A')}
- **Server:** {r.content_analysis.get('server', 'N/A')}

### Page Statistics
- **Links:** {r.content_analysis.get('links', {}).get('total', 0)} total ({r.content_analysis.get('links', {}).get('internal', 0)} internal, {r.content_analysis.get('links', {}).get('external', 0)} external)
- **Images:** {r.content_analysis.get('images', {}).get('total', 0)} ({r.content_analysis.get('images', {}).get('with_alt', 0)} with alt text)
- **Scripts:** {r.content_analysis.get('scripts', 0)}

### Structured Data (JSON-LD)
Found {len(r.metadata.get('json_ld_schemas', []))} schema(s)

---

## 🤖 robots.txt & llms.txt

### robots.txt
```
{r.robots_txt[:500]}
```

### llms.txt
{r.llms_txt[:300] if 'Not found' not in r.llms_txt else '*Not found*'}

---

## 🗺️ Sitemap

**Status:** {'✅ Found' if r.sitemap_data.get('found') else '❌ Not found'}  
**URL Count:** {r.sitemap_data.get('url_count', 0)}

---

## 📊 SEO Analysis

**Score:** {r.seo_data.get('score', 0)}/100

### Issues Found
"""
        for issue in r.seo_data.get('issues', []):
            report += f"- {issue}\n"
        
        report += f"""
---

## 🔍 Third-Party Data

### Google Index
**Indexed:** {r.third_party.get('google_index', {}).get('indexed', 'Unknown')}  
**Approximate Pages:** {r.third_party.get('google_index', {}).get('approx_pages', 'Unknown')}

---

*Report generated by Website Scanner*
"""
        return report
    
    def save_json_report(self, filename: str):
        """Save report as JSON"""
        data = {
            "scan_info": {
                "url": self.result.url,
                "domain": self.result.domain,
                "scan_date": datetime.now().isoformat()
            },
            "ip_info": self.result.ip_info,
            "ip_info": self.result.ip_info,
            "dns_info": self.result.dns_info,
            "whois_info": self.result.whois_info,
            "content_analysis": self.result.content_analysis,
            "seo": self.result.seo_data,
            "sitemap": self.result.sitemap_data,
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


    def generate_pdf_report(self, filename: str):
        """Generate comprehensive PDF report with all scan data"""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Preformatted
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            
            doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=60, leftMargin=60, topMargin=60, bottomMargin=18)
            styles = getSampleStyleSheet()
            story = []
            
            # Helper function to create styled tables
            def create_table(data, col_widths=None, header_bg=colors.HexColor('#1a73e8')):
                if col_widths is None:
                    col_widths = [2*inch, 4.5*inch]
                table = Table(data, colWidths=col_widths)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
                    ('BACKGROUND', (0, 0), (-1, 0), header_bg) if len(data) > 0 and data[0][0] != 'IPv4' else None,
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke) if len(data) > 0 and data[0][0] != 'IPv4' else None,
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold') if len(data) > 0 and data[0][0] != 'IPv4' else None,
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                return table
            
            # Title
            title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=28, spaceAfter=20, textColor=colors.HexColor('#1a73e8'))
            story.append(Paragraph("Website Scan Report", title_style))
            story.append(Paragraph(f"<b>{self.result.domain}</b>", styles['Heading2']))
            story.append(Paragraph(f"Scan Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Target: {self.result.url}", styles['Normal']))
            story.append(Spacer(1, 0.25*inch))
            
            # ============================================
            # 1. IP & NETWORK INFORMATION
            # ============================================
            story.append(Paragraph("<b>1. IP & Network Information</b>", styles['Heading2']))
            story.append(Spacer(1, 0.1*inch))
            
            ip_data = []
            # IPv4 addresses
            ipv4_list = self.result.ip_info.get('ipv4', [])
            ip_data.append(['IPv4 Addresses', ', '.join(ipv4_list) if ipv4_list else 'N/A'])
            
            # IPv6 addresses
            ipv6_list = self.result.ip_info.get('ipv6', [])
            ip_data.append(['IPv6 Addresses', ', '.join(ipv6_list) if ipv6_list else 'N/A'])
            
            # Geolocation
            geo = self.result.ip_info.get('geolocation', {})
            if geo:
                ip_data.extend([
                    ['City', geo.get('city', 'N/A')],
                    ['Region', geo.get('region', 'N/A')],
                    ['Country', f"{geo.get('country', 'N/A')} ({geo.get('country_code', 'N/A')})"],
                    ['Latitude', str(geo.get('latitude', 'N/A'))],
                    ['Longitude', str(geo.get('longitude', 'N/A'))],
                    ['Organization', geo.get('org', 'N/A')],
                    ['ASN', str(geo.get('asn', 'N/A'))],
                    ['Timezone', geo.get('timezone', 'N/A')],
                ])
            
            story.append(create_table(ip_data))
            story.append(Spacer(1, 0.2*inch))
            
            # ============================================
            # 2. DNS RECORDS
            # ============================================
            story.append(Paragraph("<b>2. DNS Records</b>", styles['Heading2']))
            story.append(Spacer(1, 0.1*inch))
            
            dns_data = [['Record Type', 'Values']]
            for record_type in ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME', 'SOA']:
                values = self.result.dns_info.get(record_type, [])
                if values and not str(values[0]).startswith("Error"):
                    # Join all values with line breaks for better readability
                    formatted_values = '\n'.join(values[:5])  # Limit to 5 entries
                    if len(values) > 5:
                        formatted_values += f"\n... ({len(values) - 5} more)"
                    dns_data.append([record_type, formatted_values])
                elif values and str(values[0]).startswith("Error"):
                    dns_data.append([record_type, values[0]])
            
            if len(dns_data) > 1:
                story.append(create_table(dns_data, col_widths=[1.2*inch, 5.3*inch]))
            else:
                story.append(Paragraph("No DNS records found.", styles['Normal']))
            story.append(PageBreak())
            
            # ============================================
            # 3. WHOIS INFORMATION
            # ============================================
            story.append(Paragraph("<b>3. WHOIS Domain Information</b>", styles['Heading2']))
            story.append(Spacer(1, 0.1*inch))
            
            whois = self.result.whois_info
            whois_data = [
                ['Registrar', whois.get('registrar', 'N/A')],
                ['Creation Date', whois.get('creation_date', 'N/A')],
                ['Expiration Date', whois.get('expiration_date', 'N/A')],
                ['Registrant Organization', whois.get('registrant_org', 'N/A')],
                ['Registrant Country', whois.get('registrant_country', 'N/A')],
                ['Domain Status', '\n'.join(whois.get('status', ['N/A']))[:200]],
                ['Name Servers', '\n'.join(whois.get('name_servers', ['N/A']))[:200]],
            ]
            story.append(create_table(whois_data))
            story.append(Spacer(1, 0.25*inch))
            
            # ============================================
            # 4. CONTENT ANALYSIS
            # ============================================
            story.append(Paragraph("<b>4. Content Analysis</b>", styles['Heading2']))
            story.append(Spacer(1, 0.1*inch))
            
            c = self.result.content_analysis
            
            # Basic metadata
            story.append(Paragraph("<b>4.1 Homepage Metadata</b>", styles['Heading3']))
            meta_data = [
                ['Status Code', str(c.get('status_code', 'N/A'))],
                ['Content Type', c.get('content_type', 'N/A')],
                ['Server', c.get('server', 'N/A')],
                ['Title', (c.get('title') or 'N/A')[:80]],
                ['Meta Description', ((c.get('description') or 'N/A'))[:120]],
                ['Meta Keywords', (c.get('keywords') or 'N/A')[:80]],
                ['Viewport', (c.get('viewport') or 'N/A')[:80]],
                ['Language', c.get('lang', 'N/A')],
            ]
            story.append(create_table(meta_data))
            story.append(Spacer(1, 0.15*inch))
            
            # Links analysis
            story.append(Paragraph("<b>4.2 Links Analysis</b>", styles['Heading3']))
            links = c.get('links', {})
            links_data = [
                ['Total Links', str(links.get('total', 0))],
                ['Internal Links', str(links.get('internal', 0))],
                ['External Links', str(links.get('external', 0))],
            ]
            story.append(create_table(links_data))
            story.append(Spacer(1, 0.15*inch))
            
            # Images analysis
            story.append(Paragraph("<b>4.3 Images Analysis</b>", styles['Heading3']))
            images = c.get('images', {})
            images_data = [
                ['Total Images', str(images.get('total', 0))],
                ['With Alt Text', str(images.get('with_alt', 0))],
                ['Without Alt Text', str(images.get('without_alt', 0))],
            ]
            story.append(create_table(images_data))
            story.append(Spacer(1, 0.15*inch))
            
            # Page resources
            story.append(Paragraph("<b>4.4 Page Resources</b>", styles['Heading3']))
            resources_data = [
                ['JavaScript Files', str(c.get('scripts', 0))],
                ['Stylesheets', str(c.get('stylesheets', 0))],
            ]
            story.append(create_table(resources_data))
            story.append(Spacer(1, 0.15*inch))
            
            # Heading structure
            story.append(Paragraph("<b>4.5 Heading Structure</b>", styles['Heading3']))
            headings = c.get('heading_structure', {})
            headings_data = [['Tag', 'Count']]
            for i in range(1, 7):
                count = headings.get(f'h{i}', 0)
                headings_data.append([f'H{i}', str(count)])
            story.append(create_table(headings_data, col_widths=[1.5*inch, 5*inch]))
            story.append(PageBreak())
            
            # ============================================
            # 5. STRUCTURED DATA
            # ============================================
            story.append(Paragraph("<b>5. Structured Data (JSON-LD)</b>", styles['Heading2']))
            json_ld = self.result.metadata.get('json_ld_schemas', [])
            story.append(Paragraph(f"Found <b>{len(json_ld)}</b> JSON-LD schema(s)", styles['Normal']))
            if json_ld:
                for i, schema in enumerate(json_ld[:3], 1):  # Show first 3 schemas
                    story.append(Spacer(1, 0.1*inch))
                    story.append(Paragraph(f"Schema {i}: @{schema.get('@context', 'N/A')} / {schema.get('@type', 'N/A')}", styles['Normal']))
            story.append(Spacer(1, 0.25*inch))
            
            # ============================================
            # 6. CRAWLER FILES
            # ============================================
            story.append(Paragraph("<b>6. Crawler Files</b>", styles['Heading2']))
            story.append(Spacer(1, 0.1*inch))
            
            # robots.txt
            story.append(Paragraph("<b>6.1 robots.txt</b>", styles['Heading3']))
            robots = self.result.robots_txt
            if robots and not robots.startswith('Error') and not robots.startswith('Status'):
                # Truncate and clean for PDF
                robots_clean = robots[:1500].replace('<', '&lt;').replace('>', '&gt;')
                story.append(Preformatted(robots_clean, styles['Code']))
            else:
                story.append(Paragraph(f"Status: {robots}", styles['Normal']))
            story.append(Spacer(1, 0.15*inch))
            
            # llms.txt
            story.append(Paragraph("<b>6.2 llms.txt</b>", styles['Heading3']))
            llms = self.result.llms_txt
            if llms and 'Not found' not in llms and not llms.startswith('Error'):
                llms_clean = llms[:1000].replace('<', '&lt;').replace('>', '&gt;')
                story.append(Preformatted(llms_clean, styles['Code']))
            else:
                story.append(Paragraph(f"Status: {llms}", styles['Normal']))
            story.append(Spacer(1, 0.15*inch))
            
            # sitemap
            story.append(Paragraph("<b>6.3 Sitemap</b>", styles['Heading3']))
            sitemap = self.result.sitemap_data
            sitemap_data = [
                ['Found', 'Yes' if sitemap.get('found') else 'No'],
                ['URL Count', str(sitemap.get('url_count', 0))],
                ['Sitemap URL', sitemap.get('url', 'N/A')],
            ]
            story.append(create_table(sitemap_data))
            story.append(PageBreak())
            
            # ============================================
            # 7. SEO ANALYSIS
            # ============================================
            story.append(Paragraph("<b>7. SEO Analysis</b>", styles['Heading2']))
            story.append(Spacer(1, 0.1*inch))
            
            score = self.result.seo_data.get('score', 0)
            score_color = colors.green if score >= 80 else colors.orange if score >= 60 else colors.red
            story.append(Paragraph(f"SEO Score: <font color='{score_color.hexval()}' size='16'><b>{score}/100</b></font>", styles['Heading3']))
            story.append(Spacer(1, 0.1*inch))
            
            issues = self.result.seo_data.get('issues', [])
            if issues:
                story.append(Paragraph("<b>Issues Found:</b>", styles['Heading4']))
                for issue in issues:
                    story.append(Paragraph(f"• {issue}", styles['Normal']))
            else:
                story.append(Paragraph("<font color='green'>✓ No major SEO issues found!</font>", styles['Normal']))
            story.append(Spacer(1, 0.25*inch))
            
            # ============================================
            # 8. THIRD-PARTY DATA
            # ============================================
            story.append(Paragraph("<b>8. Third-Party Data</b>", styles['Heading2']))
            story.append(Spacer(1, 0.1*inch))
            
            story.append(Paragraph("<b>8.1 Google Index Status</b>", styles['Heading3']))
            google = self.result.third_party.get('google_index', {})
            google_data = [
                ['Indexed', str(google.get('indexed', 'Unknown'))],
                ['Approximate Pages', str(google.get('approx_pages', 'Unknown'))],
            ]
            if google.get('error'):
                google_data.append(['Error', google.get('error')])
            story.append(create_table(google_data))
            story.append(Spacer(1, 0.25*inch))
            
            # ============================================
            # 9. DEEP SCAN RESULTS (if applicable)
            # ============================================
            if self.result.pages_scanned:
                story.append(Paragraph("<b>9. Deep Scan Results</b>", styles['Heading2']))
                story.append(Paragraph(f"Pages scanned: {len(self.result.pages_scanned)}", styles['Normal']))
                for page in self.result.pages_scanned[:5]:  # Show first 5 pages
                    url = page.get('url', 'N/A')
                    status = page.get('status', page.get('error', 'N/A'))
                    title = page.get('title', 'N/A')
                    story.append(Paragraph(f"• {url[:60]}... (Status: {status})", styles['Normal']))
                story.append(Spacer(1, 0.25*inch))
            
            # ============================================
            # FOOTER
            # ============================================
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph("<i>Report generated by Website Scanner</i>", styles['Normal']))
            
            doc.build(story)
            print(f"✅ PDF report saved: {filename}")
        except Exception as e:
            print(f"❌ PDF generation error: {e}")
            import traceback
            traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description='Comprehensive website scanner')
    parser.add_argument('url', help='Website URL to scan')
    parser.add_argument('--deep', '-d', action='store_true', help='Enable deep scan')
    parser.add_argument('--max-pages', '-m', type=int, default=5, help='Max pages to scan')
    parser.add_argument('--output', '-o', help='Output JSON file')
    parser.add_argument('--pdf', '-p', help='Output PDF file')
    
    args = parser.parse_args()
    
    scanner = WebsiteScanner(args.url, deep_scan=args.deep, max_pages=args.max_pages)
    scanner.scan()
    
    print("\n" + "="*60)
    print(scanner.generate_report())
    
    if args.output:
        scanner.save_json_report(args.output)
        print(f"\nJSON saved: {args.output}")
    
    if args.pdf:
        scanner.generate_pdf_report(args.pdf)


if __name__ == '__main__':
    main()