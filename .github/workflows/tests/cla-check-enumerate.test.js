/**
 * Repeatable check of cla-check.yml's inline `github-script` logic: the PR-head
 * commit-enumeration transform and the guiding-comment body builder.
 *
 * cla-check.yml has no checkout step (by design -- see the workflow's own header
 * comment), so its inline scripts can't require() shared logic live. The functions
 * below are byte-identical mirrors of what's actually inline in cla-check.yml, kept
 * here purely so a plain Node test can exercise them; this file is never loaded by
 * the real workflow. The workflow carries the enumeration transform and the
 * comment-body transform twice (once in the `cla-check` job, once in `cla-recheck`)
 * as intentionally identical copies -- no checkout means no shared `require()`
 * across jobs -- so mirroring either copy here covers both.
 *
 * Run: node .github/workflows/tests/cla-check-enumerate.test.js
 */
'use strict';

var assert = require('assert');

// --- mirror of cla-check.yml's enumeration transform (verbatim) -----------------
// Copied from the `cla-check` job's "Enumerate PR committers" step (identical to
// the `cla-recheck` job's copy). Takes the paginated `commits` array and the PR's
// own reported `pr.commits` count.
function enumerate(commits, pr) {
  const enumerationComplete = pr.commits <= commits.length;
  const logins = [...new Set(commits.map(c => c.author && c.author.login).filter(Boolean))];
  const unidentified = commits.filter(c => !(c.author && c.author.login)).map(c => c.sha);
  return { enumerationComplete, logins, unidentified };
}
// --- end mirror -------------------------------------------------------------------

// --- mirror of cla-check.yml's guiding-comment body transform (verbatim) --------
// Copied from the `cla-check` job's "Build guiding comment body" step (identical to
// the `cla-recheck` job's copy).
function buildCommentBody(unsigned, unidentified) {
  const sections = [];
  if (unsigned.length > 0) {
    const mentions = unsigned.map((login) => `@${login}`).join(', ');
    sections.push(
      `We could not find a signed CLA for: ${mentions}. Please sign the ` +
      '[Individual Contributor License Agreement](https://forms.gle/wvregSivqgAaJNEX8), ' +
      'or the [Software Grant and Corporate Contributor License Agreement]' +
      '(https://forms.gle/6viSVNxZjui9Vhi29) if you are contributing on behalf of your ' +
      'employer (see [CLA.md](https://github.com/fivetran/great_expectations/blob/develop/CLA.md) ' +
      'for details).'
    );
  }
  if (unidentified.length > 0) {
    const refs = unidentified.map((sha) => `\`${String(sha).substring(0, 7)}\``).join(', ');
    sections.push(
      `We were unable to identify the GitHub account for the following commit(s): ${refs}. ` +
      'Please make sure the email address on your commits is linked to your GitHub account.'
    );
  }
  if (sections.length === 0) {
    // Enumeration-incomplete case: state is `error` with neither list populated.
    // Keep the comment non-empty and honest about why.
    sections.push('We were unable to fully verify the CLA status for this pull request.');
  }

  const body = [
    'Thank you for your contribution! Before we can merge this pull request, every ' +
    'committer needs to have signed our Contributor License Agreement (CLA).',
    ...sections,
    'Once resolved, comment `@cla-bot check` on this pull request to re-run the check.',
  ].join('\n\n');

  return body;
}
// --- end mirror -------------------------------------------------------------------

var failures = 0;
var passed = 0;
function check(name, fn) {
  try { fn(); passed++; console.log('  ok   - ' + name); }
  catch (e) { failures++; console.log('  FAIL - ' + name + '\n         ' + e.message); }
}

function commit(sha, login) {
  return { sha: sha, author: login ? { login: login } : null };
}

console.log('enumeration: normal PR, full enumeration');
(function () {
  var commits = [commit('sha1', 'alice'), commit('sha2', 'bob'), commit('sha3', 'alice')];
  var pr = { commits: 3 };
  var result = enumerate(commits, pr);
  check('enumerationComplete is true when pr.commits === commits.length', function () {
    assert.strictEqual(result.enumerationComplete, true);
  });
  check('logins is the deduped set of resolvable logins', function () {
    assert.deepStrictEqual(result.logins, ['alice', 'bob']);
  });
  check('unidentified is empty', function () {
    assert.deepStrictEqual(result.unidentified, []);
  });
})();

