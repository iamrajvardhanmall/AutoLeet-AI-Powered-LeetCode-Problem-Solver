/**
 * Navbar.js
 * Simple navigation bar shown on all pages.
 */

import React from 'react';
import { Link } from 'react-router-dom';

function Navbar() {
  return (
    <nav className="navbar">
      <h1>⚡ LeetCode Auto Solver</h1>
      <div>
        <Link to="/">Home</Link>
        <Link to="/history">History</Link>
      </div>
    </nav>
  );
}

export default Navbar;
