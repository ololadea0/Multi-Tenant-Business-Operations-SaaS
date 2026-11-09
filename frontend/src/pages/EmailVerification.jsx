import { useEffect, useState } from "react"
import { Link, useSearchParams } from "react-router"
import { useResendVerificationMutation, useVerifyEmailMutation } from "../app/store/api"

export function VerifyEmail() {
  const [params] = useSearchParams()
  const [verify, result] = useVerifyEmailMutation()
  useEffect(() => { const token = params.get("token"); if (token) verify({ token }) }, [params, verify])
  const status = result.isLoading ? "loading" : result.isSuccess ? "success" : result.error ? "error" : "missing"
  const content = { loading: ["Verifying your email", "We’re confirming your secure verification link."], success: ["Email verified successfully", "Your Daymark account is ready. Sign in to continue."], error: ["Verification link unavailable", result.error?.data?.detail || "This link may be invalid, expired, or already used."], missing: ["Verify your email", "Open the verification link from your Daymark email to activate your account."] }[status]
  return <main className={`auth-card email-verification-card verification-${status}`}><div className="verification-icon" aria-hidden="true">{status === "success" ? "✓" : status === "error" ? "!" : "✉"}</div><span className="eyebrow">ACCOUNT SECURITY</span><h1>{content[0]}</h1><p className="auth-copy">{content[1]}</p>{status === "loading" ? <div className="verification-progress"><i /></div> : <div className="verification-actions">{status === "success" ? <Link className="button button-dark full" to="/login">Continue to sign in</Link> : <Link className="button button-dark full" to="/verify-email/sent">Send a new verification email</Link>}<Link className="verification-back" to="/login">Back to sign in</Link></div>}</main>
}

export function VerificationSent() {
  const [params] = useSearchParams(); const email = params.get("email") || "your email address"; const [resend, result] = useResendVerificationMutation(); const [done, setDone] = useState(false)
  async function sendAgain() { try { await resend({ email }).unwrap(); setDone(true) } catch {} }
  return <main className="auth-card email-verification-card"><div className="verification-icon" aria-hidden="true">✉</div><span className="eyebrow">CHECK YOUR INBOX</span><h1>{done ? "Verification email sent" : "Verify your email"}</h1><p className="auth-copy">{done ? <>We sent another verification link to <strong>{email}</strong>.</> : <>We sent a secure verification link to <strong>{email}</strong>.</>}</p><div className="verification-help"><b>Can’t find it?</b><span>Check your spam or junk folder, then request another email.</span></div><button className="button button-dark full" disabled={result.isLoading || done} onClick={sendAgain}>{result.isLoading ? "Sending…" : done ? "Email sent" : "Resend verification email"}</button><Link className="verification-back" to="/login">Back to sign in</Link>{result.error && <p className="form-error" role="alert">{result.error?.data?.detail || "We could not send the email. Please try again."}</p>}</main>
}
