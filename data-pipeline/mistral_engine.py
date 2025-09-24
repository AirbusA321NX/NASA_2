import asyncio
import aiohttp
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MistralInsight:
    """Data class for Mistral AI generated insights"""
    summary_input: str
    insight_type: str
    generated_text: str
    confidence_score: Optional[float] = None
    timestamp: Optional[datetime] = None

class MistralAnalysisEngine:
    """
    Engine for processing data summaries with Mistral AI
    Generates human-readable insights, explanations, and Q&A responses
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.mistral.ai/v1"
        self.session = None
        self.insights: List[MistralInsight] = []
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def generate_insight(self, summary: str, insight_type: str = "explanation") -> str:
        """Generate insight using Mistral AI"""
        
        prompts = {
            "explanation": f"""
            As a NASA space biology research expert, explain these findings in clear, accessible language:
            
            Data Summary: {summary}
            
            Please provide:
            1. What these findings mean for space biology research
            2. Why these patterns are significant
            3. Implications for future space missions
            4. Key takeaways for researchers and mission planners
            
            Keep the explanation scientific but accessible to a general audience.
            """,
            
            "research_gaps": f"""
            Based on this NASA OSDR data summary, identify potential research gaps and opportunities:
            
            Data Summary: {summary}
            
            Please identify:
            1. Underexplored research areas
            2. Missing organism models or experimental approaches
            3. Temporal gaps in research focus
            4. Collaboration opportunities
            5. Suggested priorities for future research
            
            Focus on actionable insights for research planning.
            """,
            
            "mission_implications": f"""
            Translate these NASA OSDR research findings into practical implications for space missions:
            
            Data Summary: {summary}
            
            Please explain:
            1. How these findings impact crew health and safety
            2. Relevant considerations for Mars missions
            3. Technology or countermeasure development needs
            4. Risk assessment insights
            5. Mission planning recommendations
            
            Focus on practical applications for space exploration.
            """,
            
            "trend_analysis": f"""
            Analyze the trends and patterns in this NASA OSDR data:
            
            Data Summary: {summary}
            
            Please provide:
            1. Key trends and their significance
            2. Emerging research directions
            3. Changes in research focus over time
            4. Predictions for future research priorities
            5. Recommendations for strategic research investment
            
            Focus on strategic insights for research leadership.
            """,
            
            "public_summary": f"""
            Create a public-friendly summary of these NASA space biology research findings:
            
            Data Summary: {summary}
            
            Please write:
            1. A compelling headline summarizing the key finding
            2. What NASA discovered and why it matters
            3. How this research benefits life on Earth
            4. The broader impact on space exploration
            5. What comes next in this research area
            
            Write for a general audience interested in space science.
            """
        }
        
        prompt = prompts.get(insight_type, prompts["explanation"])
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "mistral-large-latest",
                "messages": [
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            if self.session is None:
                raise RuntimeError("Session not initialized")
                
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    generated_text = result["choices"][0]["message"]["content"]
                    
                    # Store insight
                    insight = MistralInsight(
                        summary_input=summary,
                        insight_type=insight_type,
                        generated_text=generated_text,
                        timestamp=datetime.now()
                    )
                    self.insights.append(insight)
                    
                    return generated_text
                    
                else:
                    error_text = await response.text()
                    logger.error(f"Mistral API error {response.status}: {error_text}")
                    return f"Error generating insight: {response.status}"
                    
        except Exception as e:
            logger.error(f"Error calling Mistral API: {e}")
            return f"Error generating insight: {str(e)}"

    async def process_data_summaries(self, summaries: List[str]) -> Dict[str, Any]:
        """Process multiple data summaries with different insight types"""
        
        results: Dict[str, Any] = {
            "explanations": [],
            "research_gaps": [],
            "mission_implications": [],
            "trend_analyses": [],
            "public_summaries": []
        }
        
        insight_types = [
            "explanation",
            "research_gaps", 
            "mission_implications",
            "trend_analysis",
            "public_summary"
        ]
        
        logger.info(f"Processing {len(summaries)} summaries with {len(insight_types)} insight types")
        
        # Process each summary with each insight type
        for i, summary in enumerate(summaries):
            logger.info(f"Processing summary {i+1}/{len(summaries)}")
            
            for insight_type in insight_types:
                try:
                    insight = await self.generate_insight(summary, insight_type)
                    results[f"{insight_type}s"].append(insight)
                    
                    # Add delay to respect API rate limits
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error processing summary {i+1} with {insight_type}: {e}")
                    results[f"{insight_type}s"].append(f"Error: {str(e)}")
        
        return results

    async def generate_qa_responses(self, questions: List[str], context_summaries: List[str]) -> List[Dict[str, str]]:
        """Generate Q&A responses based on data summaries"""
        
        qa_responses = []
        
        # Combine summaries for context
        combined_context = "\n\n".join(context_summaries)
        
        for question in questions:
            try:
                prompt = f"""
                Based on this NASA OSDR research data, answer the following question:
                
                Research Data Context:
                {combined_context}
                
                Question: {question}
                
                Please provide a comprehensive answer based on the available data, including:
                1. Direct answer to the question
                2. Supporting evidence from the data
                3. Relevant context and implications
                4. Any limitations or caveats
                
                If the data doesn't fully address the question, clearly state what can and cannot be determined.
                """
                
                response = await self.generate_insight(prompt, "qa_response")
                
                qa_responses.append({
                    "question": question,
                    "answer": response,
                    "timestamp": datetime.now().isoformat()
                })
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error generating Q&A response for '{question}': {e}")
                qa_responses.append({
                    "question": question,
                    "answer": f"Error generating response: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                })
        
        return qa_responses

    def save_insights(self, insights: Dict[str, Any], output_path: str = "data/mistral_insights.json"):
        """Save generated insights to file"""
        
        # Add metadata
        insights_with_metadata = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_insights": len(self.insights),
                "api_model": "mistral-large-latest"
            },
            "insights": insights
        }
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(insights_with_metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(self.insights)} insights to {output_path}")

async def process_with_mistral(
    analysis_results_path: str = "data/analysis_results.json",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main function to process analysis results with Mistral AI
    """
    
    if not api_key:
        api_key = os.getenv('MISTRAL_API_KEY')
        
    if not api_key:
        logger.error("Mistral API key not provided")
        return {}
    
    # Load analysis results
    try:
        with open(analysis_results_path, 'r', encoding='utf-8') as f:
            analysis_results = json.load(f)
    except Exception as e:
        logger.error(f"Error loading analysis results: {e}")
        return {}
    
    # Extract text summaries
    summaries = analysis_results.get('text_summaries', [])
    
    if not summaries:
        logger.error("No text summaries found in analysis results")
        return {}
    
    logger.info(f"Processing {len(summaries)} summaries with Mistral AI")
    
    async with MistralAnalysisEngine(api_key) as engine:
        # Generate insights
        insights = await engine.process_data_summaries(summaries)
        
        # Common research questions
        research_questions = [
            "What are the most significant trends in NASA space biology research?",
            "Which organisms are most commonly studied and why?",
            "How has research collaboration evolved over time?",
            "What research gaps exist that should be prioritized?",
            "What are the implications for Mars mission planning?",
            "How diverse is the current research portfolio?",
            "What emerging research areas show the most promise?"
        ]
        
        # Generate Q&A responses
        qa_responses = await engine.generate_qa_responses(research_questions, summaries)
        insights["qa_responses"] = qa_responses
        
        # Save insights
        engine.save_insights(insights)
        
        logger.info("Mistral AI processing complete")
        return insights

async def main():
    """Main function for testing with real NASA data"""
    
    api_key = os.getenv('MISTRAL_API_KEY')
    if api_key:
        # Test with real analysis results
        insights = await process_with_mistral(api_key=api_key)
        if insights:
            print("Generated insights from real NASA OSDR data")
        else:
            print("No real data available - run data analysis first")
    else:
        print("No Mistral API key provided for testing")

if __name__ == "__main__":
    asyncio.run(main())