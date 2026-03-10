import re
from schemas import AwsStudyResponse


async def generate_aws_learning_response(groq_service, service_name: str) -> AwsStudyResponse:
    teaching_prompt = f"""
You are an expert AWS Solutions Architect and technical educator. Create comprehensive, detailed learning content for: {service_name}

Format your response EXACTLY as shown below with clear section headers:

CATEGORY: [Choose one: Compute, Storage, Database, Networking, Security, Analytics, Machine Learning, Developer Tools, Management, etc.]

DESCRIPTION:
Provide a comprehensive explanation (3-4 paragraphs) covering:
- What {service_name} is and its primary purpose
- How it works technically (architecture, components)
- Key features and capabilities
- Pricing model basics

USE_CASES:
Provide detailed scenarios (3-4 use cases) including:
- Specific business problems it solves
- Technical requirements it addresses
- Industries or company types that benefit
- Example implementations

IMPLEMENTATION:
Provide step-by-step technical guidance including:
- Prerequisites and setup requirements
- Basic configuration steps
- Code examples or console steps where applicable
- Important configuration options
- Monitoring and maintenance considerations

BEST_PRACTICES:
Share expert-level guidance including:
- Security configurations and IAM considerations
- Performance optimization techniques
- Cost optimization strategies
- High availability and disaster recovery
- Common mistakes to avoid
- Monitoring and logging recommendations

RELATED_SERVICES: EC2, S3, VPC, IAM, CloudWatch

Make this educational content detailed enough to teach a DevOps engineer both theoretical concepts and practical implementation. Include specific examples, real-world scenarios, and actionable guidance.
"""

    response = await groq_service.generate_response(teaching_prompt)
    print(f"=== AI Response for {service_name} ===")
    print(response[:500] + "..." if len(response) > 500 else response)
    print("=== End AI Response ===")
    return parse_aws_teaching_response(response, service_name)


def parse_aws_teaching_response(response_text: str, service_name: str) -> AwsStudyResponse:
    category = "AWS Service"
    description = ""
    use_cases = ""
    implementation = ""
    best_practices = ""
    related_services = []

    try:
        response_text = response_text.strip()
        sections = parse_with_exact_headers(response_text)

        if not sections or sum(len(v) for v in sections.values()) < 100:
            sections = parse_with_flexible_headers(response_text)

        if not sections or sum(len(v) for v in sections.values()) < 100:
            sections = parse_with_patterns(response_text)

        if sections:
            description = sections.get("description", "")
            use_cases = sections.get("use_cases", "")
            implementation = sections.get("implementation", "")
            best_practices = sections.get("best_practices", "")
            category = sections.get("category", "AWS Service")
            related_text = sections.get("related_services", "")
            if related_text:
                related_services = extract_related_services(related_text)
    except Exception as exc:
        print(f"Error parsing AWS teaching response: {exc}")

    if not description or len(description) < 50:
        description = get_service_description(service_name)
    if not use_cases or len(use_cases) < 50:
        use_cases = get_service_use_cases(service_name)
    if not implementation or len(implementation) < 50:
        implementation = get_service_implementation(service_name)
    if not best_practices:
        best_practices = get_service_best_practices(service_name)
    if not related_services:
        related_services = get_related_services(service_name)

    return AwsStudyResponse(
        service_name=service_name,
        category=category,
        description=description,
        use_cases=use_cases,
        implementation=implementation,
        best_practices=best_practices if best_practices else None,
        related_services=related_services if related_services else None,
    )


