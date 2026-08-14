/**
 * Repeatable check of pr-hygiene.yml's inline `github-script` logic: the RFC-threshold
 * file signals, the added-files-only rule, the RFC-declaration scan of the PR body, and
 * the guiding-comment builder (marker, idempotence predicate, body).
 *
 * pr-hygiene.yml has no checkout step (by design -- it runs on `pull_request_target` and
 * deliberately never checks out pull-request code, see the workflow's own header comment),
 * so its inline script can't require() shared logic live. The constants and functions
 * below are byte-identical mirrors of what's actually inline in pr-hygiene.yml's
 * "Check RFC disclosure" step, kept here purely so a plain Node test can exercise them;
 * this file is never loaded by the real workflow.
 *
 * Run: node .github/workflows/tests/pr-hygiene.test.js
 */
'use strict';

var assert = require('assert');

// --- mirror of pr-hygiene.yml's SIGNALS table (verbatim) --------------------------
// Copied from the "Check RFC disclosure" step.
const SIGNALS = [
  {
    test: (f) => /^great_expectations\/compatibility\/[a-z0-9_]+\.py$/.test(f),
    describe: 'a new compatibility module (a new optional third-party dependency)',
  },
  {
    test: (f) => /^great_expectations\/datasource\/fluent\/[a-z0-9_]+_datasource\.py$/.test(f),
    describe: 'a new fluent datasource',
  },
  {
    test: (f) => /^reqs\/requirements-dev-[a-z0-9-]+\.txt$/.test(f),
    describe: 'a new backend requirements file',
  },
];
// --- end mirror -------------------------------------------------------------------

// --- mirror of pr-hygiene.yml's signal-scan loop (verbatim) -----------------------
// Copied from the "Check RFC disclosure" step; wrapped in a function so the test can
// call it, the loop body itself is unchanged. `files` is the paginated
// `pulls.listFiles` array.
function computeTripped(files) {
  const tripped = [];
  for (const file of files) {
    if (file.status !== 'added') continue;
    for (const signal of SIGNALS) {
      if (signal.test(file.filename)) {
        tripped.push(`${file.filename} — ${signal.describe}`);
      }
    }
  }
  return tripped;
}
// --- end mirror -------------------------------------------------------------------

// --- mirror of pr-hygiene.yml's DECLARED table (verbatim) -------------------------
const DECLARED = [
  /^\s*>?\s*(?:[-*+]|\d+[.)])?\s*[`*_]*RFC[`*_]*\s*:/im,
  /^\s*>?\s*(?:[-*+]|\d+[.)])?\s*[`*_]*No RFC needed[`*_]*\s*:/im,
];
// --- end mirror -------------------------------------------------------------------

// --- mirror of pr-hygiene.yml's declaration scan and verdict (verbatim) -----------
// Copied from the "Check RFC disclosure" step; wrapped in a function so the test can
// call it. `pr` is the pull-request payload.
function evaluateRfc(tripped, pr) {
  let rfcFailed = false;
  const failures = [];
  if (tripped.length > 0) {
    // Strip HTML comments before scanning: the pull-request template's own guidance
    // lives in a comment and contains the literal token we're looking for, so scanning
    // the raw body would pass every unedited template.
    const body = (pr.body || '').replace(/<!--[\s\S]*?-->/g, '');
    const declared = DECLARED.some((re) => re.test(body));

    if (!declared) {
      rfcFailed = true;
      failures.push(
        'This change looks like it may cross the RFC threshold, but the description ' +
        "doesn't say whether an RFC applies.\n" +
        tripped.map((t) => `  - ${t}`).join('\n')
      );
    }
  }
  return { rfcFailed, failures };
}
// --- end mirror -------------------------------------------------------------------

// --- mirror of pr-hygiene.yml's guiding-comment marker and idempotence predicate
// (verbatim) -----------------------------------------------------------------------
const MARKER = '<!-- pr-hygiene:rfc-threshold -->';

function alreadyCommented(comments) {
  return comments.some((c) => c.body && c.body.includes(MARKER));
}
// --- end mirror -------------------------------------------------------------------

