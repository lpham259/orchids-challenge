'use client';

import { useState } from 'react';

export default function Home() {
  const [url, setUrl] = useState('');
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/clone', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });

      const data = await response.json();
      setResult(data.html);
    } catch(error) {
      console.error('Error:', error);
      alert('Failed to clone website');
    } finally {
      setLoading(false)
    }
  };

  return (
    <div className='p-8'>
      <h1 className='text-2xl font-bold mb-4'>Website Cloner MVP</h1>

      <form onSubmit={handleSubmit} className='mb-8'>
        <input
          type='text'
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder='Enter website URL'
          className='border p-2 mr-2 w -64'
          required
        />
        <button
          type='submit'
          disabled={loading}
          className='bg-blue-500 text-white px-4 py-2 rounded'
        >
          {loading ? 'Cloning...' : 'Clone Website'}
        </button>
      </form>

      {result && (
        <div className='border p-4'>
          <h2 className='text-lg font-bold mb-2'>Result:</h2>
          <iframe
            srcDoc={result}
            className='w-full h-64 border'
            title='Cloned Website'
          />
        </div>
      )}
    </div>
  );
}