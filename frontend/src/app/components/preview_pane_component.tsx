import { useState } from 'react';

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

interface PreviewPaneProps {
  jobResult: JobResult | null;
  currentJob: Job | null;
}

export default function EnhancedPreviewPane({ jobResult, currentJob }: PreviewPaneProps) {
  const [previewMode, setPreviewMode] = useState<'iframe' | 'code'>('iframe');
  const [iframeKey, setIframeKey] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const handleRefreshPreview = () => {
    setIframeKey(prev => prev + 1);
  };

  const handleDownloadHTML = () => {
    if (!jobResult?.generated_html) return;

    const blob = new Blob([jobResult.generated_html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cloned-website-${jobResult.job_id}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleCopyHTML = async () => {
    if (!jobResult?.generated_html) return;

    try {
      await navigator.clipboard.writeText(jobResult.generated_html);
      alert('HTML copied to clipboard!');
    } catch (err) {
      console.error('Failed to copy HTML:', err);
      alert('Failed to copy HTML to clipboard');
    }
  };

  const handleOpenInNewTab = () => {
    if (!jobResult?.job_id) return;
    const previewUrl = `http://localhost:8000/result/${jobResult.job_id}/preview`;
    window.open(previewUrl, '_blank');
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  const forceScrollableHTML = (html: string): string => {
    // Much more aggressive CSS to force scrolling
    const scrollingCSS = `
      <style>
        /* Nuclear option - force everything to be scrollable */
        html, body {
          overflow: auto !important;
          overflow-x: auto !important;
          overflow-y: auto !important;
          height: auto !important;
          min-height: 100vh !important;
          max-height: none !important;
          position: static !important;
          margin: 0 !important;
        }
        
        /* Override ALL elements that might block scrolling */
        *, *:before, *:after {
          overflow: visible !important;
          overflow-x: visible !important;
          overflow-y: visible !important;
          height: auto !important;
          min-height: auto !important;
          max-height: none !important;
          position: static !important;
        }
        
        /* Specific overrides for common problematic selectors */
        .hero-section,
        [class*="hero"],
        [class*="container"],
        [class*="wrapper"],
        main,
        section,
        div {
          overflow: visible !important;
          height: auto !important;
          min-height: auto !important;
          max-height: none !important;
          position: relative !important;
        }
        
        /* Force the page to be tall enough to scroll */
        body {
          min-height: 200vh !important;
          padding-bottom: 100px !important;
        }
        
        /* Remove any fixed positioning that might interfere */
        [style*="position: fixed"],
        [style*="position:fixed"] {
          position: relative !important;
        }
      </style>
    `;
    
    // More robust insertion logic
    if (html.includes('</head>')) {
      return html.replace('</head>', scrollingCSS + '</head>');
    } else if (html.includes('<head>')) {
      return html.replace('<head>', '<head>' + scrollingCSS);
    } else if (html.includes('<body')) {
      return html.replace('<body', scrollingCSS + '<body');
    } else {
      // Nuclear option - wrap everything
      return `<!DOCTYPE html><html><head>${scrollingCSS}</head><body style="min-height: 200vh; padding: 20px;">${html}</body></html>`;
    }
  };

  // Show loading state when job is in progress
  if (currentJob && currentJob.status !== 'completed') {
    return (
      <div className="h-96 flex items-center justify-center bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <div>
            <p className="text-lg font-medium text-gray-900">
              {currentJob.status === 'scraping' && 'Analyzing Website...'}
              {currentJob.status === 'processing' && 'Processing Design...'}
              {currentJob.status === 'generating' && 'Generating HTML...'}
              {currentJob.status === 'pending' && 'Initializing...'}
            </p>
            <p className="text-sm text-gray-600 mt-2">
              This may take a few minutes
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Show empty state when no job result
  if (!jobResult) {
    return (
      <div className="h-96 flex items-center justify-center bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <div className="text-center space-y-2">
          <div className="text-4xl mb-4">🌐</div>
          <h3 className="text-lg font-medium text-gray-900">No Preview Available</h3>
          <p className="text-sm text-gray-600">
            Enter a URL and start cloning to see the generated website here
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${isFullscreen ? 'fixed inset-0 z-50 bg-white p-4' : ''}`}>
      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setPreviewMode('iframe')}
            className={`px-3 py-1 text-sm rounded-md ${
              previewMode === 'iframe'
                ? 'bg-blue-100 text-blue-700'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Preview
          </button>
          <button
            onClick={() => setPreviewMode('code')}
            className={`px-3 py-1 text-sm rounded-md ${
              previewMode === 'code'
                ? 'bg-blue-100 text-blue-700'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            HTML Code
          </button>
        </div>

        <div className="flex items-center space-x-2">
          {previewMode === 'iframe' && (
            <>
              <button
                onClick={handleRefreshPreview}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md"
                title="Refresh Preview"
              >
                🔄
              </button>
              <button
                onClick={toggleFullscreen}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md"
                title={isFullscreen ? "Exit Fullscreen" : "Enter Fullscreen"}
              >
                {isFullscreen ? "⤵️" : "⤴️"}
              </button>
              <button
                onClick={handleOpenInNewTab}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md"
                title="Open in New Tab"
              >
                🔗
              </button>
            </>
          )}
          {previewMode === 'code' && (
            <button
              onClick={handleCopyHTML}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md"
              title="Copy HTML"
            >
              📋
            </button>
          )}
          <button
            onClick={handleDownloadHTML}
            className="px-3 py-1 text-sm bg-green-100 text-green-700 hover:bg-green-200 rounded-md"
          >
            Download HTML
          </button>
          {isFullscreen && (
            <button
              onClick={toggleFullscreen}
              className="px-3 py-1 text-sm bg-red-100 text-red-700 hover:bg-red-200 rounded-md"
            >
              ✕ Close
            </button>
          )}
        </div>
      </div>

      {/* Preview Content */}
      {previewMode === 'iframe' ? (
        <div className="border rounded-lg overflow-hidden">
          <div className="bg-gray-100 px-4 py-2 text-sm text-gray-600 border-b flex justify-between items-center">
            <div>
              <span className="font-medium">Preview:</span> {jobResult.url}
            </div>
          </div>
          <div className="relative">
            <iframe
              key={iframeKey}
              srcDoc={forceScrollableHTML(jobResult.generated_html)}
              className={`w-full border-0 ${
                isFullscreen 
                  ? 'h-[calc(100vh-120px)]' 
                  : 'h-[600px]'
              }`}
              title="Website Preview"
            />
            {/* Loading overlay */}
            <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center opacity-0 transition-opacity duration-300">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
          </div>
        </div>
      ) : (
        <div className="border rounded-lg overflow-hidden">
          <div className="bg-gray-100 px-4 py-2 text-sm text-gray-600 border-b flex justify-between items-center">
            <span><span className="font-medium">Generated HTML</span> ({jobResult.generated_html.length} characters)</span>
            <span className="text-xs">
              Generated at {new Date(jobResult.completed_at).toLocaleString()}
            </span>
          </div>
          <div className="relative">
            <pre className={`overflow-auto p-4 text-xs bg-gray-50 text-gray-800 font-mono ${
              isFullscreen 
                ? 'h-[calc(100vh-120px)]'
                : 'h-[600px]'
            }`}>
              <code>{jobResult.generated_html}</code>
            </pre>
          </div>
        </div>
      )}

      {/* Metadata */}
      {!isFullscreen && jobResult.scraped_data && (
        <div className="text-xs text-gray-500 space-y-1 p-3 bg-gray-50 rounded-lg">
          <h4 className="font-medium text-gray-700 mb-2">Scraped Data Summary:</h4>
          {jobResult.scraped_data.title && (
            <p><strong>Title:</strong> {jobResult.scraped_data.title}</p>
          )}
          {jobResult.scraped_data.color_palette && (
            <div className="flex items-center space-x-2">
              <strong>Colors:</strong>
              <div className="flex space-x-1">
                {jobResult.scraped_data.color_palette.slice(0, 5).map((color: string, index: number) => (
                  <div
                    key={index}
                    className="w-4 h-4 rounded border border-gray-300"
                    style={{ backgroundColor: color }}
                    title={color}
                  />
                ))}
              </div>
            </div>
          )}
          {jobResult.scraped_data.fonts && (
            <p><strong>Fonts:</strong> {jobResult.scraped_data.fonts.slice(0, 3).join(', ')}</p>
          )}
          <p><strong>Processing Time:</strong> {Math.round((new Date(jobResult.completed_at).getTime() - new Date(jobResult.created_at).getTime()) / 1000)}s</p>
        </div>
      )}
    </div>
  );
}