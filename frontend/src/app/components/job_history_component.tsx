// frontend/src/components/JobHistory.tsx
'use client';

import { useEffect } from 'react';

interface Job {
  id: string;
  url: string;
  status: 'pending' | 'scraping' | 'processing' | 'generating' | 'completed' | 'failed';
  progress: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

interface JobHistoryProps {
  jobs: Job[];
  onSelectJob: (jobId: string) => void;
  onDeleteJob: (jobId: string) => void;
  onRefresh: () => void;
}

export default function JobHistory({ jobs, onSelectJob, onDeleteJob, onRefresh }: JobHistoryProps) {
  
  // Auto-refresh jobs on component mount
  useEffect(() => {
    onRefresh();
  }, [onRefresh]);

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      pending: { bg: 'bg-gray-100', text: 'text-gray-800', label: 'Pending' },
      scraping: { bg: 'bg-blue-100', text: 'text-blue-800', label: 'Scraping' },
      processing: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Processing' },
      generating: { bg: 'bg-purple-100', text: 'text-purple-800', label: 'Generating' },
      completed: { bg: 'bg-green-100', text: 'text-green-800', label: 'Completed' },
      failed: { bg: 'bg-red-100', text: 'text-red-800', label: 'Failed' },
    };

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;
    
    return (
      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
        {config.label}
      </span>
    );
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));

    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
    return `${Math.floor(diffInMinutes / 1440)}d ago`;
  };

  const getDomainFromUrl = (url: string) => {
    try {
      return new URL(url).hostname.replace('www.', '');
    } catch {
      return url;
    }
  };

  if (jobs.length === 0) {
    return (
      <div className="text-center py-6">
        <div className="text-gray-400 text-2xl mb-2">📋</div>
        <p className="text-sm text-gray-500">No jobs yet</p>
        <p className="text-xs text-gray-400 mt-1">
          Clone your first website to see history here
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Header with refresh button */}
      <div className="flex items-center justify-between">
        <p className="text-xs text-gray-500">
          {jobs.length} job{jobs.length !== 1 ? 's' : ''}
        </p>
        <button
          onClick={onRefresh}
          className="text-xs text-blue-600 hover:text-blue-800"
        >
          Refresh
        </button>
      </div>

      {/* Jobs list */}
      <div className="space-y-2 max-h-80 overflow-y-auto">
        {jobs.map((job) => (
          <div
            key={job.id}
            className="border rounded-lg p-3 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2 mb-1">
                  {getStatusBadge(job.status)}
                  <span className="text-xs text-gray-500">
                    {formatTimeAgo(job.created_at)}
                  </span>
                </div>
                <p className="text-sm font-medium text-gray-900 truncate">
                  {getDomainFromUrl(job.url)}
                </p>
                <p className="text-xs text-gray-500 truncate">
                  {job.url}
                </p>
              </div>
              
              <div className="flex items-center space-x-1 ml-2">
                {job.status === 'completed' && (
                  <button
                    onClick={() => onSelectJob(job.id)}
                    className="p-1 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded"
                    title="View Result"
                  >
                    👁️
                  </button>
                )}
                <button
                  onClick={() => onDeleteJob(job.id)}
                  className="p-1 text-red-600 hover:text-red-800 hover:bg-red-50 rounded"
                  title="Delete Job"
                >
                  🗑️
                </button>
              </div>
            </div>

            {/* Progress bar for active jobs */}
            {!['completed', 'failed'].includes(job.status) && (
              <div className="mb-2">
                <div className="w-full bg-gray-200 rounded-full h-1">
                  <div
                    className="bg-blue-500 h-1 rounded-full transition-all duration-500"
                    style={{ width: `${job.progress}%` }}
                  ></div>
                </div>
              </div>
            )}

            {/* Error message for failed jobs */}
            {job.status === 'failed' && job.error_message && (
              <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                {job.error_message.length > 100 
                  ? `${job.error_message.substring(0, 100)}...` 
                  : job.error_message
                }
              </div>
            )}

            {/* Action buttons for completed jobs */}
            {job.status === 'completed' && (
              <div className="mt-2 flex space-x-2">
                <button
                  onClick={() => onSelectJob(job.id)}
                  className="text-xs px-2 py-1 bg-blue-100 text-blue-700 hover:bg-blue-200 rounded"
                >
                  View Result
                </button>
                <button
                  onClick={() => window.open(`http://localhost:8000/result/${job.id}/preview`, '_blank')}
                  className="text-xs px-2 py-1 bg-gray-100 text-gray-700 hover:bg-gray-200 rounded"
                >
                  Open Preview
                </button>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Summary stats */}
      <div className="border-t pt-3 text-xs text-gray-500">
        <div className="flex justify-between">
          <span>Completed: {jobs.filter(j => j.status === 'completed').length}</span>
          <span>Failed: {jobs.filter(j => j.status === 'failed').length}</span>
          <span>Active: {jobs.filter(j => !['completed', 'failed'].includes(j.status)).length}</span>
        </div>
      </div>
    </div>
  );
}