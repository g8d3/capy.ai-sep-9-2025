import { BrowserRouter, Route, Routes, Link } from "react-router-dom";
import ProtectedRoute from "./auth/ProtectedRoute";
import { AuthProvider, useAuth } from "./auth/useAuth";
import Login from "./pages/Login";
import Register from "./pages/Register";
import NewBacktest from "./pages/NewBacktest";
import Backtests from "./pages/Backtests";
import BacktestResult from "./pages/BacktestResult";

function Navbar() {
  const { user, logout } = useAuth();
  return (
    <div className="w-full border-b bg-background">
      <div className="container flex h-14 items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to="/" className="font-semibold">Crypto Backtester</Link>
          {user && (
            <>
              <Link to="/backtests">Backtests</Link>
              <Link to="/new">New Backtest</Link>
            </>
          )}
        </div>
        <div className="flex items-center gap-4">
          {user ? (
            <>
              <span className="text-sm text-muted-foreground">{user.email}</span>
              <button className="text-sm underline" onClick={logout}>Logout</button>
            </>
          ) : (
            <>
              <Link to="/login">Login</Link>
              <Link to="/register">Register</Link>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Navbar />
        <div className="container py-6">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            <Route element={<ProtectedRoute />}>
              <Route path="/" element={<Backtests />} />
              <Route path="/backtests" element={<Backtests />} />
              <Route path="/new" element={<NewBacktest />} />
              <Route path="/backtests/:id" element={<BacktestResult />} />
            </Route>
          </Routes>
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}