def parse_with_exact_headers(response_text: str) -> dict:
    sections = {}
    lines = response_text.split("\n")
    current_section = None
    current_content = []

    for line in lines:
        line = line.strip()
        if line.startswith("CATEGORY:"):
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = "category"
            sections["category"] = line.replace("CATEGORY:", "").strip()
            current_content = []
        elif line.startswith("DESCRIPTION:"):
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = "description"
            desc_start = line.replace("DESCRIPTION:", "").strip()
            current_content = [desc_start] if desc_start else []
        elif line.startswith("USE_CASES:"):
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = "use_cases"
            use_start = line.replace("USE_CASES:", "").strip()
            current_content = [use_start] if use_start else []
        elif line.startswith("IMPLEMENTATION:"):
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = "implementation"
            impl_start = line.replace("IMPLEMENTATION:", "").strip()
            current_content = [impl_start] if impl_start else []
        elif line.startswith("BEST_PRACTICES:"):
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = "best_practices"
            bp_start = line.replace("BEST_PRACTICES:", "").strip()
            current_content = [bp_start] if bp_start else []
        elif line.startswith("RELATED_SERVICES:"):
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content).strip()
            sections["related_services"] = line.replace("RELATED_SERVICES:", "").strip()
            current_section = None
            current_content = []
        else:
            if current_section and line:
                current_content.append(line)

    if current_section and current_content:
        sections[current_section] = "\n".join(current_content).strip()

    return sections


def parse_with_flexible_headers(response_text: str) -> dict:
    sections = {}
    patterns = {
        "category": r"(?i)^\s*(?:category|service[_\s]?type|classification)\s*[:=]\s*(.+)$",
        "description": r"(?i)^\s*(?:description|what[_\s]?is|overview|about)\s*[:=]?\s*(.*)$",
        "use_cases": r"(?i)^\s*(?:use[_\s]?cases?|when[_\s]?to[_\s]?use|scenarios?|applications?)\s*[:=]?\s*(.*)$",
        "implementation": r"(?i)^\s*(?:implementation|how[_\s]?to[_\s]?(?:implement|use|setup)|getting[_\s]?started)\s*[:=]?\s*(.*)$",
        "best_practices": r"(?i)^\s*(?:best[_\s]?practices?|recommendations?|tips)\s*[:=]?\s*(.*)$",
        "related_services": r"(?i)^\s*(?:related[_\s]?services?|integrations?|connections?)\s*[:=]?\s*(.+)$",
    }

    lines = response_text.split("\n")
    current_section = None
    current_content = []

    for line in lines:
        line = line.strip()
        matched_section = None
        header_content = None

        for section_name, pattern in patterns.items():
            match = re.match(pattern, line)
            if match:
                matched_section = section_name
                header_content = match.group(1).strip() if len(match.groups()) > 0 else ""
                break

        if matched_section:
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content).strip()

            current_section = matched_section
            if matched_section == "category":
                sections["category"] = header_content
                current_content = []
            else:
                current_content = [header_content] if header_content else []
        else:
            if current_section and line:
                current_content.append(line)

    if current_section and current_content:
        sections[current_section] = "\n".join(current_content).strip()

    return sections


def parse_with_patterns(response_text: str) -> dict:
    sections = {}
    desc_match = re.search(r"(?:amazon\s+\w+(?:\s+\([^)]+\))?\s+is\s+.+?)(?:\n\s*\n|\n.*?(?:use|when|implement|best))", response_text, re.IGNORECASE | re.DOTALL)
    if desc_match:
        sections["description"] = desc_match.group(0).strip()

    use_cases_match = re.search(r"(?:use\s+cases?|when\s+to\s+use|scenarios?)[^\n]*\n((?:(?:\d+\.|[•\-*]|\n\n)\s*.+\n?)+)", response_text, re.IGNORECASE | re.DOTALL)
    if use_cases_match:
        sections["use_cases"] = use_cases_match.group(1).strip()

    impl_match = re.search(r"(?:implementation|how\s+to|setup|getting\s+started)[^\n]*\n((?:(?:\d+\.|[•\-*]|\n\n)\s*.+\n?)+)", response_text, re.IGNORECASE | re.DOTALL)
    if impl_match:
        sections["implementation"] = impl_match.group(1).strip()

    bp_match = re.search(r"(?:best\s+practices?|recommendations?|tips)[^\n]*\n((?:(?:\d+\.|[•\-*]|\n\n)\s*.+\n?)+)", response_text, re.IGNORECASE | re.DOTALL)
    if bp_match:
        sections["best_practices"] = bp_match.group(1).strip()

    return sections


