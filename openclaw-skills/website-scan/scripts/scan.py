#!/usr/bin/env python3
"""
Website Scanner - Comprehensive website analysis tool
Analyzes IP, DNS, WHOIS, content, SEO, and generates reports
"""

import argparse
import json
import socket
import ssl
import subprocess
import urllib.request
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, urljoin

# Import compliance analyzer
try:
    from compliance_analyzer import ComplianceAnalyzer
    COMPLIANCE_AVAILABLE = True
except ImportError:
    COMPLIANCE_AVAILABLE = False

# Optional imports with fallbacks
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


@dataclass
class ScanResult:
    """Container for all scan results"""
    url: str
    domain: str
    timestamp: str
    ip_info: Dict = field(default_factory=dict)
    dns_info: Dict = field(default_factory=dict)
    whois_info: Dict = field(default_factory=dict)
    content_analysis: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)
    robots_txt: str = ""
    llms_txt: str = ""
    sitemap_data: Dict = field(default_factory=dict)
    seo_data: Dict = field(default_factory=dict)
    third_party: Dict = field(default_factory=dict)
    pages_scanned: List = field(default_factory=list)
    compliance_analysis: Dict = field(default_factory=dict)


class IPAnalyzer:
    """Analyze IP addresses and geolocation"""
    
    def analyze(self, domain: str) -> Dict:
        result = {"ipv4": [], "ipv6": [], "geolocation": {}}
        
        # Get IP addresses
        try:
            addr_info = socket.getaddrinfo(domain, None)
            for info in addr_info:
                ip = info[4][0]
                if ":" in ip and ip not in result["ipv6"]:
                    result["ipv6"].append(ip)
                elif ":" not in ip and ip not in result["ipv4"]:
                    result["ipv4"].append(ip)
        except Exception as e:
            result["error"] = str(e)
        
        # Geolocation lookup (using free IP-API)
        if result["ipv4"]:
            try:
                import urllib.request
                with urllib.request.urlopen(f"http://ip-api.com/json/{result['ipv4'][0]}", timeout=5) as response:
                    data = json.loads(response.read())
                    result["geolocation"] = {
                        "country": data.get("country"),
                        "city": data.get("city"),
                        "region": data.get("regionName"),
                        "org": data.get("org"),
                        "isp": data.get("isp"),
                    }
            except Exception:
                pass
        
        return result


