"""Mock data provider for agent testing."""
from typing import Dict, Any, List, Optional
from datetime import datetime

class MockDataProvider:
    """Provides mock data for different agent types."""
    
    @staticmethod
    def get_target_audience_data(market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get mock target audience data.
        
        Args:
            market_data: Market data containing demographics
            
        Returns:
            Mock target audience data
        """
        # Ensure we return the exact demographics from market data
        demographics = market_data.get("demographics", {})
        if not demographics and isinstance(market_data, dict):
            # If demographics not found at top level, use the entire market_data
            # This handles cases where market_data itself is the demographics
            demographics = market_data
            
        return {
            "segments": [{"type": "primary", "description": "test"}],
            "pain_points": ["test pain point"],
            "goals": ["test goal"],
            "demographics": demographics,
            "behavioral_traits": ["test trait"]
        }
    
    @staticmethod
    def get_value_proposition_data() -> Dict[str, Any]:
        """Get mock value proposition data.
        
        Returns:
            Mock value proposition data
        """
        return {
            "core_benefits": ["test benefit 1", "test benefit 2"],
            "unique_factors": ["test factor"],
            "proof_points": [{"point": "test", "evidence": "test"}],
            "competitive_advantages": ["test advantage"]
        }
    
    @staticmethod
    def get_opportunities_data() -> Dict[str, Any]:
        """Get mock opportunities and risks data.
        
        Returns:
            Mock opportunities and risks data
        """
        return {
            "opportunities": [{"name": "test opportunity", "impact": "high"}],
            "risks": [{"name": "test risk", "severity": "medium"}],
            "recommendations": [{"action": "test action", "priority": "high"}]
        }
    
    @staticmethod
    def get_assumptions_data() -> List[Dict[str, Any]]:
        """Get mock assumptions data.
        
        Returns:
            List of mock assumptions
        """
        return [
            {
                "assumption": "test assumption 1",
                "evidence": ["test evidence 1"],
                "confidence_level": 0.8,
                "potential_risks": ["test risk 1"]
            },
            {
                "assumption": "test assumption 2",
                "evidence": ["test evidence 2"],
                "confidence_level": 0.7,
                "potential_risks": ["test risk 2"]
            }
        ]
    
    @staticmethod
    def get_competitive_analysis_data() -> Dict[str, Any]:
        """Get mock competitive analysis data.
        
        Returns:
            Mock competitive analysis data
        """
        return {
            "competitors": [
                {"name": "test competitor 1", "strength": "test 1"},
                {"name": "test competitor 2", "strength": "test 2"}
            ],
            "market_share": {"test": 0.5},
            "strengths": ["test strength"],
            "weaknesses": ["test weakness"],
            "opportunities": ["test opportunity"],
            "threats": ["test threat"]
        }
    
    @staticmethod
    def get_market_analysis_data(market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get mock market analysis data.
        
        Args:
            market_data: Market data to include
            
        Returns:
            Mock market analysis data
        """
        return {
            "status": "success",
            "market_analysis": {
                "market_size": market_data.get("market_size", 0),
                "growth_rate": market_data.get("growth_rate", 0),
                "competitors": market_data.get("competitors", []),
                "target_audience": market_data.get("target_audience", "")
            },
            "recommendations": [
                "Focus on market expansion",
                "Invest in digital transformation",
                "Enhance customer experience"
            ],
            "confidence_score": 0.85
        }
