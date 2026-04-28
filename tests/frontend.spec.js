const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

function createClassList(initial = []) {
    const classes = new Set(initial);
    return {
        add: (...items) => items.forEach((item) => classes.add(item)),
        remove: (...items) => items.forEach((item) => classes.delete(item)),
        contains: (item) => classes.has(item),
        toString: () => Array.from(classes).join(' ')
    };
}

function createElement(id, options = {}) {
    return {
        id,
        value: options.value || '',
        innerHTML: options.innerHTML || '',
        innerText: options.innerText || '',
        classList: createClassList(options.classes || []),
        listeners: {},
        resetCalled: false,
        addEventListener(type, callback) {
            this.listeners[type] = callback;
        },
        reset() {
            this.resetCalled = true;
        },
        getContext() {
            return { canvasId: id };
        }
    };
}

function createHarness() {
    const elements = {};
    const fetchCalls = [];
    const alerts = [];
    const charts = [];
    const consoleErrors = [];
    let domReady = null;
    let nextFetch = async () => ({});

    const idsWithHiddenByDefault = new Set([
        'global-loader',
        'edit-modal',
        'group-edit-modal',
        'recommendation-modal',
        'leftover-container'
    ]);

    function ensureElement(id) {
        if (!elements[id]) {
            elements[id] = createElement(id, {
                classes: idsWithHiddenByDefault.has(id) ? ['hidden'] : []
            });
        }
        return elements[id];
    }

    const calculateButton = createElement('calculate-button', {
        innerHTML: '<i class="fa-solid fa-bolt mr-2"></i> Calculate'
    });

    const document = {
        addEventListener(type, callback) {
            if (type === 'DOMContentLoaded') {
                domReady = callback;
            }
        },
        getElementById(id) {
            return ensureElement(id);
        },
        querySelector(selector) {
            if (selector === 'button[onclick="calculateSmartBuy()"]') {
                return calculateButton;
            }
            return null;
        }
    };

    const sandbox = {
        document,
        window: {},
        console: {
            error: (...args) => consoleErrors.push(args),
            log: () => {}
        },
        fetch: async (url, options = {}) => {
            fetchCalls.push({ url, options });
            return {
                json: async () => nextFetch(url, options)
            };
        },
        confirm: () => true,
        alert: (message) => alerts.push(message),
        setTimeout: (callback) => {
            callback();
            return 0;
        },
        clearTimeout: () => {},
        Chart: function Chart(ctx, config) {
            charts.push({ ctx, config });
            this.destroy = () => {
                this.destroyed = true;
            };
        },
        Intl,
        Math,
        JSON,
        Promise,
        encodeURIComponent
    };

    const context = vm.createContext(sandbox);
    const scriptPath = path.join(__dirname, '..', 'frontend', 'app.js');
    const source = fs.readFileSync(scriptPath, 'utf8');
    vm.runInContext(source, context, { filename: 'app.js' });

    return {
        alerts,
        calculateButton,
        charts,
        consoleErrors,
        context,
        elements,
        fetchCalls,
        setFetchResponder(responder) {
            nextFetch = responder;
        },
        async triggerDomReady() {
            await domReady();
        },
        getElement: ensureElement
    };
}

async function runTest(name, fn) {
    try {
        await fn();
        process.stdout.write(`ok - ${name}\n`);
    } catch (error) {
        process.stderr.write(`not ok - ${name}\n${error.stack}\n`);
        process.exitCode = 1;
    }
}

