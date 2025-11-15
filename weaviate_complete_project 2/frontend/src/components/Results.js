import React,{useState} from 'react';
import './results.css';

export default function Results({results}){
  if(!results || results.length===0) return <div>No matches found.</div>;
  return (
    <div className="results-wrap">
      <h2>Search Results</h2>
      {results.map((r,i)=> <Card key={i} item={r} />)}
    </div>
  );
}

function Card({item}){
  const [open,setOpen]=useState(false);
  const preview = item.text.length>400 ? item.text.slice(0,400)+'...' : item.text;
  return (
    <div className="card">
      <div className="card-head">
        <div className="card-preview">{preview}</div>
        <div className="badge">{item.score}% match</div>
      </div>
      <div className="path">Path: <span>{item.path}</span></div>
      <div className="viewhtml"><button className="btn-view" onClick={()=>setOpen(!open)}>{open?'Hide HTML':'<> View HTML'}</button></div>
      {open && <pre className="code">{item.html}</pre>}
    </div>
  );
}
