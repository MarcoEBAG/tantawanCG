import React from 'react'
import { Routes, Route, Link } from 'react-router-dom'
export default function App(){return (<div style={{maxWidth:960,margin:'0 auto',padding:16}}><header><h1>Asia Restaurant</h1><Link to='/'>Home</Link></header><Routes><Route path='/' element={<p>Hallo Welt</p>} /></Routes></div>)}