// --- mirror of pr-hygiene.yml's guiding-comment body transform (verbatim) ---------
// Copied from the `if (rfcFailed)` branch of the "Check RFC disclosure" step; wrapped
// in a function so the test can call it, the array itself is unchanged.
function buildCommentBody(pr, tripped) {
  const body = [
    `Thanks for the pull request, @${pr.user.login}! 👋`,
    '',
    'This change touches files that usually mean new data source or execution engine ' +
      'support:',
    '',
    ...tripped.map((t) => `- \`${t}\``),
    '',
    'Changes like that need an [RFC]' +
      '(https://github.com/fivetran/great_expectations/blob/develop/CONTRIBUTING.md#requesting-comment-on-larger-changes) ' +
      'agreed before implementation, so the design discussion happens before you invest ' +
      'in code. Sorry if this arrives after the fact — the check is here so the next ' +
      'contributor finds out at the right moment.',
    '',
    '**To resolve this check**, add one of these lines to the pull-request description:',
    '',
    '- `RFC: <link to the accepted discussion>` — if an RFC exists or you open one now',
    '- `No RFC needed: <reason>` — if this isn\'t actually new backend support ' +
      '(for example, a bug fix that happens to touch these paths)',
    '',
    'Either answer satisfies the check. A maintainer will pick it up from there.',
    '',
    MARKER,
  ].join('\n');

  return body;
}
// --- end mirror -------------------------------------------------------------------

var failures = 0;
var passed = 0;
function check(name, fn) {
  try { fn(); passed++; console.log('  ok   - ' + name); }
  catch (e) { failures++; console.log('  FAIL - ' + name + '\n         ' + e.message); }
}

function added(filename) {
  return { filename: filename, status: 'added' };
}

// One tripping added file, reused by the body-scan cases so they exercise the real
// `tripped.length > 0` path rather than the declaration regexes in isolation.
var TRIPPING_FILE = 'great_expectations/compatibility/duckdb.py';
function trippedOnce() {
  return computeTripped([added(TRIPPING_FILE)]);
}

// The pull-request template's guidance comment: it contains the literal `RFC:` token,
// which is exactly why the body is comment-stripped before scanning.
var TEMPLATE_COMMENT =
  '<!--\n' +
  'If this change adds new backend support, add one of:\n' +
  '  RFC: <link to the accepted discussion>\n' +
  '  No RFC needed: <reason>\n' +
  '-->\n';

console.log('signal 1: new compatibility module');
(function () {
  check('a flat lowercase module under compatibility/ trips', function () {
    assert.deepStrictEqual(
      computeTripped([added('great_expectations/compatibility/duckdb.py')]).length, 1);
    assert.deepStrictEqual(
      computeTripped([added('great_expectations/compatibility/spark_connect.py')]).length, 1);
  });
  check('a nested subdirectory does not trip', function () {
    assert.deepStrictEqual(
      computeTripped([added('great_expectations/compatibility/vendor/duckdb.py')]), []);
  });
  check('an uppercase module name does not trip', function () {
    assert.deepStrictEqual(
      computeTripped([added('great_expectations/compatibility/DuckDB.py')]), []);
  });
  check('a hyphenated module name does not trip', function () {
    assert.deepStrictEqual(
      computeTripped([added('great_expectations/compatibility/duck-db.py')]), []);
  });
  check('a non-.py file does not trip', function () {
    assert.deepStrictEqual(
      computeTripped([added('great_expectations/compatibility/duckdb.pyi')]), []);
  });
  check('the same path under tests/ does not trip (pattern is anchored)', function () {
    assert.deepStrictEqual(
      computeTripped([added('tests/great_expectations/compatibility/duckdb.py')]), []);
  });
  check('the tripped entry is exactly "<filename> — <describe>"', function () {
    var t = computeTripped([added('great_expectations/compatibility/duckdb.py')]);
    assert.strictEqual(
      t[0],
      'great_expectations/compatibility/duckdb.py — ' +
        'a new compatibility module (a new optional third-party dependency)');
  });
})();

