from typing import List, Dict, Optional
from services.groq_service import GroqService
from datetime import datetime
import json

class InterviewEngine:
    def __init__(self):
        self.groq_service = GroqService()
        self.system_prompts = {
            "interviewer": """You are an expert Cloud DevOps mentor and technical interviewer conducting a TEACHING-FOCUSED interview.

Your primary goal is EDUCATION through realistic workplace scenarios. You should:

🎯 SCENARIO-BASED QUESTIONS:
- Create realistic, practical scenarios that mirror real workplace situations
- Frame questions as "You're working at [company type/size]..." or "Your team is facing..."
- Include specific context: company size, constraints, current architecture, business requirements
- Make questions actionable with clear objectives

📚 CLOUD PLATFORM EXPERTISE:
• AWS: Focus on EC2, Lambda, VPC, CloudFormation, EKS, Auto Scaling, load balancers
• Azure: Focus on VMs, Azure Functions, Resource Manager, AKS, DevOps Pipelines
• GCP: Focus on Compute Engine, Cloud Functions, GKE, Cloud Build, VPC networking
• DevOps/Platform: Focus on CI/CD, IaC, monitoring, containers, SRE practices

🏢 EXAMPLE SCENARIOS BY PLATFORM:

AWS Example:
"You're a DevOps engineer at a fast-growing e-commerce company with 50 developers. The application currently runs on 3 EC2 instances behind an ALB. During Black Friday, traffic increases 10x, but the current setup can't handle the load and users experience timeouts. Management wants a solution that scales automatically and keeps costs reasonable. How would you redesign this architecture?"

Azure Example:
"Your startup uses Azure and has 10 microservices running on AKS. Deployments are currently manual and take 2 hours. Developers push code multiple times per day but can only deploy once per week due to manual processes. The CEO wants faster deployment cycles. How would you implement a CI/CD pipeline using Azure DevOps?"

GCP Example:
"You work at a data-intensive company using GCP. The data processing jobs run on Compute Engine VMs but costs are high and jobs sometimes fail. The team wants to migrate to a serverless approach using Cloud Functions and Cloud Run, but they're concerned about cold starts affecting performance. How would you design and implement this migration?"

DevOps/Platform Example:
"You're the Platform Engineer at a company with 20 development teams. Each team uses different CI/CD tools (Jenkins, GitLab, CircleCI) and deployment methods. This creates inconsistency, security issues, and operational overhead. Leadership wants a unified platform. How would you design and implement a standardized platform for all teams?"

💡 TEACHING FOCUS:
- Each question should teach specific concepts and best practices
- Include enough context for learning
- Encourage thinking about trade-offs, costs, and real-world constraints
- Vary complexity based on difficulty level""",
            
            "evaluator": """You are an expert DevOps mentor providing EDUCATIONAL FEEDBACK.

Your role is to TEACH, not just score. For every answer:

📊 SCORING CRITERIA (0-10):
- Understanding of core concepts (30%)
- Practical approach and methodology (30%)
- Awareness of trade-offs and considerations (25%)
- Communication clarity (15%)

🎓 EDUCATIONAL FOCUS:
- Explain WHY the candidate's approach works or doesn't work
- Provide specific examples and best practices
- Share industry insights and real-world considerations
- Give actionable next steps for improvement

💡 FEEDBACK STRUCTURE:
- What they did well (be encouraging)
- Key concepts they missed (educational gap-filling)
- Best practice explanation (teach the right way)
- Real-world insights (industry knowledge)

Be constructive, encouraging, and focus on learning outcomes.

CRITICAL: Respond with ONLY valid JSON format. No additional text, no markdown formatting, just pure JSON."""
        }

    async def generate_question(
        self,
        platform: str,
        difficulty: str,
        category: str = None,
        previous_context: List[Dict] = None,
        previous_scores: List[float] = None,
        last_answer: Optional[str] = None,
    ) -> str:
        """Generate a scenario-based interview question for specific cloud platforms"""

        # Map platform to specific services and scenarios
        platform_contexts = {
            "aws": {
                "services": "EC2, Lambda, VPC, CloudFormation, EKS, Auto Scaling, ALB/NLB, RDS, S3",
                "scenarios": "serverless architectures, auto-scaling under traffic spikes, multi-region deployments, cost optimization, container orchestration with EKS",
                "company_types": "e-commerce startup, fintech company, media streaming service, SaaS platform"
            },
            "azure": {
                "services": "Virtual Machines, Azure Functions, AKS, Azure DevOps, Resource Manager, Application Gateway, Azure SQL",
                "scenarios": "CI/CD pipeline automation, microservices deployment, hybrid cloud setup, DevOps transformation, container migration",
                "company_types": "enterprise consulting firm, healthcare startup, manufacturing company, financial services"
            },
            "gcp": {
                "services": "Compute Engine, Cloud Functions, GKE, Cloud Build, Cloud Run, Load Balancer, Cloud SQL",
                "scenarios": "data processing pipelines, serverless migration, Kubernetes management, cost optimization, CI/CD automation",
                "company_types": "data analytics startup, IoT company, gaming studio, research organization"
            },
            "devops": {
                "services": "Jenkins, GitLab CI, Terraform, Ansible, Kubernetes, Prometheus, Grafana, Docker",
                "scenarios": "platform standardization, infrastructure as code, monitoring strategy, container adoption, site reliability engineering",
                "company_types": "tech company with multiple teams, growing startup, enterprise undergoing digital transformation"
            }
        }

        platform_context = platform_contexts.get(platform, platform_contexts["devops"])
        
        context = ""
        if previous_context and len(previous_context) > 0:
            context = "Previous questions covered these topics (avoid repetition):\n"
            for qa in previous_context[-2:]:  # Last 2 Q&A pairs to avoid repetition
                context += f"- {qa['question'][:100]}...\n"

        adaptive_instruction = "Keep complexity aligned to the requested difficulty."
        if previous_scores:
            average_score = sum(previous_scores) / len(previous_scores)
            if average_score >= 7.5:
                adaptive_instruction = (
                    "Candidate is performing strongly. Increase challenge by one notch using deeper trade-offs,"
                    " multi-step constraints, and architecture-level decisions."
                )
            elif average_score <= 4.5:
                adaptive_instruction = (
                    "Candidate is struggling. Slightly reduce complexity, focus on fundamentals, and ask a clearer"
                    " step-by-step practical scenario."
                )

        follow_up_instruction = ""
        if last_answer:
            answer_preview = " ".join(last_answer.split())[:220]
            follow_up_instruction = (
                f"Use this latest candidate answer context to generate a meaningful follow-up path: \"{answer_preview}\". "
                "Build on their approach (or gaps) while avoiding exact repetition."
            )

        prompt = f"""Generate a realistic, scenario-based {difficulty} level interview question for {platform.upper()}.

{context}
{follow_up_instruction}

Platform Focus: {platform.upper()}
Key Services: {platform_context['services']}
Common Scenarios: {platform_context['scenarios']}
Company Types: {platform_context['company_types']}
Adaptive Guidance: {adaptive_instruction}

Question Requirements:
1. Start with a realistic company scenario ("You're working at...")
2. Include specific business context and constraints
3. Present a clear technical challenge
4. Make it actionable and practical
5. Focus on {platform.upper()}-specific services and best practices
6. Appropriate for {difficulty} level experience
7. Prefer a follow-up style question when prior answers exist (build depth from the last response)

Difficulty Guidelines:
- Junior: Basic implementation, single service focus, clear requirements
- Mid: Architecture decisions, multiple services, trade-off considerations  
- Senior: Complex system design, organization-wide impact, strategic thinking

Generate only the question scenario, no additional text."""

        question = await self.groq_service.generate_response(
            prompt=prompt,
            system_prompt=self.system_prompts["interviewer"],
            temperature=0.7  # Slightly more deterministic for consistency
        )

        return question.strip()

    async def evaluate_answer(
        self,
        question: str,
        answer: str,
        expected_points: List[str] = None
    ) -> Dict:
        """Provide educational evaluation and feedback on the candidate's answer"""

        expected_context = ""
        if expected_points:
            expected_context = f"\n\nKey concepts that could be addressed: {', '.join(expected_points)}"

        prompt = f"""🎯 SCENARIO QUESTION:
{question}

💭 CANDIDATE'S RESPONSE:
{answer}{expected_context}

As a DevOps mentor, provide educational feedback that helps the candidate learn:

📊 EVALUATION CRITERIA:
- Understanding of core concepts (30%): Do they grasp the fundamental DevOps/cloud principles?
- Practical approach (30%): Is their solution realistic and actionable?
- Trade-off awareness (25%): Do they consider pros/cons, alternatives, risk mitigation?
- Communication (15%): Is their explanation clear and well-structured?
- If the answer is empty or says they do not know, the score should be 0-2.

🎓 TEACHING FEEDBACK REQUIREMENTS:
1. **Strengths**: What they did well - be specific and encouraging
2. **Learning Opportunities**: What key concepts they missed (explain WHY these matter)
3. **Best Practice Guidance**: How industry experts typically handle this scenario
4. **Real-World Insights**: Share practical considerations, common pitfalls, or industry tips
5. **Model Answer**: Comprehensive approach covering key strategies and implementation steps

FORMAT REQUIREMENTS:
- Be encouraging and constructive (this is for learning, not harsh criticism)
- Explain the 'why' behind recommendations
- Include specific examples and practical tips
- Make it actionable for skill improvement
- MUST respond with valid JSON format only

RESPOND WITH ONLY VALID JSON IN THIS EXACT FORMAT:

{{
    "score": <number 0-10 based on the criteria above>,
    "feedback": "Overall assessment of the response quality and approach",
    "learning_opportunities": "Key concepts/areas they could improve - explain why these matter",
    "best_practices": "Industry standard approaches and why they work", 
    "real_world_insights": "Practical considerations, common pitfalls, or professional tips",
    "model_answer": "Comprehensive step-by-step approach an expert would take, covering strategy, implementation, and key considerations"
}}

IMPORTANT: Return ONLY the JSON object above. No additional text, explanations, or markdown formatting."""

        response = await self.groq_service.generate_response(
            prompt=prompt,
            system_prompt=self.system_prompts["evaluator"],
            temperature=0.3  # Low temperature for consistent educational quality
        )

        try:
            # Parse JSON response
            import re
            
            print(f"🔍 Raw AI response: {response[:500]}...")

            # Clean up response - remove markdown if present
            if "```json" in response:
                json_content = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_content = response.split("```")[1].split("```")[0]
            else:
                json_content = response

            # Find JSON object - more flexible regex
            json_match = re.search(r'\{[\s\S]*\}', json_content.strip())
            if json_match:
                json_content = json_match.group(0)
                
            print(f"🔍 Extracted JSON: {json_content[:300]}...")

            evaluation = json.loads(json_content.strip())
            print(f"✅ Successfully parsed evaluation: score={evaluation.get('score')}")

            # Validate required fields
            required_fields = ["score", "learning_opportunities", "best_practices", "real_world_insights", "model_answer"]
            missing_fields = [field for field in required_fields if field not in evaluation]
            
            if missing_fields:
                print(f"⚠️ Missing fields: {missing_fields}")
                # Fill in missing fields with meaningful defaults based on the answer
                if "score" not in evaluation:
                    evaluation["score"] = 5.0
                if "learning_opportunities" not in evaluation:
                    evaluation["learning_opportunities"] = "Consider exploring additional DevOps concepts and best practices to strengthen your approach."
                if "best_practices" not in evaluation:
                    evaluation["best_practices"] = "Industry standard approaches emphasize automation, monitoring, and incremental implementation."
                if "real_world_insights" not in evaluation:
                    evaluation["real_world_insights"] = "Real-world implementations require careful consideration of scalability, reliability, and cost optimization."
                if "model_answer" not in evaluation:
                    evaluation["model_answer"] = "A comprehensive approach would involve systematic analysis, solution design, and phased implementation with proper monitoring."

            # Ensure score is numeric and in range
            evaluation["score"] = max(0, min(10, float(evaluation["score"])))
            
            # Convert any list values to strings (AI sometimes returns arrays)
            string_fields = ["feedback", "learning_opportunities", "best_practices", "real_world_insights", "model_answer"]
            for field in string_fields:
                if field in evaluation and isinstance(evaluation[field], list):
                    evaluation[field] = " ".join(evaluation[field]) if evaluation[field] else ""

            # Clamp scores for low-effort answers
            normalized_answer = (answer or "").strip().lower()
            low_effort_phrases = ["i don't know", "i dont know", "not sure", "no idea", "i have no idea"]
            is_low_effort = (len(normalized_answer.split()) < 4) or any(phrase in normalized_answer for phrase in low_effort_phrases)
            if is_low_effort and evaluation.get("score", 0) > 2:
                evaluation["score"] = 2.0
                evaluation["feedback"] = "Thanks for being honest. Since the response did not include a solution, the score reflects missing core concepts. Review the fundamentals and try again."
                evaluation["learning_opportunities"] = "Start with the basics: outline the goal, key services, and a simple high-level design before adding details."
            
            # Ensure backwards compatibility 
            if "strengths" not in evaluation and "feedback" in evaluation:
                evaluation["strengths"] = evaluation["feedback"]

        except Exception as e:
            print(f"❌ JSON parsing failed for evaluation: {e}")
            print(f"🔍 Response type: {type(response)}")
            print(f"🔍 Response length: {len(response) if response else 'None'}")
            print(f"📝 Raw response: {response}")

            # Try to extract any meaningful content from the response
            score_match = re.search(r'score["\s:]+(\d+(?:\.\d+)?)', response, re.IGNORECASE)
            extracted_score = float(score_match.group(1)) if score_match else 5.0
            
            # Educational fallback response with dynamic content based on answer
            answer_length = len(answer.split()) if answer else 0
            feedback_content = "Your response shows engagement with the problem" if answer_length > 10 else "Consider providing more detailed technical analysis"
            
            evaluation = {
                "score": extracted_score,
                "feedback": feedback_content,
                "learning_opportunities": f"Based on your {answer_length}-word response, focus on expanding technical depth and implementation details.",
                "best_practices": "Industry standard approaches emphasize systematic problem-solving, automation, and comprehensive monitoring strategies.",
                "real_world_insights": "Professional DevOps solutions balance technical excellence with business requirements and operational constraints.",
                "model_answer": f"For this scenario involving {question[:50]}..., a comprehensive approach would include: requirement analysis, solution architecture design, implementation planning, and success metrics definition."
            }

        return evaluation

    async def generate_follow_up(
        self,
        original_question: str,
        answer: str,
        evaluation: Dict
    ) -> Optional[str]:
        """Generate a follow-up question based on the answer"""

        if evaluation.get("score", 0) < 4:
            return None  # Don't follow up on very poor answers

        prompt = f"""Original Question: {original_question}

Candidate's Answer: {answer}

Based on their answer, generate ONE brief follow-up question to:
- Test deeper understanding of a concept they mentioned
- Explore a related practical scenario
- Clarify something they said

Keep it short and natural, as in a real conversation.
Generate just the question, nothing else."""

        follow_up = await self.groq_service.generate_response(
            prompt=prompt,
            system_prompt=self.system_prompts["interviewer"],
            temperature=0.7
        )

        return follow_up.strip()

    async def generate_session_summary(
        self,
        questions_and_answers: List[Dict],
        platform: str,
        difficulty: str
    ) -> Dict:
        """Generate a summary of the entire interview session"""

        qa_text = ""
        for i, qa in enumerate(questions_and_answers, 1):
            qa_text += f"\nQ{i}: {qa['question']}\nA{i}: {qa['answer']}\nScore: {qa.get('score', 'N/A')}\n"

        prompt = f"""Interview Summary Request

Platform: {platform}
Difficulty: {difficulty}
Total Questions: {len(questions_and_answers)}

Questions and Answers:
{qa_text}

Provide a comprehensive interview summary with:
1. Overall performance score (0-10)
2. Key strengths demonstrated
3. Areas for improvement
4. Specific topics to study more
5. Overall readiness assessment

Format as JSON:
{{
    "overall_score": <number>,
    "strengths": ["<strength1>", "<strength2>", ...],
    "improvements": ["<area1>", "<area2>", ...],
    "study_topics": ["<topic1>", "<topic2>", ...],
    "readiness": "<assessment>",
    "summary": "<brief paragraph>"
}}
"""

        response = await self.groq_service.generate_response(
            prompt=prompt,
            system_prompt=self.system_prompts["evaluator"],
            temperature=0.1  # Very low temperature for strict JSON formatting
        )

        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            summary = json.loads(response.strip())
        except:
            summary = {
                "overall_score": 5.0,
                "strengths": [],
                "improvements": [],
                "study_topics": [],
                "readiness": "Evaluation completed",
                "summary": response
            }

        return summary

interview_engine = InterviewEngine()
