import test from 'node:test';
import assert from 'node:assert/strict';
import { isFreePlan, getPlanBillingSummary } from './billingLogic.js';

test('free plans are treated as no-charge and no payment schedule', () => {
    const plan = { key: 'launch', monthly_price: 0, annual_price: 0, currency: 'NGN' };
    const summary = getPlanBillingSummary(plan, { status: 'active', current_period_end: '2026-12-15T00:00:00Z' }, 'monthly');

    assert.equal(isFreePlan(plan), true);
    assert.equal(summary.amountLabel, 'Free');
    assert.equal(summary.nextPaymentLabel, 'No payment scheduled');
});

test('paid plans still show pricing and next payment date', () => {
    const plan = { key: 'growth', monthly_price: 15000, annual_price: 150000, currency: 'NGN' };
    const summary = getPlanBillingSummary(plan, { status: 'active', current_period_end: '2026-12-15T00:00:00Z' }, 'monthly');

    assert.equal(isFreePlan(plan), false);
    assert.equal(summary.amountLabel.includes('₦15,000'), true);
    assert.equal(summary.nextPaymentLabel.includes('15'), true);
});
