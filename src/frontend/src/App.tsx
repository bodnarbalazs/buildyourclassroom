import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import Navbar from "./components/layout/Navbar";
import UnauthorizedModalHost from "./components/auth/UnauthorizedModalHost";
import Home from "./pages/Home";
import ApiTest from "./pages/ApiTest";
import ClassroomBuilder from "./pages/ClassroomBuilder";

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
          </Routes>
          <UnauthorizedModalHost />
        </div>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