console.log('signal 2: new fluent datasource');
(function () {
  check('a *_datasource.py directly under fluent/ trips', function () {
    assert.deepStrictEqual(
      computeTripped([added('great_expectations/datasource/fluent/duckdb_datasource.py')]).length, 1);
  });
  check('a fluent file that is not *_datasource.py does not trip', function () {
    assert.deepStrictEqual(
      computeTripped([added('great_expectations/datasource/fluent/config.py')]), []);
    assert.deepStrictEqual(
      computeTripped([added('great_expectations/datasource/fluent/duckdb_asset.py')]), []);
  });
  check('a _test.py suffix does not trip', function () {
    assert.deepStrictEqual(
      computeTripped([added('great_expectations/datasource/fluent/duckdb_datasource_test.py')]), []);
  });
  check('a nested subdirectory does not trip', function () {
    assert.deepStrictEqual(
      computeTripped([added('great_expectations/datasource/fluent/sql/duckdb_datasource.py')]), []);
  });
  check('an uppercase or hyphenated stem does not trip', function () {
    assert.deepStrictEqual(
      computeTripped([added('great_expectations/datasource/fluent/DuckDB_datasource.py')]), []);
    assert.deepStrictEqual(
      computeTripped([added('great_expectations/datasource/fluent/duck-db_datasource.py')]), []);
  });
  check('the tripped entry is exactly "<filename> — <describe>"', function () {
    var t = computeTripped([added('great_expectations/datasource/fluent/duckdb_datasource.py')]);
    assert.strictEqual(
      t[0],
      'great_expectations/datasource/fluent/duckdb_datasource.py — a new fluent datasource');
  });
})();

console.log('signal 3: new backend requirements file');
(function () {
  check('requirements-dev-<backend>.txt trips', function () {
    assert.deepStrictEqual(computeTripped([added('reqs/requirements-dev-duckdb.txt')]).length, 1);
  });
  check('a hyphenated backend segment trips', function () {
    assert.deepStrictEqual(
      computeTripped([added('reqs/requirements-dev-spark-connect.txt')]).length, 1);
  });
  check('reqs/requirements-dev.txt (no backend segment) does not trip', function () {
    assert.deepStrictEqual(computeTripped([added('reqs/requirements-dev.txt')]), []);
  });
  check('an underscore in the backend segment does not trip', function () {
    assert.deepStrictEqual(computeTripped([added('reqs/requirements-dev-spark_connect.txt')]), []);
  });
  check('an uppercase backend segment does not trip', function () {
    assert.deepStrictEqual(computeTripped([added('reqs/requirements-dev-DuckDB.txt')]), []);
  });
  check('a different extension does not trip', function () {
    assert.deepStrictEqual(computeTripped([added('reqs/requirements-dev-duckdb.txt.bak')]), []);
  });
  check('an empty backend segment does not trip', function () {
    assert.deepStrictEqual(computeTripped([added('reqs/requirements-dev-.txt')]), []);
  });
  check('the same filename outside reqs/ does not trip', function () {
    assert.deepStrictEqual(computeTripped([added('docs/reqs/requirements-dev-duckdb.txt')]), []);
  });
  check('the tripped entry is exactly "<filename> — <describe>"', function () {
    var t = computeTripped([added('reqs/requirements-dev-duckdb.txt')]);
    assert.strictEqual(
      t[0], 'reqs/requirements-dev-duckdb.txt — a new backend requirements file');
  });
})();

console.log('added-files-only rule');
(function () {
  ['modified', 'removed', 'renamed', 'changed', 'copied'].forEach(function (status) {
    check('a matching file with status "' + status + '" does not trip', function () {
      assert.deepStrictEqual(
        computeTripped([{ filename: TRIPPING_FILE, status: status }]), []);
    });
  });
  check('only the added file trips when mixed with non-added matches', function () {
    var t = computeTripped([
      { filename: 'great_expectations/compatibility/sqlalchemy.py', status: 'modified' },
      { filename: 'reqs/requirements-dev-duckdb.txt', status: 'removed' },
      added('great_expectations/datasource/fluent/duckdb_datasource.py'),
    ]);
    assert.strictEqual(t.length, 1);
    assert.ok(t[0].indexOf('duckdb_datasource.py') !== -1, t[0]);
  });
  check('several added matches all trip', function () {
    var t = computeTripped([
      added('great_expectations/compatibility/duckdb.py'),
      added('reqs/requirements-dev-duckdb.txt'),
      added('docs/whatever.md'),
    ]);
    assert.strictEqual(t.length, 2);
  });
})();