def extract_related_services(related_text: str) -> list:
    related_text = re.sub(r"(?i)^\s*(?:related\s+services?\s*[:=]?\s*)", "", related_text).strip()
    services = []

    if "," in related_text:
        services = [s.strip() for s in related_text.split(",")]
    elif " " in related_text and len(related_text.split()) <= 8:
        services = related_text.split()
    elif "\n" in related_text:
        services = [s.strip() for s in related_text.split("\n")]
    else:
        services = [related_text]

    cleaned_services = []
    for service in services:
        service = re.sub(r"[^\w\s\-]", "", service).strip()
        if service and len(service) <= 30:
            cleaned_services.append(service)

    return cleaned_services[:6]


def get_service_description(service_name: str) -> str:
    service_descriptions = {
        "EC2": """Amazon EC2 (Elastic Compute Cloud) is a web service that provides secure, resizable compute capacity in the cloud. It is designed to make web-scale cloud computing easier for developers.

EC2 provides virtual computing environments, known as instances, that can be launched with a variety of operating systems, configured with custom applications, and scaled up or down based on demand. The service offers complete control over computing resources and runs on Amazon's proven computing environment.

Key features include multiple instance types optimized for different use cases, various pricing options (On-Demand, Reserved, Spot), integration with other AWS services, and the ability to scale horizontally and vertically based on application requirements.

The service follows a pay-as-you-use pricing model where you only pay for the compute time you actually use, making it cost-effective for both small applications and large-scale enterprise workloads.""",
        "VPC": """Amazon VPC (Virtual Private Cloud) is a networking service that allows you to create a logically isolated section of the AWS cloud where you can launch AWS resources in a virtual network that you define.

VPC provides complete control over your virtual networking environment, including selection of your own IP address ranges, creation of subnets, configuration of route tables, and network gateways. You can create both public and private subnets within your VPC to architect your infrastructure according to your security and operational needs.

Key features include custom IP address ranges (CIDR blocks), subnets spanning multiple Availability Zones, internet and NAT gateways for internet connectivity, security groups and network ACLs for traffic filtering, and VPC peering for connecting multiple VPCs.

VPC is fundamental to AWS networking and provides the foundation for secure, scalable cloud architectures with enterprise-grade security and compliance capabilities.""",
        "S3": """Amazon S3 (Simple Storage Service) is an object storage service that offers industry-leading scalability, data availability, security, and performance for storing and retrieving any amount of data from anywhere.

S3 stores data as objects within buckets, where each object can be up to 5TB in size. It provides 99.999999999% (11 9's) of data durability and is designed to sustain the concurrent loss of data in two facilities. The service offers multiple storage classes optimized for different use cases and access patterns.

Key features include unlimited storage capacity, multiple storage classes for cost optimization, lifecycle policies for automated data management, versioning and cross-region replication for data protection, and integration with AWS analytics and machine learning services.

S3 follows a pay-as-you-go pricing model where you only pay for the storage you use, requests made, and data transferred, making it cost-effective for everything from backup and archiving to big data analytics and content distribution.""",
        "Lambda": """AWS Lambda is a serverless computing service that lets you run code without provisioning or managing servers. You pay only for the compute time you consume - there is no charge when your code is not running.

Lambda automatically scales your applications by running code in response to each trigger. Your code runs in parallel and processes each trigger individually, scaling precisely with the size of the workload. Lambda supports multiple programming languages including Python, Node.js, Java, C#, and Go.

Key features include automatic scaling, built-in fault tolerance, pay-per-request pricing, integration with other AWS services through event sources, and the ability to bring your own libraries and dependencies through Lambda Layers.

Lambda is ideal for building microservices, processing real-time data streams, building APIs with API Gateway, and automating operational tasks, all without the overhead of managing infrastructure.""",
    }
    return service_descriptions.get(service_name, f"""Amazon {service_name} is an AWS service that provides cloud-based solutions for modern applications and infrastructure.

{service_name} is designed to help organizations build, deploy, and manage applications and services in the AWS cloud environment. It offers scalability, reliability, and integration with other AWS services to support various business and technical requirements.

Key features include enterprise-grade security, high availability, integration with AWS ecosystem, and flexible pricing options to match different usage patterns and business needs.

The service is designed to help organizations leverage cloud computing benefits including reduced operational overhead, improved scalability, and cost optimization through pay-as-you-use pricing models.""")


