import React, { useState } from 'react';
import { FaAws, FaSearch, FaBook, FaLightbulb, FaCogs, FaArrowLeft } from 'react-icons/fa';
import { apiService } from '../services/api';

export default function AwsStudyMode({ onBack }) {
  const [resourceName, setResourceName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentLesson, setCurrentLesson] = useState(null);
  const [error, setError] = useState(null);

  const handleStartLearning = async (selectedResource = null) => {
    const targetResource = (selectedResource || resourceName).trim();
    if (!targetResource) {
      setError('Please enter an AWS service or resource name');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const lesson = await apiService.startAwsLearning(targetResource);
      setCurrentLesson(lesson);
    } catch (err) {
      setError('Failed to start learning session. Make sure the backend is running.');
      console.error('Error starting AWS learning:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewResource = () => {
    setCurrentLesson(null);
    setResourceName('');
    setError(null);
  };

  const curatedTopics = [
    { name: 'EC2', level: 'Foundations', description: 'Compute basics: instances, scaling, pricing, limits.' },
    { name: 'VPC', level: 'Foundations', description: 'Networking essentials: subnets, routing, security.' },
    { name: 'IAM', level: 'Security', description: 'Identity basics: users, roles, policies, MFA.' },
    { name: 'S3', level: 'Storage', description: 'Object storage: classes, lifecycle, encryption.' },
    { name: 'RDS', level: 'Data', description: 'Relational DBs: backups, HA, read replicas.' },
    { name: 'DynamoDB', level: 'Data', description: 'NoSQL: keys, throughput, indexes, streams.' },
    { name: 'Lambda', level: 'Serverless', description: 'Functions: triggers, limits, cold starts.' },
    { name: 'API Gateway', level: 'Serverless', description: 'APIs: auth, throttling, caching.' },
    { name: 'SQS', level: 'Messaging', description: 'Queues: retries, DLQ, ordering.' },
    { name: 'SNS', level: 'Messaging', description: 'Pub/sub: topics, fan-out, filtering.' },
    { name: 'ECS', level: 'Containers', description: 'Containers: tasks, services, scaling.' },
    { name: 'EKS', level: 'Containers', description: 'Kubernetes: clusters, nodes, workloads.' },
    { name: 'CloudWatch', level: 'Observability', description: 'Logs, metrics, alarms, dashboards.' },
    { name: 'CloudFormation', level: 'IaC', description: 'Stacks: templates, change sets, drift.' },
  ];

  const popularResources = curatedTopics.map((topic) => topic.name);

  const extractKeyPoints = (text, maxPoints = 4) => {
    if (!text) return [];
    const normalized = String(text).replace(/\s+/g, ' ').trim();
    const splitByBullets = normalized.split(/\s*[-*]\s+/).filter(Boolean);
    const base = splitByBullets.length > 1
      ? splitByBullets
      : normalized.split(/(?<=[.!?])\s+/);
    return base.map((item) => item.trim()).filter(Boolean).slice(0, maxPoints);
  };

  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-8">
      {/* Header */}
      <div className="flex items-center mb-6 sm:mb-8">
        <button
          onClick={onBack}
          className="btn btn-secondary px-3 py-2 mr-4"
        >
          <FaArrowLeft className="mr-2" />
          Back to Home
        </button>
        <h1 className="text-2xl sm:text-3xl font-bold bg-gradient-to-r from-cyan-400 to-teal-400 bg-clip-text text-transparent">
          <FaAws className="inline mr-3 text-cyan-400" />
          Cloud Refresher Hub
        </h1>
      </div>

      {!currentLesson ? (
        <>
          {/* Tutor Intro */}
          <div className="glass-dark rounded-3xl p-4 sm:p-6 border border-white/10 mb-6 sm:mb-8">
            <h2 className="text-xl sm:text-2xl font-semibold mb-2 text-cyan-300">Your AI Tutor</h2>
            <p className="text-sm sm:text-base text-gray-300">
              This is a fast refresher for people who already know the basics. Pick a service and I will
              summarize the key points, when to use it, and common pitfalls in a quick, skimmable format.
            </p>
          </div>

          {/* Input Section */}
          <div className="glass-dark rounded-3xl p-5 sm:p-8 border border-white/10 shadow-xl mb-6 sm:mb-8">
            <h2 className="text-xl sm:text-2xl font-semibold mb-5 sm:mb-6 text-center">What AWS service do you want to refresh?</h2>
            
            <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 mb-5 sm:mb-6">
              <div className="flex-1">
                <input
                  type="text"
                  value={resourceName}
                  onChange={(e) => setResourceName(e.target.value)}
                  placeholder="Enter AWS service (e.g., EC2, S3, Lambda, RDS...)"
                  className="input-base px-4 py-3"
                  onKeyDown={(e) => e.key === 'Enter' && handleStartLearning()}
                />
              </div>
              <button
                onClick={handleStartLearning}
                disabled={isLoading || !resourceName.trim()}
                className="btn btn-amber px-6 sm:px-8 py-3"
              >
                <FaSearch className="mr-2" />
                {isLoading ? 'Learning...' : 'Start Learning'}
              </button>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-6 p-4 bg-red-900/50 border border-red-500 rounded-2xl text-red-200">
                {error}
              </div>
            )}

            {/* Popular Resources */}
            <div>
              <h3 className="text-lg font-semibold mb-4 text-gray-300">Popular AWS Services:</h3>
              <div className="flex flex-wrap gap-2">
                {popularResources.map((resource) => (
                  <button
                    key={resource}
                    onClick={() => handleStartLearning(resource)}
                    className="chip hover:border-white/30 hover:text-white"
                  >
                    {resource}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Curated Topics */}
          <div className="glass-dark rounded-3xl p-5 sm:p-8 border border-white/10 mb-6 sm:mb-8">
            <h3 className="text-xl sm:text-2xl font-semibold mb-5 sm:mb-6 text-cyan-300">Curated Topics</h3>
            <div className="grid md:grid-cols-2 gap-3 sm:gap-4">
              {curatedTopics.map((topic) => (
                <button
                  key={topic.name}
                  onClick={() => handleStartLearning(topic.name)}
                  className="text-left glass-dark rounded-2xl p-4 transition-all duration-300 hover:border-white/20"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-lg font-semibold text-white">{topic.name}</h4>
                    <span className="text-xs text-slate-300 bg-slate-600/60 px-2 py-1 rounded-full">
                      {topic.level}
                    </span>
                  </div>
                  <p className="text-sm text-slate-300">{topic.description}</p>
                </button>
              ))}
            </div>
          </div>

          {/* How it works */}
          <div className="glass-dark rounded-3xl p-5 sm:p-6 border border-white/10">
            <h3 className="text-lg sm:text-xl font-semibold mb-4 text-cyan-300">
              <FaLightbulb className="inline mr-2" />
              How it works
            </h3>
            <div className="grid md:grid-cols-3 gap-4 sm:gap-6">
              <div className="text-center">
                <FaSearch className="text-3xl text-cyan-400 mx-auto mb-2" />
                <h4 className="font-semibold mb-2">1. Choose Service</h4>
                <p className="text-gray-400 text-sm">Pick a service you want to refresh quickly</p>
              </div>
              <div className="text-center">
                <FaBook className="text-3xl text-teal-400 mx-auto mb-2" />
                <h4 className="font-semibold mb-2">2. Review Key Points</h4>
                <p className="text-gray-400 text-sm">Skimmable summaries with the essentials</p>
              </div>
              <div className="text-center">
                <FaCogs className="text-3xl text-cyan-400 mx-auto mb-2" />
                <h4 className="font-semibold mb-2">3. Apply Fast</h4>
                <p className="text-gray-400 text-sm">When to use it and what to watch out for</p>
              </div>
            </div>
          </div>
        </>
      ) : (
        /* Learning Content */
        <div className="space-y-6">
          {/* Quick Refresher */}
          <div className="glass-dark rounded-3xl p-5 sm:p-6 border border-white/10">
            <h3 className="text-lg sm:text-xl font-semibold mb-4 text-cyan-300">Key Points (Quick Refresher)</h3>
            <div className="grid md:grid-cols-2 gap-3 sm:gap-4">
              <div className="panel-soft p-3 sm:p-4">
                <h4 className="text-sm uppercase tracking-wide text-slate-400 mb-2">Core Idea</h4>
                <ul className="list-disc list-inside text-gray-300 space-y-1">
                  {extractKeyPoints(currentLesson.description, 3).map((point, index) => (
                    <li key={`core-${index}`}>{point}</li>
                  ))}
                </ul>
              </div>
              <div className="panel-soft p-3 sm:p-4">
                <h4 className="text-sm uppercase tracking-wide text-slate-400 mb-2">When to Use</h4>
                <ul className="list-disc list-inside text-gray-300 space-y-1">
                  {extractKeyPoints(currentLesson.use_cases, 3).map((point, index) => (
                    <li key={`use-${index}`}>{point}</li>
                  ))}
                </ul>
              </div>
              <div className="panel-soft p-3 sm:p-4">
                <h4 className="text-sm uppercase tracking-wide text-slate-400 mb-2">How It Works</h4>
                <ul className="list-disc list-inside text-gray-300 space-y-1">
                  {extractKeyPoints(currentLesson.implementation, 3).map((point, index) => (
                    <li key={`how-${index}`}>{point}</li>
                  ))}
                </ul>
              </div>
              <div className="panel-soft p-3 sm:p-4">
                <h4 className="text-sm uppercase tracking-wide text-slate-400 mb-2">Pitfalls / Best Practices</h4>
                <ul className="list-disc list-inside text-gray-300 space-y-1">
                  {extractKeyPoints(currentLesson.best_practices, 3).map((point, index) => (
                    <li key={`best-${index}`}>{point}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* Resource Header */}
          <div className="glass-dark rounded-3xl p-5 sm:p-6 border-l-4 border-cyan-500">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl sm:text-2xl font-bold text-cyan-400">{currentLesson.service_name}</h2>
              <button
                onClick={handleNewResource}
                  className="btn btn-secondary px-4 py-2 text-sm"
              >
                Learn Another Service
              </button>
            </div>
            <p className="text-base sm:text-lg text-gray-300">{currentLesson.category}</p>
          </div>

          {/* What is it */}
          <div className="glass-dark rounded-3xl p-5 sm:p-6 border border-white/10">
            <h3 className="text-lg sm:text-xl font-semibold mb-4 text-cyan-300 flex items-center">
              <FaBook className="mr-2" />
              What is {currentLesson.service_name}?
            </h3>
            <p className="text-gray-300 whitespace-pre-line">{currentLesson.description}</p>
          </div>

          {/* Use Cases */}
          <div className="glass-dark rounded-3xl p-5 sm:p-6 border border-white/10">
            <h3 className="text-lg sm:text-xl font-semibold mb-4 text-teal-300 flex items-center">
              <FaLightbulb className="mr-2" />
              When to use {currentLesson.service_name}
            </h3>
            <p className="text-gray-300 whitespace-pre-line">{currentLesson.use_cases}</p>
          </div>

          {/* Implementation */}
          <div className="card-shell p-6">
            <h3 className="text-xl font-semibold mb-4 text-cyan-300 flex items-center">
              <FaCogs className="mr-2" />
              How to implement {currentLesson.service_name}
            </h3>
            <p className="text-gray-300 whitespace-pre-line">{currentLesson.implementation}</p>
          </div>

          {/* Best Practices */}
          {currentLesson.best_practices && (
            <div className="card-shell p-6">
              <h3 className="text-xl font-semibold mb-4 text-teal-300 flex items-center">
                <FaBook className="mr-2" />
                Best Practices
              </h3>
              <p className="text-gray-300 whitespace-pre-line">{currentLesson.best_practices}</p>
            </div>
          )}

          {/* Related Services */}
          {currentLesson.related_services && currentLesson.related_services.length > 0 && (
            <div className="card-shell p-6">
              <h3 className="text-xl font-semibold mb-4 text-cyan-300">Related AWS Services</h3>
              <div className="flex flex-wrap gap-2">
                {currentLesson.related_services.map((service, index) => (
                  <button
                    key={index}
                    onClick={() => setResourceName(service)}
                    className="btn btn-info px-3 py-2 text-sm"
                  >
                    {service}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}