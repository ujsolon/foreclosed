import React from "react";

function App() {
  return (
    <div style={{ fontFamily: "Arial", textAlign: "center", paddingTop: "40px" }}>
      <h1>Amplify Deployment Test</h1>
      <p>Environment: {process.env.REACT_APP_ENVIRONMENT}</p>
      <p>Status: ✅ Build and Deploy Successful!</p>
    </div>
  );
}

export default App;
