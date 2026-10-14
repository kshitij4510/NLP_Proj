import { useState } from "react";
import { Link } from "react-router-dom";
import {
  Loader2, Eye, EyeOff, Copy, Check, ShieldCheck,
  FlaskConical, UserCheck, ArrowRight, Sparkles, Database
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useLogin } from "@/hooks/useAuth";
import axios from "axios";

interface DemoAccount {
  role: string;
  badge: string;
  badgeColor: string;
  name: string;
  email: string;
  pass: string;
  desc: string;
}

const DEMO_ACCOUNTS: DemoAccount[] = [
  {
    role: "Lead Researcher",
    badge: "Primary Owner",
    badgeColor: "bg-blue-500/10 text-blue-500 dark:text-blue-400 border-blue-500/20",
    name: "Dr. Alex Vance",
    email: "researcher@example.com",
    pass: "ResearchPass123",
    desc: "Full access to research plans, knowledge graphs, and reports.",
  },

];

export default function LoginPage() {
  const [email, setEmail] = useState("researcher@example.com");
  const [password, setPassword] = useState("ResearchPass123");
  const [showPassword, setShowPassword] = useState(false);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);


  const login = useLogin();


  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    login.mutate({ email, password });
  };

  const fillAndLogin = (accEmail: string, accPass: string) => {
    setEmail(accEmail);
    setPassword(accPass);
    login.mutate({ email: accEmail, password: accPass });
  };

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 1500);
  };

  const handleInstantGuestAccess = () => {
    fillAndLogin("researcher@example.com", "ResearchPass123");
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between relative overflow-hidden selection:bg-blue-600 selection:text-white">
      {/* Precision ambient background grid */}
      <div
        className="absolute inset-0 pointer-events-none opacity-20"
        style={{
          backgroundImage: `
            radial-gradient(circle at 50% 0%, rgba(37, 99, 235, 0.25) 0%, transparent 65%),
            linear-gradient(to right, rgba(255, 255, 255, 0.05) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255, 255, 255, 0.05) 1px, transparent 1px)
          `,
          backgroundSize: "100% 100%, 40px 40px, 40px 40px",
        }}
      />

      {/* Header bar */}
      <header className="relative z-10 border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="p-2 rounded-lg bg-blue-600/10 border border-blue-500/20 text-blue-400 group-hover:bg-blue-600/20 transition">
              <FlaskConical className="h-5 w-5" />
            </div>
            <div>
              <span className="font-bold text-base tracking-tight text-white">ResearchMind</span>
              <span className="text-xs text-slate-400 ml-2 font-mono">v1.2 Workbench</span>
            </div>
          </Link>

          <div className="flex items-center gap-3">
            <Badge variant="outline" className="text-[11px] font-mono border-slate-700 bg-slate-800/50 text-slate-300">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5 inline-block animate-pulse" />
              Research Workspace • SQLite Local
            </Badge>
            <Link to="/">
              <Button variant="ghost" size="sm" className="text-xs text-slate-300 hover:text-white">
                Back to Home
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="relative z-10 flex-1 flex items-center justify-center p-4 sm:p-6 my-6">
        <div className="w-full max-w-4xl grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
          
          {/* Left Column: Sign In Form (5 cols on lg) */}
          <Card className="lg:col-span-5 bg-slate-900/90 border-slate-800 text-slate-100 shadow-2xl flex flex-col justify-between">
            <div>
              <CardHeader className="pb-4">
                <div className="flex items-center gap-2 text-blue-400 text-xs font-semibold uppercase tracking-wider mb-1">
                  <ShieldCheck className="h-4 w-4" /> Secure Researcher Access
                </div>
                <CardTitle className="text-2xl font-bold tracking-tight text-white">
                  Sign In to Workspace
                </CardTitle>
                <CardDescription className="text-xs text-slate-400">
                  Access autonomous evidence trees, knowledge graphs, and experiment protocols.
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-4">
                <form onSubmit={handleSubmit} className="space-y-3.5">
                  <div className="space-y-1.5">
                    <label htmlFor="email" className="text-xs font-medium text-slate-300">
                      Workstation Email ID
                    </label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="researcher@example.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                      autoComplete="email"
                      className="bg-slate-950/70 border-slate-800 text-slate-100 placeholder:text-slate-500 text-xs h-9 focus-visible:ring-blue-500"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <label htmlFor="password" className="text-xs font-medium text-slate-300">
                        Password
                      </label>
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="text-[11px] text-slate-400 hover:text-slate-200 flex items-center gap-1"
                      >
                        {showPassword ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                        {showPassword ? "Hide" : "Show"}
                      </button>
                    </div>
                    <div className="relative">
                      <Input
                        id="password"
                        type={showPassword ? "text" : "password"}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        autoComplete="current-password"
                        className="bg-slate-950/70 border-slate-800 text-slate-100 text-xs h-9 pr-9 focus-visible:ring-blue-500"
                      />
                    </div>
                  </div>

                  {login.error && (
                    <div className="p-2.5 rounded-md bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs">
                      {axios.isAxiosError(login.error) && !login.error.response ? "Cannot reach the server. Start the backend and try again." : "Sign-in failed. Check your email and password."}
                    </div>
                  )}

                  <Button
                    type="submit"
                    className="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium h-9 text-xs transition shadow-lg shadow-blue-600/20"
                    disabled={login.isPending}
                  >
                    {login.isPending && <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />}
                    Sign in with Credentials
                  </Button>
                </form>

                <div className="relative my-4">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-slate-800" />
                  </div>
                  <div className="relative flex justify-center text-[10px] uppercase">
                    <span className="bg-slate-900 px-2 text-slate-500 font-semibold tracking-wider">
                      Quick access
                    </span>
                  </div>
                </div>

                {/* Instant Guest Demo Bypass */}
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleInstantGuestAccess}
                  className="w-full border-slate-700 bg-slate-950/50 hover:bg-slate-800 text-slate-200 text-xs h-9 gap-1.5"
                >
                  <Sparkles className="h-3.5 w-3.5 text-amber-400" />
                  Sign in to Research Workspace
                </Button>
              </CardContent>
            </div>

            <div className="px-6 pb-4 pt-2 border-t border-slate-800/60 text-center">
              <p className="text-[11px] text-slate-400">
                Evaluating offline system? All research data is stored locally in SQLite.
              </p>
            </div>
          </Card>

          {/* Right Column: Pre-Configured Test Accounts (7 cols on lg) */}
          <div className="lg:col-span-7 flex flex-col justify-between space-y-4">
            <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 shadow-xl backdrop-blur-sm">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <UserCheck className="h-4 w-4 text-emerald-400" />
                  <h3 className="font-semibold text-sm text-white">
                    1-Click Test Accounts & Credentials
                  </h3>
                </div>
                <span className="text-[11px] text-slate-400">
                  Click any account below to autofill & test:
                </span>
              </div>

              {/* Cards for each account */}
              <div className="space-y-3 mt-3.5">
                {DEMO_ACCOUNTS.map((acc, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-lg border border-slate-800 bg-slate-950/60 hover:border-slate-700 hover:bg-slate-950 transition flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold text-white">{acc.name}</span>
                        <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${acc.badgeColor}`}>
                          {acc.badge}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 leading-tight">
                        {acc.desc}
                      </p>
                      <div className="flex flex-wrap items-center gap-2 pt-1 font-mono text-[11px]">
                        <div className="flex items-center gap-1 bg-slate-900 border border-slate-800 px-2 py-0.5 rounded text-slate-300">
                          <span>{acc.email}</span>
                          <button
                            type="button"
                            onClick={() => handleCopy(acc.email, `e-${idx}`)}
                            className="text-slate-500 hover:text-slate-300 ml-1"
                            title="Copy Email"
                          >
                            {copiedKey === `e-${idx}` ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                          </button>
                        </div>
                        <div className="flex items-center gap-1 bg-slate-900 border border-slate-800 px-2 py-0.5 rounded text-slate-300">
                          <span>{acc.pass}</span>
                          <button
                            type="button"
                            onClick={() => handleCopy(acc.pass, `p-${idx}`)}
                            className="text-slate-500 hover:text-slate-300 ml-1"
                            title="Copy Password"
                          >
                            {copiedKey === `p-${idx}` ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                          </button>
                        </div>
                      </div>
                    </div>

                    <div className="flex sm:flex-col gap-2 w-full sm:w-auto">
                      <Button
                        type="button"
                        size="sm"
                        onClick={() => fillAndLogin(acc.email, acc.pass)}
                        className="flex-1 sm:flex-initial text-xs h-8 bg-slate-800 hover:bg-blue-600 hover:text-white border border-slate-700 text-slate-200 transition gap-1"
                      >
                        Auto-Sign In <ArrowRight className="h-3 w-3" />
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setEmail(acc.email);
                          setPassword(acc.pass);
                        }}
                        className="text-[11px] h-7 text-slate-400 hover:text-white"
                      >
                        Fill Only
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Architecture Assurance Note */}
            <div className="bg-slate-900/40 border border-slate-800/80 rounded-xl p-4 flex items-start gap-3">
              <Database className="h-4 w-4 text-blue-400 mt-0.5 shrink-0" />
              <div className="text-xs text-slate-400 leading-relaxed">
                <span className="font-semibold text-slate-200">Research provenance:</span> Inspect evidence and verification results before accepting generated claims. Passwords are salted with bcrypt, and session tokens use JSON Web Tokens with configurable rotation.
              </div>
            </div>

          </div>

        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 border-t border-slate-800/60 bg-slate-950/80 py-3 px-6 text-center text-xs text-slate-500">
        ResearchMind Autonomous NLP Scientist • Evidence-Grounded Literature Platform
      </footer>
    </div>
  );
}
