"""Mock data provider for testing."""
from typing import Dict, Any, List

class MockDataProvider:
    """Provides mock data for testing."""
    
    @staticmethod
    def get_value_proposition_data() -> Dict[str, Any]:
        """Get mock value proposition data.
        
        Returns:
            Mock value proposition data
        """
        return {
            "key_benefits": [
                "Improved efficiency",
                "Cost reduction",
                "Enhanced accuracy"
            ],
            "unique_advantages": [
                "Advanced AI capabilities",
                "Real-time processing",
                "Domain expertise"
            ],
            "solution_features": [
                {
                    "name": "AI Analytics",
                    "description": "Advanced analytics powered by AI"
                },
                {
                    "name": "Real-time Processing",
                    "description": "Process data in real-time"
                },
                {
                    "name": "Custom Integration",
                    "description": "Easy integration with existing systems"
                }
            ],
            "target_outcomes": [
                "30% efficiency improvement",
                "25% cost reduction",
                "99% accuracy rate"
            ],
            "competitive_differentiators": [
                "Most advanced AI technology",
                "Fastest processing speed",
                "Best-in-class accuracy"
            ]
        }
    
    @staticmethod
    def get_opportunities_data() -> Dict[str, Any]:
        """Get mock opportunities data.
        
        Returns:
            Mock opportunities data
        """
        return {
            "opportunities": [
                {
                    "name": "Market Expansion",
                    "impact": "High"
                },
                {
                    "name": "Technology Leadership",
                    "impact": "Medium"
                }
            ],
            "risks": [
                {
                    "name": "Competition",
                    "severity": "Medium"
                },
                {
                    "name": "Integration Complexity",
                    "severity": "High"
                }
            ],
            "recommendations": [
                {
                    "action": "Accelerate development",
                    "priority": "High"
                },
                {
                    "action": "Build partnerships",
                    "priority": "Medium"
                }
            ]
        }
    
    @staticmethod
    def get_market_analysis_data(context: Dict[str, Any]) -> Dict[str, Any]:
        """Get mock market analysis data.
        
        Args:
            context: Context data to incorporate
            
        Returns:
            Mock market analysis data
        """
        return {
            "market_size": context.get("market_size", 5000),
            "growth_rate": context.get("growth_rate", 25),
            "competition_level": context.get("competition_level", "Medium"),
            "target_segments": context.get("target_segment", ["Enterprise"]),
            "key_trends": [
                "AI adoption increasing",
                "Focus on real-time analytics",
                "Integration demands growing"
            ]
        }
    
    @staticmethod
    def get_risk_assessment_data() -> Dict[str, Any]:
        """Get mock risk assessment data.
        
        Returns:
            Mock risk assessment data
        """
        return {
            "risk_factors": [
                {
                    "name": "Market Competition",
                    "likelihood": 0.7,
                    "impact": 0.8
                },
                {
                    "name": "Technical Complexity",
                    "likelihood": 0.6,
                    "impact": 0.7
                }
            ],
            "impact_levels": {
                "revenue": 0.7,
                "market_share": 0.6,
                "reputation": 0.5
            },
            "mitigation_strategies": [
                {
                    "strategy": "Accelerate development",
                    "effectiveness": "High"
                },
                {
                    "strategy": "Form strategic partnerships",
                    "effectiveness": "Medium"
                }
            ],
            "contingency_plans": [
                {
                    "trigger": "Market share drop",
                    "action": "Price adjustment"
                },
                {
                    "trigger": "Integration issues",
                    "action": "Additional support"
                }
            ],
            "overall_risk_level": 0.65
        }
    
    @staticmethod
    def get_market_validation_data() -> Dict[str, Any]:
        """Get mock market validation data.
        
        Returns:
            Mock market validation data
        """
        return {
            "data_sources": [
                "Market research reports",
                "Customer interviews",
                "Competitor analysis"
            ],
            "validation_methods": [
                "Survey analysis",
                "Expert interviews",
                "Data mining"
            ],
            "findings": [
                {
                    "area": "Market need",
                    "validation": "Strong demand confirmed",
                    "confidence": 0.9
                },
                {
                    "area": "Price point",
                    "validation": "Within acceptable range",
                    "confidence": 0.8
                }
            ],
            "confidence_level": 0.85,
            "recommendations": [
                {
                    "area": "Pricing",
                    "action": "Maintain premium positioning"
                },
                {
                    "area": "Features",
                    "action": "Focus on AI capabilities"
                }
            ]
        }
    
    @staticmethod
    def get_challenge_data() -> Dict[str, Any]:
        """Get mock challenge data.
        
        Returns:
            Mock challenge data
        """
        return {
            "assumptions": [
                {
                    "assumption": "Market size estimate",
                    "challenge": "May be overestimated",
                    "evidence": "Recent market slowdown"
                },
                {
                    "assumption": "Technical feasibility",
                    "challenge": "Integration complexity",
                    "evidence": "Similar project delays"
                }
            ]
        }
