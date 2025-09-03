from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, HttpUrl, Field
from typing import Dict, Any, List, Optional, Union
import asyncio
import json
import os
import re
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AuditAgents:
    def __init__(self):
        # Get API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.llm = ChatOpenAI(
            model_name="gpt-4-turbo-preview",
            temperature=0.1,
            openai_api_key=api_key
        )
        self.agents = self._initialize_agents()
        
        # Default values for calculations
        self.defaults = {
            'monthly_visitors': 1000,  # Default for small local business
            'target_conversion_rate': 0.07,  # 7% target conversion rate
            'current_conversion_rate': 0.01,  # 1% baseline conversion rate
            'close_rate': 0.20,  # 20% close rate
            'average_client_value': 300,  # Default client value in USD
            'load_time_threshold': 2.5,  # Target load time in seconds
        }
    
    def _initialize_agents(self):
        """Initialize all audit agents with their specific prompts"""
        
        # Base system prompt for all agents
        base_system_prompt = """You are a senior website auditor analyzing a website for conversion optimization opportunities. 
        Your analysis will be used to generate a comprehensive report that helps the business increase their online revenue.
        Be specific, data-driven, and provide actionable insights.
        """
        
        # Main audit prompt template
        audit_prompt_template = """{base_system_prompt}
            
CONDUCT A COMPREHENSIVE WEBSITE AUDIT FOCUSING ON THESE CRITICAL AREAS:

1. CONVERSION READINESS (25% weight)
- CTA clarity and placement
- Form fields and friction points
- Above-the-fold clarity
- Value proposition clarity

2. TRUST SIGNALS (20% weight)
- Testimonials and social proof
- Security indicators (SSL, trust badges)
- Contact information visibility
- Return/refund policies

3. USER EXPERIENCE (20% weight)
- Mobile responsiveness
- Navigation and site structure
- Page load speed
- Accessibility considerations

4. CONTENT QUALITY (15% weight)
- Readability and scannability
- Grammar and spelling
- Visual content quality
- Content relevance to target audience

5. SEO FOUNDATIONS (10% weight)
- Meta titles and descriptions
- Header structure (H1, H2, H3)
- Image alt attributes
- URL structure

6. PERFORMANCE METRICS (10% weight)
- Core Web Vitals
- Server response time
- Resource optimization
- Caching strategy

FOR EACH CATEGORY, PROVIDE:
- Score (0-100)
- Key findings (specific issues found)
- Recommendations (actionable fixes)
- Impact assessment (low/medium/high)

ADDITIONAL CONTEXT:
- Industry: {industry}
- Monthly Visitors: {monthly_visitors}
- Average Client Value: ${average_client_value}
- Website URL: {website_url}

BE SPECIFIC: Quote exact text that needs to be changed.
BE ACTIONABLE: Provide clear, implementable recommendations.
BE CONSERVATIVE: Use realistic estimates and projections.

FINAL OUTPUT MUST BE VALID JSON."""

        # Create the prompt template
        audit_prompt = ChatPromptTemplate.from_messages([
            ("system", audit_prompt_template.format(
                base_system_prompt=base_system_prompt,
                industry='{industry}',
                monthly_visitors='{monthly_visitors}',
                average_client_value='{average_client_value}',
                website_url='{website_url}'
            )),
            ("human", """
            WEBSITE CONTENT:
            {website_data}
            
            PROFILE DATA:
            {profile_data}
            
            AUDIT PARAMETERS:
            Industry: {industry}
            Monthly Visitors: {monthly_visitors}
            Average Client Value: ${average_client_value}
            
            Please provide your analysis in the required JSON format.
            """)
        ])
        
        style_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a brand and design expert. Analyze the ACTUAL website content and identify specific style/brand issues.

            ANALYZE THESE SPECIFIC ELEMENTS:
            1. Website title vs social profile: Do they match in tone?
            2. Hero section language: Is it professional, casual, or inconsistent?
            3. Content tone throughout: Quote examples of tone shifts
            4. Brand messaging: What's the actual brand voice used?
            5. Visual hierarchy: Are headings structured properly (H1, H2, H3)?

            PROVIDE SPECIFIC EXAMPLES. Quote actual text that shows inconsistencies.
            
            Return a JSON object with:
            - style_consistency: (0-100 based on actual content analysis)
            - tone_examples: ["Quote showing professional tone", "Quote showing casual tone"]
            - brand_issues: ["Specific inconsistency found: '[quote]'", "Another issue"]
            - recommendations: ["Change this text '[quote]' to match brand voice", "Fix this specific element"]"""),
            ("human", "Website data: {website_data}\nProfile data: {profile_data}")
        ])
        
        return {
            "audit": audit_prompt | self.llm,
            "style": style_prompt | self.llm
        }
    
    async def run_all_agents(self, website_data: Dict, profile_data: Dict, audit_params: Dict = None):
        """Run the audit with the provided website and profile data"""
        if audit_params is None:
            audit_params = {}
            
        # Get default values or use provided values
        monthly_visitors = audit_params.get('monthly_visitors', self.defaults['monthly_visitors'])
        average_client_value = audit_params.get('average_client_value', self.defaults['average_client_value'])
        
        # Prepare inputs for the agents
        inputs = {
            'website_data': str(website_data),
            'profile_data': str(profile_data),
            'industry': audit_params.get('industry', 'general'),
            'monthly_visitors': monthly_visitors,
            'average_client_value': average_client_value,
            'website_url': audit_params.get('website_url', '')
        }
        
        # Ensure all required parameters have default values
        inputs.setdefault('industry', 'general')
        inputs.setdefault('monthly_visitors', self.defaults['monthly_visitors'])
        inputs.setdefault('average_client_value', self.defaults['average_client_value'])
        inputs.setdefault('website_url', '')
        
        # Run the main audit
        try:
            result = await self.agents["audit"].ainvoke(inputs)
            
            # Parse the response
            audit_results = self._parse_agent_response(result.content)
            
            # Ensure we have a dictionary result
            if not isinstance(audit_results, dict):
                audit_results = {}
                
            # Add metadata
            if 'metadata' not in audit_results:
                audit_results['metadata'] = {}
                
            audit_results['metadata'].update({
                'audit_id': str(uuid.uuid4()),
                'timestamp': datetime.utcnow().isoformat(),
                'website_url': inputs.get('website_url', ''),
                'industry': inputs.get('industry', 'general'),
                'monthly_visitors': monthly_visitors,
                'average_client_value': average_client_value
            })
            
            # Calculate ROI and other metrics
            audit_results = self._calculate_roi(audit_results, monthly_visitors, average_client_value)
            
            # Ensure we have all required top-level fields
            if 'scores' not in audit_results:
                audit_results['scores'] = {}
                
            # Extract scores from individual categories
            for category, data in audit_results.items():
                if isinstance(data, dict) and 'score' in data:
                    audit_results['scores'][category] = data['score']
            
            return audit_results
            
        except Exception as e:
            return {
                "error": f"Error running audit: {str(e)}",
                "success": False
            }
    
    def _calculate_roi(self, audit_results: Dict, monthly_visitors: int, average_client_value: float) -> Dict:
        """Calculate ROI and other business metrics"""
        try:
            # Ensure we have valid inputs
            if monthly_visitors is None or average_client_value is None:
                monthly_visitors = self.defaults['monthly_visitors']
                average_client_value = self.defaults['average_client_value']
                
            # Get conversion scores (default to 1% if not available)
            conversion_score = 1  # Default 1%
            if isinstance(audit_results, dict):
                if 'scores' in audit_results and 'conversion_readiness' in audit_results['scores']:
                    conversion_score = audit_results['scores']['conversion_readiness']
                elif 'conversion_readiness' in audit_results and 'score' in audit_results['conversion_readiness']:
                    conversion_score = audit_results['conversion_readiness']['score']
            
            # Ensure conversion_score is a number between 0-100
            try:
                conversion_score = float(conversion_score)
                # If score is > 1, assume it's a percentage (e.g., 70 for 70%)
                # If score is <= 1, assume it's a decimal (e.g., 0.7 for 70%)
                if conversion_score > 1:
                    current_cr = max(0.01, min(conversion_score / 100, 1.0))  # Convert percentage to decimal
                else:
                    current_cr = max(0.01, min(conversion_score, 1.0))  # Already in decimal form
            except (TypeError, ValueError):
                current_cr = 0.01  # Fallback to 1%
                
            # Get target conversion rate and close rate with defaults
            target_cr = self.defaults.get('target_conversion_rate', 0.07)  # 7% default
            close_rate = self.defaults.get('close_rate', 0.20)  # 20% default
            
            # Calculate leads and revenue
            current_leads = max(0, monthly_visitors) * current_cr
            improved_leads = max(0, monthly_visitors) * target_cr
            
            current_revenue = max(0, current_leads * close_rate * average_client_value)
            improved_revenue = max(0, improved_leads * close_rate * average_client_value)
            monthly_upside = max(0, improved_revenue - current_revenue)
            
            # Add to results
            if not isinstance(audit_results, dict):
                audit_results = {}
                
            audit_results['roi_metrics'] = {
                'monthly_visitors': int(monthly_visitors),
                'current_conversion_rate': round(current_cr * 100, 2),  # as percentage
                'target_conversion_rate': round(target_cr * 100, 2),    # as percentage
                'average_client_value': float(average_client_value),
                'current_leads': round(current_leads, 1),
                'improved_leads': round(improved_leads, 1),
                'current_revenue': round(current_revenue, 2),
                'improved_revenue': round(improved_revenue, 2),
                'monthly_upside': round(monthly_upside, 2),
                'annual_upside': round(monthly_upside * 12, 2) if monthly_upside is not None else 0,
                'assumptions': [
                    f"Conversion rate improves from {current_cr*100:.1f}% to {target_cr*100:.1f}%",
                    f"Close rate of {close_rate*100:.0f}% applied to leads",
                    f"Average client value: ${average_client_value:,.2f}"
                ]
            }
            
            return audit_results
            
        except Exception as e:
            print(f"Error calculating ROI: {str(e)}")
            return audit_results

    def _parse_agent_response(self, response: str) -> Dict:
        """Parse agent response, handling both JSON and text responses"""
        try:
            if not response or not isinstance(response, str):
                return {"error": "Empty or invalid response from agent", "success": False}
                
            # Clean the response
            response = response.strip()
            
            # Try to extract JSON from the response
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response
            
            # Parse JSON response
            try:
                parsed = json.loads(json_str)
                if not isinstance(parsed, dict):
                    return {"response": parsed, "success": True}
                return parsed
            except json.JSONDecodeError as je:
                # If JSON parsing fails, try to extract structured data from text
                return self._extract_from_text(response)
                
        except Exception as e:
            print(f"Error parsing agent response: {str(e)}")
            return {"error": f"Failed to parse agent response: {str(e)}", "success": False}

    def _extract_from_text(self, response: str) -> Dict:
        """Extract information from text response when JSON parsing fails"""
        # Initialize result with empty structure
        result = {
            "scores": {},
            "key_findings": [],
            "recommendations": [],
            "success": True
        }
        
        try:
            # Simple text parsing logic
            lines = [line.strip() for line in response.split('\n') if line.strip()]
            
            # Try to extract scores from text
            for i, line in enumerate(lines):
                line_lower = line.lower()
                # Look for patterns like "Score: 85" or "Rating: 4.5/5"
                if any(term in line_lower for term in ["score:", "rating:", "grade:"]):
                    try:
                        # Try to extract a number from the line
                        score_match = re.search(r'([0-9.]+)', line)
                        if score_match:
                            score = float(score_match.group(1))
                            # If score is out of 5 or 10, convert to percentage
                            if score <= 5:
                                score = score * 20  # Convert 5-point scale to percentage
                            elif score <= 10:
                                score = score * 10  # Convert 10-point scale to percentage
                            result["scores"]["overall"] = min(100, max(0, score))
                            # Check next few lines for category scores
                            for j in range(i+1, min(i+10, len(lines))):
                                cat_line = lines[j].lower()
                                if ":" in cat_line and any(term in cat_line for term in ["score", "rating"]):
                                    parts = [p.strip() for p in cat_line.split(":", 1)]
                                    if len(parts) == 2:
                                        cat_name = parts[0].replace("score", "").replace("rating", "").strip()
                                        cat_score = re.search(r'([0-9.]+)', parts[1])
                                        if cat_score:
                                            result["scores"][cat_name] = float(cat_score.group(1))
                            break
                    except (ValueError, TypeError):
                        continue
            
            # Extract key findings and recommendations
            current_section = None
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Check for section headers
                if "key findings" in line.lower():
                    current_section = "findings"
                    continue
                elif "recommendations" in line.lower() or "suggestions" in line.lower():
                    current_section = "recommendations"
                    continue
                
                # Add to appropriate section
                if current_section == "findings" and line and len(line) > 10:  # Skip very short lines
                    if line.startswith("-"):
                        result["key_findings"].append(line[1:].strip())
                    else:
                        result["key_findings"].append(line)
                elif current_section == "recommendations" and line and len(line) > 10:
                    if line.startswith("-"):
                        result["recommendations"].append(line[1:].strip())
                    else:
                        result["recommendations"].append(line)
            
            # If no specific sections found, add all non-empty lines as recommendations
            if not result["key_findings"] and not result["recommendations"]:
                result["recommendations"] = [
                    line for line in lines 
                    if (len(line) > 10 and 
                        not any(term in line.lower() for term in [
                            "score:", "rating:", "grade:", 
                            "http://", "https://", "www."
                        ])
                    )
                ]
                
        except Exception as e:
            print(f"Error extracting from text response: {str(e)}")
            result["error"] = f"Error extracting from text: {str(e)}"
            result["success"] = False
        
        return result
    
    async def compile_audit(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Compile all agent results into a final audit report"""
        if not agent_results or not isinstance(agent_results, dict):
            return {"error": "Invalid or empty agent results", "success": False}
            
        # Initialize the result structure
        compiled_report = {
            "overview": "",
            "scores": {"overall": 0},
            "key_findings": [],
            "quick_wins": [],
            "recommendations": [],
            "next_steps": [],
            "metadata": {
                "compiled_at": datetime.utcnow().isoformat(),
                "version": "1.0"
            },
            "success": True
        }
        
        try:
            # Extract and merge scores from agent results
            if "scores" in agent_results and isinstance(agent_results["scores"], dict):
                compiled_report["scores"].update(agent_results["scores"])
            
            # Calculate overall score if not provided
            if "overall" not in compiled_report["scores"] and len(compiled_report["scores"]) > 0:
                total = sum(score for cat, score in compiled_report["scores"].items() 
                           if isinstance(score, (int, float)) and cat != "overall")
                count = len([s for s in compiled_report["scores"].values() 
                           if isinstance(s, (int, float)) and s > 0])
                compiled_report["scores"]["overall"] = round(total / max(1, count), 1)
            
            # Extract key findings
            for key in ["key_findings", "critical_issues"]:
                if key in agent_results and isinstance(agent_results[key], list):
                    compiled_report["key_findings"].extend(
                        str(item) for item in agent_results[key] 
                        if str(item).strip() and str(item).strip().lower() not in 
                           [f.lower() for f in compiled_report["key_findings"]]
                    )
            
            # Extract recommendations and quick wins
            if "recommendations" in agent_results and isinstance(agent_results["recommendations"], list):
                compiled_report["recommendations"] = [
                    str(r) for r in agent_results["recommendations"] 
                    if str(r).strip()
                ]
                
            # If no specific quick wins, use top 3 recommendations
            if not compiled_report["quick_wins"] and compiled_report["recommendations"]:
                compiled_report["quick_wins"] = compiled_report["recommendations"][:3]
            
            # Generate overview if not provided
            if not compiled_report["overview"]:
                score = compiled_report["scores"].get("overall", 0)
                if score >= 80:
                    overview = "The website is in good shape with strong performance and user experience."
                elif score >= 60:
                    overview = "The website has some areas for improvement but is generally functional."
                else:
                    overview = "The website requires significant improvements to meet modern web standards."
                
                if "key_findings" in agent_results and agent_results["key_findings"]:
                    overview += f" Key issues include: {', '.join(agent_results['key_findings'][:2])}"
                
                compiled_report["overview"] = overview
            
            # Generate next steps
            if not compiled_report["next_steps"]:
                compiled_report["next_steps"] = [
                    "Review the key findings and recommendations above",
                    "Prioritize quick wins for immediate improvements",
                    "Create an implementation plan for the remaining recommendations",
                    "Schedule a follow-up audit to measure improvements"
                ]
            
            # Add ROI metrics if available
            if "roi_metrics" in agent_results and isinstance(agent_results["roi_metrics"], dict):
                compiled_report["roi_metrics"] = agent_results["roi_metrics"]
            
            # Ensure all scores are numbers
            for k, v in list(compiled_report["scores"].items()):
                if not isinstance(v, (int, float)):
                    try:
                        compiled_report["scores"][k] = float(v) if v else 0
                    except (ValueError, TypeError):
                        compiled_report["scores"][k] = 0
            
            return compiled_report
            
        except Exception as e:
            error_msg = f"Error compiling audit: {str(e)}"
            print(error_msg)
            return {
                "error": error_msg,
                "success": False,
                "metadata": compiled_report.get("metadata", {})
            }