console.log('HTML-comment stripping of the PR body');
(function () {
  check('an unedited template whose comment carries "RFC:" does not count as declared', function () {
    var r = evaluateRfc(trippedOnce(), { body: TEMPLATE_COMMENT + '\nSome description.\n' });
    assert.strictEqual(r.rfcFailed, true);
  });
  check('"No RFC needed:" inside a comment does not count either', function () {
    var r = evaluateRfc(trippedOnce(), { body: '<!--\nNo RFC needed: because\n-->\ntext' });
    assert.strictEqual(r.rfcFailed, true);
  });
  check('a real declaration outside the template comment still counts', function () {
    var r = evaluateRfc(trippedOnce(), {
      body: TEMPLATE_COMMENT + '\nRFC: https://github.com/fivetran/great_expectations/issues/1\n',
    });
    assert.strictEqual(r.rfcFailed, false);
  });
  check('a multi-line comment is stripped whole', function () {
    var r = evaluateRfc(trippedOnce(), { body: '<!--\nRFC: nope\nmore\n-->\nnothing here' });
    assert.strictEqual(r.rfcFailed, true);
  });
})();

console.log('declaration forms that must count');
(function () {
  var accepted = [
    ['plain RFC', 'RFC: https://example.com/rfc'],
    ['plain No RFC needed', 'No RFC needed: this is a bug fix'],
    ['dash list marker', '- RFC: https://example.com/rfc'],
    ['star list marker', '* RFC: https://example.com/rfc'],
    ['plus list marker', '+ No RFC needed: bug fix'],
    ['numbered list "1."', '1. RFC: https://example.com/rfc'],
    ['numbered list "1)"', '1) No RFC needed: bug fix'],
    ['blockquote', '> RFC: https://example.com/rfc'],
    ['blockquote + list marker', '> - RFC: https://example.com/rfc'],
    ['bold', '**RFC**: https://example.com/rfc'],
    ['bold No RFC needed', '**No RFC needed**: bug fix'],
    ['underscore emphasis', '_RFC_: https://example.com/rfc'],
    ['code ticks', '`RFC: https://example.com/rfc`'],
    ['leading whitespace', '    RFC: https://example.com/rfc'],
    ['lowercase', 'rfc: https://example.com/rfc'],
    ['lowercase No RFC needed', 'no rfc needed: bug fix'],
    ['uppercase No RFC needed', 'NO RFC NEEDED: bug fix'],
    ['space before the colon', 'RFC : https://example.com/rfc'],
    ['on a later line of a multi-line body', 'Adds DuckDB support.\n\n- RFC: https://example.com/rfc\n'],
  ];
  accepted.forEach(function (pair) {
    check('declared: ' + pair[0], function () {
      var r = evaluateRfc(trippedOnce(), { body: pair[1] });
      assert.strictEqual(r.rfcFailed, false, 'expected declared for body: ' + JSON.stringify(pair[1]));
      assert.deepStrictEqual(r.failures, []);
    });
  });
})();

console.log('declaration forms that must NOT count');
(function () {
  var rejected = [
    ['token mid-sentence in prose', 'Discussed in the RFC: thread linked from the issue.'],
    ['token mid-sentence after a list marker', '- We agreed in the RFC: thread that this was fine.'],
    ['no colon', 'RFC https://example.com/rfc'],
    ['unrelated prose only', 'Adds DuckDB support. See the issue for background.'],
    ['empty body', ''],
    ['whitespace-only body', '   \n\n  '],
    ['null body', null],
    ['undefined body', undefined],
  ];
  rejected.forEach(function (pair) {
    check('not declared: ' + pair[0], function () {
      var r = evaluateRfc(trippedOnce(), { body: pair[1] });
      assert.strictEqual(r.rfcFailed, true,
        'expected NOT declared for body: ' + JSON.stringify(pair[1]));
    });
  });
})();

