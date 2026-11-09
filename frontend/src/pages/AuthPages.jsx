import { useEffect, useState } from "react"
import { Link, useNavigate, useSearchParams } from "react-router"
import { Arrow, Logo } from "../components/Brand"
import { useDispatch } from "react-redux"
import { signedIn } from "../app/store/slices"
import { useAcceptInvitationMutation, useLoginMutation, useRegisterInvitationMutation, useRegisterMutation } from "../app/store/api"

function GoogleButton() {
  return (
    <a className="google-button" href={`${import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"}/api/auth/google`}>
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path
          fill="#4285F4"
          d="M21.6 12.2c0-.7-.1-1.5-.2-2.2H12v4.3h5.4a4.6 4.6 0 0 1-2 3v2.8h3.5c2-1.9 3.2-4.6 3.2-7.9Z"
        />
        <path
          fill="#34A853"
          d="M12 22c2.9 0 5.3-1 7-2.6l-3.5-2.8a6.3 6.3 0 0 1-9.4-3.3H2.5v2.8A10 10 0 0 0 12 22Z"
        />
        <path
          fill="#FBBC05"
          d="M6.1 13.3A6 6 0 0 1 6.1 9V6.2H2.5a10 10 0 0 0 0 9.9l3.6-2.8Z"
        />
        <path
          fill="#EA4335"
          d="M12 5.9c1.7 0 3.1.6 4.3 1.7l3.2-3.1A10.7 10.7 0 0 0 2.5 6.2L6.1 9A6 6 0 0 1 12 5.9Z"
        />
      </svg>
      Continue with Google
    </a>
  )
}

function AuthHeader({ title, copy }) {
  return (
    <>
      <div className="mobile-auth-logo">
        <Logo />
      </div>
      <h1>{title}</h1>
      <p className="auth-copy">{copy}</p>
    </>
  )
}

export function Login() {
  const navigate = useNavigate()
  const [showPassword, setShowPassword] = useState(false)
  const dispatch = useDispatch()
  const [login, { isLoading, error }] = useLoginMutation()
  const [acceptInvitation, acceptState] = useAcceptInvitationMutation()
  const [params] = useSearchParams()
  useEffect(() => {
    const hash = new URLSearchParams(window.location.hash.replace(/^#/, ""))
    const accessToken = hash.get("access_token")
    if (accessToken) {
      localStorage.setItem("daymark.accessToken", accessToken)
      dispatch(signedIn({ token: accessToken }))
      window.history.replaceState({}, "", "/login")
      navigate("/app/organizations", { replace: true })
    }
  }, [dispatch, navigate])
  async function submit(event) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    try {
      const result = await login({ email: form.get("email"), password: form.get("password") }).unwrap()
      localStorage.setItem("daymark.accessToken", result.access_token)
      dispatch(signedIn({ token: result.access_token }))
      const inviteToken = params.get("invite")
      if (inviteToken) {
        const invitation = await acceptInvitation({ token: inviteToken }).unwrap()
        navigate(`/app/${invitation.organization_id}/dashboard`)
      } else navigate("/app/organizations")
    } catch {}
  }
  return (
    <div className="auth-card">
      <AuthHeader
        title="Welcome back."
        copy="Sign in to continue to your Daymark workspace."
      />
      <GoogleButton />
      <div className="or">
        <span>or continue with email</span>
      </div>
      <form
        onSubmit={submit}
      >
        <label>
          Email address
          <input
            name="email"
            type="email"
            required
            autoComplete="email"
            placeholder="you@company.com"
          />
        </label>
        <label>
          <span>
            Password <Link to="/forgot-password">Forgot password?</Link>
          </span>
          <div className="password-field">
            <input
              name="password"
              type={showPassword ? "text" : "password"}
              required
              autoComplete="current-password"
              placeholder="Enter your password"
            />
            <button type="button" onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? "Hide password" : "Show password"}>{showPassword ? "Hide" : "Show"}</button>
          </div>
        </label>
        <button className="button button-dark full" type="submit">
          {isLoading ? "Logging in…" : "Log in"} <Arrow />
        </button>
        {error && <p className="form-error" role="alert"><strong>{error?.data?.detail?.code === "email_verification_required" ? "Verify your email first" : "Sign-in failed"}</strong><span>{error?.data?.detail?.code === "email_verification_required" ? <Link to={`/verify-email/sent?email=${encodeURIComponent(error.data.detail.email || "")}`}>Resend the verification email</Link> : "Unable to sign in. Check your email and password, then try again."}</span></p>}
        {acceptState.error && <p className="form-error" role="alert"><strong>Could not join the organization</strong><span>{acceptState.error?.data?.detail || "This invitation may be expired, already accepted, or sent to another email address."}</span></p>}
      </form>
      <p className="auth-switch">
        New to Daymark? <Link to="/register">Create an account</Link>
      </p>
    </div>
  )
}

