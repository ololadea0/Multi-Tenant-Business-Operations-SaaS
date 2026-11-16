import { useEffect, useRef } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router";
import { useVerifyPaymentMutation } from "../../../app/store/api";

export function PaymentReturn() {
  const { organizationId } = useParams();
  const [params] = useSearchParams();
  const [verify, result] = useVerifyPaymentMutation();
  const navigate = useNavigate();
  const started = useRef(false);
  const reference = params.get("reference") || params.get("trxref");

  useEffect(() => {
    if (reference && !started.current) {
      started.current = true;
      verify({ organizationId, reference });
    }
  }, [organizationId, reference, verify]);

  if (!reference) {
    return (
      <main className="payment-return">
        <div>
          <h1>Payment reference missing</h1>
          <p>
            We could not verify this payment. No subscription changes were made.
          </p>
          <Link
            className="app-btn secondary"
            to={`/app/${organizationId}/settings/billing`}
          >
            Return to Billing
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="payment-return">
      <div>
        <span className="billing-kicker">PAYMENT VERIFICATION</span>
        <h1>
          {result.isLoading
            ? "Confirming your payment…"
            : result.isSuccess
              ? "Payment confirmed"
              : "Payment could not be confirmed"}
        </h1>
        <p>
          {result.isLoading
            ? "Please wait while Daymark confirms the transaction with Paystack."
            : result.isSuccess
              ? "Your subscription has been updated."
              : "The payment may still be processing. Your subscription was not activated from the browser redirect alone."}
        </p>
        {result.isSuccess ? (
          <button
            className="app-btn primary"
            onClick={() => navigate(`/app/${organizationId}/settings/billing`)}
          >
            Return to Billing
          </button>
        ) : result.isLoading ? null : (
          <Link
            className="app-btn secondary"
            to={`/app/${organizationId}/settings/billing`}
          >
            Return to Billing
          </Link>
        )}
      </div>
    </main>
  );
}
