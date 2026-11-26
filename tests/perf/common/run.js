//
// Copyright 2026 The Dapr Authors
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//     http://www.apache.org/licenses/LICENSE-2.0
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

const scenarios = {
    t_1_5: { executor: 'shared-iterations', vus: 1, iterations: 5, maxDuration: '5m' },
    t_10_100: { executor: 'shared-iterations', vus: 10, iterations: 100, maxDuration: '15m' },
    t_30_300: { executor: 'shared-iterations', vus: 30, iterations: 300, maxDuration: '30m' },
};
const scenario = __ENV.SCENARIO || 't_1_5';
if (!scenarios[scenario]) throw new Error('Unknown scenario: ' + scenario);
const target = (__ENV.TARGET_URL || 'http://127.0.0.1:8001').replace(/\/$/, '');
const timeout = Number(__ENV.RUN_TIMEOUT_MS || 60000);
const poll = Number(__ENV.POLL_INTERVAL_MS || 250);
if (!(timeout > 0 && poll > 0)) throw new Error('Invalid timeout or poll interval');

const completion = new Trend('agent_completion_ms', true);
const failed = new Rate('agent_failed');
const timedOut = new Rate('agent_timeout');
const completed = new Counter('agent_completed');
const started = new Counter('agent_attempted');

export const options = {
    scenarios: { [scenario]: scenarios[scenario] },
    summaryTrendStats: ['avg', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
    thresholds: { agent_failed: ['rate==0'], agent_timeout: ['rate==0'], agent_completed: ['count>0'] },
};

export function run(task) {
    const begin = Date.now();
    started.add(1);
    let success = false;
    let expired = false;
    try {
        const response = http.post(target + '/agent/run', JSON.stringify({ task }), {
            headers: { 'Content-Type': 'application/json' }, timeout: Math.min(timeout, 10000) + 'ms',
            tags: { name: 'agent_start' },
        });
        if (!check(response, { 'start accepted': r => r.status >= 200 && r.status < 300 })) return;
        const id = response.json('instance_id');
        if (!id) return;
        while (Date.now() - begin < timeout) {
            const remaining = timeout - (Date.now() - begin);
            const status = http.get(target + '/agent/instances/' + encodeURIComponent(id), {
                timeout: Math.min(remaining, 10000) + 'ms', tags: { name: 'agent_poll' },
            });
            if (status.status === 200) {
                const state = String(status.json('runtime_status')).toUpperCase();
                if (state === 'COMPLETED') {
                    success = true;
                    completed.add(1);
                    completion.add(Date.now() - begin);
                    return;
                }
                if (['FAILED', 'TERMINATED', 'CANCELED', 'CANCELLED'].includes(state)) return;
            } else if (status.status !== 404) {
                return;
            }
            sleep(Math.min(poll, Math.max(0, timeout - (Date.now() - begin))) / 1000);
        }
        expired = true;
    } finally {
        failed.add(!success);
        timedOut.add(expired);
    }
}

export function handleSummary(data) {
    return { stdout: JSON.stringify(data, null, 2), [__ENV.SUMMARY_PATH || 'summary.json']: JSON.stringify(data, null, 2) };
}