export function Register() {
  const navigate = useNavigate()
  const [showPassword, setShowPassword] = useState(false)
  const [register, { isLoading, error }] = useRegisterMutation()
  async function submit(event) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    try { const email = form.get("email"); await register({ email, full_name: `${form.get("first_name")} ${form.get("last_name")}`, business_name: form.get("business_name"), password: form.get("password") }).unwrap(); navigate(`/verify-email/sent?email=${encodeURIComponent(email)}`) } catch {}
  }
  return (
    <div className="auth-card register-card">
      <AuthHeader
        title="Create your account."
        copy="Start setting up your Daymark workspace."
      />
      <GoogleButton />
      <div className="or">
        <span>or continue with email</span>
      </div>
      <form
        onSubmit={submit}
      >
        <div className="field-row">
          <label>
            First name
            <input name="first_name" required autoComplete="given-name" />
          </label>
          <label>
            Last name
            <input name="last_name" required autoComplete="family-name" />
          </label>
        </div>
        <label>
          Work email
          <input
            name="email"
            type="email"
            required
            autoComplete="email"
            placeholder="you@company.com"
          />
        </label>
          <label>
          Business name <span className="optional-label">(optional)</span>
          <input name="business_name" autoComplete="organization" />
        </label>
        <label>
          Password
          <div className="password-field">
            <input
              name="password"
              type={showPassword ? "text" : "password"}
              required
              minLength={8}
              autoComplete="new-password"
              placeholder="At least 8 characters"
            />
            <button type="button" onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? "Hide password" : "Show password"}>{showPassword ? "Hide" : "Show"}</button>
          </div>
        </label>
        <label className="check-label">
          <input type="checkbox" required />
          <span>
            I agree to the <Link to="/terms">Terms</Link> and{" "}
            <Link to="/privacy">Privacy Policy</Link>.
          </span>
        </label>
        <button className="button button-dark full" type="submit">
          {isLoading ? "Creating account…" : "Create account"} <Arrow />
        </button>
        {error && <p className="form-error" role="alert"><strong>Account creation failed</strong><span>Check the form details and try again.</span></p>}
      </form>
      <p className="auth-switch">
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </div>
  )
}

export function InvitationRegister() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [showPassword, setShowPassword] = useState(false)
  const [registerInvitation, { isLoading, error }] = useRegisterInvitationMutation()
  async function submit(event) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    try {
      const result = await registerInvitation({ token: params.get("token"), email: form.get("email"), full_name: `${form.get("first_name")} ${form.get("last_name")}`, password: form.get("password") }).unwrap()
      localStorage.setItem("daymark.accessToken", result.access_token)
      navigate(`/app/${result.organization_id}/dashboard`)
    } catch {}
  }
  return <div className="auth-card register-card"><AuthHeader title="Join your organization." copy="Create your Daymark account to accept this invitation." /><form onSubmit={submit}><div className="field-row"><label>First name *<input name="first_name" required autoComplete="given-name" /></label><label>Last name *<input name="last_name" required autoComplete="family-name" /></label></div><label>Invited email *<input name="email" type="email" required autoComplete="email" /></label><label>Password *<div className="password-field"><input name="password" type={showPassword ? "text" : "password"} required minLength={8} autoComplete="new-password" /><button type="button" onClick={() => setShowPassword(!showPassword)}>{showPassword ? "Hide" : "Show"}</button></div></label><button className="button button-dark full" disabled={isLoading}>{isLoading ? "Joining…" : "Join organization"}</button>{error && <p className="form-error" role="alert"><strong>Invitation could not be accepted</strong><span>{error?.data?.detail || "Check that the invitation link is valid and has not expired."}</span></p>}</form><p className="auth-switch">Already have an account? <Link to={`/login?invite=${encodeURIComponent(params.get("token") || "")}`}>Log in to accept the invitation</Link></p></div>
}

export function ForgotPassword() {
  const [sent, setSent] = useState(false)
  return (
    <div className="auth-card narrow">
      {sent ? (
        <>
          <AuthHeader
            title="Check your email."
            copy="If an account exists for that address, we sent a password reset link."
          />
          <Link className="button button-dark full" to="/login">
            Return to log in <Arrow />
          </Link>
        </>
      ) : (
        <>
          <AuthHeader
            title="Reset your password."
            copy="Enter your account email and we’ll send you a secure reset link."
          />
          <form
            onSubmit={(e) => {
              e.preventDefault()
              setSent(true)
            }}
          >
            <label>
              Email address
              <input
                type="email"
                required
                autoComplete="email"
                placeholder="you@company.com"
              />
            </label>
            <button className="button button-dark full" type="submit">
              Send reset link <Arrow />
            </button>
          </form>
          <p className="auth-switch">
            <Link to="/login">← Back to log in</Link>
          </p>
        </>
      )}
    </div>
  )
}

export function ResetPassword() {
  return (
    <div className="auth-card narrow">
      <AuthHeader
        title="Choose a new password."
        copy="Use at least 8 characters and avoid a password you use elsewhere."
      />
      <form onSubmit={prevent}>
        <label>
          New password
          <input
            type="password"
            required
            minLength={8}
            autoComplete="new-password"
          />
        </label>
        <label>
          Confirm new password
          <input
            type="password"
            required
            minLength={8}
            autoComplete="new-password"
          />
        </label>
        <button className="button button-dark full" type="submit">
          Update password <Arrow />
        </button>
      </form>
    </div>
  )
}

function prevent(e) {
  e.preventDefault()
}