console.log('enumeration: truncated PR (simulated 250-commit cap)');
(function () {
  var commits = [commit('sha1', 'alice')];
  var pr = { commits: 300 };
  var result = enumerate(commits, pr);
  check('enumerationComplete is false when pr.commits exceeds the returned set', function () {
    assert.strictEqual(result.enumerationComplete, false);
  });
})();

console.log('enumeration: unidentified commit collected by SHA, not email/name');
(function () {
  var commits = [
    { sha: 'deadbeef', author: null },
    { sha: 'cafefeed', author: {} },
  ];
  var pr = { commits: 2 };
  var result = enumerate(commits, pr);
  check('unidentified lists the SHAs of unresolvable commits', function () {
    assert.deepStrictEqual(result.unidentified, ['deadbeef', 'cafefeed']);
  });
  check('logins is empty when no commit has a resolvable login', function () {
    assert.deepStrictEqual(result.logins, []);
  });
})();

console.log('enumeration: duplicate logins across commits dedupe to one entry');
(function () {
  var commits = [commit('sha1', 'alice'), commit('sha2', 'alice'), commit('sha3', 'alice')];
  var pr = { commits: 3 };
  var result = enumerate(commits, pr);
  check('logins contains "alice" exactly once', function () {
    assert.deepStrictEqual(result.logins, ['alice']);
  });
})();

console.log('comment body: both unsigned and unidentified non-empty');
(function () {
  var body = buildCommentBody(['alice', 'bob'], ['deadbeef']);
  check('is a non-empty string', function () {
    assert.ok(typeof body === 'string' && body.length > 0);
  });
  check('mentions each unsigned login', function () {
    assert.ok(body.indexOf('@alice') !== -1);
    assert.ok(body.indexOf('@bob') !== -1);
  });
  check('includes both CLA form links', function () {
    assert.ok(body.indexOf('https://forms.gle/wvregSivqgAaJNEX8') !== -1);
    assert.ok(body.indexOf('https://forms.gle/6viSVNxZjui9Vhi29') !== -1);
  });
  check('mentions the unidentified commit by its short SHA', function () {
    assert.ok(body.indexOf('deadbee') !== -1);
  });
  check('always includes the recheck instruction', function () {
    assert.ok(body.indexOf('@cla-bot check') !== -1);
  });
})();

console.log('comment body: only unsigned committers');
(function () {
  var body = buildCommentBody(['alice'], []);
  check('mentions the unsigned login and form links', function () {
    assert.ok(body.indexOf('@alice') !== -1);
    assert.ok(body.indexOf('https://forms.gle/wvregSivqgAaJNEX8') !== -1);
  });
  check('does not include the unidentified-committer section', function () {
    assert.ok(body.indexOf('unable to identify the GitHub account') === -1);
  });
  check('always includes the recheck instruction', function () {
    assert.ok(body.indexOf('@cla-bot check') !== -1);
  });
})();

console.log('comment body: only unidentified committers');
(function () {
  var body = buildCommentBody([], ['cafefeed']);
  check('mentions the unidentified commit by its short SHA', function () {
    assert.ok(body.indexOf('cafefee') !== -1);
  });
  check('does not include the unsigned-committer section', function () {
    assert.ok(body.indexOf('could not find a signed CLA') === -1);
  });
  check('always includes the recheck instruction', function () {
    assert.ok(body.indexOf('@cla-bot check') !== -1);
  });
})();

console.log('comment body: enumeration-incomplete fallback (both lists empty)');
(function () {
  var body = buildCommentBody([], []);
  check('falls back to the enumeration-incomplete sentence', function () {
    assert.ok(body.indexOf('unable to fully verify the CLA status') !== -1);
  });
  check('is still a non-empty, well-formed string', function () {
    assert.ok(typeof body === 'string' && body.length > 0);
  });
  check('always includes the recheck instruction', function () {
    assert.ok(body.indexOf('@cla-bot check') !== -1);
  });
})();

console.log('\n' + passed + ' passed, ' + failures + ' failed');
process.exit(failures ? 1 : 0);
