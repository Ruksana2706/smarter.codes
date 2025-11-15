import React, { useState } from 'react';
import Results from './Results';
import './searchform.css';

export default function SearchForm(){ 
  const [url,setUrl]=useState('');
  const [query,setQuery]=useState('');
  const [loading,setLoading]=useState(false);
  const [results,setResults]=useState(null);
  const [error,setError]=useState(null);

  const host=window.location.hostname;
  const BACKEND=`http://${host}:5000`;

  const ingestAndSearch=async(e)=>{
    e.preventDefault();
    setError(null); setResults(null); setLoading(true);
    try{
      // ingest first (upsert vectors)
      if(url){
        await fetch(`${BACKEND}/ingest`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({url})});
      }
      const r = await fetch(`${BACKEND}/search`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({query,k:10})});
      const data = await r.json();
      if(!r.ok) setError(data.error || 'Server error');
      else setResults(data.results);
    }catch(err){ setError(err.message); }
    setLoading(false);
  };

  return (
    <div className="search-wrapper">
      <h1>Website Content Search</h1>
      <label>Website URL</label>
      <div className="input-container">
        <span className="icon">🌐</span>
        <input className="input-field" placeholder="https://example.com" value={url} onChange={e=>setUrl(e.target.value)} />
      </div>

      <label>Search query</label>
      <form onSubmit={ingestAndSearch}>
        <div className="input-container">
          <span className="icon small">🔎</span>
          <input className="input-field" placeholder="AI, privacy, contact" value={query} onChange={e=>setQuery(e.target.value)} />
          <button className="btn-search" type="submit" disabled={loading}>{loading?'Searching...':'Search'}</button>
        </div>
      </form>

      {error && <div className="err">{error}</div>}
      {results && <Results results={results} />}
    </div>
  );
}
