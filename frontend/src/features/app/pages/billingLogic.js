export function isFreePlan(plan) {
    if (!plan) return false;
    if (plan.is_free === true) return true;

    const monthly = Number(plan.monthly_price ?? 0);
    const annual = Number(plan.annual_price ?? 0);
    return monthly === 0 && annual === 0;
}

export function money(value, currency = 'NGN') {
    return new Intl.NumberFormat('en-NG', {
        style: 'currency',
        currency,
        maximumFractionDigits: 0,
    }).format(Number(value || 0));
}

export function formatDate(value) {
    return value
        ? new Date(value).toLocaleDateString(undefined, {
            day: 'numeric',
            month: 'long',
            year: 'numeric',
        })
        : '—';
}

export function getPlanBillingSummary(plan, billing, interval) {
    const free = isFreePlan(plan);

    const amountLabel = free
        ? 'Free'
        : money(
            interval === 'annual'
                ? plan?.annual_price
                : plan?.monthly_price,
            plan?.currency,
        );

    const periodLabel = free
        ? 'No recurring charge'
        : `per ${interval === 'annual' ? 'year' : 'month'}`;

    const nextPaymentLabel = free || billing?.status === 'trialing'
        ? 'No payment scheduled'
        : formatDate(billing?.current_period_end);

    return {
        free,
        amountLabel,
        periodLabel,
        nextPaymentLabel,
    };
}