class DNSAnalyzer:
    """Analyze DNS records"""
    
    RECORD_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]
    
    def analyze(self, domain: str) -> Dict:
        result = {}
        
        for record_type in self.RECORD_TYPES:
            try:
                output = subprocess.run(
                    ["dig", "+short", record_type, domain],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                lines = [l.strip() for l in output.stdout.strip().split("\n") if l.strip()]
                result[record_type] = lines if lines else ["No records found"]
            except Exception as e:
                result[record_type] = [f"Error: {str(e)}"]
        
        return result


class WHOISAnalyzer:
    """Analyze WHOIS domain information"""
    
    def analyze(self, domain: str) -> Dict:
        result = {}
        
        try:
            output = subprocess.run(
                ["whois", domain],
                capture_output=True,
                text=True,
                timeout=15
            )
            whois_text = output.stdout
            
            # Parse common WHOIS fields
            result["raw"] = whois_text[:2000]  # First 2000 chars
            
            # Extract key fields
            lines = whois_text.split("\n")
            for line in lines:
                line_lower = line.lower()
                if "registrar:" in line_lower and "registrar" not in result:
                    result["registrar"] = line.split(":", 1)[1].strip()
                elif "creation date:" in line_lower or "created:" in line_lower:
                    result["creation_date"] = line.split(":", 1)[1].strip()
                elif "registry expiry date:" in line_lower or "expiration date:" in line_lower:
                    result["expiration_date"] = line.split(":", 1)[1].strip()
                    
        except Exception as e:
            result["error"] = str(e)
        
        return result


class ContentAnalyzer:
    """Analyze website content"""
    
    def analyze(self, url: str) -> Dict:
        result = {
            "title": None,
            "description": None,
            "lang": None,
            "server": None,
            "links": {"internal": 0, "external": 0, "total": 0},
            "images": {"total": 0, "with_alt": 0},
            "scripts": 0,
        }
        
        if not REQUESTS_AVAILABLE or not BS4_AVAILABLE:
            result["error"] = "Missing dependencies: requests, beautifulsoup4"
            return result
        
        try:
            response = requests.get(url, timeout=30, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            result["status_code"] = response.status_code
            result["server"] = response.headers.get("Server", "Unknown")
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Basic metadata
            result["title"] = soup.title.string if soup.title else None
            
            meta_desc = soup.find("meta", attrs={"name": "description"})
            result["description"] = meta_desc.get("content") if meta_desc else None
            
            html_tag = soup.find("html")
            result["lang"] = html_tag.get("lang") if html_tag else None
            
            # Links
            links = soup.find_all("a", href=True)
            result["links"]["total"] = len(links)
            parsed_url = urlparse(url)
            for link in links:
                href = link["href"]
                if href.startswith("http"):
                    if parsed_url.netloc in href:
                        result["links"]["internal"] += 1
                    else:
                        result["links"]["external"] += 1
                elif href.startswith("/"):
                    result["links"]["internal"] += 1
            
            # Images
            images = soup.find_all("img")
            result["images"]["total"] = len(images)
            result["images"]["with_alt"] = sum(1 for img in images if img.get("alt"))
            
            # Scripts
            result["scripts"] = len(soup.find_all("script"))
            
            # JSON-LD structured data
            json_ld_scripts = soup.find_all("script", type="application/ld+json")
            result["json_ld_schemas"] = []
            for script in json_ld_scripts:
                try:
                    schema = json.loads(script.string)
                    result["json_ld_schemas"].append(schema.get("@type", "Unknown"))
                except:
                    pass
                    
        except Exception as e:
            result["error"] = str(e)
        
        return result


class SEOAnalyzer:
    """Analyze SEO metrics"""
    
    def analyze(self, content_analysis: Dict, url: str) -> Dict:
        result = {"score": 0, "issues": [], "recommendations": []}
        
        # Check title
        title = content_analysis.get("title")
        if not title:
            result["issues"].append("Missing title tag")
        elif len(title) < 10:
            result["issues"].append(f"Title too short ({len(title)} chars)")
        elif len(title) > 70:
            result["issues"].append(f"Title too long ({len(title)} chars)")
        else:
            result["score"] += 20
        
        # Check description
        desc = content_analysis.get("description")
        if not desc:
            result["issues"].append("Missing meta description")
        elif len(desc) < 50:
            result["issues"].append(f"Description too short ({len(desc)} chars)")
        elif len(desc) > 160:
            result["issues"].append(f"Description too long ({len(desc)} chars)")
        else:
            result["score"] += 20
        
        # Check images alt text
        images = content_analysis.get("images", {})
        if images.get("total", 0) > 0:
            alt_ratio = images.get("with_alt", 0) / images["total"]
            if alt_ratio < 0.5:
                result["issues"].append(f"Many images missing alt text ({images['with_alt']}/{images['total']})")
            else:
                result["score"] += 20
        
        # Check HTTPS
        if url.startswith("https://"):
            result["score"] += 20
        else:
            result["issues"].append("Site not using HTTPS")
        
        # Check language
        if content_analysis.get("lang"):
            result["score"] += 20
        else:
            result["issues"].append("Missing language attribute")
        
        return result


class ThirdPartyAnalyzer:
    """Fetch third-party data about the website"""
    
    def analyze(self, url: str) -> Dict:
        result = {"google_index": {}}
        
        # Try to estimate Google index
        domain = urlparse(url).netloc
        try:
            # Simple check via Google search query
            search_url = f"https://www.google.com/search?q=site:{domain}"
            if REQUESTS_AVAILABLE:
                response = requests.get(search_url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }, timeout=10)
                
                if "did not match" in response.text.lower() or "no results" in response.text.lower():
                    result["google_index"]["indexed"] = "No"
                    result["google_index"]["approx_pages"] = "0"
                else:
                    result["google_index"]["indexed"] = "Yes"
                    # Try to extract approximate count
                    import re
                    matches = re.search(r'about ([\d,]+) results', response.text, re.IGNORECASE)
                    if matches:
                        result["google_index"]["approx_pages"] = matches.group(1)
                    else:
                        result["google_index"]["approx_pages"] = "Unknown"
            else:
                result["google_index"]["indexed"] = "Unable to check"
                result["google_index"]["error"] = "requests library not available"
                
        except Exception as e:
            result["google_index"]["indexed"] = "Error"
            result["google_index"]["error"] = str(e)
        
        return result


class WebsiteScanner:
    """Main scanner class that orchestrates all analysis"""
    
    def __init__(self, url: str, deep_scan: bool = False, max_pages: int = 5):
        self.url = url if url.startswith("http") else f"https://{url}"
        self.domain = urlparse(self.url).netloc
        self.deep_scan = deep_scan
        self.max_pages = max_pages
        self.result = ScanResult(
            url=self.url,
            domain=self.domain,
            timestamp=datetime.now().isoformat()
        )
        
        # Initialize analyzers
        self.ip_analyzer = IPAnalyzer()
        self.dns_analyzer = DNSAnalyzer()
        self.whois_analyzer = WHOISAnalyzer()
        self.content_analyzer = ContentAnalyzer()
        self.seo_analyzer = SEOAnalyzer()
        self.third_party_analyzer = ThirdPartyAnalyzer()
        
        # Initialize compliance analyzer if available
        if COMPLIANCE_AVAILABLE:
            self.compliance_analyzer = ComplianceAnalyzer()
        else:
            self.compliance_analyzer = None
    
    def scan(self):
        """Run all analyses"""
        print(f"🔍 Scanning {self.url}...")
        
        # IP Analysis
        print("  📍 Analyzing IP addresses...")
        self.result.ip_info = self.ip_analyzer.analyze(self.domain)
        
        # DNS Analysis
        print("  🌐 Analyzing DNS records...")
        self.result.dns_info = self.dns_analyzer.analyze(self.domain)
        
        # WHOIS Analysis
        print("  📋 Fetching WHOIS data...")
        self.result.whois_info = self.whois_analyzer.analyze(self.domain)
        
        # Content Analysis
        print("  📄 Analyzing content...")
        self.result.content_analysis = self.content_analyzer.analyze(self.url)
        
        # Extract metadata from content analysis
        self.result.metadata["json_ld_schemas"] = self.result.content_analysis.get("json_ld_schemas", [])
        
        # Fetch robots.txt
        print("  🤖 Checking robots.txt...")
        self.result.robots_txt = self._fetch_file("/robots.txt")
        
        # Fetch llms.txt
        print("  📖 Checking llms.txt...")
        self.result.llms_txt = self._fetch_file("/llms.txt")
        
        # Sitemap
        print("  🗺️ Checking sitemap...")
        self.result.sitemap_data = self._check_sitemap()
        
        # SEO Analysis
        print("  📊 Analyzing SEO...")
        self.result.seo_data = self.seo_analyzer.analyze(
            self.result.content_analysis, self.url
        )
        
        # Third-party data
        print("  🔎 Fetching third-party data...")
        self.result.third_party = self.third_party_analyzer.analyze(self.url)
        
        # Compliance Analysis
        if self.compliance_analyzer:
            print("  ⚖️  Analyzing compliance requirements...")
            self.result.compliance_analysis = self.compliance_analyzer.analyze(
                self.result.content_analysis, self.url, self.domain
            )
        
        # Deep scan if requested
        if self.deep_scan:
            print("  🔬 Running deep scan...")
            self._deep_scan()
        
        print("✅ Scan complete!")
    
    def _fetch_file(self, path: str) -> str:
        """Fetch a file from the website"""
        if not REQUESTS_AVAILABLE:
            return "requests library not available"
        
        try:
            url = urljoin(self.url, path)
            response = requests.get(url, timeout=10, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            if response.status_code == 200:
                return response.text[:2000]  # First 2000 chars
            else:
                return f"Not found (HTTP {response.status_code})"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _check_sitemap(self) -> Dict:
        """Check for sitemap.xml"""
        result = {"found": False, "url_count": 0, "urls": []}
        
        if not REQUESTS_AVAILABLE:
            return result
        
        try:
            response = requests.get(urljoin(self.url, "/sitemap.xml"), timeout=10)
            if response.status_code == 200:
                result["found"] = True
                # Count URLs
                import re
                urls = re.findall(r'<loc>(.*?)</loc>', response.text)
                result["url_count"] = len(urls)
                result["urls"] = urls[:10]  # First 10 URLs
        except Exception:
            pass
        
        return result
    
    def _deep_scan(self):
        """Scan multiple pages"""
        if not REQUESTS_AVAILABLE or not BS4_AVAILABLE:
            return
        
        # Get links from homepage
        try:
            response = requests.get(self.url, timeout=30)
            soup = BeautifulSoup(response.text, "html.parser")
            links = [urljoin(self.url, a["href"]) for a in soup.find_all("a", href=True)]
            links = [l for l in links if l.startswith(self.url)][:self.max_pages]
            
            for url in links:
                try:
                    response = requests.get(url, timeout=10)
                    soup = BeautifulSoup(response.text, "html.parser")
                    
                    self.result.pages_scanned.append({
                        "url": url,
                        "status": response.status_code,
                        "title": soup.title.string if soup.title else None,
                    })
                except Exception as e:
                    self.result.pages_scanned.append({"url": url, "error": str(e)})
        except Exception:
            pass
    
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

## ⚖️ Compliance Analysis

### Detected Website Type

primary_type = r.compliance_analysis.get('primary_type')
if primary_type:
    report += f"**Type:** {primary_type.get('name', 'N/A')}\n"
    report += f"**Confidence:** {primary_type.get('confidence', 0)}%\n"
    report += f"**Description:** {primary_type.get('description', 'N/A')}\n\n"
else:
    report += "No specific website type detected\n\n"

# Risk Level
report += f"**Risk Level:** {r.compliance_analysis.get('risk_level', 'low').upper()}\n\n"

# Jurisdictions
jurisdictions = r.compliance_analysis.get('jurisdictions', [])
if jurisdictions:
    report += "### Likely Jurisdictions\n"
    for j in jurisdictions:
        report += f"- {j}\n"
    report += "\n"

# Compliance Requirements
requirements = r.compliance_analysis.get('compliance_requirements', {})
if requirements:
    report += "### Compliance Requirements\n"
    for reg, info in requirements.items():
        report += f"**{reg}:** {info.get('description', 'N/A')}\n"
    report += "\n"

# Recommendations
recommendations = r.compliance_analysis.get('recommendations', [])
if recommendations:
    report += "### Recommendations\n"
    for rec in recommendations[:5]:  # Top 5
        report += f"- {rec}\n"
    report += "\n"

report += "---

*Report generated by Website Scanner*
"""
        return report
    
    def save_json_report(self, filename: str):
        """Save results as JSON"""
        with open(filename, "w") as f:
            json.dump(self.result.__dict__, f, indent=2, default=str)
    
    def generate_pdf_report(self, filename: str):
        """Generate PDF report using reportlab"""
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
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
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
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                textColor=colors.HexColor('#1a73e8'),
                alignment=1  # Center
            )
            story.append(Paragraph(f"Website Scan Report", title_style))
            story.append(Paragraph(f"<b>{self.result.domain}</b>", styles['Heading2']))
            story.append(Paragraph(f"Scan Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            
            # 1. IP Information
            story.append(Paragraph("<b>1. IP & Network Information</b>", styles['Heading2']))
            ip_data = [
                ['IPv4', ', '.join(self.result.ip_info.get('ipv4', ['N/A']))],
                ['IPv6', ', '.join(self.result.ip_info.get('ipv6', ['N/A']))],
            ]
            geo = self.result.ip_info.get('geolocation', {})
            if geo:
                ip_data.extend([
                    ['Country', geo.get('country', 'N/A')],
                    ['City', geo.get('city', 'N/A')],
                    ['Organization', geo.get('org', 'N/A')],
                ])
            story.append(create_table(ip_data))
            story.append(Spacer(1, 0.25*inch))
            
            # 2. DNS Records
            story.append(Paragraph("<b>2. DNS Records</b>", styles['Heading2']))
            dns_data = []
            for record_type, values in self.result.dns_info.items():
                display_values = ', '.join(values[:3]) if values and not str(values[0]).startswith('Error') else 'N/A'
                dns_data.append([record_type, display_values])
            story.append(create_table(dns_data))
            story.append(Spacer(1, 0.25*inch))
            story.append(PageBreak())
            
            # 3. WHOIS
            story.append(Paragraph("<b>3. WHOIS Information</b>", styles['Heading2']))
            whois_data = [
                ['Registrar', self.result.whois_info.get('registrar', 'N/A')],
                ['Creation Date', self.result.whois_info.get('creation_date', 'N/A')],
                ['Expiration Date', self.result.whois_info.get('expiration_date', 'N/A')],
            ]
            story.append(create_table(whois_data))
            story.append(Spacer(1, 0.25*inch))
            
            # 4. Content Analysis
            story.append(Paragraph("<b>4. Content Analysis</b>", styles['Heading2']))
            content_data = [
                ['Title', self.result.content_analysis.get('title', 'N/A') or 'N/A'],
                ['Description', (self.result.content_analysis.get('description', '') or '')[:100] + '...'],
                ['Language', self.result.content_analysis.get('lang', 'N/A') or 'N/A'],
                ['Server', self.result.content_analysis.get('server', 'N/A')],
            ]
            story.append(create_table(content_data))
            story.append(Spacer(1, 0.1*inch))
            
            # Page stats
            stats_data = [
                ['Total Links', str(self.result.content_analysis.get('links', {}).get('total', 0))],
                ['Internal Links', str(self.result.content_analysis.get('links', {}).get('internal', 0))],
                ['External Links', str(self.result.content_analysis.get('links', {}).get('external', 0))],
                ['Images', str(self.result.content_analysis.get('images', {}).get('total', 0))],
                ['Images with Alt', str(self.result.content_analysis.get('images', {}).get('with_alt', 0))],
                ['Scripts', str(self.result.content_analysis.get('scripts', 0))],
            ]
            story.append(create_table(stats_data))
            story.append(Spacer(1, 0.25*inch))
            
            # 5. Structured Data
            story.append(Paragraph("<b>5. Structured Data (JSON-LD)</b>", styles['Heading2']))
            schemas = self.result.metadata.get('json_ld_schemas', [])
            if schemas:
                story.append(Paragraph(f"Found {len(schemas)} schema(s): {', '.join(schemas)}", styles['Normal']))
            else:
                story.append(Paragraph("No JSON-LD schemas found", styles['Normal']))
            story.append(Spacer(1, 0.25*inch))
            story.append(PageBreak())
            
            # 6. Crawler Files
            story.append(Paragraph("<b>6. Crawler Files</b>", styles['Heading2']))
            
            story.append(Paragraph("<b>robots.txt</b>", styles['Heading3']))
            robots_text = self.result.robots_txt[:800] if self.result.robots_txt else "Not found"
            story.append(Preformatted(robots_text, styles['Code']))
            story.append(Spacer(1, 0.1*inch))
            
            story.append(Paragraph("<b>llms.txt</b>", styles['Heading3']))
            llms_text = self.result.llms_txt[:500] if self.result.llms_txt and 'Not found' not in self.result.llms_txt else "Not found"
            story.append(Preformatted(llms_text, styles['Code']))
            story.append(Spacer(1, 0.25*inch))
            
            # Sitemap
            story.append(Paragraph("<b>Sitemap</b>", styles['Heading3']))
            sitemap_status = "Found" if self.result.sitemap_data.get('found') else "Not found"
            sitemap_data = [
                ['Status', sitemap_status],
                ['URL Count', str(self.result.sitemap_data.get('url_count', 0))],
            ]
            story.append(create_table(sitemap_data))
            story.append(PageBreak())
            
            # 7. SEO Analysis
            story.append(Paragraph("<b>7. SEO Analysis</b>", styles['Heading2']))
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
            
            # 8. Third-Party Data
            story.append(Paragraph("<b>8. Third-Party Data</b>", styles['Heading2']))
            story.append(Paragraph("<b>Google Index Status</b>", styles['Heading3']))
            google = self.result.third_party.get('google_index', {})
            google_data = [
                ['Indexed', str(google.get('indexed', 'Unknown'))],
                ['Approximate Pages', str(google.get('approx_pages', 'Unknown'))],
            ]
            if google.get('error'):
                google_data.append(['Error', google.get('error')])
            story.append(create_table(google_data))
            story.append(Spacer(1, 0.25*inch))
            
            # 9. Compliance Analysis
            story.append(PageBreak())
            story.append(Paragraph("<b>9. Compliance Analysis</b>", styles['Heading2']))
            
            compliance = self.result.compliance_analysis
            
            # Detected Type
            primary_type = compliance.get('primary_type')
            if primary_type:
                story.append(Paragraph("<b>Detected Website Type</b>", styles['Heading3']))
                type_data = [
                    ['Type', primary_type.get('name', 'N/A')],
                    ['Confidence', f"{primary_type.get('confidence', 0)}%"],
                    ['Description', primary_type.get('description', 'N/A')],
                    ['Risk Level', compliance.get('risk_level', 'low').upper()],
                ]
                story.append(create_table(type_data))
                story.append(Spacer(1, 0.15*inch))
            else:
                story.append(Paragraph("<b>Website Type:</b> Not detected", styles['Normal']))
                story.append(Paragraph(f"<b>Risk Level:</b> {compliance.get('risk_level', 'low').upper()}", styles['Normal']))
                story.append(Spacer(1, 0.15*inch))
            
            # Jurisdictions
            jurisdictions = compliance.get('jurisdictions', [])
            if jurisdictions:
                story.append(Paragraph("<b>Likely Jurisdictions</b>", styles['Heading3']))
                for j in jurisdictions:
                    story.append(Paragraph(f"• {j}", styles['Normal']))
                story.append(Spacer(1, 0.15*inch))
            
            # Compliance Requirements
            requirements = compliance.get('compliance_requirements', {})
            if requirements:
                story.append(Paragraph("<b>Compliance Requirements</b>", styles['Heading3']))
                for reg, info in requirements.items():
                    story.append(Paragraph(f"<b>{reg}:</b> {info.get('description', 'N/A')}", styles['Normal']))
                    story.append(Spacer(1, 0.05*inch))
                story.append(Spacer(1, 0.1*inch))
            
            # Recommendations
            recommendations = compliance.get('recommendations', [])
            if recommendations:
                story.append(Paragraph("<b>Recommendations</b>", styles['Heading3']))
                for rec in recommendations[:6]:  # Top 6
                    story.append(Paragraph(f"• {rec}", styles['Normal']))
                story.append(Spacer(1, 0.15*inch))
            
            # 10. Deep Scan Results
            if self.result.pages_scanned:
                story.append(Paragraph("<b>9. Deep Scan Results</b>", styles['Heading2']))
                story.append(Paragraph(f"Pages scanned: {len(self.result.pages_scanned)}", styles['Normal']))
                for page in self.result.pages_scanned[:5]:
                    url = page.get('url', 'N/A')
                    status = page.get('status', page.get('error', 'N/A'))
                    story.append(Paragraph(f"• {url} - {status}", styles['Normal']))
            
            # Build PDF
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