console.log('overall decision');
(function () {
  check('tripped signals + no declaration => failure with an explanatory message', function () {
    var t = computeTripped([
      added('great_expectations/compatibility/duckdb.py'),
      added('reqs/requirements-dev-duckdb.txt'),
    ]);
    var r = evaluateRfc(t, { body: 'Adds DuckDB support.' });
    assert.strictEqual(r.rfcFailed, true);
    assert.strictEqual(r.failures.length, 1);
    assert.ok(r.failures[0].indexOf('may cross the RFC threshold') !== -1);
    assert.ok(r.failures[0].indexOf('great_expectations/compatibility/duckdb.py') !== -1);
    assert.ok(r.failures[0].indexOf('reqs/requirements-dev-duckdb.txt') !== -1);
  });
  check('each tripped file is listed on its own indented line', function () {
    var t = computeTripped([
      added('great_expectations/compatibility/duckdb.py'),
      added('reqs/requirements-dev-duckdb.txt'),
    ]);
    var r = evaluateRfc(t, { body: 'Adds DuckDB support.' });
    assert.ok(
      r.failures[0].indexOf('\n  - great_expectations/compatibility/duckdb.py — ') !== -1,
      JSON.stringify(r.failures[0]));
    assert.ok(
      r.failures[0].indexOf('\n  - reqs/requirements-dev-duckdb.txt — ') !== -1,
      JSON.stringify(r.failures[0]));
  });
  check('tripped signals + declaration => pass, no failures', function () {
    var t = computeTripped([added('great_expectations/compatibility/duckdb.py')]);
    var r = evaluateRfc(t, { body: 'Adds DuckDB support.\n\nRFC: https://example.com/rfc' });
    assert.strictEqual(r.rfcFailed, false);
    assert.deepStrictEqual(r.failures, []);
  });
  check('no tripped signals + no declaration => pass, no failures', function () {
    var t = computeTripped([
      { filename: 'great_expectations/compatibility/sqlalchemy.py', status: 'modified' },
      added('docs/whatever.md'),
      added('tests/test_something.py'),
    ]);
    assert.deepStrictEqual(t, []);
    var r = evaluateRfc(t, { body: 'Doc tweak.' });
    assert.strictEqual(r.rfcFailed, false);
    assert.deepStrictEqual(r.failures, []);
  });
  check('no tripped signals + empty body => pass', function () {
    var r = evaluateRfc([], { body: '' });
    assert.strictEqual(r.rfcFailed, false);
    assert.deepStrictEqual(r.failures, []);
  });
})();

console.log('deliberate accepts (the check asks only that the question was answered)');
(function () {
  // These three all satisfy the check. That is the intended reading of the workflow's own
  // header comment: it "only enforces that the question was answered, never what the answer
  // is". Pinned here so a future tightening is a deliberate decision rather than drift.
  check('a bare "RFC:" with no link is accepted (a maintainer judges the answer)', function () {
    var r = evaluateRfc(trippedOnce(), { body: 'RFC:' });
    assert.strictEqual(r.rfcFailed, false);
  });
  check('a bare "No RFC needed:" with no reason is accepted', function () {
    var r = evaluateRfc(trippedOnce(), { body: 'No RFC needed:' });
    assert.strictEqual(r.rfcFailed, false);
  });
  check('a declaration inside a fenced code block is accepted', function () {
    var r = evaluateRfc(trippedOnce(), { body: '```\nRFC: https://example.com/rfc\n```' });
    assert.strictEqual(r.rfcFailed, false);
  });
  check('quoting the bot\'s own comment back is accepted', function () {
    var quoted = buildCommentBody({ user: { login: 'contributor' } }, trippedOnce())
      .split('\n').map(function (l) { return '> ' + l; }).join('\n');
    var r = evaluateRfc(trippedOnce(), { body: quoted });
    assert.strictEqual(r.rfcFailed, false);
  });
})();