def get_service_use_cases(service_name: str) -> str:
    use_cases_map = {
        "EC2": """1. Web Application Hosting: Host dynamic websites and web applications that can scale based on traffic demands. Perfect for e-commerce sites, content management systems, and SaaS applications.

2. Development and Testing: Create isolated environments for software development, testing, and staging. Teams can quickly spin up instances that mirror production environments.

3. Data Processing and Analytics: Run batch processing jobs, data analysis workloads, and machine learning training tasks. The ability to scale compute resources makes it ideal for processing large datasets.

4. Enterprise Applications: Host business-critical applications like ERP systems, databases, and enterprise software that require specific performance, compliance, and security requirements.""",
        "VPC": """1. Multi-tier Application Architecture: Design secure network architectures with public subnets for web servers and private subnets for databases and application servers, ensuring proper traffic isolation.

2. Hybrid Cloud Integration: Connect on-premises data centers to AWS using VPN or Direct Connect, creating a seamless hybrid cloud environment for gradual cloud migration or burst capacity scenarios.

3. Compliance and Security Requirements: Meet strict regulatory requirements by creating isolated network environments with granular security controls, custom routing, and network monitoring.

4. Multi-environment Isolation: Separate development, staging, and production environments using different VPCs or subnets, ensuring proper isolation while maintaining connectivity where needed.""",
        "S3": """1. Website and Application Hosting: Store and serve static website content, application assets, and media files with high availability and global content distribution through CloudFront integration.

2. Backup and Archive: Implement cost-effective backup solutions with multiple storage classes including Glacier for long-term archival, ensuring data durability and compliance with retention policies.

3. Big Data and Analytics: Store large datasets for processing with AWS analytics services like Athena, EMR, and Redshift, enabling data lakes and analytics pipelines.

4. Content Distribution: Distribute software updates, mobile app assets, and media content globally with integration to CloudFront CDN for low-latency access.""",
        "Lambda": """1. API Backend Services: Build serverless APIs using Lambda with API Gateway for mobile applications, web applications, and microservices without managing server infrastructure.

2. Event-driven Processing: Process events from S3 uploads, DynamoDB changes, or CloudWatch alarms automatically, enabling real-time data processing and automated workflows.

3. Scheduled Tasks: Replace cron jobs and scheduled tasks with Lambda functions triggered by CloudWatch Events for maintenance tasks, data processing, and automated operations.

4. Real-time Data Transformation: Process streaming data from Kinesis, transform and filter data in real-time for analytics, monitoring, or downstream applications.""",
    }
    return use_cases_map.get(service_name, f"""1. Cloud Infrastructure: Use {service_name} to build scalable and reliable cloud infrastructure solutions that can grow with your business needs.

2. Application Development: Integrate {service_name} into your application architecture to leverage cloud-native capabilities and improve application performance.

3. Data Management: Utilize {service_name} for managing, processing, or analyzing data in cloud environments with enterprise-grade security and compliance.

4. Operational Efficiency: Implement {service_name} to automate operational tasks, reduce manual overhead, and improve overall system reliability.""")


