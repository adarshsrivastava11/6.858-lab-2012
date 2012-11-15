var system = require('system');
var webpage = require('webpage');

var args = system.args;
if (args.length !== 2) {
    console.log('USAGE: phantomjs ' + args[0] + ' TEST');
    phantom.exit();
}

function runTest(test, cb) {
    var page = webpage.create();

    // Print uncaught JS errors to the console.
    page.onError = function(msg, trace) {
        console.log('  ' + 'JS error: ' + msg);
        trace.forEach(function(t) {
            console.log(
                '    ' + t.file + ': ' + t.line +
                    (t.function ? ' (in function "' + t.function + '")' : ''));
        });
    };

    page.onConsoleMessage = function(data) {
        console.log('  ' + 'console: ' + data);
    }

    page.onNavigationRequested = function(url, type, willNavigate, main) {
        if (cb === undefined) return;

        var prefix = 'http://localhost:8900/';
        if (url.substr(0, prefix.length) == prefix) {
            var rest = url.substr(prefix.length);
            var testBroken = 'test-broken';
            if (rest == 'test-ok')
                console.log('Sandbox: OK');
            else if (rest == 'test-bad')
                console.log('Sandbox: Escaped');
            else if (rest.substr(0, testBroken.length) == testBroken)
                console.log('Sandbox: Broken: ' + rest);
            else
                console.log('Unknown URL: ' + rest);

            page.close();
            setTimeout(cb);
            cb = undefined;
        }
    }

    // Set a timeout.
    setTimeout(function () {
        if (cb === undefined) return;
        console.log('TIMEOUT!');

        page.close();
        setTimeout(cb);
        cb = undefined;
    }, 30 * 1000);

    page.open(test);
}

runTest(args[1], function() {
    phantom.exit();
});
