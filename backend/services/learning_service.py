from typing import List, Dict, Optional
from datetime import datetime, timedelta
import asyncio
import json
import re
import uuid

from motor.motor_asyncio import AsyncIOMotorDatabase
import httpx

from schemas import (
    LearningPathResponse, UserProgressResponse,
    CareerJourneyRequest, CareerJourneyResponse, ProgressUpdate,
    JourneyPlanResponse, JourneyPathDetail, JourneyModuleDetail,
    JourneyTopicContent, JourneyHandsOn, JourneyMcq, JourneyModuleAssessment,
    TopicProgressResponse, ModuleProgressSummary, TopicProgressUpdate,
    ModuleAssessmentProgressResponse, ModuleAssessmentUpdate, ModuleAssessmentReset,
    CareerTrack, ExperienceLevel, CloudPlatform
)
from services.groq_service import GroqService


class LearningJourneyService:
    def __init__(self):
        self.doc_cache: Dict[str, str] = {}
        self._sync_state_doc_id = "learning-content-sync-state"
        self.career_paths = {
            CareerTrack.CLOUD_ENGINEERING: {
                "description": "Focus on cloud infrastructure, services, and architecture",
                "core_skills": [
                    "Cloud Architecture",
                    "Infrastructure as Code",
                    "Networking",
                    "Security",
                    "Cost Optimization"
                ],
                "paths": [
                    {
                        "path_id": "cloud-foundations",
                        "name": "Cloud Engineering Foundations",
                        "description": "Build strong cloud fundamentals with AWS-first workflows.",
                        "difficulty": ExperienceLevel.JUNIOR,
                        "duration": "8 weeks",
                        "modules": [
                            {
                                "module_id": "cloud-basics",
                                "name": "Cloud Foundations",
                                "description": "Core cloud models, networking, and identity controls.",
                                "estimated_time": "2 weeks",
                                "topics": [
                                    {
                                        "topic_id": "cloud-models",
                                        "title": "Cloud service models",
                                        "teaching": "Understand IaaS, PaaS, and SaaS and when to choose each.",
                                        "key_points": [
                                            "IaaS gives you infrastructure control",
                                            "PaaS accelerates delivery",
                                            "SaaS reduces ops overhead"
                                        ],
                                        "steps": [
                                            "Map workloads to responsibility boundaries",
                                            "Identify managed services that reduce toil",
                                            "Validate compliance and cost impacts"
                                        ],
                                        "hands_on": {
                                            "scenario": "You are migrating a legacy app to AWS and must pick a service model for speed and control.",
                                            "tasks": [
                                                "List the trade-offs for EC2 vs Elastic Beanstalk",
                                                "Select a model and justify the choice",
                                                "Document the operational responsibilities"
                                            ],
                                            "validation": [
                                                "Clear mapping of responsibilities",
                                                "Decision tied to business goals"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "Which model offers the most operational control?",
                                            "options": ["SaaS", "PaaS", "IaaS", "FaaS"],
                                            "correct_option": "IaaS",
                                            "explanation": "IaaS gives direct control of the OS and infrastructure configuration."
                                        }
                                    },
                                    {
                                        "topic_id": "networking-basics",
                                        "title": "VPC networking fundamentals",
                                        "teaching": "Design subnetting, routing, and security boundaries in AWS VPC.",
                                        "key_points": [
                                            "Public vs private subnets",
                                            "Route tables control traffic flow",
                                            "Security groups and NACLs"
                                        ],
                                        "steps": [
                                            "Plan CIDR ranges with growth in mind",
                                            "Place workloads in private subnets",
                                            "Use NAT gateways for outbound access"
                                        ],
                                        "hands_on": {
                                            "scenario": "Your team needs a secure VPC for a three-tier app.",
                                            "tasks": [
                                                "Sketch subnets for web, app, and data tiers",
                                                "Define route tables for each tier",
                                                "Explain how outbound traffic is handled"
                                            ],
                                            "validation": [
                                                "Private data tier",
                                                "NAT for outbound access"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "Which component allows instances in private subnets to access the internet?",
                                            "options": ["Internet Gateway", "NAT Gateway", "Route 53", "VPC Peering"],
                                            "correct_option": "NAT Gateway",
                                            "explanation": "NAT gateways provide outbound internet access for private subnets."
                                        }
                                    }
                                ]
                            },
                            {
                                "module_id": "compute-storage",
                                "name": "Compute and Storage",
                                "description": "Pick compute and storage services for scale and cost.",
                                "estimated_time": "3 weeks",
                                "topics": [
                                    {
                                        "topic_id": "compute-selection",
                                        "title": "EC2 vs Lambda selection",
                                        "teaching": "Choose between serverless and instance-based compute based on workload patterns.",
                                        "key_points": [
                                            "Lambda fits event-driven workloads",
                                            "EC2 suits long-running processes",
                                            "Cost depends on utilization"
                                        ],
                                        "steps": [
                                            "Estimate runtime and concurrency",
                                            "Review operational overhead",
                                            "Match scaling needs to service limits"
                                        ],
                                        "hands_on": {
                                            "scenario": "A batch job runs for 20 minutes every hour and spikes in traffic.",
                                            "tasks": [
                                                "Compare Lambda and EC2 costs",
                                                "Decide on the compute model",
                                                "List scaling considerations"
                                            ],
                                            "validation": [
                                                "Cost comparison included",
                                                "Clear scaling plan"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "Which service removes the need to manage servers?",
                                            "options": ["EC2", "Lambda", "EBS", "S3"],
                                            "correct_option": "Lambda",
                                            "explanation": "Lambda is serverless and abstracts server management."
                                        }
                                    },
                                    {
                                        "topic_id": "storage-choices",
                                        "title": "Storage classes and tiers",
                                        "teaching": "Match S3 storage classes to access patterns and compliance needs.",
                                        "key_points": [
                                            "Standard for frequent access",
                                            "IA and Glacier for infrequent access",
                                            "Lifecycle policies automate transitions"
                                        ],
                                        "steps": [
                                            "Classify data by access frequency",
                                            "Define lifecycle policies",
                                            "Monitor storage costs"
                                        ],
                                        "hands_on": {
                                            "scenario": "You have log data accessed monthly and must reduce costs.",
                                            "tasks": [
                                                "Select a storage class",
                                                "Write a lifecycle rule",
                                                "Explain retrieval expectations"
                                            ],
                                            "validation": [
                                                "Appropriate storage class",
                                                "Lifecycle strategy defined"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "Which S3 class is best for archive data?",
                                            "options": ["Standard", "Intelligent-Tiering", "Glacier", "One Zone-IA"],
                                            "correct_option": "Glacier",
                                            "explanation": "Glacier is designed for long-term archival storage."
                                        }
                                    }
                                ]
                            },
                            {
                                "module_id": "iac-basics",
                                "name": "Infrastructure as Code",
                                "description": "Automate provisioning with Terraform and CloudFormation.",
                                "estimated_time": "3 weeks",
                                "topics": [
                                    {
                                        "topic_id": "iac-workflows",
                                        "title": "IaC workflow design",
                                        "teaching": "Establish safe workflows for change management and reviews.",
                                        "key_points": [
                                            "Use version control",
                                            "Plan and review changes",
                                            "Separate environments"
                                        ],
                                        "steps": [
                                            "Define a branch strategy",
                                            "Run plans in CI",
                                            "Apply with approval gates"
                                        ],
                                        "hands_on": {
                                            "scenario": "Your team needs repeatable VPC creation across dev and prod.",
                                            "tasks": [
                                                "Outline a Terraform module",
                                                "Describe state management",
                                                "Explain environment separation"
                                            ],
                                            "validation": [
                                                "Reusable module defined",
                                                "State management considered"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "What is the primary benefit of using IaC?",
                                            "options": ["Lower latency", "Repeatable infrastructure", "Unlimited scaling", "No testing"],
                                            "correct_option": "Repeatable infrastructure",
                                            "explanation": "IaC enables consistent and repeatable infrastructure provisioning."
                                        }
                                    },
                                    {
                                        "topic_id": "iac-security",
                                        "title": "Secure IaC practices",
                                        "teaching": "Protect secrets and apply policy controls in IaC pipelines.",
                                        "key_points": [
                                            "Never hardcode secrets",
                                            "Use policy-as-code",
                                            "Validate before apply"
                                        ],
                                        "steps": [
                                            "Integrate secret managers",
                                            "Run policy checks in CI",
                                            "Scan for misconfigurations"
                                        ],
                                        "hands_on": {
                                            "scenario": "A pipeline failed due to exposed credentials in a Terraform file.",
                                            "tasks": [
                                                "Identify secure secret storage",
                                                "Add policy checks",
                                                "Describe remediation steps"
                                            ],
                                            "validation": [
                                                "Secure storage identified",
                                                "Policy checks included"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "Which practice prevents secrets from being stored in code?",
                                            "options": ["Local files", "Environment variables", "Hardcoding", "Public repos"],
                                            "correct_option": "Environment variables",
                                            "explanation": "Environment variables or secret managers avoid hardcoding secrets."
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "path_id": "cloud-professional",
                        "name": "Cloud Engineering Professional",
                        "description": "Design resilient, secure, and cost-aware cloud platforms.",
                        "difficulty": ExperienceLevel.MID,
                        "duration": "10 weeks",
                        "modules": [
                            {
                                "module_id": "reliable-architecture",
                                "name": "Reliable Architecture",
                                "description": "Build for scalability, resilience, and recovery.",
                                "estimated_time": "3 weeks",
                                "topics": [
                                    {
                                        "topic_id": "autoscaling-design",
                                        "title": "Autoscaling strategies",
                                        "teaching": "Design autoscaling based on demand patterns and service limits.",
                                        "key_points": [
                                            "Use metrics-based policies",
                                            "Scale at multiple layers",
                                            "Plan for warm capacity"
                                        ],
                                        "steps": [
                                            "Define scaling metrics",
                                            "Set safe min/max limits",
                                            "Test scaling behaviors"
                                        ],
                                        "hands_on": {
                                            "scenario": "Traffic spikes 5x weekly and latency increases.",
                                            "tasks": [
                                                "Design scaling policies",
                                                "Add cache layers",
                                                "Document rollback plan"
                                            ],
                                            "validation": [
                                                "Scaling metrics defined",
                                                "Cache strategy included"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "Which metric is commonly used for autoscaling EC2?",
                                            "options": ["CPU utilization", "Disk size", "VPC count", "Route tables"],
                                            "correct_option": "CPU utilization",
                                            "explanation": "CPU utilization is a common scaling signal for EC2 workloads."
                                        }
                                    },
                                    {
                                        "topic_id": "disaster-recovery",
                                        "title": "Disaster recovery planning",
                                        "teaching": "Define RTO/RPO and select a recovery strategy.",
                                        "key_points": [
                                            "Align RTO/RPO with business",
                                            "Choose pilot light or warm standby",
                                            "Test recovery runbooks"
                                        ],
                                        "steps": [
                                            "Define business impact",
                                            "Select recovery tier",
                                            "Automate recovery steps"
                                        ],
                                        "hands_on": {
                                            "scenario": "A regional outage affects your primary region.",
                                            "tasks": [
                                                "Select a DR strategy",
                                                "Describe data replication",
                                                "Define failover steps"
                                            ],
                                            "validation": [
                                                "DR strategy justified",
                                                "Replication method specified"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "Which DR strategy has the lowest cost but longest recovery?",
                                            "options": ["Multi-site active", "Warm standby", "Pilot light", "Hot standby"],
                                            "correct_option": "Pilot light",
                                            "explanation": "Pilot light keeps minimal resources running and scales during recovery."
                                        }
                                    }
                                ]
                            },
                            {
                                "module_id": "security-governance",
                                "name": "Security and Governance",
                                "description": "Implement security controls and compliance checks.",
                                "estimated_time": "3 weeks",
                                "topics": [
                                    {
                                        "topic_id": "iam-guardrails",
                                        "title": "IAM guardrails",
                                        "teaching": "Design least-privilege policies with centralized control.",
                                        "key_points": [
                                            "Use roles over users",
                                            "Apply SCPs and permission boundaries",
                                            "Audit access regularly"
                                        ],
                                        "steps": [
                                            "Create role-based access",
                                            "Limit permissions with policies",
                                            "Enable logging and alerts"
                                        ],
                                        "hands_on": {
                                            "scenario": "Developers need access to S3 but not production databases.",
                                            "tasks": [
                                                "Design role policies",
                                                "Add permission boundaries",
                                                "Explain audit strategy"
                                            ],
                                            "validation": [
                                                "Least privilege applied",
                                                "Audit plan provided"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "What enforces account-wide permission limits in AWS Organizations?",
                                            "options": ["Security Groups", "SCPs", "KMS", "CloudTrail"],
                                            "correct_option": "SCPs",
                                            "explanation": "Service control policies set boundaries for accounts in an organization."
                                        }
                                    },
                                    {
                                        "topic_id": "cost-controls",
                                        "title": "Cost governance",
                                        "teaching": "Establish budgets and tagging to control spend.",
                                        "key_points": [
                                            "Use cost allocation tags",
                                            "Set budgets and alerts",
                                            "Review reserved instances"
                                        ],
                                        "steps": [
                                            "Define tagging standards",
                                            "Enable budget alerts",
                                            "Review monthly cost reports"
                                        ],
                                        "hands_on": {
                                            "scenario": "Cloud spend is 30% over budget for two months.",
                                            "tasks": [
                                                "Identify cost drivers",
                                                "Apply tagging for accountability",
                                                "Recommend optimization actions"
                                            ],
                                            "validation": [
                                                "Cost drivers identified",
                                                "Optimization actions listed"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "Which AWS tool helps set alerts for spending thresholds?",
                                            "options": ["CloudWatch", "Budgets", "Trusted Advisor", "CloudTrail"],
                                            "correct_option": "Budgets",
                                            "explanation": "AWS Budgets provides cost and usage alerts."
                                        }
                                    }
                                ]
                            },
                            {
                                "module_id": "platform-automation",
                                "name": "Platform Automation",
                                "description": "Automate delivery and infrastructure operations.",
                                "estimated_time": "4 weeks",
                                "topics": [
                                    {
                                        "topic_id": "pipeline-automation",
                                        "title": "CI/CD for infrastructure",
                                        "teaching": "Build pipelines that test and deploy infrastructure safely.",
                                        "key_points": [
                                            "Use plan and validate stages",
                                            "Add approvals for prod",
                                            "Keep state secure"
                                        ],
                                        "steps": [
                                            "Define pipeline stages",
                                            "Add automated checks",
                                            "Document rollback strategies"
                                        ],
                                        "hands_on": {
                                            "scenario": "A Terraform change caused outage in production.",
                                            "tasks": [
                                                "Add a validation gate",
                                                "Define rollback steps",
                                                "Introduce canary changes"
                                            ],
                                            "validation": [
                                                "Validation gate included",
                                                "Rollback plan exists"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "Which stage should run before applying IaC changes?",
                                            "options": ["Destroy", "Plan", "Deploy", "Monitor"],
                                            "correct_option": "Plan",
                                            "explanation": "Plan previews changes and helps detect risky modifications."
                                        }
                                    },
                                    {
                                        "topic_id": "observability-ops",
                                        "title": "Observability operations",
                                        "teaching": "Implement metrics, logs, and traces to detect issues.",
                                        "key_points": [
                                            "Define SLOs",
                                            "Centralize logging",
                                            "Alert on symptoms"
                                        ],
                                        "steps": [
                                            "Identify key service indicators",
                                            "Set alert thresholds",
                                            "Build dashboards for teams"
                                        ],
                                        "hands_on": {
                                            "scenario": "Users report latency spikes but no clear logs.",
                                            "tasks": [
                                                "Define required metrics",
                                                "Add tracing",
                                                "Create an alerting rule"
                                            ],
                                            "validation": [
                                                "Metrics and tracing specified",
                                                "Alert defined"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "What does an SLO represent?",
                                            "options": ["A log format", "A reliability target", "A backup strategy", "A billing plan"],
                                            "correct_option": "A reliability target",
                                            "explanation": "SLOs define measurable reliability goals."
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
            CareerTrack.DEVOPS_PLATFORM: {
                "description": "Focus on CI/CD, automation, and platform engineering",
                "core_skills": [
                    "CI/CD",
                    "Containerization",
                    "Orchestration",
                    "Monitoring",
                    "Automation"
                ],
                "paths": [
                    {
                        "path_id": "devops-foundations",
                        "name": "DevOps Foundations",
                        "description": "Build core DevOps workflows and tooling expertise.",
                        "difficulty": ExperienceLevel.JUNIOR,
                        "duration": "9 weeks",
                        "modules": [
                            {
                                "module_id": "devops-culture",
                                "name": "DevOps Culture",
                                "description": "Adopt collaboration and continuous delivery habits.",
                                "estimated_time": "2 weeks",
                                "topics": [
                                    {
                                        "topic_id": "devops-principles",
                                        "title": "DevOps principles",
                                        "teaching": "Learn CALMS and how it drives delivery speed.",
                                        "key_points": [
                                            "Culture and collaboration",
                                            "Automation for repeatability",
                                            "Measurement and feedback"
                                        ],
                                        "steps": [
                                            "Assess current delivery gaps",
                                            "Define cross-team workflows",
                                            "Set delivery metrics"
                                        ],
                                        "hands_on": {
                                            "scenario": "Teams release once a month and want weekly releases.",
                                            "tasks": [
                                                "Identify blockers",
                                                "Propose automation steps",
                                                "Define success metrics"
                                            ],
                                            "validation": [
                                                "Automation steps listed",
                                                "Metrics defined"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "Which element is part of CALMS?",
                                            "options": ["Culture", "Latency", "Memory", "Storage"],
                                            "correct_option": "Culture",
                                            "explanation": "CALMS stands for Culture, Automation, Lean, Measurement, Sharing."
                                        }
                                    },
                                    {
                                        "topic_id": "version-control",
                                        "title": "Version control workflows",
                                        "teaching": "Create branching and review practices for quality.",
                                        "key_points": [
                                            "Use pull requests",
                                            "Protect main branches",
                                            "Automate checks"
                                        ],
                                        "steps": [
                                            "Define branching model",
                                            "Enforce code review",
                                            "Integrate automated testing"
                                        ],
                                        "hands_on": {
                                            "scenario": "A team needs a consistent merge process for 10 developers.",
                                            "tasks": [
                                                "Choose a branching strategy",
                                                "List required checks",
                                                "Define merge policies"
                                            ],
                                            "validation": [
                                                "Branch strategy selected",
                                                "Checks included"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "Which practice improves code quality before merging?",
                                            "options": ["Force push", "Pull request review", "Direct commits", "Skip tests"],
                                            "correct_option": "Pull request review",
                                            "explanation": "Pull request reviews introduce quality gates and collaboration."
                                        }
                                    }
                                ]
                            },
                            {
                                "module_id": "ci-cd-basics",
                                "name": "CI/CD Pipelines",
                                "description": "Build pipelines for testing and deployment automation.",
                                "estimated_time": "3 weeks",
                                "topics": [
                                    {
                                        "topic_id": "pipeline-design",
                                        "title": "Pipeline stages",
                                        "teaching": "Plan build, test, and deploy stages with quality gates.",
                                        "key_points": [
                                            "Short feedback loops",
                                            "Automated tests",
                                            "Promotion between environments"
                                        ],
                                        "steps": [
                                            "Define stage order",
                                            "Add test coverage",
                                            "Automate deployment approvals"
                                        ],
                                        "hands_on": {
                                            "scenario": "Deployments take 2 hours and block engineers.",
                                            "tasks": [
                                                "Identify automation steps",
                                                "Map pipeline stages",
                                                "Define rollbacks"
                                            ],
                                            "validation": [
                                                "Automation steps outlined",
                                                "Rollback included"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "What is the primary goal of CI?",
                                            "options": ["Manual deployments", "Frequent integration", "Daily backups", "Network tuning"],
                                            "correct_option": "Frequent integration",
                                            "explanation": "CI focuses on integrating code often to detect issues early."
                                        }
                                    },
                                    {
                                        "topic_id": "artifact-management",
                                        "title": "Artifact management",
                                        "teaching": "Store and promote build artifacts across environments.",
                                        "key_points": [
                                            "Immutable artifacts",
                                            "Versioning and traceability",
                                            "Secure storage"
                                        ],
                                        "steps": [
                                            "Pick a registry",
                                            "Define versioning",
                                            "Automate artifact promotion"
                                        ],
                                        "hands_on": {
                                            "scenario": "Teams rebuild artifacts per environment, causing inconsistencies.",
                                            "tasks": [
                                                "Propose an artifact strategy",
                                                "Explain versioning",
                                                "List required controls"
                                            ],
                                            "validation": [
                                                "Immutable artifact strategy",
                                                "Traceability included"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "Why use immutable artifacts?",
                                            "options": ["Faster boot", "Repeatable deployments", "Lower CPU", "More logs"],
                                            "correct_option": "Repeatable deployments",
                                            "explanation": "Immutable artifacts ensure consistent deployments across environments."
                                        }
                                    }
                                ]
                            },
                            {
                                "module_id": "containers-k8s",
                                "name": "Containers and Orchestration",
                                "description": "Package apps and run them at scale with Kubernetes.",
                                "estimated_time": "4 weeks",
                                "topics": [
                                    {
                                        "topic_id": "docker-essentials",
                                        "title": "Docker essentials",
                                        "teaching": "Build container images and manage runtime configs.",
                                        "key_points": [
                                            "Small images reduce risk",
                                            "Use multi-stage builds",
                                            "Externalize configuration"
                                        ],
                                        "steps": [
                                            "Create a Dockerfile",
                                            "Scan images for vulnerabilities",
                                            "Use environment variables"
                                        ],
                                        "hands_on": {
                                            "scenario": "Your image size is 1.2GB and builds are slow.",
                                            "tasks": [
                                                "Use multi-stage build",
                                                "Remove unused packages",
                                                "Optimize caching"
                                            ],
                                            "validation": [
                                                "Multi-stage build noted",
                                                "Cache optimization included"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "What reduces container image size?",
                                            "options": ["Single-stage build", "Multi-stage build", "Unused packages", "No caching"],
                                            "correct_option": "Multi-stage build",
                                            "explanation": "Multi-stage builds allow shipping only runtime dependencies."
                                        }
                                    },
                                    {
                                        "topic_id": "k8s-workloads",
                                        "title": "Kubernetes workloads",
                                        "teaching": "Deploy and scale apps with Deployments and Services.",
                                        "key_points": [
                                            "Use Deployments for rollout",
                                            "Services provide stable access",
                                            "Configure liveness/readiness"
                                        ],
                                        "steps": [
                                            "Define deployment specs",
                                            "Add probes",
                                            "Set resource limits"
                                        ],
                                        "hands_on": {
                                            "scenario": "A deployment rollout keeps failing due to crashes.",
                                            "tasks": [
                                                "Add readiness probes",
                                                "Check resource limits",
                                                "Propose rollback strategy"
                                            ],
                                            "validation": [
                                                "Probes defined",
                                                "Rollback plan included"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "Which resource ensures a stable endpoint for pods?",
                                            "options": ["Deployment", "Service", "ConfigMap", "Secret"],
                                            "correct_option": "Service",
                                            "explanation": "Services provide stable networking for pods."
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "path_id": "devops-professional",
                        "name": "Platform Engineering Professional",
                        "description": "Build scalable internal platforms and automation frameworks.",
                        "difficulty": ExperienceLevel.MID,
                        "duration": "11 weeks",
                        "modules": [
                            {
                                "module_id": "platform-architecture",
                                "name": "Platform Architecture",
                                "description": "Design shared platforms and golden paths.",
                                "estimated_time": "3 weeks",
                                "topics": [
                                    {
                                        "topic_id": "platform-strategy",
                                        "title": "Platform strategy",
                                        "teaching": "Create platform roadmaps based on developer needs.",
                                        "key_points": [
                                            "Define golden paths",
                                            "Measure developer experience",
                                            "Prioritize self-service"
                                        ],
                                        "steps": [
                                            "Collect developer pain points",
                                            "Define platform KPIs",
                                            "Build a reference architecture"
                                        ],
                                        "hands_on": {
                                            "scenario": "Developers use five CI tools and want consistency.",
                                            "tasks": [
                                                "Define a golden path",
                                                "Describe migration phases",
                                                "Set adoption metrics"
                                            ],
                                            "validation": [
                                                "Migration phases defined",
                                                "Metrics listed"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "What is a golden path?",
                                            "options": ["A backup plan", "Preferred platform workflow", "A security policy", "A monitoring tool"],
                                            "correct_option": "Preferred platform workflow",
                                            "explanation": "Golden paths are recommended workflows for teams to use."
                                        }
                                    },
                                    {
                                        "topic_id": "self-service",
                                        "title": "Self-service platforms",
                                        "teaching": "Enable teams to provision environments without manual tickets.",
                                        "key_points": [
                                            "Use templates",
                                            "Provide guardrails",
                                            "Automate approvals"
                                        ],
                                        "steps": [
                                            "Design service catalog",
                                            "Define guardrails",
                                            "Automate provisioning"
                                        ],
                                        "hands_on": {
                                            "scenario": "Provisioning takes two weeks due to manual approvals.",
                                            "tasks": [
                                                "Propose a service catalog",
                                                "Define guardrails",
                                                "Recommend automation steps"
                                            ],
                                            "validation": [
                                                "Service catalog included",
                                                "Guardrails set"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "What improves provisioning speed the most?",
                                            "options": ["Manual tickets", "Self-service templates", "Weekly meetings", "Email approvals"],
                                            "correct_option": "Self-service templates",
                                            "explanation": "Self-service templates remove manual bottlenecks."
                                        }
                                    }
                                ]
                            },
                            {
                                "module_id": "observability-sre",
                                "name": "Observability and SRE",
                                "description": "Build monitoring and reliability practices.",
                                "estimated_time": "4 weeks",
                                "topics": [
                                    {
                                        "topic_id": "slo-management",
                                        "title": "SLO management",
                                        "teaching": "Set SLOs and error budgets to drive reliability decisions.",
                                        "key_points": [
                                            "Define SLIs",
                                            "Set error budgets",
                                            "Balance reliability with velocity"
                                        ],
                                        "steps": [
                                            "Identify key user journeys",
                                            "Set SLI thresholds",
                                            "Review error budget burn"
                                        ],
                                        "hands_on": {
                                            "scenario": "Latency breaches are frequent and teams disagree on priorities.",
                                            "tasks": [
                                                "Define an SLO",
                                                "Set an error budget",
                                                "Describe escalation steps"
                                            ],
                                            "validation": [
                                                "SLO defined",
                                                "Escalation included"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "What does an error budget represent?",
                                            "options": ["Monthly budget", "Allowed unreliability", "CPU budget", "Logging quota"],
                                            "correct_option": "Allowed unreliability",
                                            "explanation": "Error budgets quantify acceptable unreliability before action."
                                        }
                                    },
                                    {
                                        "topic_id": "incident-response",
                                        "title": "Incident response",
                                        "teaching": "Build runbooks and postmortems to improve resilience.",
                                        "key_points": [
                                            "Use runbooks",
                                            "Practice game days",
                                            "Blameless postmortems"
                                        ],
                                        "steps": [
                                            "Define incident roles",
                                            "Document response steps",
                                            "Capture lessons learned"
                                        ],
                                        "hands_on": {
                                            "scenario": "A production outage lasted two hours without clear ownership.",
                                            "tasks": [
                                                "Define incident roles",
                                                "Draft a runbook outline",
                                                "Describe postmortem steps"
                                            ],
                                            "validation": [
                                                "Roles defined",
                                                "Postmortem included"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "Which practice strengthens incident learning?",
                                            "options": ["Blameless postmortems", "Assigning blame", "Skipping reviews", "Ignoring alerts"],
                                            "correct_option": "Blameless postmortems",
                                            "explanation": "Blameless postmortems focus on learning and system improvement."
                                        }
                                    }
                                ]
                            },
                            {
                                "module_id": "security-automation",
                                "name": "Security Automation",
                                "description": "Integrate security into CI/CD and runtime.",
                                "estimated_time": "4 weeks",
                                "topics": [
                                    {
                                        "topic_id": "devsecops",
                                        "title": "DevSecOps integration",
                                        "teaching": "Embed security checks into delivery pipelines.",
                                        "key_points": [
                                            "Shift-left security",
                                            "Automated scanning",
                                            "Policy enforcement"
                                        ],
                                        "steps": [
                                            "Add SAST and DAST",
                                            "Define gating rules",
                                            "Monitor runtime security"
                                        ],
                                        "hands_on": {
                                            "scenario": "Security reviews happen at the end and slow releases.",
                                            "tasks": [
                                                "Move scanning to CI",
                                                "Define security gates",
                                                "Set alerting for vulnerabilities"
                                            ],
                                            "validation": [
                                                "Scanning in CI",
                                                "Gates defined"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "What does shift-left security mean?",
                                            "options": ["Security at the end", "Security early in pipeline", "Security after deployment", "Security only in prod"],
                                            "correct_option": "Security early in pipeline",
                                            "explanation": "Shift-left integrates security earlier in the SDLC."
                                        }
                                    },
                                    {
                                        "topic_id": "policy-as-code",
                                        "title": "Policy as code",
                                        "teaching": "Use policy checks to enforce security and compliance.",
                                        "key_points": [
                                            "Automate compliance",
                                            "Prevent drift",
                                            "Use reusable policies"
                                        ],
                                        "steps": [
                                            "Define policy rules",
                                            "Integrate with CI",
                                            "Monitor violations"
                                        ],
                                        "hands_on": {
                                            "scenario": "A team deploys resources without encryption.",
                                            "tasks": [
                                                "Define a policy to require encryption",
                                                "Add policy checks to CI",
                                                "Describe remediation"
                                            ],
                                            "validation": [
                                                "Encryption policy defined",
                                                "CI checks added"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "Which tool is commonly used for policy as code?",
                                            "options": ["OPA", "NGINX", "Redis", "Jenkins"],
                                            "correct_option": "OPA",
                                            "explanation": "Open Policy Agent is a common policy-as-code tool."
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
            CareerTrack.HYBRID: {
                "description": "Balanced approach covering both cloud and DevOps expertise",
                "core_skills": [
                    "Cloud Platforms",
                    "DevOps Practices",
                    "Infrastructure Automation",
                    "Security",
                    "Monitoring"
                ],
                "paths": [
                    {
                        "path_id": "hybrid-foundations",
                        "name": "Hybrid Cloud-DevOps Foundations",
                        "description": "Blend cloud and DevOps fundamentals for modern platforms.",
                        "difficulty": ExperienceLevel.JUNIOR,
                        "duration": "9 weeks",
                        "modules": [
                            {
                                "module_id": "cloud-native-basics",
                                "name": "Cloud-Native Basics",
                                "description": "Learn cloud-native architecture and service basics.",
                                "estimated_time": "3 weeks",
                                "topics": [
                                    {
                                        "topic_id": "cloud-native-architecture",
                                        "title": "Cloud-native architecture",
                                        "teaching": "Understand microservices and managed services patterns.",
                                        "key_points": [
                                            "Microservices separation",
                                            "Managed services reduce ops",
                                            "Resilience by design"
                                        ],
                                        "steps": [
                                            "Identify service boundaries",
                                            "Select managed services",
                                            "Design for failure"
                                        ],
                                        "hands_on": {
                                            "scenario": "A monolith needs to scale independently by feature.",
                                            "tasks": [
                                                "Identify candidate services",
                                                "Define data boundaries",
                                                "Propose migration steps"
                                            ],
                                            "validation": [
                                                "Service boundaries defined",
                                                "Migration steps included"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "What is a key benefit of microservices?",
                                            "options": ["Single deploy", "Independent scaling", "No monitoring", "No APIs"],
                                            "correct_option": "Independent scaling",
                                            "explanation": "Microservices allow services to scale independently."
                                        }
                                    },
                                    {
                                        "topic_id": "shared-responsibility",
                                        "title": "Shared responsibility",
                                        "teaching": "Clarify security and operational responsibilities between cloud and team.",
                                        "key_points": [
                                            "Cloud secures the infrastructure",
                                            "You secure data and configs",
                                            "Compliance is shared"
                                        ],
                                        "steps": [
                                            "List provider vs customer duties",
                                            "Map controls to services",
                                            "Review compliance needs"
                                        ],
                                        "hands_on": {
                                            "scenario": "An audit requires proof of responsibility boundaries.",
                                            "tasks": [
                                                "List shared responsibilities",
                                                "Identify control ownership",
                                                "Document compliance evidence"
                                            ],
                                            "validation": [
                                                "Responsibilities mapped",
                                                "Evidence identified"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "Who is responsible for data encryption configuration?",
                                            "options": ["Cloud provider", "Customer", "No one", "Third party"],
                                            "correct_option": "Customer",
                                            "explanation": "Customers are responsible for configuring data encryption."
                                        }
                                    }
                                ]
                            },
                            {
                                "module_id": "delivery-automation",
                                "name": "Delivery Automation",
                                "description": "Automate delivery workflows for cloud-native apps.",
                                "estimated_time": "3 weeks",
                                "topics": [
                                    {
                                        "topic_id": "gitops-basics",
                                        "title": "GitOps fundamentals",
                                        "teaching": "Use Git as the source of truth for deployments.",
                                        "key_points": [
                                            "Declarative configs",
                                            "Automated reconciliation",
                                            "Auditability"
                                        ],
                                        "steps": [
                                            "Create Git repo for configs",
                                            "Use a GitOps controller",
                                            "Set environment rules"
                                        ],
                                        "hands_on": {
                                            "scenario": "Deployments drift between environments.",
                                            "tasks": [
                                                "Set Git as source of truth",
                                                "Introduce a controller",
                                                "Define sync policies"
                                            ],
                                            "validation": [
                                                "Source of truth defined",
                                                "Sync policies included"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "What is the core principle of GitOps?",
                                            "options": ["Manual deployments", "Git as source of truth", "No automation", "Centralized DB"],
                                            "correct_option": "Git as source of truth",
                                            "explanation": "GitOps relies on Git to define desired system state."
                                        }
                                    },
                                    {
                                        "topic_id": "progressive-delivery",
                                        "title": "Progressive delivery",
                                        "teaching": "Deploy changes safely with canary and blue-green strategies.",
                                        "key_points": [
                                            "Limit blast radius",
                                            "Use automated validation",
                                            "Rollback quickly"
                                        ],
                                        "steps": [
                                            "Define rollout steps",
                                            "Add health checks",
                                            "Automate rollback"
                                        ],
                                        "hands_on": {
                                            "scenario": "A release failed and impacted 30% of users.",
                                            "tasks": [
                                                "Select a deployment strategy",
                                                "Define automated checks",
                                                "Plan rollback criteria"
                                            ],
                                            "validation": [
                                                "Strategy selected",
                                                "Rollback criteria set"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "Which strategy sends traffic to a new version gradually?",
                                            "options": ["Canary", "Blue-green", "Big bang", "Manual"],
                                            "correct_option": "Canary",
                                            "explanation": "Canary deployments gradually shift traffic to new versions."
                                        }
                                    }
                                ]
                            },
                            {
                                "module_id": "production-excellence",
                                "name": "Production Excellence",
                                "description": "Operate, secure, and optimize modern cloud platforms.",
                                "estimated_time": "3 weeks",
                                "topics": [
                                    {
                                        "topic_id": "cost-performance",
                                        "title": "Cost and performance",
                                        "teaching": "Balance performance targets with cost optimization.",
                                        "key_points": [
                                            "Right-size resources",
                                            "Use autoscaling",
                                            "Monitor utilization"
                                        ],
                                        "steps": [
                                            "Review utilization data",
                                            "Adjust instance types",
                                            "Enable autoscaling"
                                        ],
                                        "hands_on": {
                                            "scenario": "Monthly costs spiked after a product launch.",
                                            "tasks": [
                                                "Identify high-cost services",
                                                "Recommend right-sizing",
                                                "Create a savings plan"
                                            ],
                                            "validation": [
                                                "High-cost services identified",
                                                "Right-sizing plan included"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "Which action reduces cost without changing architecture?",
                                            "options": ["Right-sizing", "Replatforming", "Rebuilding", "Manual scaling"],
                                            "correct_option": "Right-sizing",
                                            "explanation": "Right-sizing adjusts resource sizes to match usage."
                                        }
                                    },
                                    {
                                        "topic_id": "security-observability",
                                        "title": "Security and observability",
                                        "teaching": "Implement security monitoring and alerting practices.",
                                        "key_points": [
                                            "Centralize logs",
                                            "Alert on anomalies",
                                            "Track security posture"
                                        ],
                                        "steps": [
                                            "Define security log sources",
                                            "Set alert thresholds",
                                            "Review findings regularly"
                                        ],
                                        "hands_on": {
                                            "scenario": "Security incidents were detected late due to missing alerts.",
                                            "tasks": [
                                                "Define required log sources",
                                                "Create alert rules",
                                                "Recommend response steps"
                                            ],
                                            "validation": [
                                                "Log sources defined",
                                                "Alert rules included"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "What is the benefit of centralized logging?",
                                            "options": ["More latency", "Unified visibility", "Less storage", "Fewer alerts"],
                                            "correct_option": "Unified visibility",
                                            "explanation": "Centralized logging provides unified observability across systems."
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "path_id": "hybrid-professional",
                        "name": "Hybrid Cloud-DevOps Professional",
                        "description": "Master advanced cloud and DevOps integration practices.",
                        "difficulty": ExperienceLevel.MID,
                        "duration": "11 weeks",
                        "modules": [
                            {
                                "module_id": "platform-integration",
                                "name": "Platform Integration",
                                "description": "Connect cloud platforms with DevOps automation.",
                                "estimated_time": "4 weeks",
                                "topics": [
                                    {
                                        "topic_id": "service-integration",
                                        "title": "Service integration patterns",
                                        "teaching": "Connect services with reliable event-driven patterns.",
                                        "key_points": [
                                            "Use queues and events",
                                            "Avoid tight coupling",
                                            "Design for retries"
                                        ],
                                        "steps": [
                                            "Define event schema",
                                            "Implement retries",
                                            "Monitor failures"
                                        ],
                                        "hands_on": {
                                            "scenario": "Two services frequently fail due to synchronous calls.",
                                            "tasks": [
                                                "Design an async pattern",
                                                "Define event payloads",
                                                "Explain monitoring approach"
                                            ],
                                            "validation": [
                                                "Async pattern selected",
                                                "Monitoring approach provided"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "Which component decouples services in event-driven design?",
                                            "options": ["Queue", "Load balancer", "DNS", "VPN"],
                                            "correct_option": "Queue",
                                            "explanation": "Queues buffer messages and reduce coupling between services."
                                        }
                                    },
                                    {
                                        "topic_id": "infra-automation",
                                        "title": "Infrastructure automation",
                                        "teaching": "Automate platform setup and configuration with IaC.",
                                        "key_points": [
                                            "Reusable modules",
                                            "Versioned infrastructure",
                                            "Policy enforcement"
                                        ],
                                        "steps": [
                                            "Create IaC modules",
                                            "Automate environment provisioning",
                                            "Enforce policies"
                                        ],
                                        "hands_on": {
                                            "scenario": "Teams create infrastructure manually, causing drift.",
                                            "tasks": [
                                                "Propose IaC workflow",
                                                "Define module structure",
                                                "List policy checks"
                                            ],
                                            "validation": [
                                                "IaC workflow defined",
                                                "Policy checks included"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "What prevents configuration drift?",
                                            "options": ["Manual changes", "IaC", "Local scripts", "No versioning"],
                                            "correct_option": "IaC",
                                            "explanation": "IaC keeps infrastructure definitions consistent and versioned."
                                        }
                                    }
                                ]
                            },
                            {
                                "module_id": "secure-operations",
                                "name": "Secure Operations",
                                "description": "Run secure, compliant, and observable systems.",
                                "estimated_time": "3 weeks",
                                "topics": [
                                    {
                                        "topic_id": "compliance-automation",
                                        "title": "Compliance automation",
                                        "teaching": "Automate compliance checks and reporting.",
                                        "key_points": [
                                            "Automated evidence",
                                            "Continuous compliance",
                                            "Audit readiness"
                                        ],
                                        "steps": [
                                            "Define compliance controls",
                                            "Automate evidence collection",
                                            "Schedule compliance reviews"
                                        ],
                                        "hands_on": {
                                            "scenario": "An audit is due in 30 days with limited evidence.",
                                            "tasks": [
                                                "List required evidence",
                                                "Automate evidence collection",
                                                "Define review cadence"
                                            ],
                                            "validation": [
                                                "Evidence plan included",
                                                "Review cadence defined"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "What supports continuous compliance?",
                                            "options": ["Manual checklists", "Automated evidence", "Annual audits", "Email reports"],
                                            "correct_option": "Automated evidence",
                                            "explanation": "Automated evidence collection keeps compliance up to date."
                                        }
                                    },
                                    {
                                        "topic_id": "zero-trust",
                                        "title": "Zero trust operations",
                                        "teaching": "Apply least-privilege and continuous verification.",
                                        "key_points": [
                                            "Verify every request",
                                            "Use least privilege",
                                            "Monitor continuously"
                                        ],
                                        "steps": [
                                            "Segment access",
                                            "Enforce MFA",
                                            "Monitor identity events"
                                        ],
                                        "hands_on": {
                                            "scenario": "A compromised credential accessed production resources.",
                                            "tasks": [
                                                "Define access segmentation",
                                                "Implement MFA policies",
                                                "Describe monitoring changes"
                                            ],
                                            "validation": [
                                                "Access segmentation defined",
                                                "Monitoring changes included"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "Which principle is core to zero trust?",
                                            "options": ["Trust internal network", "Verify every request", "Single password", "Disable logs"],
                                            "correct_option": "Verify every request",
                                            "explanation": "Zero trust assumes no implicit trust and verifies every request."
                                        }
                                    }
                                ]
                            },
                            {
                                "module_id": "engineering-leadership",
                                "name": "Engineering Leadership",
                                "description": "Lead platform adoption and drive outcomes.",
                                "estimated_time": "4 weeks",
                                "topics": [
                                    {
                                        "topic_id": "change-management",
                                        "title": "Change management",
                                        "teaching": "Drive adoption with communication and training.",
                                        "key_points": [
                                            "Stakeholder alignment",
                                            "Training programs",
                                            "Measure adoption"
                                        ],
                                        "steps": [
                                            "Define stakeholder map",
                                            "Create training sessions",
                                            "Track adoption metrics"
                                        ],
                                        "hands_on": {
                                            "scenario": "Teams resist a new platform workflow.",
                                            "tasks": [
                                                "Identify stakeholders",
                                                "Create a training plan",
                                                "Define success metrics"
                                            ],
                                            "validation": [
                                                "Training plan included",
                                                "Metrics defined"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "What is a good adoption metric?",
                                            "options": ["Number of emails", "Active teams on platform", "Server uptime", "Total logs"],
                                            "correct_option": "Active teams on platform",
                                            "explanation": "Adoption is measured by active usage of the platform."
                                        }
                                    },
                                    {
                                        "topic_id": "platform-metrics",
                                        "title": "Platform success metrics",
                                        "teaching": "Measure impact using DORA and developer experience signals.",
                                        "key_points": [
                                            "Deployment frequency",
                                            "Lead time",
                                            "Change failure rate"
                                        ],
                                        "steps": [
                                            "Define DORA metrics",
                                            "Instrument pipelines",
                                            "Review metrics regularly"
                                        ],
                                        "hands_on": {
                                            "scenario": "Leadership wants evidence of platform value.",
                                            "tasks": [
                                                "Define key metrics",
                                                "Set baselines",
                                                "Report improvements"
                                            ],
                                            "validation": [
                                                "Metrics defined",
                                                "Baselines included"
                                            ]
                                        },
                                        "mcq": {
                                            "question": "Which metric reflects release speed?",
                                            "options": ["Deployment frequency", "CPU usage", "Ticket count", "Cost per hour"],
                                            "correct_option": "Deployment frequency",
                                            "explanation": "Deployment frequency indicates how often changes reach production."
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }

    def _normalize_doc(self, doc: Optional[Dict]) -> Dict:
        if not doc:
            return {}
        data = dict(doc)
        if "_id" in data:
            data["id"] = str(data["_id"])
            data.pop("_id", None)
        return data if data else {}

    def _path_response(self, doc: Dict) -> LearningPathResponse:
        return LearningPathResponse.model_validate(self._normalize_doc(doc))

    def _progress_response(self, doc: Dict) -> UserProgressResponse:
        return UserProgressResponse.model_validate(self._normalize_doc(doc))

    async def ensure_paths_initialized(self, db: AsyncIOMotorDatabase) -> None:
        for track, track_info in self.career_paths.items():
            for path_info in track_info["paths"]:
                path = await self._get_path_by_id(db, path_info["path_id"])
                if not path:
                    path_doc = {
                        "path_id": path_info["path_id"],
                        "name": path_info["name"],
                        "description": path_info["description"],
                        "career_track": track.value if isinstance(track, CareerTrack) else track,
                        "difficulty_level": path_info["difficulty"].value
                        if isinstance(path_info["difficulty"], ExperienceLevel)
                        else path_info["difficulty"],
                        "estimated_duration": path_info["duration"],
                        "prerequisites": [],
                        "skills_earned": track_info["core_skills"],
                        "completion_badge": None,
                        "is_active": True,
                        "created_at": datetime.utcnow(),
                    }
                    insert_result = await db.learning_paths.insert_one(path_doc)
                    path_doc["_id"] = insert_result.inserted_id
                    path = path_doc

                for index, module_info in enumerate(path_info["modules"], start=1):
                    module = await self._get_module_by_id(db, module_info["module_id"])
                    if module:
                        continue

                    topic_titles = [topic["title"] for topic in module_info["topics"]]
                    assessment = self._build_module_assessment(module_info)
                    module_doc = {
                        "module_id": module_info["module_id"],
                        "path_id": path["path_id"],
                        "name": module_info["name"],
                        "description": module_info["description"],
                        "topics": topic_titles,
                        "order_index": index,
                        "estimated_time": module_info["estimated_time"],
                        "content": {
                            "topics": module_info["topics"],
                            "assessment": assessment,
                        },
                    }
                    await db.learning_modules.insert_one(module_doc)

    async def get_career_journey(self, db: AsyncIOMotorDatabase, request: CareerJourneyRequest) -> CareerJourneyResponse:
        if request.career_track == CareerTrack.CLOUD_ENGINEERING:
            provider = self._resolve_cloud_provider(request)
            cloud_blueprint = self._build_cloud_path_blueprint(provider, request.experience_level)
            timeline = cloud_blueprint.get("estimated_duration", "16 weeks")
            return CareerJourneyResponse(
                recommended_paths=[
                    LearningPathResponse(
                        path_id=cloud_blueprint["path_id"],
                        name=cloud_blueprint["name"],
                        description=cloud_blueprint["description"],
                        career_track=CareerTrack.CLOUD_ENGINEERING,
                        difficulty_level=request.experience_level,
                        estimated_duration=timeline,
                        prerequisites=cloud_blueprint.get("prerequisites", []),
                        skills_earned=cloud_blueprint.get("skills_earned", []),
                        completion_badge="Cloud Engineer Journey",
                        is_active=True,
                    )
                ],
                skill_roadmap=cloud_blueprint.get("skill_roadmap", {}),
                estimated_timeline=timeline,
                next_steps=cloud_blueprint.get("next_steps", []),
                selected_platform=provider,
            )

        track_info = self.career_paths.get(request.career_track)
        if not track_info:
            raise ValueError(f"Invalid career track: {request.career_track}")

        await self.ensure_paths_initialized(db)

        recommended_paths = []
        for path_info in track_info["paths"]:
            if self._matches_experience(path_info["difficulty"], request.experience_level):
                path = await self._get_path_by_id(db, path_info["path_id"])
                if path:
                    recommended_paths.append(self._path_response(path))

        if not recommended_paths:
            for path_info in track_info["paths"]:
                path = await self._get_path_by_id(db, path_info["path_id"])
                if path:
                    recommended_paths.append(self._path_response(path))

        skill_roadmap = {
            "Foundation": ["Cloud Basics", "Linux Fundamentals", "Networking"],
            "Intermediate": track_info["core_skills"][:3],
            "Advanced": track_info["core_skills"][3:] + ["Leadership", "Architecture Design"]
        }

        total_weeks = sum(int(path["duration"].split()[0]) for path in track_info["paths"])
        estimated_timeline = f"{total_weeks} weeks to completion"

        next_steps = [
            f"Start with {track_info['paths'][0]['name']}",
            "Set up a learning schedule",
            "Join relevant communities",
            "Practice with hands-on labs"
        ]

        return CareerJourneyResponse(
            recommended_paths=recommended_paths,
            skill_roadmap=skill_roadmap,
            estimated_timeline=estimated_timeline,
            next_steps=next_steps,
            selected_platform=None,
        )

    async def get_journey_plan(
        self,
        db: AsyncIOMotorDatabase,
        request: CareerJourneyRequest,
        user_id: Optional[str] = None
    ) -> JourneyPlanResponse:
        if request.career_track == CareerTrack.CLOUD_ENGINEERING:
            return await self._get_cloud_journey_plan(db, request, user_id)

        await self.ensure_paths_initialized(db)

        path_info = self._select_path_info(request.career_track, request.experience_level)
        if not path_info:
            raise ValueError("No learning path available for selected track")

        path = await self._get_path_by_id(db, path_info["path_id"])
        if not path:
            raise ValueError("Learning path not found")

        modules = await self._get_modules_for_path(db, path["path_id"])
        module_details = [self._map_module_detail(module) for module in modules]

        topic_progress = []
        module_progress = []
        module_assessment_progress = []
        overall_progress = 0.0

        if user_id:
            topic_progress = await self._get_topic_progress(db, user_id, [m["module_id"] for m in modules])
            module_progress = await self._get_module_progress_summaries(db, user_id, modules, topic_progress)
            module_assessment_progress = await self._get_module_assessment_progress(db, user_id, [m["module_id"] for m in modules])
            overall_progress = await self._get_overall_progress(db, user_id, path["path_id"], module_progress)

        return JourneyPlanResponse(
            path=JourneyPathDetail(
                path_id=path["path_id"],
                name=path["name"],
                description=path["description"],
                career_track=path["career_track"],
                difficulty_level=path["difficulty_level"],
                selected_platform=path.get("selected_platform"),
                estimated_duration=path["estimated_duration"],
                skills_earned=path["skills_earned"],
            ),
            modules=module_details,
            topic_progress=topic_progress,
            module_progress=module_progress,
            module_assessment_progress=module_assessment_progress,
            overall_progress=overall_progress
        )

    async def get_learning_paths(self, db: AsyncIOMotorDatabase, career_track: Optional[CareerTrack] = None) -> List[LearningPathResponse]:
        await self.ensure_paths_initialized(db)
        query = {"is_active": True}
        if career_track:
            query["career_track"] = career_track.value if isinstance(career_track, CareerTrack) else career_track

        cursor = db.learning_paths.find(query)
        paths = await cursor.to_list(length=None)
        return [self._path_response(path) for path in paths]

    async def start_learning_path(self, db: AsyncIOMotorDatabase, user_id: str, path_id: str) -> UserProgressResponse:
        existing_progress = await self._get_user_progress(db, user_id, path_id)
        if existing_progress and not existing_progress.get("is_completed", False):
            return self._progress_response(existing_progress)

        first_module = await self._get_first_module_for_path(db, path_id)

        progress_doc = {
            "user_id": user_id,
            "path_id": path_id,
            "current_module_id": first_module.get("module_id") if first_module else None,
            "completed_modules": [],
            "overall_progress": 0.0,
            "started_at": datetime.utcnow(),
            "last_accessed": datetime.utcnow(),
            "estimated_completion": None,
            "is_completed": False,
            "completion_date": None,
        }

        result = await db.user_progress.insert_one(progress_doc)
        progress_doc["_id"] = result.inserted_id

        return self._progress_response(progress_doc)

    async def update_module_progress(self, db: AsyncIOMotorDatabase, user_id: str, update_data: ProgressUpdate) -> Dict:
        module_progress = await self._get_module_progress(db, user_id, update_data.module_id)
        if not module_progress:
            module_progress = {
                "user_id": user_id,
                "module_id": update_data.module_id,
                "progress_percentage": 0.0,
                "questions_attempted": 0,
                "questions_correct": 0,
                "average_score": 0.0,
                "time_spent_minutes": 0,
                "last_accessed": datetime.utcnow(),
                "is_completed": False,
                "completion_date": None,
            }

        if update_data.progress_percentage is not None:
            module_progress["progress_percentage"] = update_data.progress_percentage
        if update_data.time_spent_minutes is not None:
            module_progress["time_spent_minutes"] = module_progress.get("time_spent_minutes", 0) + update_data.time_spent_minutes
        if update_data.questions_attempted is not None:
            module_progress["questions_attempted"] = module_progress.get("questions_attempted", 0) + update_data.questions_attempted
        if update_data.questions_correct is not None:
            module_progress["questions_correct"] = module_progress.get("questions_correct", 0) + update_data.questions_correct

        module_progress["last_accessed"] = datetime.utcnow()

        attempted = module_progress.get("questions_attempted", 0)
        if attempted > 0:
            module_progress["average_score"] = (
                module_progress.get("questions_correct", 0) / attempted
            ) * 100

        if module_progress.get("progress_percentage", 0) >= 100:
            module_progress["is_completed"] = True
            module_progress["completion_date"] = datetime.utcnow()

        if module_progress.get("_id"):
            await db.module_progress.replace_one({"_id": module_progress["_id"]}, module_progress)
        else:
            result = await db.module_progress.insert_one(module_progress)
            module_progress["_id"] = result.inserted_id

        await self._update_path_progress(db, user_id, update_data.module_id)

        return {
            "module_progress": module_progress.get("progress_percentage", 0.0),
            "is_completed": module_progress.get("is_completed", False),
            "average_score": module_progress.get("average_score", 0.0),
        }

    async def update_topic_progress(
        self,
        db: AsyncIOMotorDatabase,
        user_id: str,
        update_data: TopicProgressUpdate
    ) -> TopicProgressResponse:
        module = await self._get_module_by_id(db, update_data.module_id)
        if not module:
            raise ValueError("Module not found")

        topic = self._find_topic(module, update_data.topic_id)
        if not topic:
            raise ValueError("Topic not found")

        progress = await self._get_topic_progress_record(db, user_id, update_data.module_id, update_data.topic_id)
        if not progress:
            progress = {
                "user_id": user_id,
                "module_id": update_data.module_id,
                "topic_id": update_data.topic_id,
                "scenario_completed": False,
                "mcq_correct": False,
                "mcq_attempts": 0,
                "is_completed": False,
                "started_at": datetime.utcnow(),
                "completed_at": None,
                "time_spent_minutes": 0,
                "last_updated": datetime.utcnow(),
            }

        if not progress.get("started_at"):
            progress["started_at"] = datetime.utcnow()

        if update_data.time_spent_minutes is not None:
            progress["time_spent_minutes"] = progress.get("time_spent_minutes", 0) + update_data.time_spent_minutes

        if update_data.scenario_completed is not None:
            progress["scenario_completed"] = update_data.scenario_completed

        if update_data.mcq_answer is not None:
            progress["mcq_attempts"] = progress.get("mcq_attempts", 0) + 1
            correct_option = topic.get("mcq", {}).get("correct_option")
            progress["mcq_correct"] = update_data.mcq_answer == correct_option

        progress["is_completed"] = bool(progress.get("scenario_completed") and progress.get("mcq_correct"))
        if progress["is_completed"] and not progress.get("completed_at"):
            progress["completed_at"] = datetime.utcnow()
        progress["last_updated"] = datetime.utcnow()

        if progress.get("_id"):
            await db.topic_progress.replace_one({"_id": progress["_id"]}, progress)
        else:
            result = await db.topic_progress.insert_one(progress)
            progress["_id"] = result.inserted_id

        await self._update_module_progress_from_topics(db, user_id, module)
        await self._update_path_progress(db, user_id, update_data.module_id)

        return TopicProgressResponse(
            module_id=progress.get("module_id"),
            topic_id=progress.get("topic_id"),
            scenario_completed=progress.get("scenario_completed", False),
            mcq_correct=progress.get("mcq_correct", False),
            mcq_attempts=progress.get("mcq_attempts", 0),
            is_completed=progress.get("is_completed", False),
            started_at=progress.get("started_at"),
            completed_at=progress.get("completed_at"),
            time_spent_minutes=progress.get("time_spent_minutes", 0),
            last_updated=progress.get("last_updated"),
        )

    async def update_module_assessment(
        self,
        db: AsyncIOMotorDatabase,
        user_id: str,
        update_data: ModuleAssessmentUpdate
    ) -> ModuleAssessmentProgressResponse:
        module = await self._get_module_by_id(db, update_data.module_id)
        if not module:
            raise ValueError("Module not found")

        assessment = (module.get("content") or {}).get("assessment")
        if not assessment:
            raise ValueError("Module assessment not found")

        progress = await self._get_module_assessment_record(db, user_id, update_data.module_id)
        if not progress:
            progress = {
                "user_id": user_id,
                "module_id": update_data.module_id,
                "scenario_completed": False,
                "mcq_attempts": 0,
                "mcq_correct": 0,
                "answer_map": {},
                "is_completed": False,
                "last_updated": datetime.utcnow(),
            }

        if update_data.scenario_completed is not None:
            progress["scenario_completed"] = update_data.scenario_completed

        if update_data.mcq_index is not None and update_data.mcq_answer is not None:
            mcqs = assessment.get("mcqs", [])
            if update_data.mcq_index < 0 or update_data.mcq_index >= len(mcqs):
                raise ValueError("Invalid MCQ index")

            answer_key = str(update_data.mcq_index)
            answer_map = progress.get("answer_map") or {}
            if answer_key not in answer_map:
                progress["mcq_attempts"] = progress.get("mcq_attempts", 0) + 1
            answer_map[answer_key] = update_data.mcq_answer
            progress["answer_map"] = answer_map

            correct_option = mcqs[update_data.mcq_index].get("correct_option")
            if update_data.mcq_answer == correct_option:
                progress["mcq_correct"] = len([
                    value
                    for key, value in answer_map.items()
                    if key.isdigit()
                    and int(key) < len(mcqs)
                    and value == mcqs[int(key)].get("correct_option")
                ])

        total_mcqs = len(assessment.get("mcqs", []))
        required_correct = max(1, int(total_mcqs * 0.7)) if total_mcqs else 0
        progress["is_completed"] = bool(
            progress.get("scenario_completed") and progress.get("mcq_correct", 0) >= required_correct
        )
        progress["last_updated"] = datetime.utcnow()

        if progress.get("_id"):
            await db.module_assessment_progress.replace_one({"_id": progress["_id"]}, progress)
        else:
            result = await db.module_assessment_progress.insert_one(progress)
            progress["_id"] = result.inserted_id

        return ModuleAssessmentProgressResponse(
            module_id=progress.get("module_id"),
            scenario_completed=progress.get("scenario_completed", False),
            mcq_attempts=progress.get("mcq_attempts", 0),
            mcq_correct=progress.get("mcq_correct", 0),
            is_completed=progress.get("is_completed", False),
            last_updated=progress.get("last_updated"),
        )

    async def reset_module_assessment(
        self,
        db: AsyncIOMotorDatabase,
        user_id: str,
        reset_data: ModuleAssessmentReset
    ) -> ModuleAssessmentProgressResponse:
        progress = await self._get_module_assessment_record(db, user_id, reset_data.module_id)
        if not progress:
            progress = {
                "user_id": user_id,
                "module_id": reset_data.module_id,
                "answer_map": {},
                "last_updated": datetime.utcnow(),
            }

        progress["scenario_completed"] = False
        progress["mcq_attempts"] = 0
        progress["mcq_correct"] = 0
        progress["answer_map"] = {}
        progress["is_completed"] = False
        progress["last_updated"] = datetime.utcnow()

        if progress.get("_id"):
            await db.module_assessment_progress.replace_one({"_id": progress["_id"]}, progress)
        else:
            result = await db.module_assessment_progress.insert_one(progress)
            progress["_id"] = result.inserted_id

        return ModuleAssessmentProgressResponse(
            module_id=progress.get("module_id"),
            scenario_completed=progress.get("scenario_completed", False),
            mcq_attempts=progress.get("mcq_attempts", 0),
            mcq_correct=progress.get("mcq_correct", 0),
            is_completed=progress.get("is_completed", False),
            last_updated=progress.get("last_updated"),
        )

    async def get_user_progress(self, db: AsyncIOMotorDatabase, user_id: str) -> List[UserProgressResponse]:
        cursor = db.user_progress.find({"user_id": user_id})
        progress_records = await cursor.to_list(length=None)
        return [self._progress_response(progress) for progress in progress_records]

    def _resolve_cloud_provider(self, request: CareerJourneyRequest) -> CloudPlatform:
        if request.cloud_provider:
            return request.cloud_provider
        if request.preferred_platforms:
            first = str(request.preferred_platforms[0]).strip().lower()
            if first in {"aws", "azure", "gcp"}:
                return CloudPlatform(first)
        return CloudPlatform.AWS

    def _platform_label(self, platform: CloudPlatform) -> str:
        return {
            CloudPlatform.AWS: "AWS",
            CloudPlatform.AZURE: "Azure",
            CloudPlatform.GCP: "Google Cloud",
        }.get(platform, "Cloud")

    def _build_cloud_path_blueprint(self, platform: CloudPlatform, level: ExperienceLevel) -> Dict:
        platform_label = self._platform_label(platform)
        week_map = {
            ExperienceLevel.JUNIOR: 24,
            ExperienceLevel.MID: 18,
            ExperienceLevel.SENIOR: 14,
            ExperienceLevel.EXPERT: 12,
        }
        duration_weeks = week_map.get(level, 18)
        base = f"cloud-engineer-{platform.value}-{level.value}"

        modules = self._cloud_modules_blueprint(platform, level)
        foundation_skills = [
            f"{platform_label} core services",
            "Networking and identity",
            "Security and governance",
            "Infrastructure as Code",
            "Operations and reliability",
        ]

        return {
            "path_id": f"{base}-path",
            "name": f"{platform_label} Cloud Engineer Roadmap",
            "description": f"Structured {platform_label}-first plan from fundamentals to production operations.",
            "estimated_duration": f"{duration_weeks} weeks",
            "prerequisites": ["Basic Linux/terminal skills", "Basic networking concepts"],
            "skills_earned": foundation_skills,
            "skill_roadmap": {
                "Phase 1 (Foundation)": ["Core cloud concepts", "Identity and access basics", "Virtual networking"],
                "Phase 2 (Build)": ["Compute and storage design", "Databases and app hosting", "IaC workflows"],
                "Phase 3 (Operate)": ["Monitoring and incident handling", "Security hardening", "Cost and reliability"],
            },
            "next_steps": [
                f"Start Module 1 in the {platform_label} roadmap",
                "Commit 5-7 focused study hours weekly",
                "Complete each module lab before moving forward",
                "Run one capstone deployment at the end",
            ],
            "modules": modules,
        }

    def _cloud_modules_blueprint(self, platform: CloudPlatform, level: ExperienceLevel) -> List[Dict]:
        docs = {
            CloudPlatform.AWS: {
                "networking": "https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html",
                "iam": "https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html",
                "ec2": "https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/concepts.html",
                "s3": "https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html",
                "rds": "https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Welcome.html",
                "iac": "https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/Welcome.html",
                "monitoring": "https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/WhatIsCloudWatch.html",
                "well_arch": "https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html",
            },
            CloudPlatform.AZURE: {
                "networking": "https://learn.microsoft.com/azure/virtual-network/virtual-networks-overview",
                "iam": "https://learn.microsoft.com/azure/active-directory/fundamentals/active-directory-whatis",
                "ec2": "https://learn.microsoft.com/azure/virtual-machines/overview",
                "s3": "https://learn.microsoft.com/azure/storage/common/storage-introduction",
                "rds": "https://learn.microsoft.com/azure/azure-sql/database/sql-database-paas-overview",
                "iac": "https://learn.microsoft.com/azure/azure-resource-manager/templates/overview",
                "monitoring": "https://learn.microsoft.com/azure/azure-monitor/overview",
                "well_arch": "https://learn.microsoft.com/azure/well-architected/",
            },
            CloudPlatform.GCP: {
                "networking": "https://cloud.google.com/vpc/docs/overview",
                "iam": "https://cloud.google.com/iam/docs/overview",
                "ec2": "https://cloud.google.com/compute/docs/instances",
                "s3": "https://cloud.google.com/storage/docs/introduction",
                "rds": "https://cloud.google.com/sql/docs/mysql/introduction",
                "iac": "https://cloud.google.com/deployment-manager/docs",
                "monitoring": "https://cloud.google.com/monitoring/docs/monitoring-overview",
                "well_arch": "https://cloud.google.com/architecture/framework",
            },
        }[platform]

        module_weeks = "4 weeks" if level == ExperienceLevel.JUNIOR else "3 weeks"
        prefix = f"{platform.value}-{level.value}"
        return [
            {
                "module_id": f"{prefix}-foundations",
                "name": "Cloud Foundations",
                "description": "Cloud principles, shared responsibility, and core services.",
                "estimated_time": module_weeks,
                "topics": [
                    {"topic_id": "core-models", "title": "Cloud service models", "source_urls": [docs["well_arch"]]},
                    {"topic_id": "identity-basics", "title": "Identity and access basics", "source_urls": [docs["iam"]]},
                ],
            },
            {
                "module_id": f"{prefix}-networking",
                "name": "Networking and Connectivity",
                "description": "Virtual networking, segmentation, and secure connectivity.",
                "estimated_time": module_weeks,
                "topics": [
                    {"topic_id": "vpc-design", "title": "Virtual network design", "source_urls": [docs["networking"]]},
                    {"topic_id": "secure-connectivity", "title": "Secure connectivity patterns", "source_urls": [docs["networking"], docs["iam"]]},
                ],
            },
            {
                "module_id": f"{prefix}-compute-storage",
                "name": "Compute and Storage",
                "description": "Compute options, storage classes, and workload placement.",
                "estimated_time": module_weeks,
                "topics": [
                    {"topic_id": "compute-basics", "title": "Compute service selection", "source_urls": [docs["ec2"]]},
                    {"topic_id": "storage-lifecycle", "title": "Object storage lifecycle and access", "source_urls": [docs["s3"]]},
                ],
            },
            {
                "module_id": f"{prefix}-data-platform",
                "name": "Data and Application Platform",
                "description": "Managed databases and app service integration patterns.",
                "estimated_time": module_weeks,
                "topics": [
                    {"topic_id": "managed-databases", "title": "Managed relational databases", "source_urls": [docs["rds"]]},
                    {"topic_id": "resilience-patterns", "title": "Resilience and backup patterns", "source_urls": [docs["rds"], docs["s3"]]},
                ],
            },
            {
                "module_id": f"{prefix}-iac-automation",
                "name": "Infrastructure as Code and Automation",
                "description": "Template-driven provisioning and repeatable delivery workflows.",
                "estimated_time": module_weeks,
                "topics": [
                    {"topic_id": "iac-fundamentals", "title": "IaC fundamentals", "source_urls": [docs["iac"]]},
                    {"topic_id": "change-safety", "title": "Change management and safe rollout", "source_urls": [docs["iac"], docs["well_arch"]]},
                ],
            },
            {
                "module_id": f"{prefix}-operations",
                "name": "Operations, Reliability, and Cost",
                "description": "Monitoring, incident response, and cost/reliability optimization.",
                "estimated_time": module_weeks,
                "topics": [
                    {"topic_id": "observability", "title": "Monitoring and observability", "source_urls": [docs["monitoring"]]},
                    {"topic_id": "reliability-cost", "title": "Reliability and cost optimization", "source_urls": [docs["well_arch"], docs["monitoring"]]},
                ],
            },
        ]

    async def _get_cloud_journey_plan(
        self,
        db: AsyncIOMotorDatabase,
        request: CareerJourneyRequest,
        user_id: Optional[str] = None,
    ) -> JourneyPlanResponse:
        provider = self._resolve_cloud_provider(request)
        blueprint = self._build_cloud_path_blueprint(provider, request.experience_level)

        await self._upsert_cloud_path(db, blueprint, request.experience_level, provider)
        for order_index, module in enumerate(blueprint["modules"], start=1):
            existing_module = await self._get_module_by_id(db, module["module_id"])
            if existing_module and not self._is_module_refresh_due(existing_module):
                continue

            cached_content = await self._get_cached_cloud_module_content(
                db,
                provider,
                request.experience_level,
                module["module_id"],
            )

            if cached_content and not self._is_cache_refresh_due(cached_content):
                topic_content = cached_content.get("topics", [])
                assessment = cached_content.get("assessment") or self._build_module_assessment({"name": module["name"], "topics": topic_content})
            else:
                topic_content = await self._generate_module_topics_from_docs(provider, request.experience_level, module)
                assessment = self._build_module_assessment({"name": module["name"], "topics": topic_content})
                await self._upsert_cloud_content_cache(
                    db,
                    provider,
                    request.experience_level,
                    module,
                    topic_content,
                    assessment,
                )

            await self._upsert_cloud_module(
                db,
                path_id=blueprint["path_id"],
                module_info=module,
                order_index=order_index,
                topics=topic_content,
                assessment=assessment,
            )

        path = await self._get_path_by_id(db, blueprint["path_id"])
        modules = await self._get_modules_for_path(db, blueprint["path_id"])
        module_details = [self._map_module_detail(module) for module in modules]

        topic_progress = []
        module_progress = []
        module_assessment_progress = []
        overall_progress = 0.0

        if user_id:
            topic_progress = await self._get_topic_progress(db, user_id, [m["module_id"] for m in modules])
            module_progress = await self._get_module_progress_summaries(db, user_id, modules, topic_progress)
            module_assessment_progress = await self._get_module_assessment_progress(db, user_id, [m["module_id"] for m in modules])
            overall_progress = await self._get_overall_progress(db, user_id, path["path_id"], module_progress)

        return JourneyPlanResponse(
            path=JourneyPathDetail(
                path_id=path["path_id"],
                name=path["name"],
                description=path["description"],
                career_track=path["career_track"],
                difficulty_level=path["difficulty_level"],
                selected_platform=path.get("selected_platform"),
                estimated_duration=path["estimated_duration"],
                skills_earned=path["skills_earned"],
            ),
            modules=module_details,
            topic_progress=topic_progress,
            module_progress=module_progress,
            module_assessment_progress=module_assessment_progress,
            overall_progress=overall_progress,
        )

    async def sync_cloud_content_cache(
        self,
        db: AsyncIOMotorDatabase,
        cloud_provider: Optional[CloudPlatform] = None,
        experience_level: Optional[ExperienceLevel] = None,
        force_refresh: bool = False,
    ) -> Dict:
        providers = [cloud_provider] if cloud_provider else [CloudPlatform.AWS, CloudPlatform.AZURE, CloudPlatform.GCP]
        levels = [experience_level] if experience_level else [
            ExperienceLevel.JUNIOR,
            ExperienceLevel.MID,
            ExperienceLevel.SENIOR,
            ExperienceLevel.EXPERT,
        ]

        synced_modules = 0
        reused_modules = 0
        failed_modules = 0
        errors: List[str] = []

        for provider in providers:
            for level in levels:
                blueprint = self._build_cloud_path_blueprint(provider, level)
                await self._upsert_cloud_path(db, blueprint, level, provider)

                for module in blueprint.get("modules", []):
                    try:
                        cached_content = await self._get_cached_cloud_module_content(
                            db,
                            provider,
                            level,
                            module.get("module_id"),
                        )

                        if cached_content and not force_refresh and not self._is_cache_refresh_due(cached_content):
                            reused_modules += 1
                            continue

                        topic_content = await self._generate_module_topics_from_docs(provider, level, module)
                        assessment = self._build_module_assessment({"name": module.get("name"), "topics": topic_content})
                        await self._upsert_cloud_content_cache(
                            db,
                            provider,
                            level,
                            module,
                            topic_content,
                            assessment,
                        )
                        synced_modules += 1
                    except Exception as exc:
                        failed_modules += 1
                        errors.append(f"{provider.value}/{level.value}/{module.get('module_id')}: {exc}")

        return {
            "synced_modules": synced_modules,
            "reused_modules": reused_modules,
            "failed_modules": failed_modules,
            "provider_scope": [provider.value for provider in providers],
            "level_scope": [level.value for level in levels],
            "errors": errors[:50],
        }

    async def start_cloud_content_sync_job(
        self,
        db: AsyncIOMotorDatabase,
        requested_by: str,
        cloud_provider: Optional[CloudPlatform] = None,
        experience_level: Optional[ExperienceLevel] = None,
        force_refresh: bool = False,
    ) -> Dict:
        now = datetime.utcnow()
        run_id = str(uuid.uuid4())
        provider_scope = [cloud_provider.value] if cloud_provider else [CloudPlatform.AWS.value, CloudPlatform.AZURE.value, CloudPlatform.GCP.value]
        level_scope = [experience_level.value] if experience_level else [
            ExperienceLevel.JUNIOR.value,
            ExperienceLevel.MID.value,
            ExperienceLevel.SENIOR.value,
            ExperienceLevel.EXPERT.value,
        ]

        await db.learning_content_sync_state.update_one(
            {"_id": self._sync_state_doc_id},
            {
                "$setOnInsert": {
                    "is_running": False,
                    "created_at": now,
                },
            },
            upsert=True,
        )

        acquire_result = await db.learning_content_sync_state.update_one(
            {
                "_id": self._sync_state_doc_id,
                "is_running": False,
            },
            {
                "$set": {
                    "is_running": True,
                    "run_id": run_id,
                    "requested_by": requested_by,
                    "provider_scope": provider_scope,
                    "level_scope": level_scope,
                    "force_refresh": force_refresh,
                    "started_at": now,
                    "updated_at": now,
                },
            },
        )

        if acquire_result.modified_count != 1:
            raise ValueError("A journey content sync is already running.")

        run_doc = {
            "run_id": run_id,
            "status": "running",
            "requested_by": requested_by,
            "provider_scope": provider_scope,
            "level_scope": level_scope,
            "force_refresh": force_refresh,
            "started_at": now,
            "updated_at": now,
            "synced_modules": 0,
            "reused_modules": 0,
            "failed_modules": 0,
            "errors": [],
        }
        await db.learning_content_sync_runs.insert_one(run_doc)

        asyncio.create_task(
            self._run_cloud_content_sync_job(
                db,
                run_id=run_id,
                cloud_provider=cloud_provider,
                experience_level=experience_level,
                force_refresh=force_refresh,
            )
        )

        return {
            "run_id": run_id,
            "status": "running",
            "provider_scope": provider_scope,
            "level_scope": level_scope,
            "force_refresh": force_refresh,
            "started_at": now,
        }

    async def _run_cloud_content_sync_job(
        self,
        db: AsyncIOMotorDatabase,
        run_id: str,
        cloud_provider: Optional[CloudPlatform],
        experience_level: Optional[ExperienceLevel],
        force_refresh: bool,
    ) -> None:
        started_at = datetime.utcnow()
        try:
            result = await self.sync_cloud_content_cache(
                db,
                cloud_provider=cloud_provider,
                experience_level=experience_level,
                force_refresh=force_refresh,
            )
            completed_at = datetime.utcnow()
            duration_seconds = round((completed_at - started_at).total_seconds(), 2)
            await db.learning_content_sync_runs.update_one(
                {"run_id": run_id},
                {
                    "$set": {
                        "status": "completed",
                        "completed_at": completed_at,
                        "duration_seconds": duration_seconds,
                        "synced_modules": result.get("synced_modules", 0),
                        "reused_modules": result.get("reused_modules", 0),
                        "failed_modules": result.get("failed_modules", 0),
                        "errors": result.get("errors", []),
                        "provider_scope": result.get("provider_scope", []),
                        "level_scope": result.get("level_scope", []),
                        "updated_at": completed_at,
                    }
                },
            )
            await db.learning_content_sync_state.update_one(
                {"_id": self._sync_state_doc_id},
                {
                    "$set": {
                        "is_running": False,
                        "updated_at": completed_at,
                        "last_run_id": run_id,
                        "last_status": "completed",
                        "last_completed_at": completed_at,
                        "last_duration_seconds": duration_seconds,
                    }
                },
            )
        except Exception as exc:
            completed_at = datetime.utcnow()
            duration_seconds = round((completed_at - started_at).total_seconds(), 2)
            await db.learning_content_sync_runs.update_one(
                {"run_id": run_id},
                {
                    "$set": {
                        "status": "failed",
                        "completed_at": completed_at,
                        "duration_seconds": duration_seconds,
                        "failed_modules": 1,
                        "errors": [str(exc)],
                        "updated_at": completed_at,
                    }
                },
            )
            await db.learning_content_sync_state.update_one(
                {"_id": self._sync_state_doc_id},
                {
                    "$set": {
                        "is_running": False,
                        "updated_at": completed_at,
                        "last_run_id": run_id,
                        "last_status": "failed",
                        "last_completed_at": completed_at,
                        "last_duration_seconds": duration_seconds,
                    }
                },
            )

    async def get_cloud_content_sync_status(self, db: AsyncIOMotorDatabase) -> Dict:
        state = await db.learning_content_sync_state.find_one({"_id": self._sync_state_doc_id})
        active_run_id = state.get("run_id") if state and state.get("is_running") else None

        run_doc = None
        if active_run_id:
            run_doc = await db.learning_content_sync_runs.find_one({"run_id": active_run_id})
        if not run_doc:
            run_doc = await db.learning_content_sync_runs.find_one(sort=[("started_at", -1)])

        if not run_doc:
            return {
                "run_id": None,
                "status": "idle",
                "is_running": False,
                "provider_scope": [],
                "level_scope": [],
                "force_refresh": False,
                "started_at": None,
                "completed_at": None,
                "duration_seconds": None,
                "synced_modules": 0,
                "reused_modules": 0,
                "failed_modules": 0,
                "errors": [],
            }

        is_running = bool(state.get("is_running")) if state else run_doc.get("status") == "running"
        return {
            "run_id": run_doc.get("run_id"),
            "status": run_doc.get("status", "idle"),
            "is_running": is_running,
            "provider_scope": run_doc.get("provider_scope", []),
            "level_scope": run_doc.get("level_scope", []),
            "force_refresh": bool(run_doc.get("force_refresh", False)),
            "started_at": run_doc.get("started_at"),
            "completed_at": run_doc.get("completed_at"),
            "duration_seconds": run_doc.get("duration_seconds"),
            "synced_modules": int(run_doc.get("synced_modules", 0)),
            "reused_modules": int(run_doc.get("reused_modules", 0)),
            "failed_modules": int(run_doc.get("failed_modules", 0)),
            "errors": run_doc.get("errors", []),
        }

    async def _upsert_cloud_path(
        self,
        db: AsyncIOMotorDatabase,
        blueprint: Dict,
        level: ExperienceLevel,
        platform: CloudPlatform,
    ) -> None:
        path_doc = {
            "path_id": blueprint["path_id"],
            "name": blueprint["name"],
            "description": blueprint["description"],
            "career_track": CareerTrack.CLOUD_ENGINEERING.value,
            "difficulty_level": level.value,
            "selected_platform": platform.value,
            "estimated_duration": blueprint["estimated_duration"],
            "prerequisites": blueprint.get("prerequisites", []),
            "skills_earned": blueprint.get("skills_earned", []),
            "completion_badge": "Cloud Engineer Journey",
            "is_active": True,
            "updated_at": datetime.utcnow(),
        }
        await db.learning_paths.update_one(
            {"path_id": blueprint["path_id"]},
            {"$set": path_doc, "$setOnInsert": {"created_at": datetime.utcnow()}},
            upsert=True,
        )

    async def _upsert_cloud_module(
        self,
        db: AsyncIOMotorDatabase,
        path_id: str,
        module_info: Dict,
        order_index: int,
        topics: List[Dict],
        assessment: Dict,
    ) -> None:
        module_doc = {
            "module_id": module_info["module_id"],
            "path_id": path_id,
            "name": module_info["name"],
            "description": module_info["description"],
            "topics": [topic.get("title") for topic in topics],
            "order_index": order_index,
            "estimated_time": module_info["estimated_time"],
            "content": {
                "topics": topics,
                "assessment": assessment,
            },
            "updated_at": datetime.utcnow(),
        }
        await db.learning_modules.update_one(
            {"module_id": module_info["module_id"]},
            {"$set": module_doc, "$setOnInsert": {"created_at": datetime.utcnow()}},
            upsert=True,
        )

    async def _get_cached_cloud_module_content(
        self,
        db: AsyncIOMotorDatabase,
        provider: CloudPlatform,
        level: ExperienceLevel,
        module_id: str,
    ) -> Optional[Dict]:
        cache_doc = await db.learning_content_cache.find_one(
            {
                "provider": provider.value,
                "experience_level": level.value,
                "module_id": module_id,
            }
        )
        if not cache_doc:
            return None

        if not self._is_cached_module_content_usable(cache_doc):
            return None
        return cache_doc

    async def _upsert_cloud_content_cache(
        self,
        db: AsyncIOMotorDatabase,
        provider: CloudPlatform,
        level: ExperienceLevel,
        module_info: Dict,
        topics: List[Dict],
        assessment: Dict,
    ) -> None:
        now = datetime.utcnow()
        cache_doc = {
            "provider": provider.value,
            "experience_level": level.value,
            "module_id": module_info.get("module_id"),
            "module_name": module_info.get("name"),
            "module_description": module_info.get("description"),
            "estimated_time": module_info.get("estimated_time"),
            "topics": topics,
            "assessment": assessment,
            "updated_at": now,
        }
        await db.learning_content_cache.update_one(
            {
                "provider": provider.value,
                "experience_level": level.value,
                "module_id": module_info.get("module_id"),
            },
            {"$set": cache_doc, "$setOnInsert": {"created_at": now}},
            upsert=True,
        )

    def _is_cached_module_content_usable(self, cache_doc: Dict) -> bool:
        topics = cache_doc.get("topics") if isinstance(cache_doc.get("topics"), list) else []
        if not topics:
            return False
        for topic in topics:
            if not isinstance(topic, dict):
                return False
            lesson_content = str(topic.get("lesson_content") or "").strip()
            if len(lesson_content) < 220:
                return False
            lower = lesson_content.lower()
            if any(token in lower for token in ["@context", "breadcrumblist", "itemlistelement", "documentation aws"]):
                return False
        return True

    def _is_cache_refresh_due(self, cache_doc: Dict) -> bool:
        if not self._is_cached_module_content_usable(cache_doc):
            return True
        updated_at = cache_doc.get("updated_at")
        if not isinstance(updated_at, datetime):
            return True
        return datetime.utcnow() - updated_at > timedelta(days=7)

    async def _generate_module_topics_from_docs(
        self,
        platform: CloudPlatform,
        level: ExperienceLevel,
        module_info: Dict,
    ) -> List[Dict]:
        source_payload = []
        for topic in module_info.get("topics", []):
            source_urls = topic.get("source_urls", [])[:2]
            snippets_raw = await asyncio.gather(*[self._fetch_doc_snippet(url) for url in source_urls])
            snippets = [snippet[:1100] for snippet in snippets_raw if snippet]
            source_payload.append(
                {
                    "topic_id": topic.get("topic_id"),
                    "title": topic.get("title"),
                    "source_urls": topic.get("source_urls", []),
                    "doc_excerpt": "\n".join(snippets)[:2000],
                }
            )

        source_payload_map = {
            str(item.get("topic_id")): item
            for item in source_payload
            if item.get("topic_id")
        }

        prompt = f"""You are a principal cloud engineer and beginner-friendly instructor.
Rewrite these official documentation excerpts into practical study topics.

Requirements:
- Platform: {self._platform_label(platform)}
- Learner level: {level.value}
- Module: {module_info.get('name')}
- Keep language simple and concrete for the learner level.
- All lesson material must be self-contained in-app. Do NOT instruct learner to leave the app or read elsewhere.
- Do NOT include raw HTML, JavaScript, JSON blobs, telemetry text, or documentation UI metadata.
- Return ONLY JSON array with topic objects using this exact shape:
[{{
  \"topic_id\": \"string\",
  \"title\": \"string\",
  \"teaching\": \"2-4 sentence explanation\",
    \"lesson_content\": \"Detailed beginner-friendly lesson (8-12 short paragraphs, minimum ~900 characters)\",
  \"key_points\": [\"point 1\", \"point 2\", \"point 3\"],
  \"steps\": [\"step 1\", \"step 2\", \"step 3\"],
  \"hands_on\": {{\"scenario\": \"...\", \"tasks\": [\"...\", \"...\", \"...\"], \"validation\": [\"...\", \"...\"]}},
  \"mcq\": {{\"question\": \"...\", \"options\": [\"...\", \"...\", \"...\", \"...\"], \"correct_option\": \"must match one option exactly\", \"explanation\": \"...\"}}
}}]

Source material:
{json.dumps(source_payload)}
"""

        generated_topics = []
        llm_output = await self._generate_with_groq(prompt)
        if llm_output:
            try:
                generated_topics = self._extract_json_array(llm_output)
            except Exception:
                generated_topics = []

        generated_map = {
            str(topic.get("topic_id")): topic
            for topic in generated_topics
            if isinstance(topic, dict) and topic.get("topic_id")
        }

        topics = []
        for fallback_topic in module_info.get("topics", []):
            topic_id = fallback_topic.get("topic_id")
            generated = generated_map.get(topic_id, {}) if isinstance(generated_map.get(topic_id, {}), dict) else {}

            generated_mcq = generated.get("mcq", {}) if isinstance(generated.get("mcq", {}), dict) else {}
            options = [str(opt).strip() for opt in (generated_mcq.get("options", []) or []) if str(opt).strip()]
            if len(options) < 4:
                options = [
                    "Use least privilege and validate access",
                    "Skip identity checks for speed",
                    "Use wildcard admin access by default",
                    "Disable logging in production",
                ]

            correct_option = generated_mcq.get("correct_option") or options[0]
            if correct_option not in options:
                correct_option = options[0]

            generated_hands_on = generated.get("hands_on", {}) if isinstance(generated.get("hands_on", {}), dict) else {}
            hands_on = self._sanitize_hands_on(fallback_topic, generated_hands_on)

            key_points = generated.get("key_points", [])
            if not isinstance(key_points, list):
                key_points = []
            key_points = [str(point).strip() for point in key_points if str(point).strip()][:5]
            if not key_points:
                key_points = [
                    "Start with core concepts",
                    "Apply one practical example",
                    "Validate and observe outcomes",
                ]

            steps = generated.get("steps", [])
            if not isinstance(steps, list):
                steps = []
            steps = [str(step).strip() for step in steps if str(step).strip()][:6]
            if not steps:
                steps = [
                    "Understand the concept and expected outcome",
                    "Implement a minimal lab",
                    "Verify results and document takeaways",
                ]

            lesson_content = str(generated.get("lesson_content") or "").strip()
            if not self._is_lesson_content_usable(lesson_content):
                source_entry = source_payload_map.get(str(topic_id), {})
                lesson_content = self._build_inline_lesson_content(
                    topic_title=fallback_topic.get("title", "Topic"),
                    doc_excerpt=str(source_entry.get("doc_excerpt") or ""),
                    platform_label=self._platform_label(platform),
                    level=level,
                )

            topics.append(
                {
                    "topic_id": topic_id,
                    "title": generated.get("title") or fallback_topic.get("title", "Topic"),
                    "teaching": generated.get("teaching") or f"Study {fallback_topic.get('title', 'this topic')} on {self._platform_label(platform)} with hands-on practice.",
                    "lesson_content": lesson_content,
                    "key_points": key_points,
                    "steps": steps,
                    "hands_on": hands_on,
                    "mcq": {
                        "question": generated_mcq.get("question") or f"Which action best supports {fallback_topic.get('title', 'this topic')}?",
                        "options": options[:4],
                        "correct_option": correct_option,
                        "explanation": generated_mcq.get("explanation") or "Choose the option aligned with platform security and reliability guidance.",
                    },
                    "source_urls": fallback_topic.get("source_urls", []),
                }
            )

        return topics

    async def _generate_with_groq(self, prompt: str) -> Optional[str]:
        try:
            groq_service = GroqService()
        except Exception:
            return None
        try:
            return await groq_service.generate_response(prompt=prompt, system_prompt=None, temperature=0.2)
        except Exception:
            return None

    async def _fetch_doc_snippet(self, url: str) -> str:
        if url in self.doc_cache:
            return self.doc_cache[url]
        try:
            async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                text = self._strip_html(response.text)
                snippet = text[:3000]
                self.doc_cache[url] = snippet
                return snippet
        except Exception:
            return ""

    def _sanitize_hands_on(self, fallback_topic: Dict, generated_hands_on: Dict) -> Dict:
        scenario = str(generated_hands_on.get("scenario") or "").strip()
        tasks = generated_hands_on.get("tasks") if isinstance(generated_hands_on.get("tasks"), list) else []
        validation = generated_hands_on.get("validation") if isinstance(generated_hands_on.get("validation"), list) else []

        cleaned_tasks = [str(task).strip() for task in tasks if str(task).strip()][:5]
        cleaned_validation = [str(item).strip() for item in validation if str(item).strip()][:4]

        if not scenario:
            scenario = f"You are implementing {fallback_topic.get('title', 'this capability')} for a small production workload."
        if not cleaned_tasks:
            cleaned_tasks = [
                "Define the goal and expected outcome",
                "Implement the baseline configuration",
                "Validate security, reliability, and cost impact",
            ]
        if not cleaned_validation:
            cleaned_validation = [
                "Outcome is measurable",
                "Configuration follows platform best practices",
            ]

        return {
            "scenario": scenario,
            "tasks": cleaned_tasks,
            "validation": cleaned_validation,
        }

    def _build_inline_lesson_content(
        self,
        topic_title: str,
        doc_excerpt: str,
        platform_label: str,
        level: ExperienceLevel,
    ) -> str:
        cleaned_excerpt = self._clean_doc_excerpt(doc_excerpt or "")
        sentences = re.split(r"(?<=[.!?])\s+", cleaned_excerpt)
        useful_sentences = [
            s.strip()
            for s in sentences
            if self._is_clean_sentence(s)
        ][:12]

        excerpt_summary = " ".join(useful_sentences[:4]) if useful_sentences else ""
        excerpt_details = " ".join(useful_sentences[4:8]) if len(useful_sentences) > 4 else ""

        level_guidance = {
            ExperienceLevel.JUNIOR: "Focus on first principles and safe defaults before optimization.",
            ExperienceLevel.MID: "Connect service behavior to architecture decisions and operational trade-offs.",
            ExperienceLevel.SENIOR: "Evaluate design trade-offs, reliability patterns, and governance implications.",
            ExperienceLevel.EXPERT: "Critique platform patterns deeply and optimize across scale, cost, and risk.",
        }.get(level, "Build practical understanding and apply disciplined operational patterns.")

        sections = [
            f"Overview\n{topic_title} in {platform_label} is a foundational cloud engineering capability. {level_guidance}",
            f"Core Concept\n{excerpt_summary or f'This topic explains what {topic_title} does, its responsibility boundaries, and how it fits into production workloads.'}",
            "How It Works\nStart by identifying the main components, how they connect, and which parts you control versus what the platform manages for you. Then map request flow, authentication path, and failure behavior.",
            f"Architecture Context\n{excerpt_details or f'Use {topic_title} with adjacent identity, networking, monitoring, and data services. Always define boundaries clearly to avoid hidden coupling and brittle designs.'}",
            "Security and Reliability\nApply least privilege, encrypted transport, and auditable access by default. Define rollback strategy, alerting thresholds, and simple recovery runbooks before broad rollout.",
            "Cost and Operations\nTrack the main cost drivers early, set baseline usage expectations, and verify observability dashboards. Prefer predictable configurations first, then optimize based on measured traffic and incidents.",
            "Implementation Walkthrough\nCreate a minimal working setup, validate access and network controls, run a small realistic workload, and capture expected outputs. Expand only after tests pass and rollback is validated.",
            "Common Mistakes\nTeams often over-permission identities, skip monitoring setup, and scale before validating behavior under failure. Avoid these by using staged environments and explicit acceptance checks.",
            "Interview Readiness\nBe ready to explain why this service fits a scenario, what constraints it introduces, and what alternatives you considered. Strong answers include trade-offs across security, reliability, and cost.",
        ]

        lesson = "\n\n".join(sections)
        if len(lesson) < 900:
            lesson += "\n\nPractice Goal\nAfter studying this lesson, you should be able to design a minimal production-safe implementation, explain key trade-offs, and troubleshoot common issues without leaving the app."

        return lesson

    def _is_lesson_content_usable(self, content: str) -> bool:
        if not content or len(content.strip()) < 700:
            return False
        lowered = content.lower()
        noise_tokens = [
            "assignmentcontext",
            "variantnames",
            "vardataversion",
            "var msdocs",
            "pagetemplate",
            "{\"source\"",
            "source\":\"live\"",
            "microsoft learn {",
            "@context",
            "breadcrumblist",
            "itemlistelement",
            "documentation aws",
            "aws well-architected framework - aws well-architected framework",
        ]
        return not any(token in lowered for token in noise_tokens)

    def _clean_doc_excerpt(self, text: str) -> str:
        cleaned = text
        cleaned = re.sub(r"\{\s*\"@context\"[\s\S]*?\}\s*", " ", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\b(itemListElement|BreadcrumbList|Documentation AWS Well-Architected Framework)\b", " ", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"(AWS Well-Architected Framework\s*-\s*){2,}", "AWS Well-Architected Framework ", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\{[^\n]{20,}\}", " ", cleaned)
        cleaned = re.sub(r"\b(var|let|const)\s+[a-zA-Z0-9_]+\s*=\s*\{[\s\S]*?\}", " ", cleaned)
        cleaned = re.sub(r"https?://\S+", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip()

    def _is_clean_sentence(self, sentence: str) -> bool:
        s = (sentence or "").strip()
        if len(s) < 45:
            return False
        lower = s.lower()
        blocked = [
            "assignmentcontext",
            "variantnames",
            "msdocs",
            "pagetemplate",
            "source\":\"live\"",
            "data version",
            "microsoft learn {",
            "@context",
            "breadcrumblist",
            "itemlistelement",
            "documentation aws",
        ]
        if any(token in lower for token in blocked):
            return False
        if s.count("{") + s.count("}") > 1:
            return False
        return True

    def _is_module_refresh_due(self, module_doc: Dict) -> bool:
        content_topics = ((module_doc.get("content") or {}).get("topics") or [])
        if not content_topics:
            return True

        has_rich_lessons = all(
            bool(str(topic.get("lesson_content") or "").strip()) and len(str(topic.get("lesson_content") or "").strip()) >= 220
            for topic in content_topics
            if isinstance(topic, dict)
        )
        if not has_rich_lessons:
            return True

        updated_at = module_doc.get("updated_at")
        if not isinstance(updated_at, datetime):
            return True
        return datetime.utcnow() - updated_at > timedelta(hours=24)

    def _strip_html(self, html_content: str) -> str:
        text = re.sub(r"<script[\s\S]*?</script>", " ", html_content, flags=re.IGNORECASE)
        text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _extract_json_array(self, raw: str) -> List[Dict]:
        content = raw
        if "```json" in content:
            content = content.split("```json", 1)[1].split("```", 1)[0]
        elif "```" in content:
            content = content.split("```", 1)[1].split("```", 1)[0]

        match = re.search(r"\[[\s\S]*\]", content)
        if match:
            content = match.group(0)
        parsed = json.loads(content)
        return parsed if isinstance(parsed, list) else []

    def _matches_experience(self, path_level: ExperienceLevel, user_level: ExperienceLevel) -> bool:
        if user_level == ExperienceLevel.JUNIOR:
            return path_level == ExperienceLevel.JUNIOR
        if user_level == ExperienceLevel.MID:
            return path_level in [ExperienceLevel.MID, ExperienceLevel.JUNIOR]
        return path_level in [ExperienceLevel.MID, ExperienceLevel.SENIOR]

    def _select_path_info(self, track: CareerTrack, level: ExperienceLevel) -> Optional[Dict]:
        track_info = self.career_paths.get(track)
        if not track_info:
            return None

        for path_info in track_info["paths"]:
            if self._matches_experience(path_info["difficulty"], level):
                return path_info

        return track_info["paths"][0] if track_info["paths"] else None

    async def _get_path_by_id(self, db: AsyncIOMotorDatabase, path_id: str) -> Optional[Dict]:
        return await db.learning_paths.find_one({"path_id": path_id})

    async def _get_module_by_id(self, db: AsyncIOMotorDatabase, module_id: str) -> Optional[Dict]:
        return await db.learning_modules.find_one({"module_id": module_id})

    async def _get_modules_for_path(self, db: AsyncIOMotorDatabase, path_id: str) -> List[Dict]:
        cursor = db.learning_modules.find({"path_id": path_id}).sort("order_index", 1)
        return await cursor.to_list(length=None)

    async def _get_first_module_for_path(self, db: AsyncIOMotorDatabase, path_id: str) -> Optional[Dict]:
        return await db.learning_modules.find_one({"path_id": path_id}, sort=[("order_index", 1)])

    async def _get_user_progress(self, db: AsyncIOMotorDatabase, user_id: str, path_id: str) -> Optional[Dict]:
        return await db.user_progress.find_one({"user_id": user_id, "path_id": path_id})

    async def _get_module_progress(self, db: AsyncIOMotorDatabase, user_id: str, module_id: str) -> Optional[Dict]:
        return await db.module_progress.find_one({"user_id": user_id, "module_id": module_id})

    async def _get_module_assessment_record(
        self,
        db: AsyncIOMotorDatabase,
        user_id: str,
        module_id: str,
    ) -> Optional[Dict]:
        return await db.module_assessment_progress.find_one({"user_id": user_id, "module_id": module_id})

    async def _get_topic_progress_record(
        self,
        db: AsyncIOMotorDatabase,
        user_id: str,
        module_id: str,
        topic_id: str,
    ) -> Optional[Dict]:
        return await db.topic_progress.find_one(
            {"user_id": user_id, "module_id": module_id, "topic_id": topic_id}
        )

    async def _get_topic_progress(
        self,
        db: AsyncIOMotorDatabase,
        user_id: str,
        module_ids: List[str],
    ) -> List[TopicProgressResponse]:
        if not module_ids:
            return []

        cursor = db.topic_progress.find(
            {"user_id": user_id, "module_id": {"$in": module_ids}}
        )
        progress_records = await cursor.to_list(length=None)
        return [
            TopicProgressResponse(
                module_id=record.get("module_id"),
                topic_id=record.get("topic_id"),
                scenario_completed=record.get("scenario_completed", False),
                mcq_correct=record.get("mcq_correct", False),
                mcq_attempts=record.get("mcq_attempts", 0),
                is_completed=record.get("is_completed", False),
                started_at=record.get("started_at"),
                completed_at=record.get("completed_at"),
                time_spent_minutes=record.get("time_spent_minutes", 0),
                last_updated=record.get("last_updated"),
            )
            for record in progress_records
        ]

    async def _get_module_progress_summaries(
        self,
        db: AsyncIOMotorDatabase,
        user_id: str,
        modules: List[Dict],
        topic_progress: List[TopicProgressResponse]
    ) -> List[ModuleProgressSummary]:
        progress_map = {(item.module_id, item.topic_id): item for item in topic_progress}
        module_ids = [module.get("module_id") for module in modules]
        module_records = await db.module_progress.find(
            {"user_id": user_id, "module_id": {"$in": module_ids}}
        ).to_list(length=None)
        module_record_map = {record.get("module_id"): record for record in module_records}
        summaries = []

        for module in modules:
            topics = (module.get("content") or {}).get("topics", [])
            total_topics = len(topics)
            completed_topics = 0
            for topic in topics:
                progress = progress_map.get((module.get("module_id"), topic.get("topic_id")))
                if progress and progress.is_completed:
                    completed_topics += 1
            progress_percentage = (completed_topics / total_topics) * 100 if total_topics else 0
            module_record = module_record_map.get(module.get("module_id"), {})

            summaries.append(ModuleProgressSummary(
                module_id=module.get("module_id"),
                progress_percentage=progress_percentage,
                completed_topics=completed_topics,
                total_topics=total_topics,
                is_completed=completed_topics == total_topics and total_topics > 0,
                started_at=module_record.get("started_at"),
                completed_at=module_record.get("completion_date"),
                last_accessed=module_record.get("last_accessed"),
            ))

        return summaries

    async def _get_module_assessment_progress(
        self,
        db: AsyncIOMotorDatabase,
        user_id: str,
        module_ids: List[str]
    ) -> List[ModuleAssessmentProgressResponse]:
        if not module_ids:
            return []

        cursor = db.module_assessment_progress.find(
            {"user_id": user_id, "module_id": {"$in": module_ids}}
        )
        progress_records = await cursor.to_list(length=None)
        return [
            ModuleAssessmentProgressResponse(
                module_id=record.get("module_id"),
                scenario_completed=record.get("scenario_completed", False),
                mcq_attempts=record.get("mcq_attempts", 0),
                mcq_correct=record.get("mcq_correct", 0),
                is_completed=record.get("is_completed", False),
                last_updated=record.get("last_updated")
            )
            for record in progress_records
        ]

    async def _get_overall_progress(
        self,
        db: AsyncIOMotorDatabase,
        user_id: str,
        path_id: str,
        module_progress: List[ModuleProgressSummary]
    ) -> float:
        if not module_progress:
            return 0.0

        completed_modules = sum(1 for summary in module_progress if summary.is_completed)
        total_modules = len(module_progress)
        overall = (completed_modules / total_modules) * 100 if total_modules else 0

        progress = await self._get_user_progress(db, user_id, path_id)
        if progress:
            progress["overall_progress"] = overall
            progress["last_accessed"] = datetime.utcnow()
            await db.user_progress.replace_one({"_id": progress["_id"]}, progress)

        return overall

    def _map_module_detail(self, module: Dict) -> JourneyModuleDetail:
        topics = []
        for topic in (module.get("content") or {}).get("topics", []):
            topics.append(JourneyTopicContent(
                topic_id=topic["topic_id"],
                title=topic["title"],
                teaching=topic["teaching"],
                lesson_content=topic.get("lesson_content") or topic.get("teaching", ""),
                key_points=topic["key_points"],
                steps=topic["steps"],
                hands_on=JourneyHandsOn(**topic["hands_on"]),
                mcq=JourneyMcq(**topic["mcq"]),
                source_urls=topic.get("source_urls", [])
            ))

        assessment_data = (module.get("content") or {}).get("assessment")
        if not assessment_data:
            assessment_data = self._build_module_assessment({
                "name": module.get("name"),
                "description": module.get("description"),
                "topics": (module.get("content") or {}).get("topics", [])
            })

        assessment = None
        if assessment_data:
            assessment = JourneyModuleAssessment(
                scenario=assessment_data["scenario"],
                tasks=assessment_data["tasks"],
                validation=assessment_data.get("validation"),
                mcqs=[JourneyMcq(**mcq) for mcq in assessment_data.get("mcqs", [])]
            )

        return JourneyModuleDetail(
            module_id=module.get("module_id"),
            name=module.get("name"),
            description=module.get("description"),
            order_index=module.get("order_index"),
            estimated_time=module.get("estimated_time"),
            topics=topics,
            assessment=assessment
        )

    async def _update_module_progress_from_topics(
        self,
        db: AsyncIOMotorDatabase,
        user_id: str,
        module: Dict
    ) -> None:
        topic_progress = await self._get_topic_progress(db, user_id, [module.get("module_id")])
        total_topics = len((module.get("content") or {}).get("topics", []))
        completed_topics = sum(1 for item in topic_progress if item.is_completed)
        progress_percentage = (completed_topics / total_topics) * 100 if total_topics else 0

        module_progress = await self._get_module_progress(db, user_id, module.get("module_id"))
        if not module_progress:
            module_progress = {
                "user_id": user_id,
                "module_id": module.get("module_id"),
                "progress_percentage": progress_percentage,
                "started_at": datetime.utcnow(),
                "last_accessed": datetime.utcnow(),
                "is_completed": completed_topics == total_topics and total_topics > 0,
                "completion_date": datetime.utcnow() if completed_topics == total_topics and total_topics > 0 else None,
            }
        else:
            if not module_progress.get("started_at"):
                module_progress["started_at"] = datetime.utcnow()
            module_progress["progress_percentage"] = progress_percentage
            module_progress["last_accessed"] = datetime.utcnow()
            module_progress["is_completed"] = completed_topics == total_topics and total_topics > 0
            if module_progress["is_completed"]:
                module_progress["completion_date"] = datetime.utcnow()

        if module_progress.get("_id"):
            await db.module_progress.replace_one({"_id": module_progress["_id"]}, module_progress)
        else:
            result = await db.module_progress.insert_one(module_progress)
            module_progress["_id"] = result.inserted_id

    async def _update_path_progress(self, db: AsyncIOMotorDatabase, user_id: str, module_id: str) -> None:
        module = await self._get_module_by_id(db, module_id)
        if not module:
            return

        path_id = module.get("path_id")
        path_progress = await self._get_user_progress(db, user_id, path_id)
        if not path_progress:
            path_progress = {
                "user_id": user_id,
                "path_id": path_id,
                "current_module_id": module.get("module_id"),
                "completed_modules": [],
                "overall_progress": 0.0,
                "started_at": datetime.utcnow(),
                "last_accessed": datetime.utcnow(),
                "estimated_completion": None,
                "is_completed": False,
                "completion_date": None,
            }
            result = await db.user_progress.insert_one(path_progress)
            path_progress["_id"] = result.inserted_id

        all_modules = await self._get_modules_for_path(db, path_id)
        completed_modules_cursor = db.module_progress.find(
            {
                "user_id": user_id,
                "module_id": {"$in": [m.get("module_id") for m in all_modules]},
                "is_completed": True,
            }
        )
        completed_modules = await completed_modules_cursor.to_list(length=None)

        total_modules = len(all_modules)
        completed_count = len(completed_modules)
        completed_module_ids = [m.get("module_id") for m in completed_modules]
        next_module = next((m for m in all_modules if m.get("module_id") not in completed_module_ids), None)
        path_progress["overall_progress"] = (completed_count / total_modules) * 100 if total_modules > 0 else 0
        path_progress["completed_modules"] = completed_module_ids
        path_progress["current_module_id"] = next_module.get("module_id") if next_module else None
        path_progress["last_accessed"] = datetime.utcnow()

        remaining_modules = max(0, total_modules - completed_count)
        if remaining_modules > 0:
            path_progress["estimated_completion"] = datetime.utcnow() + timedelta(days=remaining_modules * 10)
        else:
            path_progress["estimated_completion"] = datetime.utcnow()

        if completed_count == total_modules and total_modules > 0:
            path_progress["is_completed"] = True
            path_progress["completion_date"] = datetime.utcnow()

        await db.user_progress.replace_one({"_id": path_progress["_id"]}, path_progress)

    def _find_topic(self, module: Dict, topic_id: str) -> Optional[Dict]:
        for topic in (module.get("content") or {}).get("topics", []):
            if topic.get("topic_id") == topic_id:
                return topic
        return None

    def _build_module_assessment(self, module_info: Dict) -> Dict:
        topics = module_info.get("topics", [])
        topic_titles = [topic.get("title") for topic in topics if topic.get("title")]
        scenario = (
            f"You are leading a workstream for {module_info.get('name', 'this module')} and must deliver a practical solution."
        )
        tasks = [
            f"Define the goal and success criteria for {module_info.get('name', 'the module')}",
            "Outline a step-by-step implementation plan",
            "Identify risks and mitigation steps"
        ]
        if topic_titles:
            tasks.append(f"Include checkpoints for: {', '.join(topic_titles[:3])}")

        validation = [
            "Clear success criteria",
            "Actionable plan with trade-offs",
            "Risk mitigation included"
        ]

        mcqs = []
        for topic in topics:
            mcq = topic.get("mcq")
            if mcq:
                mcqs.append(mcq)

        if len(mcqs) < 3 and topics:
            for topic in topics:
                mcqs.append({
                    "question": f"Which action best supports {topic.get('title', 'this topic').lower()}?",
                    "options": topic.get("key_points", [])[:4] or [
                        "Define goals",
                        "Skip validation",
                        "Ignore monitoring",
                        "Avoid documentation"
                    ],
                    "correct_option": (topic.get("key_points", [])[:1] or ["Define goals"])[0],
                    "explanation": "Use the core principle from the topic key points."
                })
                if len(mcqs) >= 3:
                    break

        return {
            "scenario": scenario,
            "tasks": tasks,
            "validation": validation,
            "mcqs": mcqs[:5]
        }


# Global learning journey service instance
learning_service = LearningJourneyService()