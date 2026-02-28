import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import Navbar from "./components/layout/Navbar";
import UnauthorizedModalHost from "./components/auth/UnauthorizedModalHost";
import Home from "./pages/Home";
import ApiTest from "./pages/ApiTest";
import ClassroomBuilder from "./pages/ClassroomBuilder";
import TestGenerator from "./pages/TestGenerator";
import ClassEvaluation from "./pages/ClassEvaluation";
import LiveFeedCamera from "./pages/LiveFeedCamera";
import LiveFeedDisplay from "./pages/LiveFeedDisplay";
import Research from "./pages/Research";

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="min-h-screen bg-gray-50">
          <Navbar />
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/api-test" element={<ApiTest />} />
            <Route path="/classroom-builder" element={<ClassroomBuilder />} />
            <Route path="/test-generator" element={<TestGenerator />} />
            <Route path="/class-evaluation" element={<ClassEvaluation />} />
            <Route path="/livefeed/camera" element={<LiveFeedCamera />} />
            <Route path="/livefeed/display" element={<LiveFeedDisplay />} />
            <Route path="/research" element={<Research />} />
          </Routes>
          <UnauthorizedModalHost />
        </div>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