def get_service_implementation(service_name: str) -> str:
    implementation_map = {
        "VPC": """1. Planning and Design:
   - Define your IP address ranges (CIDR blocks) avoiding conflicts with on-premises networks
   - Plan subnet layout across multiple Availability Zones for high availability
   - Design security group and NACL rules based on application requirements

2. VPC Creation:
   - Create VPC with custom CIDR block (e.g., 10.0.0.0/16)
   - Create public subnets for internet-facing resources and private subnets for internal resources
   - Set up Internet Gateway for public subnet connectivity
   - Configure NAT Gateway or NAT Instance for private subnet internet access

3. Network Configuration:
   - Create and configure route tables for public and private subnets
   - Set up security groups as stateful firewalls for instance-level protection
   - Configure Network ACLs as stateless firewalls for subnet-level protection
   - Implement VPC endpoints for private access to AWS services

4. Monitoring and Optimization:
   - Enable VPC Flow Logs for network traffic monitoring
   - Use AWS Config for compliance monitoring of network configurations
   - Implement CloudWatch metrics for network performance monitoring""",
        "S3": """1. Setup and Configuration:
   - Create S3 buckets with appropriate naming conventions and region selection
   - Configure bucket policies and IAM roles for secure access management
   - Enable versioning for data protection and change tracking
   - Set up lifecycle policies for automated cost optimization

2. Data Organization:
   - Design folder structure and naming conventions for efficient data management
   - Implement object tagging for cost allocation and automated management
   - Configure cross-region replication for disaster recovery scenarios
   - Set up event notifications for automated processing workflows

3. Security Implementation:
   - Enable encryption at rest using SSE-S3 or SSE-KMS
   - Configure bucket policies for fine-grained access control
   - Implement access logging for audit trails
   - Use pre-signed URLs for secure temporary access

4. Performance Optimization:
   - Use multipart uploads for large files
   - Implement transfer acceleration for global access
   - Choose appropriate storage classes based on access patterns
   - Monitor and optimize request patterns using CloudWatch metrics""",
    }

    return implementation_map.get(service_name, f"""1. Setup and Prerequisites:
   - Create an AWS account and configure appropriate IAM permissions for {service_name}
   - Choose the appropriate AWS region based on latency and compliance requirements
   - Review service limits and quotas for your use case

2. Configuration:
   - Access the AWS Management Console and navigate to {service_name}
   - Configure the service according to your specific requirements
   - Set up appropriate security groups, IAM roles, and access policies
   - Configure monitoring and logging using CloudWatch

3. Integration:
   - Integrate {service_name} with other AWS services as needed
   - Set up appropriate networking and connectivity
   - Configure backup and disaster recovery procedures
   - Implement security best practices and compliance requirements

4. Monitoring and Maintenance:
   - Set up CloudWatch alarms for key metrics
   - Implement regular backup and testing procedures
   - Monitor costs and optimize usage based on actual requirements""")


def get_service_best_practices(service_name: str) -> str:
    return f"""Security Best Practices:
- Implement least-privilege access using IAM roles and policies
- Enable encryption for data at rest and in transit
- Use VPC and security groups for network-level protection
- Enable AWS CloudTrail for audit logging and compliance

Performance Optimization:
- Monitor key performance metrics using CloudWatch
- Right-size resources based on actual usage patterns
- Use appropriate service configurations for your workload
- Implement caching and optimization strategies where applicable

Cost Optimization:
- Monitor costs using AWS Cost Explorer and billing alerts
- Use appropriate pricing models (On-Demand, Reserved, Spot instances)
- Implement automated scaling policies to match demand
- Regular review and cleanup of unused resources

Operational Excellence:
- Implement Infrastructure as Code using CloudFormation or Terraform
- Set up automated backup and disaster recovery procedures
- Use tags for resource organization and cost allocation
- Establish monitoring and alerting for operational metrics"""


def get_related_services(service_name: str) -> list:
    related_services_map = {
        "EC2": ["S3", "VPC", "IAM", "CloudWatch", "ELB"],
        "VPC": ["EC2", "NAT Gateway", "Internet Gateway", "Route 53", "Direct Connect"],
        "S3": ["CloudFront", "Lambda", "IAM", "CloudWatch", "Athena"],
        "Lambda": ["API Gateway", "S3", "DynamoDB", "CloudWatch", "SNS"],
        "RDS": ["VPC", "IAM", "CloudWatch", "Lambda", "S3"],
        "IAM": ["CloudTrail", "CloudWatch", "Organizations", "STS", "Cognito"],
    }

    return related_services_map.get(service_name, ["IAM", "CloudWatch", "VPC", "S3", "CloudFormation"])