async function main() {
    await runTest('DOMContentLoaded wires forms and fetches wallet', async () => {
        const harness = createHarness();
        harness.setFetchResponder(async () => ({
            assets: [],
            groups: {},
            exchange_rate: 5.0
        }));

        await harness.triggerDomReady();
        await Promise.resolve();
        await Promise.resolve();

        assert.strictEqual(harness.fetchCalls[0].url, '/api/wallet');
        assert.ok(harness.getElement('add-asset-form').listeners.submit);
        assert.ok(harness.getElement('edit-asset-form').listeners.submit);
        assert.ok(harness.getElement('group-edit-form').listeners.submit);
    });

    await runTest('add asset form uppercases ticker and parses comma decimals', async () => {
        const harness = createHarness();
        harness.setFetchResponder(async (url) => {
            if (url === '/api/wallet') {
                return { assets: [], groups: {}, exchange_rate: 5.0 };
            }
            return {};
        });

        await harness.triggerDomReady();

        harness.getElement('add-ticker').value = 'ivvb11';
        harness.getElement('add-qty').value = '10,5';
        harness.getElement('add-price').value = '20,3';
        harness.getElement('add-nota').value = '80';
        harness.getElement('add-tag').value = 'BR ETFs';

        const event = {
            preventDefault() {},
            target: harness.getElement('add-asset-form')
        };

        await harness.getElement('add-asset-form').listeners.submit(event);
        await Promise.resolve();

        const createCall = harness.fetchCalls.find((call) => call.url === '/api/wallet/asset');
        assert.ok(createCall);
        assert.strictEqual(createCall.options.method, 'POST');
        assert.deepStrictEqual(JSON.parse(createCall.options.body), {
            ticker: 'IVVB11',
            quantity: 10.5,
            average_price: 20.3,
            nota: 80,
            tag: 'BR ETFs'
        });
        assert.strictEqual(event.target.resetCalled, true);
    });

    await runTest('group edit form clears target when blank', async () => {
        const harness = createHarness();
        harness.setFetchResponder(async () => ({ assets: [], groups: {}, exchange_rate: 5.0 }));

        await harness.triggerDomReady();

        harness.getElement('group-edit-tag').value = 'Ações';
        harness.getElement('group-edit-target').value = ' ';

        await harness.getElement('group-edit-form').listeners.submit({
            preventDefault() {}
        });
        await Promise.resolve();

        const updateCall = harness.fetchCalls.find((call) => call.url === '/api/wallet/group/A%C3%A7%C3%B5es');
        assert.ok(updateCall);
        assert.strictEqual(updateCall.options.method, 'PUT');
        assert.deepStrictEqual(JSON.parse(updateCall.options.body), {
            target_percent: null
        });
    });

    await runTest('renderWallet normalizes wallet targets and unifies chart values', async () => {
        const harness = createHarness();
        vm.runInContext(`
            walletGroups = {
                "Ações": { target_percent: 30 },
                "US ETFs": { target_percent: 20 }
            };
        `, harness.context);

        harness.context.renderWallet([
            {
                ticker: 'PETR4.SA',
                quantity: 1,
                average_price: 100,
                current_price: 100,
                variation: 0,
                total_value: 100,
                nota: 100,
                tag: 'Ações',
                currency: 'BRL'
            },
            {
                ticker: 'VOO',
                quantity: 1,
                average_price: 20,
                current_price: 20,
                variation: 0,
                total_value: 20,
                nota: 100,
                tag: 'US ETFs',
                currency: 'USD'
            }
        ], 5.0);

        const html = harness.getElement('asset-groups-container').innerHTML;
        assert.ok(html.includes('/ 60.0%</span>'));
        assert.ok(html.includes('/ 40.0%</span>'));
        assert.deepStrictEqual(Array.from(harness.charts[0].config.data.datasets[0].data), [100, 100]);
    });

    await runTest('calculateSmartBuy warns on empty input and shows leftover output', async () => {
        const harness = createHarness();
        vm.runInContext('currentExchangeRate = 5.0;', harness.context);

        harness.getElement('invest-brl').value = '0';
        harness.getElement('invest-usd').value = '0';
        await harness.context.calculateSmartBuy();
        assert.deepStrictEqual(harness.alerts, ['Please enter an amount to invest.']);

        harness.alerts.length = 0;
        harness.getElement('invest-brl').value = '100';
        harness.getElement('invest-usd').value = '10';
        harness.setFetchResponder(async () => ({
            recommendations: [
                {
                    ticker: 'PETR4.SA',
                    tag: 'Ações',
                    currency: 'BRL',
                    current_value: 100,
                    value_to_buy: 50,
                    shares_to_buy: 5,
                    ideal_percent: 0.6
                },
                {
                    ticker: 'VOO',
                    tag: 'US ETFs',
                    currency: 'USD',
                    current_value: 20,
                    value_to_buy: 0,
                    shares_to_buy: 0,
                    ideal_percent: 0.4
                }
            ],
            leftover_brl: 5,
            leftover_usd: 1.5
        }));

        await harness.context.calculateSmartBuy();

        assert.strictEqual(harness.fetchCalls[harness.fetchCalls.length - 1].url, '/api/smart-buy');
        assert.ok(harness.getElement('recommendation-body').innerHTML.includes('PETR4.SA'));
        assert.ok(harness.getElement('leftover-amount').innerHTML.includes('R$'));
        assert.ok(harness.getElement('leftover-amount').innerHTML.includes('$'));
        assert.strictEqual(harness.getElement('recommendation-modal').classList.contains('show'), true);
        assert.strictEqual(harness.calculateButton.innerHTML, '<i class="fa-solid fa-bolt mr-2"></i> Calculate');
    });
}

main().catch((error) => {
    process.stderr.write(`${error.stack}\n`);
    process.exit(1);
});
