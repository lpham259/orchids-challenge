'use client';

import { useState } from 'react';
import URLInput from '../app/components/url_input_component'
import JobStatus from '../app/components/job_status_component';
import PreviewPane from '../app/components/preview_pane_component';
import JobHistory from '../app/components/job_history_component';

interface Job {
  id: string;
  url: string;
  status: 'pending' | 'scraping' | 'processing' | 'generating' | 'completed' | 'failed';
  progress: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

interface JobResult {
  job_id: string;
  url: string;
  generated_html: string;
  scraped_data?: {
    title?: string;
    color_palette?: string[];
    fonts?: string[];
    dom_structure?: {
      text_content?: string;
    };
    [key: string]: unknown;
  };
  created_at: string;
  completed_at: string;
}

export default function Home() {
  const [currentJob, setCurrentJob] = useState<Job | null>(null);
  const [jobResult, setJobResult] = useState<JobResult | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleStartCloning = async (url: string) => {
    setIsLoading(true);
    setCurrentJob(null);
    setJobResult(null);

    try {
      const response = await fetch('http://localhost:8000/clone', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: url,
          include_screenshots: true,
          include_dom: true,
          include_styles: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Start polling for status
      pollJobStatus(data.job_id);
    } catch (error) {
      console.error('Error starting cloning:', error);
      alert('Failed to start cloning. Please check if the backend is running.');
    } finally {
      setIsLoading(false);
    }
  };

  const pollJobStatus = async (jobId: string) => {
    const poll = async () => {
      try {
        const response = await fetch(`http://localhost:8000/status/${jobId}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const job: Job = await response.json();
        setCurrentJob(job);

        if (job.status === 'completed') {
          // Fetch the result
          const resultResponse = await fetch(`http://localhost:8000/result/${jobId}`);
          if (resultResponse.ok) {
            const result: JobResult = await resultResponse.json();
            setJobResult(result);
          }
          // Refresh job history
          fetchJobs();
        } else if (job.status === 'failed') {
          // Stop polling on failure
          fetchJobs();
        } else {
          // Continue polling
          setTimeout(poll, 2000);
        }
      } catch (error) {
        console.error('Error polling job status:', error);
      }
    };

    poll();
  };

  const fetchJobs = async () => {
    try {
      const response = await fetch('http://localhost:8000/jobs');
      if (response.ok) {
        const jobsData: Job[] = await response.json();
        setJobs(jobsData);
      }
    } catch (error) {
      console.error('Error fetching jobs:', error);
    }
  };

  const handleSelectJob = async (jobId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/result/${jobId}`);
      if (response.ok) {
        const result: JobResult = await response.json();
        setJobResult(result);
        setCurrentJob(null);
      }
    } catch (error) {
      console.error('Error fetching job result:', error);
    }
  };

  const handleDeleteJob = async (jobId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/jobs/${jobId}`, {
        method: 'DELETE',
      });
      if (response.ok) {
        fetchJobs();
        if (jobResult?.job_id === jobId) {
          setJobResult(null);
        }
      }
    } catch (error) {
      console.error('Error deleting job:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Website DUPE</h1>
              <p className="text-sm text-gray-600">
                Clone any website with AI-powered HTML generation
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-xs text-gray-500">
                Powered by Claude & Hyperbrowser
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Left Column - Input and Controls */}
          <div className="lg:col-span-1 space-y-6">
            {/* URL Input */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Clone Website
              </h2>
              <URLInput 
                onSubmit={handleStartCloning}
                isLoading={isLoading}
              />
            </div>

            {/* Job Status */}
            {currentJob && (
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  Progress
                </h2>
                <JobStatus job={currentJob} />
              </div>
            )}

            {/* Job History */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Recent Jobs
              </h2>
              <JobHistory 
                jobs={jobs}
                onSelectJob={handleSelectJob}
                onDeleteJob={handleDeleteJob}
                onRefresh={fetchJobs}
              />
            </div>
          </div>

          {/* Right Column - Preview */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-sm border">
              <div className="p-6 border-b">
                <h2 className="text-lg font-semibold text-gray-900">
                  {jobResult ? 'Generated Website' : 'Preview'}
                </h2>
                {jobResult && (
                  <p className="text-sm text-gray-600 mt-1">
                    Cloned from: {jobResult.url}
                  </p>
                )}
              </div>
              <div className="p-6">
                <PreviewPane 
                  jobResult={jobResult}
                  currentJob={currentJob}
                />
              </div>
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}