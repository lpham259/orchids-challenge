// frontend/src/components/JobStatus.tsx
'use client';

interface Job {
  id: string;
  url: string;
  status: 'pending' | 'scraping' | 'processing' | 'generating' | 'completed' | 'failed';
  progress: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

interface JobStatusProps {
  job: Job;
}

export default function JobStatus({ job }: JobStatusProps) {
  const getStatusInfo = (status: string) => {
    switch (status) {
      case 'pending':
        return {
          label: 'Initializing',
          description: 'Preparing to scrape website...',
          color: 'bg-gray-200',
          textColor: 'text-gray-600',
          icon: '⏳'
        };
      case 'scraping':
        return {
          label: 'Scraping',
          description: 'Analyzing website structure and design...',
          color: 'bg-blue-200',
          textColor: 'text-blue-600',
          icon: '🔍'
        };
      case 'processing':
        return {
          label: 'Processing',
          description: 'Extracting design patterns and content...',
          color: 'bg-yellow-200',
          textColor: 'text-yellow-600',
          icon: '⚙️'
        };
      case 'generating':
        return {
          label: 'Generating',
          description: 'AI is creating HTML clone...',
          color: 'bg-purple-200',
          textColor: 'text-purple-600',
          icon: '🤖'
        };
      case 'completed':
        return {
          label: 'Completed',
          description: 'Website clone generated successfully!',
          color: 'bg-green-200',
          textColor: 'text-green-600',
          icon: '✅'
        };
      case 'failed':
        return {
          label: 'Failed',
          description: job.error_message || 'An error occurred during processing',
          color: 'bg-red-200',
          textColor: 'text-red-600',
          icon: '❌'
        };
      default:
        return {
          label: 'Unknown',
          description: 'Unknown status',
          color: 'bg-gray-200',
          textColor: 'text-gray-600',
          icon: '❓'
        };
    }
  };

  const statusInfo = getStatusInfo(job.status);
  const isActive = !['completed', 'failed'].includes(job.status);

  return (
    <div className="space-y-4">
      {/* Status Header */}
      <div className="flex items-center space-x-3">
        <span className="text-2xl">{statusInfo.icon}</span>
        <div className="flex-1">
          <h3 className={`font-semibold ${statusInfo.textColor}`}>
            {statusInfo.label}
          </h3>
          <p className="text-sm text-gray-600">{statusInfo.description}</p>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Progress</span>
          <span className={`font-medium ${statusInfo.textColor}`}>
            {job.progress}%
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-500 ease-out ${
              job.status === 'failed' ? 'bg-red-500' : 'bg-blue-500'
            }`}
            style={{ width: `${job.progress}%` }}
          ></div>
        </div>
      </div>

      {/* URL being processed */}
      <div className="text-xs text-gray-500 space-y-1">
        <p><strong>URL:</strong> {job.url}</p>
        <p><strong>Job ID:</strong> {job.id}</p>
        <p><strong>Started:</strong> {new Date(job.created_at).toLocaleTimeString()}</p>
      </div>

      {/* Loading animation for active jobs */}
      {isActive && (
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <div className="animate-pulse flex space-x-1">
            <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce"></div>
            <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
            <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
          </div>
          <span>Processing...</span>
        </div>
      )}

      {/* Error details for failed jobs */}
      {job.status === 'failed' && job.error_message && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md">
          <h4 className="text-sm font-medium text-red-800 mb-1">Error Details:</h4>
          <p className="text-sm text-red-700">{job.error_message}</p>
        </div>
      )}

      {/* Success message for completed jobs */}
      {job.status === 'completed' && (
        <div className="p-3 bg-green-50 border border-green-200 rounded-md">
          <p className="text-sm text-green-700">
            🎉 Your website clone is ready! Check the preview on the right.
          </p>
        </div>
      )}
    </div>
  );
}