console.log('guiding comment: body');
(function () {
  var tripped = computeTripped([
    added('great_expectations/compatibility/duckdb.py'),
    added('reqs/requirements-dev-duckdb.txt'),
  ]);
  var body = buildCommentBody({ user: { login: 'contributor' } }, tripped);
  check('is a non-empty string', function () {
    assert.ok(typeof body === 'string' && body.length > 0);
  });
  check('mentions the pull-request author', function () {
    assert.ok(body.indexOf('@contributor') !== -1);
  });
  check('carries the idempotence marker', function () {
    assert.ok(body.indexOf('<!-- pr-hygiene:rfc-threshold -->') !== -1);
    assert.ok(body.indexOf(MARKER) !== -1);
  });
  check('lists each tripped file as its own code-ticked bullet', function () {
    tripped.forEach(function (t) {
      assert.ok(body.indexOf('\n- `' + t + '`') !== -1, JSON.stringify(t));
    });
  });
  check('links CONTRIBUTING.md\'s RFC section', function () {
    assert.ok(body.indexOf(
      'https://github.com/fivetran/great_expectations/blob/develop/' +
      'CONTRIBUTING.md#requesting-comment-on-larger-changes') !== -1);
  });
})();

console.log('guiding comment: idempotence predicate');
(function () {
  check('a prior comment carrying the marker suppresses a second comment', function () {
    var comments = [
      { body: 'unrelated review chatter' },
      { body: 'Thanks for the pull request!\n\n' + MARKER },
    ];
    assert.strictEqual(alreadyCommented(comments), true);
  });
  check('comments without the marker do not suppress', function () {
    assert.strictEqual(alreadyCommented([{ body: 'looks good to me' }]), false);
  });
  check('no comments at all does not suppress', function () {
    assert.strictEqual(alreadyCommented([]), false);
  });
  check('a body-less comment does not throw and does not suppress', function () {
    assert.strictEqual(alreadyCommented([{ body: null }, { body: undefined }, {}]), false);
  });
  check('a freshly built comment body would suppress a repeat of itself', function () {
    var body = buildCommentBody({ user: { login: 'contributor' } }, trippedOnce());
    assert.strictEqual(alreadyCommented([{ body: body }]), true);
  });
})();

console.log('end-to-end: the remediation lines the bot prints satisfy the check');
(function () {
  // The whole point of the loosened DECLARED regexes: a contributor who pastes a
  // remediation line out of the bot's comment verbatim must satisfy the check. These
  // lines are *derived* from the mirrored builder, not re-typed, so rewording them in
  // pr-hygiene.yml without also loosening DECLARED breaks this test.
  var commentBody = buildCommentBody({ user: { login: 'contributor' } }, trippedOnce());
  var lines = commentBody.split('\n');
  var start = lines.findIndex(function (l) {
    return l.indexOf('**To resolve this check**') !== -1;
  });
  var remediation = lines.slice(start + 1).filter(function (l) { return /^\s*-\s/.test(l); });

  check('the comment offers exactly two remediation bullets', function () {
    assert.strictEqual(remediation.length, 2, JSON.stringify(remediation));
  });
  check('the first is the RFC form, the second the "No RFC needed" form', function () {
    assert.ok(/RFC\s*:/i.test(remediation[0]), JSON.stringify(remediation[0]));
    assert.ok(/No RFC needed\s*:/i.test(remediation[1]), JSON.stringify(remediation[1]));
  });
  remediation.forEach(function (line, i) {
    check('pasting remediation line ' + (i + 1) + ' verbatim satisfies the check', function () {
      var r = evaluateRfc(trippedOnce(), { body: line });
      assert.strictEqual(r.rfcFailed, false,
        'the bot asked for this line but the check rejects it: ' + JSON.stringify(line));
    });
    check('pasting remediation line ' + (i + 1) + ' into a longer description works', function () {
      var r = evaluateRfc(trippedOnce(), {
        body: 'Adds DuckDB support.\n\n## Checklist\n\n' + line + '\n\nThanks!',
      });
      assert.strictEqual(r.rfcFailed, false, JSON.stringify(line));
    });
  });
})();

console.log('\n' + passed + ' passed, ' + failures + ' failed');
process.exit(failures ? 1 : 0);
