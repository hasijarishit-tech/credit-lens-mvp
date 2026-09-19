import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import IntakePage from "./pages/IntakePage";
import ReviewPage from "./pages/ReviewPage";
import MyScorePage from "./pages/msme/MyScorePage";
import ScoreResultPage from "./pages/msme/ScoreResultPage";
import PortfolioPage from "./pages/lender/PortfolioPage";
import DrilldownPage from "./pages/lender/DrilldownPage";

function ProtectedRoute({ children, role }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  if (role && user.role !== role) return <Navigate to={user.role === "lender" ? "/lender" : "/msme"} replace />;
  return children;
}

function RoleHome() {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  return <Navigate to={user.role === "lender" ? "/lender" : "/msme"} replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/" element={<RoleHome />} />

      <Route
        path="/msme"
        element={
          <ProtectedRoute role="msme">
            <MyScorePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/msme/upload"
        element={
          <ProtectedRoute role="msme">
            <IntakePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/msme/score/:recordId"
        element={
          <ProtectedRoute role="msme">
            <ScoreResultPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/lender"
        element={
          <ProtectedRoute role="lender">
            <PortfolioPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/lender/add"
        element={
          <ProtectedRoute role="lender">
            <IntakePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/lender/company/:companyId"
        element={
          <ProtectedRoute role="lender">
            <DrilldownPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/review/:recordId"
        element={
          <ProtectedRoute>
            <ReviewPage />
          </ProtectedRoute>
        }
      />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
