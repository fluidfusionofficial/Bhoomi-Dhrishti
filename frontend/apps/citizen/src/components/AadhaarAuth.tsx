'use client';

import * as React from 'react';
import {
  Shield,
  Fingerprint,
  CheckCircle2,
  Loader2,
  AlertCircle,
  ArrowRight,
  Lock,
} from 'lucide-react';
import { Button } from '@bhoomi/ui';

const STORAGE_KEY = 'bhoomi_citizen_aadhaar_auth';

interface AuthState {
  authenticated: boolean;
  maskedAadhaar: string;
  timestamp: number;
}

function getStoredAuth(): AuthState | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as AuthState;
    if (parsed.authenticated) return parsed;
  } catch {}
  return null;
}

function storeAuth(maskedAadhaar: string) {
  sessionStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      authenticated: true,
      maskedAadhaar,
      timestamp: Date.now(),
    })
  );
}

type Step = 'aadhaar' | 'otp' | 'verifying' | 'done';

export function AadhaarAuth({
  onAuthenticated,
}: {
  onAuthenticated: (maskedAadhaar: string) => void;
}) {
  const [step, setStep] = React.useState<Step>('aadhaar');
  const [aadhaar, setAadhaar] = React.useState('');
  const [otp, setOtp] = React.useState('');
  const [error, setError] = React.useState('');
  const otpRefs = React.useRef<(HTMLInputElement | null)[]>([]);

  const maskedAadhaar = aadhaar.length === 12
    ? `XXXX XXXX ${aadhaar.slice(8)}`
    : '';

  const formatAadhaarDisplay = (val: string) => {
    const digits = val.replace(/\D/g, '').slice(0, 12);
    return digits.replace(/(\d{4})(?=\d)/g, '$1 ');
  };

  const handleAadhaarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const digits = e.target.value.replace(/\D/g, '').slice(0, 12);
    setAadhaar(digits);
    setError('');
  };

  const handleSendOtp = () => {
    if (aadhaar.length !== 12) {
      setError('Please enter a valid 12-digit Aadhaar number');
      return;
    }
    setError('');
    setStep('otp');
    setTimeout(() => otpRefs.current[0]?.focus(), 100);
  };

  const handleOtpDigit = (index: number, value: string) => {
    const digit = value.replace(/\D/g, '').slice(-1);
    const newOtp = otp.slice(0, index) + digit + otp.slice(index + 1);
    setOtp(newOtp.slice(0, 6));
    setError('');

    if (digit && index < 5) {
      otpRefs.current[index + 1]?.focus();
    }
  };

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      otpRefs.current[index - 1]?.focus();
    }
  };

  const handleVerify = () => {
    if (otp.length !== 6) {
      setError('Please enter the 6-digit OTP');
      return;
    }
    setError('');
    setStep('verifying');

    setTimeout(() => {
      setStep('done');
      storeAuth(maskedAadhaar);
      setTimeout(() => onAuthenticated(maskedAadhaar), 800);
    }, 1500);
  };

  return (
    <div className="min-h-screen bg-[#F4F7FB] flex flex-col">
      {/* Tricolor strip */}
      <div className="w-full h-[3px] flex" role="presentation">
        <div className="flex-1 bg-[#FF9933]" />
        <div className="flex-1 bg-[#FFFFFF]" />
        <div className="flex-1 bg-[#138808]" />
      </div>

      {/* Header */}
      <header className="bg-[#14548C] text-white px-4 py-3">
        <div className="max-w-md mx-auto flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-[4px] bg-white text-[#14548C] flex items-center justify-center font-serif font-bold text-base">
            BD
          </div>
          <div>
            <div className="text-base font-bold tracking-tight leading-none">
              Bhoomi Dhrishti
            </div>
            <div className="text-[10px] text-[#E2ECF5] tracking-wide mt-0.5 opacity-90">
              Department of Land Resources (DoLR)
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 max-w-md w-full mx-auto p-4 flex flex-col items-center justify-center">
        <div className="w-full space-y-6">
          {/* Aadhaar Logo / Badge */}
          <div className="text-center space-y-3">
            <div className="w-16 h-16 mx-auto rounded-full bg-[#E2ECF5] flex items-center justify-center">
              <Fingerprint className="w-8 h-8 text-[#14548C]" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-[#16212E]">
                Citizen Authentication
              </h1>
              <p className="text-xs text-[#4A5B6E] mt-1">
                Verify your identity via Aadhaar e-KYC to access the Citizen Portal
              </p>
            </div>
          </div>

          {/* Card */}
          <div className="bg-white border border-[#DCE3EA] rounded-lg shadow-sm">
            {/* Step: Enter Aadhaar */}
            {step === 'aadhaar' && (
              <div className="p-5 space-y-4">
                <div className="flex items-center gap-2 text-xs text-[#4A5B6E]">
                  <Shield className="w-3.5 h-3.5 text-[#14548C]" />
                  <span>UIDAI Aadhaar e-KYC Authentication</span>
                </div>

                <div className="space-y-2">
                  <label
                    htmlFor="aadhaar-input"
                    className="text-sm font-semibold text-[#16212E]"
                  >
                    Aadhaar Number
                  </label>
                  <input
                    id="aadhaar-input"
                    type="text"
                    inputMode="numeric"
                    autoComplete="off"
                    placeholder="XXXX XXXX XXXX"
                    value={formatAadhaarDisplay(aadhaar)}
                    onChange={handleAadhaarChange}
                    className="w-full px-3 py-2.5 border border-[#DCE3EA] rounded-md text-center text-lg font-serif tracking-[0.25em] tabular-nums placeholder:tracking-[0.15em] placeholder:text-[#B0BDC9] focus:outline-none focus:ring-2 focus:ring-[#14548C]/30 focus:border-[#14548C] transition-colors"
                    maxLength={14}
                  />
                  <p className="text-[10px] text-[#4A5B6E]">
                    Enter your 12-digit Aadhaar number linked to your land records
                  </p>
                </div>

                {error && (
                  <div className="flex items-center gap-1.5 text-xs text-[#A32E2E]">
                    <AlertCircle className="w-3.5 h-3.5" />
                    <span>{error}</span>
                  </div>
                )}

                <Button
                  className="w-full justify-center"
                  size="default"
                  onClick={handleSendOtp}
                  disabled={aadhaar.length < 12}
                >
                  <span className="flex items-center gap-2">
                    Send OTP
                    <ArrowRight className="w-4 h-4" />
                  </span>
                </Button>

                <div className="flex items-center gap-1.5 text-[10px] text-[#4A5B6E] justify-center pt-1">
                  <Lock className="w-3 h-3" />
                  <span>
                    Your Aadhaar is encrypted & never stored. Governed by
                    Aadhaar Act 2016.
                  </span>
                </div>
              </div>
            )}

            {/* Step: Enter OTP */}
            {step === 'otp' && (
              <div className="p-5 space-y-4">
                <div className="flex items-center gap-2 text-xs text-[#4A5B6E]">
                  <Shield className="w-3.5 h-3.5 text-[#14548C]" />
                  <span>OTP sent to mobile linked with Aadhaar</span>
                </div>

                <div className="text-center">
                  <p className="text-xs text-[#4A5B6E]">
                    Aadhaar: <span className="font-serif font-semibold text-[#16212E]">{maskedAadhaar}</span>
                  </p>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-semibold text-[#16212E] text-center block">
                    Enter 6-digit OTP
                  </label>
                  <div className="flex justify-center gap-2">
                    {Array.from({ length: 6 }).map((_, i) => (
                      <input
                        key={i}
                        ref={(el) => { otpRefs.current[i] = el; }}
                        type="text"
                        inputMode="numeric"
                        autoComplete="one-time-code"
                        maxLength={1}
                        value={otp[i] || ''}
                        onChange={(e) => handleOtpDigit(i, e.target.value)}
                        onKeyDown={(e) => handleOtpKeyDown(i, e)}
                        className="w-10 h-12 border border-[#DCE3EA] rounded-md text-center text-lg font-serif tabular-nums focus:outline-none focus:ring-2 focus:ring-[#14548C]/30 focus:border-[#14548C] transition-colors"
                      />
                    ))}
                  </div>
                  <p className="text-[10px] text-[#4A5B6E] text-center">
                    For demo purposes, enter any 6 digits
                  </p>
                </div>

                {error && (
                  <div className="flex items-center gap-1.5 text-xs text-[#A32E2E] justify-center">
                    <AlertCircle className="w-3.5 h-3.5" />
                    <span>{error}</span>
                  </div>
                )}

                <Button
                  className="w-full justify-center"
                  size="default"
                  onClick={handleVerify}
                  disabled={otp.length < 6}
                >
                  Verify & Proceed
                </Button>

                <button
                  type="button"
                  onClick={() => { setStep('aadhaar'); setOtp(''); setError(''); }}
                  className="text-xs text-[#14548C] font-semibold hover:underline w-full text-center"
                >
                  Change Aadhaar Number
                </button>
              </div>
            )}

            {/* Step: Verifying */}
            {step === 'verifying' && (
              <div className="p-8 flex flex-col items-center gap-4">
                <Loader2 className="w-10 h-10 text-[#14548C] animate-spin" />
                <div className="text-center">
                  <p className="text-sm font-semibold text-[#16212E]">
                    Verifying with UIDAI...
                  </p>
                  <p className="text-xs text-[#4A5B6E] mt-1">
                    Authenticating {maskedAadhaar}
                  </p>
                </div>
              </div>
            )}

            {/* Step: Verified */}
            {step === 'done' && (
              <div className="p-8 flex flex-col items-center gap-4">
                <div className="w-14 h-14 rounded-full bg-[#E8F5E9] flex items-center justify-center">
                  <CheckCircle2 className="w-8 h-8 text-[#1E7B4D]" />
                </div>
                <div className="text-center">
                  <p className="text-sm font-semibold text-[#1E7B4D]">
                    Identity Verified
                  </p>
                  <p className="text-xs text-[#4A5B6E] mt-1">
                    Aadhaar e-KYC successful. Redirecting to portal...
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Government disclaimer */}
          <div className="text-center space-y-2">
            <p className="text-[10px] text-[#4A5B6E] leading-relaxed">
              This is a demonstration environment. No real Aadhaar validation is
              performed. In production, authentication is handled via UIDAI
              Aadhaar e-KYC APIs as per the Aadhaar (Targeted Delivery of
              Financial and Other Subsidies, Benefits and Services) Act, 2016.
            </p>
            <div className="flex items-center justify-center gap-3 text-[10px] text-[#4A5B6E]">
              <span>Ministry of Rural Development</span>
              <span className="w-1 h-1 rounded-full bg-[#DCE3EA]" />
              <span>Government of India</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export function useAadhaarAuth() {
  const [authState, setAuthState] = React.useState<AuthState | null>(null);
  const [checked, setChecked] = React.useState(false);

  React.useEffect(() => {
    setAuthState(getStoredAuth());
    setChecked(true);
  }, []);

  const authenticate = React.useCallback((maskedAadhaar: string) => {
    setAuthState({
      authenticated: true,
      maskedAadhaar,
      timestamp: Date.now(),
    });
  }, []);

  return {
    isAuthenticated: authState?.authenticated ?? false,
    maskedAadhaar: authState?.maskedAadhaar ?? '',
    checked,
    authenticate,
  };
}
