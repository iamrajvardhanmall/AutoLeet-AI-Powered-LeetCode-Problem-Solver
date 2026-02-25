/**
 * Spinner.js
 * A simple loading spinner with an optional message.
 */

import React from 'react';

function Spinner({ message = 'Processing... This may take a few minutes.' }) {
  return (
    <div className="spinner-wrapper">
      <div className="spinner"></div>
      <p>{message}</p>
    </div>
  );
}

export default Spinner;
